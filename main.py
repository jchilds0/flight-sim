from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import Vec3, NodePath, PandaNode, TextNode, GeoMipTerrain, TextureStage, WindowProperties, LineSegs
from curves import solve_frenet_serre, tangent_to_hpr


class MyApp(ShowBase):
    INTERVAL = 150
    SCALE = 0.1

    def __init__(self):
        ShowBase.__init__(self)

        # Window Size
        props = WindowProperties()
        props.setSize(1920, 1080)
        base.win.requestProperties(props)

        # Landscape
        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("myDynamicTerrain")
        self.root = self.terrain.getRoot()

        self.__init_terrain()

        # Skybox
        self.skysphere = loader.loadModel("SkySphere.bam")
        self.skysphere.setBin('background', 1)
        self.skysphere.setDepthWrite(0)
        self.skysphere.reparentTo(render)
        taskMgr.add(self.skysphereTask, "SkySphere Task")

        # Plane Model
        self.plane = loader.loadModel("models/plane/piper_pa18.obj")

        self.__init_plane()

        # Text Nodes
        self.text = {
            'Pos': TextNode('pos'),
            'Tangent': TextNode('tangent'),
            'Normal': TextNode('normal'),
            'Binormal': TextNode('binormal'),
            'kappa': TextNode('kappa'),
            'tau': TextNode('tau'),
        }

        self.control_nodes = []

        self.__init_text()

        self.__init_controls()

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane)
        self.floater.setZ(5)

        self.keyMap = {
            "tor+": False,
            "tor-": False,
            "curv+": False,
            "curv-": False,
            "tor0": False,
            "curv0": False,
        }

        self.accept("w", self.updateKeyMap, ["tor+", True])
        self.accept("w-up", self.updateKeyMap, ["tor+", False])
        self.accept("s", self.updateKeyMap, ["tor-", True])
        self.accept("s-up", self.updateKeyMap, ["tor-", False])
        self.accept("a", self.updateKeyMap, ["curv-", True])
        self.accept("a-up", self.updateKeyMap, ["curv-", False])
        self.accept("d", self.updateKeyMap, ["curv+", True])
        self.accept("d-up", self.updateKeyMap, ["curv+", False])
        self.accept("q", self.updateKeyMap, ["curv0", True])
        self.accept("q-up", self.updateKeyMap, ["curv0", False])
        self.accept("e", self.updateKeyMap, ["tor0", True])
        self.accept("e-up", self.updateKeyMap, ["tor0", False])

        self.updateTask = taskMgr.add(self.updateCurvTor, "updatePos")

        # Curve
        self.line = LineSegs()
        self.prev_line = LineSegs()
        self.line_node = self.prev_node = None
        self.line_np = self.prev_np = None

    def __init_text(self):
        lst = list(self.text.items())

        for i, item in enumerate(lst):
            key, value = item
            node = key + "NodePath"
            self.text[node] = aspect2d.attachNewNode(self.text[key])
            self.text[node].setScale(0.07)
            self.text[node].setPos(-1.6, 0, -0.3 - i / 10)

        self.updateTaskText = taskMgr.add(self.updateText, "updateText")

    def __init_controls(self):
        controls = [
            "W + S: Torsion",
            "A + D: Curvature",
            "Q: Set Curvature 0",
            "E: Set Torsion 0",
        ]

        for i, item in enumerate(controls):
            node = TextNode(str(i))
            np = aspect2d.attachNewNode(node)
            np.setScale(0.07)
            np.setPos(-1.6, 0, 0.8 - i / 10)
            node.setText(item)
            self.control_nodes.append((node, np))

    def __init_terrain(self):
        self.terrain.setHeightfield("models/terrain/heightmap.png")

        # Set terrain properties
        self.terrain.setBlockSize(128)
        self.terrain.setNear(40)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)

        # Store the root NodePath for convenience
        self.root.reparentTo(render)
        terrainNormal = loader.loadTexture("models/terrain/normal.png")
        self.root.setTexture(terrainNormal)
        self.root.setSz(50)

        # Generate it.
        self.terrain.generate()
        taskMgr.add(self.updateTerrain, "updateTer")

    def __init_plane(self):
        self.plane.reparentTo(render)
        planeTS = TextureStage('ts')
        planeDiffuse = loader.loadTexture("models/plane/textures/piper_diffuse.jpg")
        planeBump = loader.loadTexture("models/plane/textures/piper_bump.jpg")
        planeRefl = loader.loadTexture("models/plane/textures/piper_refl.jpg")
        self.plane.setTexture(planeTS, planeDiffuse)

        self.plane.setPos(100, 100, 100)
        self.plane.setHpr(0, 90, 0)
        self.time = 0
        self.tau = 0
        self.kappa = 0
        self.plane_T = (0, 1, 0)
        self.plane_N = (1, 0, 0)
        self.plane_B = (0, 0, 1)

    def skysphereTask(self, task):
        self.skysphere.setPos(base.camera, 0, 0, 0)
        return task.cont

    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    # Add a task to keep updating the terrain
    def updateTerrain(self, task):
        self.terrain.update()
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
        if self.keyMap["curv0"]:
            self.kappa = 0
        if self.keyMap["tor0"]:
            self.tau = 0

        sol = solve_frenet_serre(self.plane.getPos(), self.plane_T,
                                 self.plane_N, self.plane_B, self.kappa, self.tau, self.INTERVAL)

        self.draw_curve(sol[:, 0], sol[:, 1], sol[:, 2])

        index = 1
        self.plane.setPos(sol[index, 0], sol[index, 1], sol[index, 2])
        self.plane_T = (sol[index, 3], sol[index, 4], sol[index, 5])
        self.plane_N = (sol[index, 6], sol[index, 7], sol[index, 8])
        self.plane_B = (sol[index, 9], sol[index, 10], sol[index, 11])

        self.plane.setHpr(tangent_to_hpr(self.plane_T, self.plane_N, self.plane_B))
        self.camera.setPos(self.plane.getPos() - self.planeDir(20) + Vec3(0, 0, 10))
        self.camera.lookAt(self.floater)

        return task.cont

    def planeDir(self, scale):
        return Vec3(scale * self.plane_T[0], scale * self.plane_T[1], scale * self.plane_T[2])

    def updateText(self, task):
        pos_str = "Plane Pos: " + self.strVector(self.plane.getPos())
        tanjent_str = "Tangent: " + self.strVector(self.plane_T)
        normal_str = "Normal: " + self.strVector(self.plane_N)
        binormal_str = "Binormal: " + self.strVector(self.plane_B)
        kappa_str = "Curvature: " + str(round(self.kappa, 4))
        tau_str = "Torsion: " + str(round(self.tau, 4))

        self.text['Pos'].setText(pos_str)
        self.text['Tangent'].setText(tanjent_str)
        self.text['Normal'].setText(normal_str)
        self.text['Binormal'].setText(binormal_str)
        self.text['kappa'].setText(kappa_str)
        self.text['tau'].setText(tau_str)

        return task.cont

    def draw_curve(self, x, y, z):
        if self.line_np is not None:
            self.line_np.detach_node()

        self.prev_line.moveTo(x[0], y[0], z[0])
        self.prev_line.drawTo(x[1], y[1], z[1])
        self.prev_line.setThickness(4)

        for i in range(len(x) - 1):
            self.line.moveTo(x[i], y[i], z[i])
            self.line.drawTo(x[i + 1], y[i + 1], z[i + 1])
            self.line.setThickness(4)

        self.line_node = self.line.create()
        self.line_np = NodePath(self.line_node)
        self.line_np.reparentTo(render)

        self.prev_node = self.prev_line.create()
        self.prev_np = NodePath(self.prev_node)
        self.prev_np.reparentTo(render)

    @staticmethod
    def strVector(vector):
        digits = 2

        return "(" + str(round(vector[0], digits)) + ", " + str(round(vector[1], digits)) \
               + ", " + str(round(vector[2], digits)) + ")"

app = MyApp()
app.run()