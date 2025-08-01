import os
import sys
import json
import base64
import argparse
from pathlib import Path
from dotenv import load_dotenv

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run OMOP cohort diagnostics')
    parser.add_argument(
        '--output-path', 
        type=str, 
        default='./results',
        help='Path where results will be saved (default: ./results)'
    )
    parser.add_argument(
        '--output-filename',
        type=str,
        default='cohort_diagnostics_results.zip',
        help='Filename for the results zip file (default: cohort_diagnostics_results.zip)'
    )
    return parser.parse_args()

def main():
    """Main function to run the cohort diagnostics."""
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Parse command line arguments
        args = parse_arguments()

        # Create output directory if it doesn't exist
        output_path = Path(args.output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Results will be saved to: {output_path / args.output_filename}")

        # Import vantage6 client
        try:
            from vantage6.client import Client
        except ImportError:
            print("Error: vantage6 module not found. Please install it with: pip install vantage6")
            sys.exit(1)

        # Configure vantage6 client
        v6_api_url = os.getenv("V6_API_URL")
        v6_api_port = os.getenv("V6_API_PORT", "443")
        v6_api_path = os.getenv("V6_API_PATH", "/server/api")
        v6_api_user = os.getenv("V6_API_USER")
        v6_api_password = os.getenv("V6_API_PASSWORD")
        collaboration_id_str = os.getenv("COLLABORATION_ID")
        algorithm_image = os.getenv("ALGORITHM_IMAGE")
        organisations_ids_str = os.getenv("ORGANISATIONS_IDS")

        # Validate required environment variables
        required_vars = {
            "V6_API_URL": v6_api_url,
            "V6_API_USER": v6_api_user,
            "V6_API_PASSWORD": v6_api_password,
            "COLLABORATION_ID": collaboration_id_str,
            "ALGORITHM_IMAGE": algorithm_image,
            "ORGANISATIONS_IDS": organisations_ids_str
        }

        missing_vars = [var for var, value in required_vars.items() if value is None or value.strip() == ""]

        if missing_vars:
            print("Error: The following required environment variables are not set:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease set these variables in your .env file or as environment variables.")
            print("See README.md for more information about configuration.")
            sys.exit(1)

        # Parse validated environment variables
        organisations_to_include = [int(x.strip()) for x in organisations_ids_str.split(",")]
        collaboration_id = int(collaboration_id_str)

        # Authenticate to the vantage6 server
        print("Connecting to vantage6 server...")
        client = Client(v6_api_url, v6_api_port, v6_api_path, log_level="debug")
        client.authenticate(v6_api_user, v6_api_password)
        client.setup_encryption(None)
        print("Successfully connected and authenticated!")

        # Load the cohort definitions from a folder. These can be created using the ATLAS tool
        print("Loading cohort definitions...")
        folder_ = Path(r"./cohort_definitions/")
        if not folder_.exists():
            raise FileNotFoundError(f"Cohort definitions folder not found: {folder_}")

        files = list(folder_.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No JSON files found in cohort definitions folder: {folder_}")

        omop_jsons = [(file_).read_text() for file_ in files]
        names = [file_.stem for file_ in files]
        print(f"Loaded {len(files)} cohort definitions: {names}")

        result_json = execute_cohort_diagnostics(algorithm_image, client, collaboration_id, names, omop_jsons,
                                                 organisations_to_include)

        if result_json and 'data' in result_json and len(result_json['data']) > 0 and 'result' in result_json['data'][0]:
            print("Extracting zip data from results...")
            result_data = result_json['data'][0]['result']
            parsed_result = json.loads(result_data)

            if isinstance(parsed_result, list) and len(parsed_result) > 0 and 'zip' in parsed_result[0]:
                zip_data_encoded = parsed_result[0]['zip']
                zip_data = base64.b64decode(zip_data_encoded)
                output_file = output_path / args.output_filename
                with open(output_file, 'wb') as f:
                    f.write(zip_data)
                print(f"Results saved to: {output_file}")
            else:
                raise ValueError("No zip data found in parsed results")
        else:
            raise ValueError("No data found in results or invalid result structure")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)


def execute_cohort_diagnostics(algorithm_image, client, collaboration_id, names, omop_jsons, organisations_to_include):
    # Create covariate settings
    # To see all the available options please refer to the documentation of the
    # OHDSI package: https://ohdsi.github.io/FeatureExtraction/reference/createTemporalCovariateSettings.html.
    # Note that all arguments are converted from camelCase to snake_case
    temporal_covariate_settings = {
        "use_demographics_gender": True,
        "use_demographics_age": True,
        "use_demographics_age_group": True,
        "use_demographics_race": True,
        "use_demographics_ethnicity": True,
        "use_demographics_index_year": True,
        "use_demographics_index_month": True,
        "use_demographics_index_year_month": True,
        "use_demographics_prior_observation_time": True,
        "use_demographics_post_observation_time": True,
        "use_demographics_time_in_cohort": True,
        "use_condition_occurrence": True,
        "use_procedure_occurrence": True,
        "use_drug_era_start": True,
        "use_measurement": True,
        "use_condition_era_start": True,
        "use_condition_era_overlap": True,
        "use_condition_era_group_start": False,
        # do not use because https://github.com/ohdsi/feature_extraction/issues/144
        "use_condition_era_group_overlap": True,
        "use_drug_exposure": False,  # leads to too many concept id
        "use_drug_era_overlap": False,
        "use_drug_era_group_start": False,  # do not use because https://github.com/ohdsi/feature_extraction/issues/144
        "use_drug_era_group_overlap": True,
        "use_observation": True,
        "use_visit_concept_count": True,
        "use_visit_count": True,
        "use_device_exposure": True,
        "use_charlson_index": True,
        "use_dcsi": True,
        "use_chads2": True,
        "use_chads2_vasc": True,
        "use_hfrs": False,
        "temporal_start_days": [
            # components displayed in cohort characterization
            -9999,  # anytime prior
            -365,  # long term prior
            -180,  # medium term prior
            -30,  # short term prior
            # components displayed in temporal characterization
            -365,  # one year prior to -31
            -30,  # 30 day prior not including day 0
            0,  # index date only
            1,  # 1 day after to day 30
            31,
            -9999,  # any time prior to any time future
        ],
        "temporal_end_days": [
            0,  # anytime prior
            0,  # long term prior
            0,  # medium term prior
            0,  # short term prior
            # components displayed in temporal characterization
            -31,  # one year prior to -31
            -1,  # 30 day prior not including day 0
            0,  # index date only
            30,  # 1 day after to day 30
            365,
            9999,  # any time prior to any time future
        ],
    }
    # Execute cohort diagnostics settings
    # To see all the available options please refer to the documentation of the
    # OHDSI package: https://ohdsi.github.io/CohortDiagnostics/reference/executeDiagnostics.html
    diagnostics_settings = {
        "run_inclusion_statistics": True,
        "run_included_source_concepts": True,
        "run_orphan_concepts": True,
        "run_time_series": False,
        "run_visit_context": True,
        "run_breakdown_index_events": False,
        "run_incidence_rate": True,
        "run_cohort_relationship": True,
        "run_temporal_cohort_characterization": True,
    }
    # Create a new vantage6 task that executes the cohort diagnostics at all the
    # nodes that are part of the collaboration.
    print("Creating vantage6 task...")
    task = client.task.create(
        collaboration=collaboration_id,
        organizations=organisations_to_include,
        name="omop-test",
        description="@",
        input_={
            "method": "cohort_diagnostics_central",
            "kwargs": {
                "cohort_definitions": omop_jsons,
                "cohort_names": names,
                "temporal_covariate_settings": temporal_covariate_settings,
                "diagnostics_settings": diagnostics_settings,
                "meta_cohorts": [{"task_id": 13}],
            },
        },
        databases=[{"label": "omop"}],
        image=algorithm_image
    )
    task_id = task.get("id")
    print(f"Task created with ID: {task_id}")

    # Obtain the results
    print("Waiting for task results...")
    client.wait_for_results(task_id=task_id)
    print("Task completed!")

    result_info = client.result.from_task(task_id=task_id)
    print("Retrieved results from task.")
    return result_info


if __name__ == "__main__":
    main()
