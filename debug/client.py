import os
from pathlib import Path
from vantage6.client import Client

# Authenticate to the vantage6 server
# defaults are for local setup, overrule by env.vars
v6_api_url = os.getenv("V6_API_URL", "https://vantage6.local")
v6_api_port = os.getenv("V6_API_PORT", "443")
v6_api_path = os.getenv("V6_API_PATH", "/server/api")
v6_api_user = os.getenv("V6_API_USER", "user1")
v6_api_password = os.getenv("V6_API_PASSWORD", "User1User1!")
client = Client(v6_api_url, v6_api_port, v6_api_path, log_level="debug")
client.authenticate(v6_api_user, v6_api_password)
client.setup_encryption(None)

# Load the cohort definitions from a folder. These can be created using the
# ATLAS tool
folder_ = Path(r"./cohort_definitions/")
files = list(folder_.glob("*.json"))
omop_jsons = [(file_).read_text() for file_ in files]
names = [file_.stem for file_ in files]


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
    "use_condition_era_group_start": False,  # do not use because https://github.com/ohdsi/feature_extraction/issues/144
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
    "temporal_start_days": -365,
    "temporal_end_days": 1,
#    "temporal_start_days": [
#        # components displayed in cohort characterization
#        -9999,  # anytime prior
#        -365,  # long term prior
#        -180,  # medium term prior
#        -30,  # short term prior
#        # components displayed in temporal characterization
#        -365,  # one year prior to -31
#        -30,  # 30 day prior not including day 0
#        0,  # index date only
#        1,  # 1 day after to day 30
#        31,
#        -9999,  # any time prior to any time future
#    ],
#    "temporal_end_days": [
#        0,  # anytime prior
#        0,  # long term prior
#        0,  # medium term prior
#        0,  # short term prior
#        # components displayed in temporal characterization
#        -31,  # one year prior to -31
#        -1,  # 30 day prior not including day 0
#        0,  # index date only
#        30,  # 1 day after to day 30
#        365,
#        9999,  # any time prior to any time future
#    ],
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
task = client.task.create(
    collaboration=1,
    organizations=[2],
    name="omop-test",
    description="@",
    input_={
        "method": "cohort_diagnostics_central",
        "kwargs": {
            "cohort_definitions": omop_jsons,
            "cohort_names": names,
            "temporal_covariate_settings": temporal_covariate_settings,
            "diagnostics_settings": diagnostics_settings,
            # as far is I can tell, this is just an id we decide upon
            "meta_cohorts": [{"task_id": 13}],
        },
    },
    databases=[{"label": "omop"}],
    image="registry.vantage6.local/omop-cohort-diagnostics-debug",
)

# Obtain the results
client.wait_for_results(task_id=task.get("id"))
