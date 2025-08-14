# Using the RStudio-server docker image

This directory contains a reference configuration for running the Diagnostics Explorer Shiny application
from a dockerized setup of Rstudio-server. 

## setup

Create the Docker image by running
``docker build -t rockstudio-v6-cohort-diagnostics .``
in this directory.
The provided `makefile` can be optionally used to run the same command.

## configuration

Make sure the volumes in `docker-compose.yml` match your setup. The defaults work if you have saved the
results from the execution of the Cohort Diagnostics algorithm (.sqlite file) in its default directory `results`.

You can optionally alter the port or the password to your preference.

## starting / running / stopping

You can start the container by running ``docker compose up -d`` from the command line. 

You can then access rstudio-server by accessing
`http://localhost:8787` in a web browser, and log in with user `rstudio`, password `password`. Ig you changed the
settings for password or port in `docker-compose.yml` you also need to change them here.

When logged in, all you need to do is:

1. set the working directory to `workspace`: ``setwd("~/workspace")``
2. start Diagnostics Explorer: ``CohortDiagnostics::launchDiagnosticsExplorer()``

After you are done, you can stop the container from the command line: ``docker compose down``. 