#
# builds a debug version from an image meant for use in the local deployment
#
FROM registry.vantage6.local/omop-cohort-diagnostics:latest

# vim is handy, git is needed for getting the source files of the OHDSI CohortDiagnostics package
RUN apt update -y && apt install -y vim git procps wget net-tools iproute2
#RUN apt update && apt install -y libssl-dev libfontconfig1-dev libcurl4-openssl-dev libxml2-dev libharfbuzz-dev libfribidi-dev libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev

# the the number of CPU cores that make can use, speeds up the build of C/C++/Fortran dependencies for R source packages
ARG MAKEFLAGS="-j 15"	

# install R extensions to support debugging
RUN Rscript -e "install.packages('languageserver')"
RUN Rscript -e "install.packages('remotes')"
RUN Rscript -e "remotes::install_github('ManuelHentschel/vscDebugger@v0.5.4', dependencies=TRUE)"
RUN Rscript -e "install.packages('devtools')"
RUN Rscript -e "install.packages('pkgload')"
 
# install Python debug/trace utilities
RUN pip install hunter

# install R-studio server
#RUN apt install -y gdebi-core
#RUN wget https://download2.rstudio.org/server/jammy/amd64/rstudio-server-2025.05.1-513-amd64.deb
#RUN gdebi rstudio-server-2025.05.1-513-amd64.deb

# copy the local CohortDiagnostics package source into the container, and install the package from there (this should effectively overwrite the already installed package)
ADD ./CohortDiagnostics /root/CohortDiagnostics
ADD ./FeatureExtraction /root/FeatureExtraction
ADD ./CohortGenerator /root/CohortGenerator
#RUN rm -rf /usr/local/lib/R/site-library/CohortDiagnostics
RUN Rscript -e "install.packages('/root/FeatureExtraction', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"
RUN Rscript -e "install.packages('/root/CohortGenerator', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"
RUN Rscript -e "install.packages('/root/CohortDiagnostics', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"

CMD ["sleep", "infinity"]
