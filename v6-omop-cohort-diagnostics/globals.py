# The following global variables are algorithm settings. They can be overwritten by
# the node admin by setting the corresponding environment variables.

# The minimum cell count for fields, contains person counts or fractions. To be
# overwritten by setting the "CD_MIN_RECORDS" environment variable. It corresponds 
# to OHDSI's CohortDiagnostics min_cell_count variable.
DEFAULT_CD_MIN_RECORDS = "5"