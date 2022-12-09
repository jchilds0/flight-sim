from typing import Tuple, List

from scipy.integrate import odeint
import numpy as np
from math import atan, pi


def frenet_serre(y: List[float], t: float, kappa: float, tau: float):
    """
    gamma(t) = (y[0], y[1], y[2])
    T = (y[3], y[4], y[5])
    N = (y[6], y[7], y[8])
    B = (y[9], y[10], y[11])
    """
    gamma_prime1 = y[3]
    gamma_prime2 = y[4]
    gamma_prime3 = y[5]

    t_prime1 = kappa * y[6]
    t_prime2 = kappa * y[7]
    t_prime3 = kappa * y[8]

    n_prime1 = -kappa * y[3] + tau * y[9]
    n_prime2 = -kappa * y[4] + tau * y[10]
    n_prime3 = -kappa * y[5] + tau * y[11]

    b_prime1 = -tau * y[6]
    b_prime2 = -tau * y[7]
    b_prime3 = -tau * y[8]

    return [
        gamma_prime1, gamma_prime2, gamma_prime3,
        t_prime1, t_prime2, t_prime3,
        n_prime1, n_prime2, n_prime3,
        b_prime1, b_prime2, b_prime3
    ]


def solve_frenet_serre(p0: Tuple[float, float, float],
                       t0: Tuple[float, float, float],
                       n0: Tuple[float, float, float],
                       b0: Tuple[float, float, float],
                       kappa: float, tau: float, ival: float):
    """
    Solves the Frenet Serre equations to calculate a curve with
    the given inital conditions, curvature and torsion.'

    Example: Curve in the yz plane
        pos((0, 1, 0), 10, (0, 0, 1), (0, -1, 0), (1, 0, 0), 1, 0)

    :param p0: initial curve position
    :param t0: initial tanjent vector
    :param n0: initial normal vector
    :param b0: initial binormal vector
    :param kappa: curvature
    :param tau: torsion
    :param ival: iterval to sample ahead
    :return: solution curve from 0 to s
    """
    y0 = [
        p0[0], p0[1], p0[2],
        t0[0], t0[1], t0[2],
        n0[0], n0[1], n0[2],
        b0[0], b0[1], b0[2]
    ]
    t = np.arange(0, ival, 0.1)

    # Plotting
    # ax = plt.axes(projection='3d')
    # ax.view_init(15, 0)
    # ax.plot3D(sol[:, 0], sol[:, 1], sol[:, 2])
    # ax.set_xlabel('x')
    # ax.set_ylabel('y')
    # ax.set_zlabel('z')
    # plt.show()

    sol = odeint(frenet_serre, y0, t, args=(kappa, tau))

    return sol


def tangent_to_hpr(tangent: Tuple[float, float, float],
                   normal: Tuple[float, float, float],
                   binormal: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """ Use the frenet frame to calculate the heading, pitch and roll """
    if tangent[0] == 0:
        h = 180
    elif tangent[0] > 0:
        h = atan(tangent[1] / tangent[0]) * 180 / pi + 90
    else:
        h = atan(tangent[1] / tangent[0]) * 180 / pi - 90
    p = 90 - atan(tangent[2]) * 180 / pi
    r = 0

    return h, p, r


if __name__ == "__main__":
    pass
