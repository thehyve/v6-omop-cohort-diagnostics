#!/usr/bin/env bash

# make sure there are no leftovers from a previous run
docker stop $(docker ps|grep "sleep infinity"|awk '{print $1}')

# let the client.py script kick off the algorithm start, ignore ouput, put in the background
nohup python client.py >client.log 2>&1 &

# need to wait a bit for the "monitor" container to become available
sleep 5

# obtain the docker id of the "monitor" container
monitor=$(docker ps | grep "omop-cohort-diagnostics-debug" | awk '{print($1)}')
echo "monitor id is $monitor"

# let the "monitor" start the algorithm container, ignore output, put in the background
nohup docker exec $monitor bash -c "python -c 'from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()'" > monitor.log 2>&1 &

# need to wait a bit for the "executor" container to become available
sleep 7

# obtain the docker id of the "executor" container
executor=$(docker ps | grep "omop-cohort-diagnostics-debug" | grep -v $monitor | awk '{print($1)}')
echo "executor id is $executor"

# start the actual algorithm, in the foreground, keep a log of all the output
docker exec -ti $executor bash -c "python -c 'from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()'" 2>&1 | tee executor-debug.log
