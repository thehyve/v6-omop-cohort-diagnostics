"""
This file contains all algorithm pieces that are executed on the nodes.
It is important to note that the central method is executed on a node, just
like any other method.

The results in a return statement are sent to the central vantage6 server after
encryption (if that is enabled).
"""
import os
import jwt
import pandas as pd

from functools import wraps
from dataclasses import dataclass
from pathlib import Path
from vantage6.algorithm.tools.util import info, warn
from vantage6.algorithm.tools.decorators import database_connection
# from vantage6.algorithm.tools.decorators import algorithm_client
# from vantage6.algorithm.client import AlgorithmClient

from ohdsi import circe
from ohdsi import cohort_generator
from ohdsi import common as ohdsi_common
from ohdsi import feature_extraction
from ohdsi import cohort_diagnostics

from rpy2.robjects import RS4


@dataclass
class RunMetaData():
    """Dataclass containing metadata of the run."""
    task_id: int | None
    node_id: int | None
    collaboration_id: int | None
    organization_id: int | None
    temporary_directory: Path | None
    output_file: Path | None
    input_file: Path | None
    token_file: Path | None


@dataclass
class OMOPMetaData():
    """Dataclass containing metadata of the OMOP database."""
    database: str | None
    cdm_schema: str | None
    results_schema: str | None
    incremental_folder: Path | None
    cohort_statistics_folder: Path | None
    export_folder: Path | None


def metadata(type_: str = "run") -> callable:
    """
    Decorator to add run metadata to the algorithm.

    These items should always be present at either the node environment vars,
    or in the token payload.

    Example
    -------
    >>> @metadata()
    >>> def my_algorithm(metadata: RunMetaData, <other arguments>):
    >>>     pass
    """
    match type_.lower():
        case "run":
            return run_metadata
        case "omop":
            return omop_metadata
        case _:
            info(f"Unknown metadata type: {type_}. Exiting.")
            exit(1)


def run_metadata(func: callable, *args, **kwargs) -> callable:
    @wraps(func)
    def decorator(*args, **kwargs) -> callable:
        """
        Wrap the function with metadata from the run.
        """
        token_file = os.environ["TOKEN_FILE"]
        info("Reading token")
        with open(token_file) as fp:
            token = fp.read().strip()

        info("Extracting payload from token")
        payload = extract_payload(token)

        metadata = RunMetaData(
            task_id=payload["task_id"],
            node_id=payload["node_id"],
            collaboration_id=payload["collaboration_id"],
            organization_id=payload["organization_id"],
            temporary_directory=Path(os.environ["TEMPORARY_FOLDER"]),
            output_file=Path(os.environ["OUTPUT_FILE"]),
            input_file=Path(os.environ["INPUT_FILE"]),
            token_file=Path(os.environ["TOKEN_FILE"])
        )
        return func(metadata, *args, **kwargs)
    return decorator


def omop_metadata(func: callable, *args, **kwargs) -> callable:
    @wraps(func)
    def decorator(*args, **kwargs) -> callable:
        """
        Wrap the function with metadata from the OMOP database.

        The following environment variables are expected to be set in the
        node configuration:
        - CDM_DATABASE
        - CDM_SCHEMA
        - RESULTS_SCHEMA

        In case these are not set, the `None` value are returned.
        """
        # check that all node environment variables are set
        expected_env_vars = ["CDM_DATABASE", "CDM_SCHEMA", "RESULTS_SCHEMA"]
        if not all((key.upper() in os.environ for key in expected_env_vars)):
            warn("Missing settings in the node configuration.")
            warn("This can result an algorithm crash if dependent on these.")
            warn("Will continue with the missing settings...")

        tmp = Path(os.environ["TEMPORARY_FOLDER"])
        metadata = OMOPMetaData(
            database=os.environ.get("CDM_DATABASE"),
            cdm_schema=os.environ.get("CDM_SCHEMA"),
            results_schema=os.environ.get("RESULTS_SCHEMA"),
            incremental_folder=tmp / "incremental",
            cohort_statistics_folder=tmp / "cohort_statistics",
            export_folder=tmp / "export"
        )
        return func(metadata, *args, **kwargs)
    return decorator


def extract_payload(token: str) -> dict:
    """
    Extract the payload from the token.

    Parameters
    ----------
    token: str
        The token as a string.

    Returns
    -------
    dict
        The payload as a dictionary. It contains the keys: `client_type`,
        `node_id`, `organization_id`, `collaboration_id`, `task_id`, `image`,
        and `databases`
    """
    jwt_payload = jwt.decode(token, options={"verify_signature": False})
    return jwt_payload['sub']


@database_connection(type="OMOP")
@metadata("omop")
@metadata("run")
def central(meta_run: RunMetaData, meta_omop: OMOPMetaData, connection: RS4,
            cohort_definitions: dict, cohort_names: list[str],
            temporal_covariate_settings: dict, diagnostics_settings: dict) \
                -> pd.DataFrame:
    """Central part of the algorithm."""

    # Generate unique cohort ids, based on the task id and the number of files.
    # The first six digits are the task id, the last three digits are the index
    # of the file.
    n = len(cohort_definitions)
    cohort_definition_set = pd.DataFrame(
        {
            'cohortId': [float(f'{meta_run.task_id:06d}{i:03d}') for i in
                         range(0, n)],
            'cohortName': cohort_names,
            'json': cohort_definitions,
            'sql': [create_cohort_query(cohort) for cohort in
                    cohort_definitions],
            'logicDescription': [None] * n,
            'generateStats': [True] * n,
        }
    )
    info(f"Generated {n} cohort definitions")

    # Generate the table names for the cohort tables
    cohort_table = f'cohort_{meta_run.task_id}'
    cohort_table_names = cohort_generator.get_cohort_table_names(cohort_table)
    info(f"Cohort table name: {cohort_table}")
    info(f"Tables: {cohort_table_names}")

    # Create the tables in the database
    info(f"OMOP results schema: {meta_omop.results_schema}")
    cohort_generator.create_cohort_tables(
        connection=connection,
        cohort_database_schema=meta_omop.results_schema,
        cohort_table_names=cohort_table_names)
    info("Created cohort tables")

    # Generate the cohort set
    cohort_definition_set = ohdsi_common.convert_to_r(cohort_definition_set)
    cohort_generator.generate_cohort_set(
        connection=connection,
        cdm_database_schema=meta_omop.cdm_schema,
        cohort_database_schema=meta_omop.results_schema,
        cohort_table_names=cohort_table_names,
        cohort_definition_set=cohort_definition_set
    )
    info("Generated cohort set")

    temporal_covariate_settings = \
        feature_extraction.create_temporal_covariate_settings(
            **temporal_covariate_settings)
    info("Created temporal covariate settings")

    cohort_diagnostics.execute_diagnostics(
        cohort_definition_set=cohort_definition_set,
        export_folder=str(meta_omop.export_folder / 'exports'),
        database_id=meta_run.task_id,
        database_name=f"{meta_run.task_id:06d}",
        database_description='todo',
        cohort_database_schema=meta_omop.results_schema,
        connection=connection,
        cdm_database_schema=meta_omop.cdm_schema,
        cohort_table=cohort_table,
        cohort_table_names=cohort_table_names,
        vocabulary_database_schema=meta_omop.cdm_schema,
        cohort_ids=None,
        cdm_version=5,
        temporal_covariate_settings=temporal_covariate_settings,
        **diagnostics_settings
        # min_cell_count=min_cell_count,
        # incremental=False, #default was True
        # incremental_folder=my_params['incremental_folder']
    )
    info("Executed diagnostics")

    # Read back the CSV file with the results
    # TODO: check URL
    df = pd.read_csv(meta_omop.export_folder / 'exports' /
                     "incidence_rate.csv")

    return df.to_json()


def create_cohort_query(cohort_definition: dict) -> str:
    """
    Creates a cohort query from a cohort definition in JSON format.

    Parameters
    ----------
    cohort_definition: dict
        The cohort definition in JSON format, for example created from ATLAS.

    Returns
    -------
    str
        The cohort query.
    """
    cohort_expression = circe.cohort_expression_from_json(cohort_definition)
    options = circe.create_generate_options(generate_stats=True)
    return circe.build_cohort_query(cohort_expression, options)[0]

