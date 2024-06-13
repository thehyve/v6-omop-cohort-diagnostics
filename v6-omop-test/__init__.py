"""
This file contains all algorithm pieces that are executed on the nodes.
It is important to note that the main method is executed on a node, just
like any other method.

The results in a return statement are sent to the central vantage6 server after
encryption (if that is enabled for the collaboration).
"""
import base64
import pandas as pd

from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import (
    algorithm_client,
    AlgorithmClient,
    database_connection,
    metadata,
    RunMetaData,
    OHDSIMetaData,
)

from ohdsi import circe
from ohdsi import cohort_generator
from ohdsi import common as ohdsi_common
from ohdsi import feature_extraction
from ohdsi import cohort_diagnostics as ohdsi_cohort_diagnostics

from rpy2.robjects import RS4


@algorithm_client
def central(
    client: AlgorithmClient,
    cohort_definitions: dict,
    cohort_names: list[str],
    meta_cohorts: list[dict],
    temporal_covariate_settings: dict,
    diagnostics_settings: dict,
    min_cell_count=5,
    organizations_to_include="ALL",
) -> list[pd.DataFrame]:
    """
    Executes the central algorithm on the specified client and returns the results.

    Parameters
    ----------
    client : AlgorithmClient
        Interface to the central server. This is supplied by the wrapper.
    cohort_definitions : dict
        A dictionary containing the cohort definitions from ATLAS.
    cohort_names : list[str]
        A list of cohort names.
    temporal_covariate_settings : dict
        A dictionary containing the temporal covariate settings.
    diagnostics_settings : dict
        A dictionary containing the diagnostics settings.
    organizations_to_include : str, optional
        The organizations to include. Defaults to 'ALL'.

    Returns
    -------
    list[pd.DataFrame]
        A list of pandas DataFrames containing the results.
    """
    info("Collecting participating organizations")
    # obtain organizations for which to run the algorithm
    organizations = client.organization.list()
    ids = [org["id"] for org in organizations]
    if organizations_to_include != "ALL":
        # check that organizations_to_include is a subset of ids, so we can return
        # a nice error message. The server can also return an error, but this is
        # more user friendly.
        if not set(organizations_to_include).issubset(set(ids)):
            return {
                "msg": "You specified an organization that is not part of the "
                "collaboration"
            }
        ids = organizations_to_include

    # This requests the cohort diagnostics to be computed on all nodes
    info("Requesting partial computation")
    task = client.task.create(
        input_={
            "method": "cohort_diagnostics",
            "kwargs": {
                "meta_cohorts": meta_cohorts,
                "cohort_definitions": cohort_definitions,
                "cohort_names": cohort_names,
                "temporal_covariate_settings": temporal_covariate_settings,
                "diagnostics_settings": diagnostics_settings,
                "min_cell_count": min_cell_count,
            },
        },
        organizations=ids,
    )
    info(f'Task assigned, id: {task.get("id")}')

    # This function is blocking until the results from all nodes are in
    info("Waiting for results")
    all_results = client.wait_for_results(task_id=task["id"])

    info("Results received, sending them back to server")
    return all_results


@metadata
@database_connection(types=["OMOP"], include_metadata=True)
def cohort_diagnostics(
    connection: RS4,
    meta_omop: OHDSIMetaData,
    meta_run: RunMetaData,
    meta_cohorts: list[dict],
    cohort_definitions: dict,
    cohort_names: list[str],
    temporal_covariate_settings: dict,
    diagnostics_settings: dict,
    min_cell_count: int
) -> pd.DataFrame:
    """Computes the OHDSI cohort diagnostics."""

    # Generate unique cohort ids, based on the task id and the number of files.
    # The first six digits are the task id, the last three digits are the index
    # of the file.
    n = len(cohort_definitions)
    shared_ids = []
    cohort_ids = []
    for i in range(0, n):
        # These are the IDs to be shared with the user and should be identical for all
        # nodes that participate
        task_id = meta_cohorts[0]['task_id']
        temp_id = f"{task_id:04d}{i:03d}"
        shared_ids.append(temp_id)
        # The node id is appended at runtim by the node itself
        cohort_ids.append(float(f"{meta_run.node_id}{temp_id}"))

    info(f"Full local cohort ids: {cohort_ids}")
    info(f"Shared cohort ids: {shared_ids}")

    cohort_definition_set = pd.DataFrame(
        {
            "cohortId": cohort_ids,
            "cohortName": cohort_names,
            "json": cohort_definitions,
            "sql": [_create_cohort_query(cohort) for cohort in cohort_definitions],
            "logicDescription": [None] * n,
            "generateStats": [True] * n,
        }
    )
    cohort_definition_set = ohdsi_common.convert_to_r(cohort_definition_set)
    info(f"Generated {n} cohort definitions")

    # Generate the table names for the cohort tables
    cohort_table = f"cohort_{task_id}_{meta_run.node_id}"
    cohort_table_names = cohort_generator.get_cohort_table_names(cohort_table)
    info(f"Cohort table name: {cohort_table}")
    info(f"Tables: {cohort_table_names}")

    temporal_covariate_settings = feature_extraction.create_temporal_covariate_settings(
        **temporal_covariate_settings
    )
    info("Created temporal covariate settings")

    database_name = f"{meta_run.task_id:06d}"
    ohdsi_cohort_diagnostics.execute_diagnostics(
        cohort_definition_set=cohort_definition_set,
        export_folder=str(meta_omop.export_folder / "exports"),
        database_id=task_id,
        database_name=database_name,
        database_description="todo",
        cohort_database_schema=meta_omop.results_schema,
        connection=connection,
        cdm_database_schema=meta_omop.cdm_schema,
        cohort_table=cohort_table,
        cohort_table_names=cohort_table_names,
        vocabulary_database_schema=meta_omop.cdm_schema,
        cohort_ids=None,
        cdm_version=5,
        temporal_covariate_settings=temporal_covariate_settings,
        **diagnostics_settings,
        min_cell_count=min_cell_count,
        # incremental=False, #default was True
        # incremental_folder=my_params['incremental_folder']
    )
    info("Executed diagnostics")

    # Read back the zip file with results
    file_ = meta_omop.export_folder / "exports" / f"Results_{task_id}.zip"
    with open(file_, 'rb') as f:
        contents = f.read()
    contents = base64.b64encode(contents).decode("UTF-8")

    return contents


def _create_cohort_query(cohort_definition: dict) -> str:
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
