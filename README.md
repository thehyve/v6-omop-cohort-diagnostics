<h1 align="center">
  <br>
  <a href="https://vantage6.ai"><img src="https://github.com/IKNL/guidelines/blob/master/resources/logos/vantage6.png?raw=true" alt="vantage6" width="400"></a>
</h1>

<h3 align=center> A privacy preserving federated learning solution</h3>

--------------------

# v6-boilerplate-py
This algorithm is part of the [vantage6](https://vantage6.ai) solution. Vantage6 allowes to execute computations on federated datasets. This repository provides a boilerplate for new algorithms.

## Usage
First clone the repository.
```bash
# Clone this repository
git clone https://github.com/IKNL/v6-boilerplate-py
```
Rename the directories to something that fits your algorithm, we use the convention `v6-{name}-{language}`. Then you can edit the following files:

### Dockerfile
Update the `ARG PKG_NAME=...` to the name of your algorithm (preferable the same as the directory name).

### LICENSE
Determine which license suits your project.

### `{algorithm_name}/__init__.py`

This file contains all the methods that can be called at the nodes. In the
example below, one example function is shown.

```python

import pandas as pd
from vantage6.client.algorithm_client import AlgorithmClient

@algorithm_client
@data(1)
def my_function(client: AlgorithmClient, df1: pd.DataFrame, column_name: str):
    pass
```

This function uses an
`@algorithm_client` decorator to insert an algorithm client, which can be used
to e.g. create subtasks or find the VPN addresses of algorithm containers
within the same task running on other nodes. Also, the `@data` decorator is
used to insert a single [pandas dataframe](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html?highlight=dataframe#pandas.DataFrame).
This requires the user creating a task to specify one database when calling
this function. Note that you can specify any number `x` in  `data(x)`.
The number that you specify will determine how many databases will be added to
your function profile.

### setup.py
In order for the Docker image to find the methods the algorithm needs to be installable. Make sure the *name* matches the `ARG PKG_NAME` in the Dockerfile.

Also, make sure to add any dependencies that your algorithm needs to `setup.py`
and `requirements.txt`!

## Read more
See the [documentation](https://docs.vantage6.ai/) for detailed instructions on how to install and use the server and nodes.

------------------------------------
> [vantage6](https://vantage6.ai)
