# basic python3 image as base
FROM harbor2.vantage6.ai/algorithms/algorithm-base

# This is a placeholder that should be overloaded by invoking
# docker build with '--build-arg PKG_NAME=...'
ARG PKG_NAME="v6-boilerplate-py"

# install federated algorithm
COPY . /app
RUN pip install /app

# In Vantage6 versions 3.0+, you can use VPN to communicate between nodes.
# The algorithms are only allowed to communicate via VPN over specific ports,
# that may be specified here, along with a label that helps you identify them.
# If no ports are specified (and VPN is available), only port 8888 is available
# by default
EXPOSE 8888
LABEL p8888 = 'Explanation usage port 8888'
EXPOSE 9999
LABEL p9999 = 'Explanation usage port 9999'

ENV PKG_NAME=${PKG_NAME}

# Tell docker to execute `docker_wrapper()` when the image is run.
CMD python -c "from vantage6.tools.docker_wrapper import docker_wrapper; docker_wrapper('${PKG_NAME}')"
