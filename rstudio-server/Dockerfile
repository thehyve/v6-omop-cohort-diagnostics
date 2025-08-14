FROM rocker/verse:4

RUN apt update && apt -y upgrade
RUN apt install -y r-cran-rjava

RUN Rscript -e "install.packages(c('remotes'))"

#
# set of packages that seems to work well the vantage6 ohdsi cohort diagnostics
# when running the Shiny app for the generated data
#
RUN Rscript -e "remotes::install_github('ohdsi/DatabaseConnector', ref='v6.2.4')"
RUN Rscript -e "remotes::install_github('ohdsi/FeatureExtraction', ref='v3.3.1')"
RUN Rscript -e "remotes::install_github('ohdsi/OhdsiShinyModules', ref='v2.1.5')"
RUN Rscript -e "remotes::install_github('ohdsi/CohortDiagnostics', ref='v3.2.5')"
