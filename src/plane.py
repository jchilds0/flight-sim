from panda3d.core import TextureStage
from typing import Tuple


class Plane:
    def __init__(self):

        self.time = None
        self.tau = None
        self.kappa = None
        self.plane_T = None
        self.plane_N = None
        self.plane_B = None

        self.model = loader.loadModel("models/plane/piper_pa18.obj")
        planeTS = TextureStage('ts')
        planeDiffuse = loader.loadTexture("models/plane/textures/piper_diffuse.jpg")
        planeBump = loader.loadTexture("models/plane/textures/piper_bump.jpg")
        planeRefl = loader.loadTexture("models/plane/textures/piper_refl.jpg")
        self.model.setTexture(planeTS, planeDiffuse)
        self.model.reparentTo(render)

    def start(self, p0: Tuple[float, float, float],
              tangent: Tuple[float, float, float] = (0, 1, 0),
              normal: Tuple[float, float, float] = (1, 0, 0),
              binormal: Tuple[float, float, float] = (0, 0, 1)):
        """ Initialise plane parameters """
        self.model.setPos(p0[0], p0[1], p0[2])
        self.model.setHpr(0, 90, 0)
        self.time = 0
        self.tau = 0
        self.kappa = 0
        self.plane_T = tangent
        self.plane_N = normal
        self.plane_B = binormal

    def getT(self) -> Tuple[float, float, float]:
        return self.plane_T

    def setT(self, tx: float, ty: float, tz: float):
        self.plane_T = (tx, ty, tz)

    def getN(self) -> Tuple[float, float, float]:
        return self.plane_N

    def setN(self, nx: float, ny: float, nz: float):
        self.plane_N = (nx, ny, nz)

    def getB(self) -> Tuple[float, float, float]:
        return self.plane_B

    def setB(self, bx: float, by: float, bz: float):
        self.plane_B = (bx, by, bz)

    def setPos(self, x: float, y: float, z: float):
        self.model.setPos(x, y, z)

    def getPos(self) -> Tuple[float, float, float]:
        return self.model.getPos()

    def setHpr(self, hpr: Tuple[float, float, float]):
        self.model.setHpr(hpr[0], hpr[1], hpr[2])
