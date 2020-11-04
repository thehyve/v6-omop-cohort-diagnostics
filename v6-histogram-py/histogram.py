import time
import numpy as np

from vantage6.common import info
from vantage6.tools.container_client import ContainerClient

def master(client: ContainerClient, data, edges, column_name):
    """Master method that returns the total counts per bin and the
       removed bins due to disclosure checks

    Parameters
    ----------
    client : ContainerClient
        Supplied by vantage6
    data : pandas.DataFrame
        pandas dataframe not used but supplied
    edges : list
        list containing bin edges
    column_name : column name
        to be used in calculation

    Returns
    -------
    total_count, mask
        total counts per bin after disclosure checks and True/False for
        bins that were removed due to disclosure checks
    """
    organizations = client.get_organizations_in_my_collaboration()
    ids = [organization.get("id") for organization in organizations]

    input_ = {
        "method": "non_disclosive_binary_binning",
        "kwargs": {
            "edges": edges,
            "column_name": column_name
        }
    }
    task = client.create_new_task(
        input_=input_,
        organization_ids=ids
    )
    results = wait_and_collect_results(client, task.get("id"))
    print(results)
    counts = []
    removed = []
    for result in results:
        counts.append(result[0])
        removed.append(result[1])

    total_count = list(map(sum, zip(*counts)))
    mask = [all(tup) for tup in zip(*removed)]

    return total_count, mask


def RPC_non_disclosive_binary_binning(data, edges, column_name):
    """Make the results of the binary binnin non-disclosive.

    Parameters
    ----------
    data : Pandas.Dataframe
        Supplied by vantage6
    edges : list
        containing bin edges
    column_name : string
        identifies column of pandas dataframe to use

    Returns
    -------
    nd_count and removed
        nd_count is the non disclosive counts per bin and removed
        are the bins that have failed the disclosive checks
    """

    # np array for performance improvements
    data = data[column_name].dropna()
    data = np.array(data)

    # cant have more edges than 1/3 of the length of the data
    if len(edges) >= 0.33 * len(data):
        return

    # perform the binning
    counts = binary_binning(data, edges)

    # Bins smaller than 10 are removed
    removed = []
    nd_count = []
    for count in counts:
        if count < 10:
            removed.append(True)
            nd_count.append(0)
        else:
            removed.append(False)
            nd_count.append(count)

    return nd_count, removed


def wait_and_collect_results(client, task_id):
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)

    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))
    return results


def binary_binning(data, edges):
    """Binning algorithm that bins the data.

    Parameters
    ----------
    data : numpy array
        data to be sorted and binned
    edges : list
        list of bin edges

    Returns
    -------
    list bin counts
        counts per bin
    """

    # D is the sorted data
    D = np.sort(data)
    N = len(D)

    # E contains the edges [[lower, upper], ...]
    len_edges = len(edges)
    E = []
    for i in range(len_edges-1):
        E.append((edges[i], edges[i+1]))
    E = np.array(E)

    # B contains the count of each bin
    B = [np.array([]) for bin_ in range(len(E))]

    # for every bin
    for b_id, bin_ in enumerate(E):

        # Check that there are items left to bin
        if not len(D):
            break

        N = len(D)
        idx = N//2 - 1

        # as long as the first value in remaining data is bigger than
        # the lower bound of the current bin
        while (D[0] >= bin_[0]):

            # if the current data value (at check idx) is smaller than the
            # upper bound of the current bin
            if D[idx] <= bin_[1]:

                B[b_id] = np.concatenate((B[b_id], D[:idx+1]))
                D = D[idx+1:]

                # in case there are still values left in D, move the index
                # back to the middle of the new (shortend) D
                if len(D):
                    N = len(D)
                    idx = N//2 - 1
                    # this happens when N = 1, so we need to set it to the
                    # first value in D
                    if idx < 0:
                        idx = 0

                    continue
                # in case there are no values left in D, move out of bin
                # and binning is done (outer loop checks for len(D) too)
                else:
                    break

            # in case the current value is bigger than the bin max we need to
            # look at smaller values in D
            if D[idx] > bin_[1]:

                # ok if we aleady check elements, there are no smaller elements
                # to be checked
                if idx == 0:
                    break

                idx = idx//2

    # count the number of values in each bin
    return [len(b) for b in B]

