from math import cos, pi, sin, fabs
from typing import Tuple

import numpy as np
from panda3d.core import LineSegs, NodePath


def unitVector(x, y):
    """ Unit vector of x - y """
    z = (
        x[0] - y[0],
        x[1] - y[1],
        x[2] - y[2],
    )

    zHat = (z[0] ** 2 + z[1] ** 2 + z[2] ** 2) ** 0.5

    return z[0] / zHat, z[1] / zHat, z[2] / zHat


def rotateVector(pos, center, theta):
    """ Rotate pos by theta radians about center """
    x = pos[0] - center[0]
    y = pos[1] - center[1]

    rotX = cos(theta) * x - sin(theta) * y
    rotY = sin(theta) * x + cos(theta) * y

    return rotX + center[0], rotY + center[1], center[2]


class TorusCircle:
    """ Create a circle which is a slice of a Torus using LineSegs """

    def __init__(self, theta: float, r1: float, c2: Tuple[float, float, float],
                 r2: float, parent):
        self.line = LineSegs()
        self.ring = None
        self.parent = parent
        self.line.setThickness(20)
        self.v = theta
        self.radius = r1
        self.outerCenter = c2
        self.outerRadius = r2

        self.draw()

    def draw(self):
        """ Torus Map: x(u,v)=((r cosu + a)cosv,(r cosu + a)sinv, r sinu) """
        for u in np.arange(0, 2 * pi + 0.2, 0.05):
            next_pos = (
                (self.radius * cos(u) + self.outerRadius) * cos(self.v),
                (self.radius * cos(u) + self.outerRadius) * sin(self.v),
                self.radius * sin(u)
            )
            self.line.drawTo(next_pos[0] + self.outerCenter[0],
                             next_pos[1] + self.outerCenter[1],
                             next_pos[2] + self.outerCenter[2])

        self.ring = self.line.create()
        NodePath(self.ring).reparentTo(NodePath(self.parent))

    def isInsideRing(self, pos: Tuple[float, float, float]):
        """ Check if the point pos is contained in the interior of the ring """
        dirVec = unitVector(pos, self.outerCenter)
        ringVec = (cos(self.v), sin(self.v))

        # Check if the angle to the centre point is the same
        if fabs(dirVec[0] - ringVec[0]) > 0.01 or fabs(dirVec[1] - ringVec[1]) > 0.01:
            return False

        # Rotate pos
        rotVec = rotateVector(pos, self.outerCenter, -self.v)

        x = rotVec[0] - (self.outerCenter[0] + self.outerRadius)
        z = rotVec[2] - self.outerCenter[2]

        return (x ** 2 + z ** 2) <= self.radius ** 2

    def setColor(self, num: int):
        """
        Set the color of a ring
        :param num: 0 - White, 1 - Yellow, 2 - Green
        :return: None
        """
        color = None
        if num == 0:
            color = (255, 255, 255, 1)
        elif num == 1:
            color = (255, 255, 0, 1)
        elif num == 2:
            color = (0, 255, 0, 1)
        else:
            pass

        for i in range(self.line.getNumVertices()):
            self.line.setVertexColor(i, color[0], color[1], color[2], color[3])
