#
# builds a debug version from an image meant for use in the local deployment
#
FROM registry.vantage6.local/omop-cohort-diagnostics:latest

# vim is handy, git is needed for getting the source files of the OHDSI CohortDiagnostics package
RUN apt update -y && apt install -y vim git procps wget net-tools iproute2
RUN apt update && apt install -y libssl-dev libfontconfig1-dev libcurl4-openssl-dev libxml2-dev libharfbuzz-dev libfribidi-dev libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev

ARG MAKEFLAGS="-j 15"
# install R extensions to support debugging
RUN Rscript -e "install.packages('languageserver')"
RUN Rscript -e "install.packages('remotes')"
#RUN Rscript -e "install.packages('vscDebugger', repos = 'https://manuelhentschel.r-universe.dev')"
RUN Rscript -e "remotes::install_github('ManuelHentschel/vscDebugger@v0.5.4', dependencies=TRUE)"
RUN Rscript -e "install.packages('devtools')"
RUN Rscript -e "install.packages('pkgload')"
 
# install Python debug/trace utilities
RUN pip install hunter

# install R-studio server
RUN apt install -y gdebi-core
RUN wget https://download2.rstudio.org/server/jammy/amd64/rstudio-server-2025.05.1-513-amd64.deb
RUN gdebi rstudio-server-2025.05.1-513-amd64.deb

# copy the local CohortDiagnostics package source into the container, and install the package from there (this should effectively overwrite the already installed package)
ADD ./CohortDiagnostics /root/CohortDiagnostics
ADD ./FeatureExtraction /root/FeatureExtraction
ADD ./CohortGenerator /root/CohortGenerator
#RUN rm -rf /usr/local/lib/R/site-library/CohortDiagnostics
RUN Rscript -e "install.packages('/root/FeatureExtraction', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"
RUN Rscript -e "install.packages('/root/CohortGenerator', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"
RUN Rscript -e "install.packages('/root/CohortDiagnostics', repos = NULL, INSTALL_opts='--with-keep.source', type='source', lib='/usr/local/lib/R/site-library')"
#RUN cp -r /app/debug/CohortDiagnostics /usr/local/lib/R/site-library/CohortDiagnostics
#RUN Rscript -e "library(devtools); devtools::install(pkg='/root/CohortDiagnostics', dependencies=FALSE, keep_source=TRUE)"

# get the CohortDiagnostics source files, and replace the compiled version of CohortDiagnostics by the R source files
#RUN (cd /usr/local/lib/R/site-library/CohortDiagnostics/ && mkdir git && cd git && git clone https://github.com/OHDSI/CohortDiagnostics.git && \
	#cd ../R && rm *.rd? && cp ../git/CohortDiagnostics/R/*.R .)

# alter the cohort_diagnostics Python code to create the R CohortDiagnostics from source instead of loading the compiled version
#RUN sed -i.bak -e 's/^from rpy2.robjects.packages import importr$/&, SignatureTranslatedAnonymousPackage/' \
#	-e "s%cohort_diagnostics = importr('CohortDiagnostics')%#&\n    r_code=''\n    for r in Path('/usr/local/lib/R/site-library/CohortDiagnostics/R').glob('**/*.R'):\n        r_code += r.read_text()\n    cohort_diagnostics = SignatureTranslatedAnonymousPackage(r_code, 'CohortDiagnostics')%" /usr/local/lib/python3.10/site-packages/ohdsi/cohort_diagnostics/__init__.py

# alter the cohort_diagnostics Python code to create the R CohortDiagnostics from source instead using pkgload::load_all()
#RUN sed -i.bak -e "s/^from rpy2.robjects.packages import importr$/&\n   pkgload=importr('pkgload')/" \
#	-e "s%cohort_diagnostics = importr('CohortDiagnostics')%#&\n   cohort_diagnostics=pkgload.load_all('/root/CohortDiagnostics')%" /usr/local/lib/python3.10/site-packages/ohdsi/cohort_diagnostics/__init__.py

# try a newer rpy2 version
#RUN pip install rpy2==3.5.16

CMD ["sleep", "infinity"]
