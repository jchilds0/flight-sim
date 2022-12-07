from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, NodePath, PandaNode, TextNode
from math import pi
from curves import solve_frenet_serre, tanjent_to_hpr


class MyApp(ShowBase):
    DEFAULT_STEP = 0.1
    SCALE = 0.1

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
        self.plane.setHpr(0, 90, 0)
        self.time = 0
        self.tau = 0
        self.kappa = 0
        self.plane_pos = (0, 0, 0)
        self.plane_T = [(0, -1, 0), (0, -1, 0)]
        self.plane_N = [(1, 0, 0), (1, 0, 0)]
        self.plane_B = [(0, 0, 1), (0, 0, 1)]

        # Text Nodes
        self.text = {
            'Pos': TextNode('pos'),
            'GetPos': TextNode('get_pos'),
            'Tanjent': TextNode('tanjent'),
            'Normal': TextNode('normal'),
            'Binormal': TextNode('binormal'),
            'kappa': TextNode('kappa'),
            'tau': TextNode('tau'),
        }

        self.__init_text()

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane)
        self.floater.setZ(5)

        self.keyMap = {
            "tor+": False,
            "tor-": False,
            "curv+": False,
            "curv-": False,
        }

        self.accept("w", self.updateKeyMap, ["tor+", True])
        self.accept("w-up", self.updateKeyMap, ["tor+", False])
        self.accept("s", self.updateKeyMap, ["tor-", True])
        self.accept("s-up", self.updateKeyMap, ["tor-", False])
        self.accept("a", self.updateKeyMap, ["curv+", True])
        self.accept("a-up", self.updateKeyMap, ["curv+", False])
        self.accept("d", self.updateKeyMap, ["curv-", True])
        self.accept("d-up", self.updateKeyMap, ["curv-", False])

        self.updateTask = taskMgr.add(self.updateCurvTor, "updatePos")
        self.updateTaskText = taskMgr.add(self.updateText, "updateText")

    def __init_text(self):
        lst = list(self.text.items())

        for i, item in enumerate(lst):
            key, value = item
            node = key + "NodePath"
            self.text[node] = aspect2d.attachNewNode(self.text[key])
            self.text[node].setScale(0.07)
            self.text[node].setPos(-1, 0, -i/10)

    def updateKeyMap(self, controlName, controlState):
        self.time = 0
        self.plane_pos = self.plane.getPos()
        self.plane_T[1] = self.plane_T[0]
        self.plane_N[1] = self.plane_N[0]
        self.plane_B[1] = self.plane_B[0]
        self.keyMap[controlName] = controlState

    def updateDefault(self, task):
        """ Default movement """
        dt = globalClock.getDt()

        self.plane.setPos(self.plane.getPos() + self.planeDir(1 / 20))

        # If any movement keys are pressed, use the above time
        # to calculate how far to move the character, and apply that.
        if self.keyMap["up"]:
            self.plane.setPos(self.plane.getPos() + Vec3(0, 0, 5.0 * dt))
        if self.keyMap["down"]:
            self.plane.setPos(self.plane.getPos() + Vec3(0, 0, -5.0 * dt))
        if self.keyMap["left"]:
            self.plane_theta += dt / 2
            self.plane.setHpr(self.plane_theta * 180 / pi + 90, 90, 0)
        if self.keyMap["right"]:
            self.plane_theta -= dt / 2
            self.plane.setHpr(self.plane_theta * 180 / pi + 90, 90, 0)

        self.camera.setPos(self.plane.getPos() - self.planeDir(15) + Vec3(0, 0, 5))
        self.camera.lookAt(self.floater)

        return task.cont

    def updateCurvTor(self, task):
        """ Movement bases on curvature and torsion """
        dt = globalClock.getDt()

        if self.keyMap["tor+"]:
            self.tau += dt * self.SCALE
        if self.keyMap["tor-"]:
            self.tau -= dt * self.SCALE
        if self.keyMap["curv+"]:
            self.kappa += dt * self.SCALE
        if self.keyMap["curv-"]:
            self.kappa -= dt * self.SCALE

        sol = solve_frenet_serre(self.plane_pos, self.time + 1, self.plane_T[1],
                                 self.plane_N[1], self.plane_B[1], self.kappa, self.tau)

        self.plane.setPos(sol[self.time, 0], sol[self.time, 1], sol[self.time, 2])
        self.plane_T[0] = (sol[self.time, 3], sol[self.time, 4], sol[self.time, 5])
        self.plane_N[0] = (sol[self.time, 6], sol[self.time, 7], sol[self.time, 8])
        self.plane_B[0] = (sol[self.time, 9], sol[self.time, 10], sol[self.time, 11])

        self.plane.setHpr(tanjent_to_hpr(self.plane_T[0], self.plane_N[0], self.plane_B[0]))
        self.camera.setPos(self.plane.getPos() - self.planeDir(20) + Vec3(0, 0, 10))
        self.camera.lookAt(self.floater)
        self.time += 1

        return task.cont

    def planeDir(self, scale):
        return Vec3(scale * self.plane_T[0][0], scale * self.plane_T[0][1], scale * self.plane_T[0][2])

    def updateText(self, task):
        pos_str = "Plane Pos: " + str(self.plane_pos)
        get_pos_str = "Get Pos: " + str(self.plane.getPos())
        tanjent_str = "Tanjent: " + str(self.plane_T)
        normal_str = "Normal: " + str(self.plane_N)
        binormal_str = "Binormal: " + str(self.plane_B)
        kappa_str = "Curvature: " + str(self.kappa)
        tau_str = "Torsion: " + str(self.tau)

        self.text['Pos'].setText(pos_str)
        self.text['GetPos'].setText(get_pos_str)
        self.text['Tanjent'].setText(tanjent_str)
        self.text['Normal'].setText(normal_str)
        self.text['Binormal'].setText(binormal_str)
        self.text['kappa'].setText(kappa_str)
        self.text['tau'].setText(tau_str)

        return task.cont


app = MyApp()
app.run()