import os
import sys
import json
import base64
import argparse
import subprocess
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
    parser.add_argument(
        '--prepare-r',
        action='store_true',  # This makes it a flag, e.g., --prepare-r
        help='Initialize an R environment for the OHDSI Diagnostics Explorer Shiny application.'
    )
    return parser.parse_args()


def prepare_r_environment(results_path: Path):
    """    Sets up the R environment for the OHDSI Diagnostics Explorer Shiny app.
    """
    print("\n--- Executing extra task: Prepare R --- ")
    print("Preparing R environment for the OHDSI Diagnostics Explorer viewer...")

    results_dir = results_path.parent.parent
    zip_filename = results_path.name
    r_dir_str = str(results_dir.resolve()).replace('\\', '/')

    # R code to be executed by Rscript
    r_script_content = f"""
    # Set the working directory to the directory containing the results zip
    print(paste("Setting working directory to:", "{r_dir_str}"))
    setwd("{r_dir_str}")
    
    # Bootstrap renv: install if not present, then initialize the environment
    if (!requireNamespace("renv", quietly = TRUE)) {{
        install.packages("renv")
    }}
    # Initialize the project-local environment, create 'renv' folder.
    renv::init()

    # Install specific packages into the renv project library
    print("Installing packages into the renv environment...")
    packages_to_install <- c(
        "remotes",
        "usethis",
        "shiny",
        "OHDSI/CohortDiagnostics@v3.2.5"
    )
    renv::install(packages_to_install)

    # Load CohortDiagnostics
    library(CohortDiagnostics)

    # Create the merged results file from the zip archive
    print(paste("Creating merged results file from:", "{zip_filename}"))
    CohortDiagnostics::createMergedResultsFile(dataFolder = './data', overwrite = TRUE)

    # Snapshot the dependencies to create renv.lock for reproducibility
    print("Snapshotting dependencies to renv.lock...")
    renv::snapshot()

    print("\\n renv environment created, data prepared, and lockfile saved!")
    """

    r_script_path = results_dir / "prepare_cohort_diagnostics.R"
    with open(r_script_path, "w") as f:
        f.write(r_script_content)

    try:
        print("Executing R setup script... (this can take several minutes on the first run)")
        process = subprocess.run(
            ["Rscript", str(r_script_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print("----- R SCRIPT OUTPUT -----")
        print(process.stdout)
        if process.stderr:
            print("----- R SCRIPT STDERR -----")
            print(process.stderr)
        print("----- END OF R SCRIPT LOGS ----- \n\n")

    except FileNotFoundError:
        print("\nError: 'Rscript' not found.")
        print("Please ensure R is installed and its bin directory is in your system's PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nError occurred during R script execution (Exit Code: {e.returncode}):")
        print("----- R STDOUT -----")
        print(e.stdout)
        print("----- R STDERR -----")
        print(e.stderr)
        print("--------------------")
        sys.exit(1)
    finally:
        # Clean up the temporary R script
        if r_script_path.exists():
            os.remove(r_script_path)
        print("\n------------------- R preparation completed ---------------------")
        print(f"To launch the OHDSI Diagnostics Explorer viewer, open {r_dir_str} folder in R/RStudio and run:")
        print("-----------------------------------------------------------------")
        print(f"  setwd('{r_dir_str}')")
        print("  renv::restore()")
        print("  library(CohortDiagnostics)")
        print("  CohortDiagnostics::launchDiagnosticsExplorer()")
        print("-----------------------------------------------------------------")


def main():
    """Main function to run the cohort diagnostics."""
    try:
        # Load environment variables from .env file
        load_dotenv()

        # Parse command line arguments
        args = parse_arguments()

        # Create output directory if it doesn't exist
        output_path = Path(args.output_path)
        output_data_path = output_path / "data"
        output_data_path.mkdir(parents=True, exist_ok=True)

        print(f"Results will be saved to: {output_data_path / args.output_filename}")

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
                output_file = output_data_path / args.output_filename
                with open(output_file, 'wb') as f:
                    f.write(zip_data)
                print(f"Results saved to: {output_file}")
            else:
                raise ValueError("No zip data found in parsed results")
        else:
            raise ValueError("No data found in results or invalid result structure")

        # Prepare R environment (renv) for Shiny app
        if args.prepare_r:
            if not output_file.exists():
                print(f"Error: Cannot prepare R environment because results file is missing: {output_file}")
                sys.exit(1)
            prepare_r_environment(output_file)

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
                "organizations_to_include": organisations_to_include
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
