from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import Vec3, NodePath, PandaNode
from math import pi, cos, sin


class MyApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # Landscape
        self.environ = self.loader.loadModel("models/world")
        self.environ.reparentTo(render)

        self.environ.setPos(0, 0, -30)

        # Plane Model
        self.plane = loader.loadModel("models/plane/piper_pa18.obj")
        self.plane.reparentTo(render)
        planeTexture = loader.loadTexture("models/plane/textures/piper_diffuse.jpg")
        self.plane.setTexture(planeTexture)

        self.plane.setPos(0, 30, 0)
        self.plane.setHpr(180, 90, 0)
        self.plane_theta = pi / 2

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane)
        self.floater.setZ(5)

        self.keyMap = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }

        self.accept("w", self.updateKeyMap, ["up", True])
        self.accept("w-up", self.updateKeyMap, ["up", False])
        self.accept("s", self.updateKeyMap, ["down", True])
        self.accept("s-up", self.updateKeyMap, ["down", False])
        self.accept("a", self.updateKeyMap, ["left", True])
        self.accept("a-up", self.updateKeyMap, ["left", False])
        self.accept("d", self.updateKeyMap, ["right", True])
        self.accept("d-up", self.updateKeyMap, ["right", False])

        self.updateTask = taskMgr.add(self.update, "update")

    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    def update(self, task):
        dt = globalClock.getDt()

        self.plane.setPos(self.plane.getPos() + self.plane_dir(1/20))

        # If any movement keys are pressed, use the above time
        # to calculate how far to move the character, and apply that.
        if self.keyMap["up"]:
            self.plane.setPos(self.plane.getPos() + Vec3(0, 0, 5.0 * dt))
        if self.keyMap["down"]:
            self.plane.setPos(self.plane.getPos() + Vec3(0, 0, -5.0 * dt))
        if self.keyMap["left"]:
            self.plane_theta += dt / 2
            self.plane.setHpr(90 + self.plane_theta * 180 / pi, 90, 0)
        if self.keyMap["right"]:
            self.plane_theta -= dt / 2
            self.plane.setHpr(90 + self.plane_theta * 180 / pi, 90, 0)

        self.camera.setPos(self.plane.getPos() - self.plane_dir(15) + Vec3(0, 0, 5))
        self.camera.lookAt(self.floater)

        return task.cont

    def plane_dir(self, scale):
        return Vec3(cos(self.plane_theta) * scale, sin(self.plane_theta) * scale, 0)


app = MyApp()
app.run()