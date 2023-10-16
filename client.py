from pathlib import Path
from vantage6.client import Client
client = Client('http://127.0.0.1', 5000, '/api', log_level='debug')
client.authenticate('org_1-admin', 'password')
client.setup_encryption(None)

folder_ = Path(r"C:\Users\FMa1805.36838\IKNL\524_Clinical Data Science_int - Infrastructure\OMOP utils")
task_id = 101
files = list(folder_.glob('*.json'))
omop_jsons = [(folder_ / file_).read_text() for file_ in files]

# omop_jsons = [
#      {
#        "id": 0,
#        "name": "Celecoxib",
#        "expression": {
#          "items": [
#            {
#              "concept": {
#                "CONCEPT_CLASS_ID": "Ingredient",
#                "CONCEPT_CODE": "140587",
#                "CONCEPT_ID": 1118084,
#                "CONCEPT_NAME": "celecoxib",
#                "DOMAIN_ID": "Drug",
#                "INVALID_REASON": "V",
#                "INVALID_REASON_CAPTION": "Valid",
#                "STANDARD_CONCEPT": "S",
#                "STANDARD_CONCEPT_CAPTION": "Standard",
#                "VOCABULARY_ID": "RxNorm"
#              }
#            }
#          ]
#        }
#      }
#    ]

client.task.create(
    collaboration=1,
    organizations=[1],
    name='omop-test',
    description='@',
    input_={
        'method': 'central',
        'kwargs': {
            'cohort_definitions': omop_jsons,
            'cohort_names': ['henk1', 'henk2', 'henk3'],
            'temporal_covariate_settings': {
                'use_demographics_gender': True,
                'use_demographics_age': True,
                'use_demographics_age_group': True,
                'use_demographics_race': True,
                'use_demographics_ethnicity': True,
                'use_demographics_index_year': True,
                'use_demographics_index_month': True,
                'use_demographics_index_year_month': True,
                'use_demographics_prior_observation_time': True,
                'use_demographics_post_observation_time': True,
                'use_demographics_time_in_cohort': True,
                'use_condition_occurrence': True,
                'use_procedure_occurrence': True,
                'use_drug_era_start': True,
                'use_measurement': True,
                'use_condition_era_start': True,
                'use_condition_era_overlap': True,
                'use_condition_era_group_start': False, # do not use because https://github.com/ohdsi/feature_extraction/issues/144
                'use_condition_era_group_overlap': True,
                'use_drug_exposure': False, # leads to too many concept id
                'use_drug_era_overlap': False,
                'use_drug_era_group_start': False, # do not use because https://github.com/ohdsi/feature_extraction/issues/144
                'use_drug_era_group_overlap': True,
                'use_observation': True,
                'use_visit_concept_count': True,
                'use_visit_count': True,
                'use_device_exposure': True,
                'use_charlson_index': True,
                'use_dcsi': True,
                'use_chads2': True,
                'use_chads2_vasc': True,
                'use_hfrs': False,
                'temporal_start_days': [
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
                    -9999  # any time prior to any time future
                ],
                'temporal_end_days': [
                    0, # anytime prior
                    0, # long term prior
                    0, # medium term prior
                    0, # short term prior

                    # components displayed in temporal characterization
                    -31, # one year prior to -31
                    -1, # 30 day prior not including day 0
                    0, # index date only
                    30, # 1 day after to day 30
                    365,
                    9999 # any time prior to any time future
                ]
            },
            'diagnostics_settings': {
                'run_inclusion_statistics': True,
                'run_included_source_concepts': True,
                'run_orphan_concepts': True,
                'run_time_series': False,
                'run_visit_context': True,
                'run_breakdown_index_events': False,
                'run_incidence_rate': True,
                'run_cohort_relationship': True,
                'run_temporal_cohort_characterization': True
            },
        }
    },
	databases=[
		{
			'label': 'default'
		}
	],
	image='omop-tester'
)


