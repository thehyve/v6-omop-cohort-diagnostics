ARG BASE=4.5
ARG TAG=latest
ARG PKG_NAME="v6-omop-cohort-diagnostics"

FROM harbor2.vantage6.ai/infrastructure/algorithm-ohdsi-base:${BASE}

LABEL version=${TAG}
LABEL maintainer="F.C. Martin <f.martin@iknl.nl>"
LABEL maintainer="A.J. van Gestel <a.vangestel@iknl.nl>"

#install some dangling R dependencies
RUN Rscript -e "install.packages('scales')"
RUN Rscript -e "install.packages('pool')"
RUN Rscript -e "install.packages('later')"

# install federated algorithm
COPY . /app
RUN pip install /app

# Set environment variable to make name of the package available within the
# docker image.
ENV PKG_NAME=${PKG_NAME}

# Tell docker to execute `wrap_algorithm()` when the image is run. This function
# will ensure that the algorithm method is called properly.
CMD python -c "from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()"
