#
# builds a debug version from an image meant for use in the local deployment
#
FROM registry.vantage6.local/omop-cohort-diagnostics:latest

# vim is handy, git is needed for getting the source files of the OHDSI CohortDiagnostics package
RUN apt update -y && apt install -y vim git procps

# install R extensions to support debugging
RUN Rscript -e "install.packages('languageserver')"
RUN Rscript -e "install.packages('vscDebugger', repos = 'https://manuelhentschel.r-universe.dev')"
 
# install Python debug/trace utilities
RUN pip install hunter

# copy the local CohortDiagnostics package source into the container, and install the package from there (this should effectively overwrite the already installed package)
ADD ./CohortDiagnostics /root/CohortDiagnostics
RUN Rscript -e "install.packages('/root/CohortDiagnostics', repos = NULL, type='source')"

# get the CohortDiagnostics source files, and replace the compiled version of CohortDiagnostics by the R source files
#RUN (cd /usr/local/lib/R/site-library/CohortDiagnostics/ && mkdir git && cd git && git clone https://github.com/OHDSI/CohortDiagnostics.git && \
	#cd ../R && rm *.rd? && cp ../git/CohortDiagnostics/R/*.R .)

# alter the cohort_diagnostics Python code to create the R CohortDiagnostics from source instead of loading the compiled version
#RUN sed -i.bak -e 's/^from rpy2.robjects.packages import importr$/&, SignatureTranslatedAnonymousPackage/' \
#	-e "s%cohort_diagnostics = importr('CohortDiagnostics')%#&\n    r_code=''\n    for r in Path('/usr/local/lib/R/site-library/CohortDiagnostics/R').glob('**/*.R'):\n        r_code += r.read_text()\n    cohort_diagnostics = SignatureTranslatedAnonymousPackage(r_code, 'CohortDiagnostics')%" /usr/local/lib/python3.10/site-packages/ohdsi/cohort_diagnostics/__init__.py

CMD ["sleep", "infinity"]
