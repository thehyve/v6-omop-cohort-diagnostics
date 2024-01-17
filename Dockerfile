# basic python3 image as base
#FROM harbor2.vantage6.ai/infrastructure/algorithm-base
FROM harbor2.vantage6.ai/infrastructure/algorithm-ohdsi-base:4.1

# This is a placeholder that should be overloaded by invoking
# docker build with '--build-arg PKG_NAME=...'
ARG PKG_NAME="v6-omop-test"

#install some dangling R dependencies
RUN Rscript -e "install.packages('scales')"
RUN Rscript -e "install.packages('pool')"
RUN Rscript -e "install.packages('later')"

# TODO: remove me at release
# RUN apt update && apt install -y git
# RUN pip install --force-reinstall git+https://github.com/vantage6/vantage6@bugfix/some-minor-fixes#subdirectory=vantage6-algorithm-tools

# install federated algorithm
COPY . /app
RUN pip install /app

# In Vantage6 versions 3.1+, you can use VPN communication between algorithms
# over multiple ports. You can specify the ports that are allowed for
# communication here, along with a label that helps you identify them. As an
# example, port 8888 is used here. You can also specify additional ports in the
# same way, by adding an extra EXPOSE and LABEL statement
#EXPOSE 8888
#LABEL p8888 = 'some_label'


# Set environment variable to make name of the package available within the
# docker image.
ENV PKG_NAME=${PKG_NAME}

# Tell docker to execute `wrap_algorithm()` when the image is run. This function
# will ensure that the algorithm method is called properly.
CMD python -c "from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm('${PKG_NAME}')"
