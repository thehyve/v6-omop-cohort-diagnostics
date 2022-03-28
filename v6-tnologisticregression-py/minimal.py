import argparse
from typing import Sequence
from mpyc.runtime import mpc
secint =mpc.SecInt()
# seclist = mpc.Sec

def parse_args():
   parser = argparse.ArgumentParser()
   parser.add_argument(
       "-x", "--x-value", type=int, required=False
   )
   parser.add_argument(
       "-y", "--y-value", type=int, required=False
   )
   args = parser.parse_args()
   return args

async def transfer(x=[], y=[]):
    # v = int(value) if value != "0" else None
    # compute length of null vector

    print(f"this is the number of parties:{mpc.parties}")

    print(11)

    l = mpc.input(secint(len(x)))
    l = mpc.max(l)
    n = await mpc.output(l)

    print(f"This is n: {n}")

    ly = mpc.input(secint(len(y)))
    ly = mpc.max(ly)
    ny = await mpc.output(ly)

    print(f"this is ny: {ny}")

    print(22)


    if not x:
        x = [secint(None)] * n
        print(f"this is the party that sends xnone, {mpc.pid}")



    if not y:
        y = [secint(None)] * ny
        print(f"this is the party that sends ynone, {mpc.pid}")

    print(5)

    X = mpc.input(x, senders = [0,2])

    X_t = mpc.sum(sum(x) for x in X)

    # X_t = [(lambda f, x: f(f, x))(lambda g, x: [g(g, y) for y in x] if isinstance(x, list) else x ** 2, x_) for x_ in X]
    Y = mpc.input(y, senders = 1)

    # print(f"this is bigX: {X}")
    # print(f"this is bigY: {Y}")
    # if id:

    X_t = await mpc.output(X_t)
    print(f"this is X_t: {X_t}")

    Y_t = await mpc.output(Y)
    print(f"this is Y_t: {Y_t}")


if __name__ == "__main__":
    args = parse_args()
    mpc.run(mpc.start())
    if args.x_value:
        mpc.run(transfer(x=[secint(args.x_value),secint(args.x_value)]))
    else:
        mpc.run(transfer(y=[secint(args.y_value)]))
    mpc.run(mpc.shutdown())

# python minimal.py -M2 -I0 -x 2

# python minimal.py -M3 -I0 -x 2
# python minimal.py -M3 -I1 -y 2
# python minimal.py -M3 -I2 -x 2