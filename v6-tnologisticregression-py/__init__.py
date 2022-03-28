import pandas as pd
import numpy as np
import argparse
import numpy.typing as npt
from .mpc import setup

from mpyc.sectypes import SecFxp, SecInt
from tno.mpc.mpyc.secure_learning.models import Logistic, SolverTypes, ExponentiationTypes, PenaltyTypes


secint = SecInt()
secnum = SecFxp(l=64, f=32)


def RPC_get_x(data):

    # X = np.array([[xi for xi in data[coln]] for coln in data.columns]).tolist()
    X = data.to_numpy()
    if np.shape(X)[1] == 1:
        X_mpc = [secnum(x, integral = False) for x in X]
    else:
        X_mpc = [[secnum(x, integral = False) for x in row] for row in X.tolist()]
    return X_mpc

def RPC_get_y(data):
    # y = np.array([[yi for yi in data[coln]] for coln in data.columns])
    y = data.to_numpy()

    if all(list(map(lambda x:x in y, (0,1)))):
        y = np.array([-1 if x==0 else 1 for x in y])
    elif not all(list(map(lambda x:x in y, (-1,1)))):
        raise ValueError("All values in the response must be {-1,1}")

    y_mpc = [secnum(x, integral = False) for x in y]

    return y_mpc

async def secure_data(self, x=None, y=None):

    if x:
        y = []

    if y:
        x = []

    async with self.mpc as mpc:
        len_x = mpc.input(secint(len(x)))
        len_x = mpc.max(len_x)
        n_x = await mpc.output(len)

        len_y = mpc.input(secint(len(y)))
        len_y = mpc.max(len_y)
        n_y = await mpc.output(len_y)

        if not x:
            x = [secnum(None)] * n_x

        if not y:
            y = [secnum(None)] * n_y

        x = mpc.input(x, senders = [0,2])
        y = mpc.input(y, senders = 1)

    return [y, x]

async def logistic_regression(self, x, y, alpha, tolerance=None, penalty=None):

    if penalty == "L1":
        penalty = PenaltyTypes.L1
    if penalty == "L2":
        penalty = PenaltyTypes.L2
    if penalty == "elastic":
        penalty = PenaltyTypes.ELASTICNET
    elif isinstance(penalty, None):
        penalty = PenaltyTypes.NONE
    else:
        raise ValueError(f"cannot use penalty type, {penalty}")

    if isinstance(tolerance, None):
        tolerance = 1e-4
    if not isinstance(tolerance, float):
        raise ValueError(f"Invalid tolerance type, {type(tolerance)}")

    model = Logistic(solver_type=SolverTypes.GD, exponentiation=ExponentiationTypes.APPROX,
                penalty=penalty, alpha=alpha)

    weights = await model.compute_weights_mpc(X=x, y=y, tolerance=tolerance)

    return weights

