from vantage6.algorithm.tools.mock_client import MockAlgorithmClient


## Mock client
client = MockAlgorithmClient(
    datasets=[
        {
            "database": "local/data.csv",
            "type": "csv",
            "input_data": {}
        },
        {
            "database": "local/data.csv",
            "type": "csv",
            "input_data": {}
        }
    ],
    module="v6-boilerplate-py"
)

# list mock organizations
organizations = client.organization.list()
print(organizations)
org_ids = [organization["id"] for organization in organizations]

# Run a method in the algorithm for all nodes
task = client.task.create(
    input_={
        "method":"some_example_method",
        "kwargs": {
            "example_arg": "example_value"
        }
    },
    organizations=org_ids)
print(task)

# Get the results from the task
results = client.result.get(task.get("id"))
# or, alternatively:
# results = client.wait_for_results(task.get("id"))
print(results)

# Run the central method on 1 node and get the results
central_task = client.task.create(
    input_={"method":"some_central_method"},
    organizations=[org_ids[0]]
)
results = client.result.from_task(task.get("id"))
print(results)
