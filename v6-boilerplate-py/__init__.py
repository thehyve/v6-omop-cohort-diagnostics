"""
This file contains all algorithm pieces that are executed on the nodes.
It is important to note that the central method is executed on a node, just
like any other method.

The results in a return statement are sent to the central vantage6 server after
encryption (if that is enabled).
"""
import pandas as pd

from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client, data
from vantage6.algorithm.client import AlgorithmClient

@algorithm_client
def central(client: AlgorithmClient):
    """Central part of the algorithm."""

    # get all organizations (ids) within the collaboration
    organizations = client.organization.list()
    org_ids = [organization.get("id") for organization in organizations]

    # The input fot the algorithm is the same for all organizations
    # in this case
    info("Defining input parameters")
    input_ = {
        "method": "some_example_method",
        "kwargs": {
            "example_arg": "example_value"
        }
    }

    # create a new task for all organizations in the collaboration.
    info("Dispatching node-tasks")
    task = client.task.create(
        input_=input_,
        organization_ids=org_ids,
        name="My subtask",
        description="This is a very important subtask"
    )

    # wait for node to return results.
    info("Waiting for results")
    results = client.wait_for_results(task_id=task.get("id"))

    info("Results obtained!")
    print(results)

    info("master algorithm complete")

    # return the final results of the algorithm
    return results

@data(1)
def some_example_method(df: pd.DataFrame, example_arg: str):
    """Some_example_method.

    This example returns average age by gender.
    """
    info("Computing mean age by gender")
    result = df[["Sex", "Age"]].groupby("Sex").mean()

    # what you return here is sent to the central server. So make sure
    # no privacy sensitive data is shared
    return result.to_dict()
