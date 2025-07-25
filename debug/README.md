# Setup for debugging the R code of the cohort diagnostics algorithm container

## Makefile, Dockerfile

This directory contains a Dockerfile that created a debug version of the algorithm container. Before you build and publish this container, please make sure of the following:

- you have a valid local Vantage6 deployment up and running, preferably initialized by running `test/runsetup.sh`) (with the omop database configured for the node)
- there is currently no debug version of the algorithm available as an approved algorithm. (You can invalidate an existing one in the V6 UI, or run the `test/runsetup.sh` script in the deployment).

To build, push and publish the container in the local Vantage6 deployment, run `make publish`. If not already present, this will checkout a local copy of the OHDSI CohortDiagnostics package, where you can insert debug/print statements. Mind that this local copy is in `.gitignore`, so if you ever need to save code from there, you need to do that manually.

The directory further contains an adapted version of `client.py` that starts the debug version of the algorithm, and copies of some files used by `client.py`.

## Short workflow for debugging

1. Adapt R code, probably by inserting `browser()` statements
2. run `make publish` - this will build a new debug container and enable it in Vantage6
3. run `./startDebug.sh` - this should eventually bring you to the point where you inserted the `browser()` statement

## How this is supposed to work

A normal run of an algorithm container is completely "invisible". When an algorithm is started, e.g by running `python client.py`, a set of 4 containers is started:

1. an algorithm container that monitors the progress. We will call this container the Monitor.
2. a helper container for 1.
3. an algorithm container that runs executes the actual algorithm. We will call this container the Executor.
4. a helper container for 3.

The helper containers are mentioned here so that people running `docker ps` understand why running an algorithm container results in no less than 4 containers running. They are ignored
in this text.

In order to debug what's going on in container 4., which actually runs the algorithm, it is necessary to have manual control over when the algorithm code actually starts, like when you want to attach a debugger. For this reason, the Dockerfile in this directory replaces the 
automatic start of the algorithm by `CMD [ "sleep", "infinity" ]`. 
When the algorithm is now started, this results in container 1. and 2. starting to run, but doing nothing (sleeping forever). You can start the actual algorithm by performing the follwing steps (you will need 3 terminal tabs):

1. make sure you set the env. var REQUESTS_CA_BUNDLE to point to the pem file that is used by the Vantage6 deployment you want to debug with, and that the python dependencies are installed (`pip install -r requirements.txt`)
2. start the algorithm as normal by running `python client.py` in a terminal tab
3. in the second terminal tab, determine the id of container 1 (the Monitor) by using `docker ps`. Container name is `registry.vantage6.local/omop-cohort-diagnostics-debug`, and the command running is `"sleep infinity"`
4. start the normal process in the Monitor container by executing
  `docker exec -ti <id> bash -c "python -c 'from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()'"`
  After a few seconds you will start to see a repetition of `info > Waiting for results of task #...` messages (with an actual number for `#`)
5. in the third terminal tab, determine the id of container 3 (the Executor) by using `docker ps`. Make sure you get the other one than the id in step 2
6. start the normal process in the Executor container by executing
  `docker exec -ti <id> bash -c "python -c 'from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()'"`
  Assuming you did not insert any kind of breakpoint, you will now see the logs of the algorithm running to completion.
  None of the 4 containers will stop automatically, by the way.
7. Once you are done, stop all the algorithm containers by executing `docker stop $(docker ps|grep "sleep infinity"|awk '{print $1}')` 
  This assumes that you have no other containers running `"sleep infinity"`. If you do, you need to be more selective.

## Actual debugging of R code

What currently works is starting the R command line debugger by inserting `browser()` statements in de R code and rebuilding the container, and running the algorithm using the steps described above. [Documentation of the R command line debugger](https://www.rdocumentation.org/packages/base/versions/3.6.2/topics/browser).

Ataching VSCode to a running container, and attaching the R Debugger in VSCode to the running algorithm can already be done, but actually stepping through the code and inspecting variables does not work yet.
TODO: describe the VSCode setup so far (janblom)

## Notes on debug results

# newer versions of OHDSI packages (CohortDiagnostics, FeatureExtraction, ...)

When trying this, there are errors that point to the parameters passed in not having the right format. Solving one (by hacking in a value that is accepted, but makes no sense) just leads to another
error concerning the parameters.
