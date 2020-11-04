<h1 align="center">
  <br>
  <a href="https://vantage6.ai"><img src="https://github.com/IKNL/guidelines/blob/master/resources/logos/vantage6.png?raw=true" alt="vantage6" width="400"></a>
</h1>

<h3 align=center> A privacy preserving federated learning solution</h3>

--------------------

# v6-histogram-py
This algoithm is part of the [vantage6](https://vantage6.ai) solution. Vantage6 allowes to execute computations on federated datasets.

## Usage

```python
from vantage6.client import Client

# Authenticate to the server
client = Client("http://127.0.0.1", 5000, "/api")
client.authenticate("frank@iknl.nl", "password")
client.setup_encryption(None)

# algorithm input
input_ = {
    "master": True,
    "method": "histogram_master", # or "round_robin_master"
    "args": [["Column from dataframe"], "number of bins", "minimum number of patients per bar"]
}

# Create task for the server
task = client.post_task(
    "testing task",
    "harbor.vantage6.ai/algorithms/histogram",
    collaboration_id=2,
    input_=input_,
    organization_ids=[1]
)

# obtain the results
client.get_results(task_id=task.get("id"))
```

## Read more
See the [documentation](https://docs.vantage6.ai/) for detailed instructions on how to install and use the server and nodes.

------------------------------------
> [vantage6](https://vantage6.ai)