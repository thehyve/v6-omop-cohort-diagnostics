import argparse
from mpyc.runtime import mpc
import pandas as pd
import numpy as np


from mpyc.runtime import mpc

import tno.mpc.mpyc.secure_learning.test.plaintext_utils.plaintext_objective_functions as plain_obj
from tno.mpc.mpyc.secure_learning import (
    PenaltyTypes,
    Logistic,
    SolverTypes,
    ExponentiationTypes
)
# from .mpc import setup

secnum = mpc.SecFxp(l=64, f=32)
## These are fixed for now, but they wcan be overwriten.
random_state = 3
tolerance = 1e-4
INTERNAL_PORT = 8888
WAIT = 4
RETRY = 10
secint = mpc.SecInt()


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--response',
                    type=argparse.FileType('r', encoding='UTF-8'),
                    required=False)

    parser.add_argument('-z', '--covariate',
                    type=argparse.FileType('r', encoding='UTF-8'),
                    required=False)

    args = parser.parse_args()
    print(1)
    # print(f"This is args: {args}")
    if args.r is not None:
        print(2)
        data = pd.read_csv(args.r.name, header=None)
        name = "response"


    elif args.z is not None:
        print(3)
        data = pd.read_csv(args.z.name, header=None)
        name = "covariate"

    print(99)
    ans = {"data":data, "name":name}

    return ans
    # print(ans["data"])


def get_data(data: pd.DataFrame, col: str):

    print(4)
    # secnum = mpc.SecFxp(l=64, f=32)
    # if not isinstance(data, None):
    if col=="response":
        print(5)
        # name = data.columns[0]
        # y = np.array(data[name].head())

        y = data.to_numpy().flatten()
          # Need to transform labels from {0,1} -> {-1,+1}
        if all(list(map(lambda x:x in y, (0,1)))):
            y = np.array([-1 if x==0 else 1 for x in y])
        # elif not all(list(map(lambda x:x in y, (-1,1)))):
        #     raise ValueError("All values in the response must be {-1,1}")
        print(y)
        y_mpc = [secnum(x, integral = False) for x in y.tolist()]

        print(88)

        return y_mpc

    if col == "covariate":
        print(6)
        # assume for now that each site has 1 coln
        if data.shape[1] == 1:
            data = data.to_numpy().flatten()
            X = np.array(data, ndmin=1)
            X_mpc = [[secnum(x, integral = False) for x in X.tolist()]]
            print("not transpose")
        else:
            print("Transpose")
            X = data.to_numpy().T
            X_mpc = [[secnum(x, integral=False) for x in row] for row in X.tolist()]

        print(X)
        print(f"This is X: {len(X_mpc)}")
        return X_mpc


# solver = Model.solver

async def transfer_y(y=[], X=[]):

    print(7)
    # with mpc.run:
            ### create a dataset


    # newy = await mpc.input()
    # y = await mpc.transfer(y)
    # X = await mpc.transfer(X)
    try:
        X = X[0]
    except:
        pass
    l = mpc.input(secint(len(X)))
    l = mpc.max(l)
    n = await mpc.output(l)

    print(f"This is n: {n}")

    ly = mpc.input(secint(len(y)))
    ly = mpc.max(ly)
    ny = await mpc.output(ly)

    if not X:
        X = [secnum(None)] * n
        print(f"this is the party that sends xnone, {mpc.pid}")



    if not y:
        y = [secnum(None)] * ny
        print(f"this is the party that sends ynone, {mpc.pid}")

    print(88)
    print(f"This is y: {y}")
    print(f"This is X: {X}")
    X = np.transpose(mpc.input(X, senders = [0,2])).tolist()
    Y = mpc.input(y, senders = 1)
    print(f"This is y: {np.shape(Y)}")
    print(f"This is X: {np.shape(X)}")
    print("&&")
    # y = [x for x in Y if x]
    # X = [x for x in X if x]

    # X = X[0]
    # y = y[0]

    # print(888)

    # print("!!!")
    # print(f"this is x00: {X[0][0]}")
    # print(f"this is y00: {y[0]}")
    print("FF")
    model = Logistic(solver_type=SolverTypes.GD,
                exponentiation=ExponentiationTypes.APPROX,
                penalty=PenaltyTypes.L1,
                alpha=0.1)
    print("DDD")

    [[print(i.share) for i in x] for x in X]
    # import pickle

    # with open('dist.hasan', 'w') as f:
    #     pickle.dump([[await x for x in X],await Y], f)

    weights = mpc.sum(sum(x) for x in X)

    # weights = await model.compute_weights_mpc(
    #     X=X,
    #     y=Y ,
    #     tolerance=tolerance
    # )
    print(222)
    # weights = await mpc.output(weights)

    # print(weights)
    # print(await mpc.output(weights))

    return {
        "weights":weights
        }
    #     "objective":objective
    # }


if __name__ == "__main__":

    args = parse_args()

    mpc.run(mpc.start())

    data = get_data(data = args["data"], col = args["name"])
    print("Did the data")
    # print(data)

    if args['name'] == 'covariate':
        X = mpc.run(transfer_y(X=data))
    else:
        y = mpc.run(transfer_y(y=data))

    print("Transferring")

    # mpc.run(transfer_y(data))

    mpc.run(mpc.shutdown())
