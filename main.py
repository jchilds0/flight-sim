from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import NodePath, PandaNode, TextNode, GeoMipTerrain, WindowProperties, LineSegs, \
    PointLight, TextureStage, TexGenAttrib
from src.curves import solve_frenet_serre, tangent_to_hpr
from direct.gui.DirectGui import *
from collections import deque
from src.plane import Plane


class MyApp(ShowBase):
    INTERVAL = 150
    SCALE = 0.001

    def __init__(self):
        ShowBase.__init__(self)

        # Window Size
        props = WindowProperties()
        props.setSize(1920, 1080)
        base.win.requestProperties(props)

        # Landscape
        self.terrain = GeoMipTerrain("myDynamicTerrain")
        self.root = self.terrain.getRoot()

        self.__init_terrain()

        # Skybox
        self.sphere = loader.loadModel("models/skysphere/InvertedSphere.egg")

        self.__init_skybox()

        # Plane
        self.plane = Plane()

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

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane.model)
        self.floater.setZ(5)

        self.keyMap = {
            "tor+": False,
            "tor-": False,
            "curv+": False,
            "curv-": False,
            "tor0": False,
            "curv0": False,
            "esc": False,
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
        self.accept("escape", self.startGame)

        # Curve
        self.line = LineSegs()
        self.prev_line = LineSegs()
        self.line_node = self.prev_node = None
        self.line_np = None
        self.prev_np = deque()

        # Lighting
        plight = PointLight('plight')
        plight.setColor((1, 1, 1, 1))
        plnp = render.attachNewNode(plight)
        plnp.setPos(200, 200, 200)
        render.setLight(plnp)

        self.font = loader.loadFont("fonts/Wbxkomik.ttf")

        # Start Screen
        self.buttonImages = (
            loader.loadTexture("ui/UIButton.png"),
            loader.loadTexture("ui/UIButtonPressed.png"),
            loader.loadTexture("ui/UIButtonHighlighted.png"),
            loader.loadTexture("ui/UIButtonDisabled.png")
        )

        self.titleMenuBackdrop = DirectFrame(frameColor=(0, 0, 0, 1),
                                             frameSize=(-1, 1, -1, 1),
                                             parent=render2d)
        self.titleMenu = DirectFrame(frameColor=(1, 1, 1, 0))
        self.__init_titleScreen()

        # Game over
        self.gameOverScreen = DirectDialog(frameSize=(-0.7, 0.7, -0.7, 0.7),
                                           fadeScreen=0.4,
                                           relief=DGG.FLAT,
                                           frameTexture="ui/stoneFrame.png")
        self.__init_gameoverScreen()
        self.menu = True

    def startGame(self):
        self.gameOverScreen.hide()
        self.titleMenu.hide()
        self.titleMenuBackdrop.hide()

        # Initialise Plane
        self.plane.start(p0=(50, 50, 30))

        # Clear Lines
        if self.prev_np is not None:
            n = len(self.prev_np)
            for _ in range(n):
                self.prev_np.pop().detach_node()

            self.prev_np.clear()

        # Tasks
        if self.menu:
            self.menu = True
            self.__init_controls()

            taskMgr.add(self.updateCollisionDetection, "updateCol")
            taskMgr.add(self.updateCurvTor, "updatePos")
            taskMgr.add(self.updateText, "updateText")

    def quit(self):
        base.userExit()

    def __init_text(self):
        lst = list(self.text.items())

        for i, item in enumerate(lst):
            key, value = item
            node = key + "NodePath"
            self.text[node] = aspect2d.attachNewNode(self.text[key])
            self.text[node].setScale(0.07)
            self.text[node].setPos(-1.6, 0, -0.3 - i / 10)

    def __init_controls(self):
        controls = [
            "W + S: Torsion",
            "A + D: Curvature",
            "Q: Set Curvature to 0",
            "E: Set Torsion to 0",
            "Esc: Restart"
        ]

        for i, item in enumerate(controls):
            node = TextNode(str(i))
            np = aspect2d.attachNewNode(node)
            np.setScale(0.07)
            np.setPos(-1.6, 0, 0.8 - i / 10)
            node.setText(item)
            self.control_nodes.append((node, np))

    def __init_terrain(self):
        self.terrain.setHeightfield("terrain/heightmap_2049.png")

        # Set terrain properties
        self.terrain.setBlockSize(1024)
        self.terrain.setNear(40)
        self.terrain.setFar(1000)
        self.terrain.setFocalPoint(base.camera)

        # Store the root NodePath for convenience
        self.root.reparentTo(render)
        terrainNormal = loader.loadTexture("terrain/base_color_darker_2049.png")
        self.root.setTexture(terrainNormal)
        self.root.setSz(75)
        self.root.setSx(0.1)
        self.root.setSy(0.1)

        # Generate it.
        self.terrain.generate()
        # taskMgr.add(self.updateTerrain, "updateTer")

    def __init_skybox(self):
        # Load a sphere with a radius of 1 unit and the faces directed inward.
        self.sphere.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        self.sphere.setTexProjector(TextureStage.getDefault(), render, self.sphere)
        self.sphere.setTexPos(TextureStage.getDefault(), 0, 0, 0)
        self.sphere.setTexScale(TextureStage.getDefault(), .5)
        # Create some 3D texture coordinates on the sphere. For more info on this, check the Panda3D manual.

        tex = loader.loadCubeMap("models/skysphere/BlueGreenNebula_#.png")
        self.sphere.setTexture(tex)
        # Load the cube map and apply it to the sphere.

        self.sphere.setLightOff()
        # Tell the sphere to ignore the lighting.

        self.sphere.setScale(1000)
        # Increase the scale of the sphere so it will be larger than the scene.

        self.sphere.reparentTo(render)

    def __init_titleScreen(self):
        title3 = DirectLabel(text="Flight Simulator",
                             scale=0.125,
                             pos=(0, 0, 0.65),
                             parent=self.titleMenu,
                             relief=None,
                             text_font=self.font,
                             text_fg=(1, 1, 1, 1))

        btn = DirectButton(text="Start Game",
                           command=self.startGame,
                           pos=(0, 0, 0.2),
                           parent=self.titleMenu,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

        btn = DirectButton(text="Quit",
                           command=self.quit,
                           pos=(0, 0, -0.2),
                           parent=self.titleMenu,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def __init_gameoverScreen(self):
        self.gameOverScreen.hide()

        label = DirectLabel(text="You Crashed!",
                            parent=self.gameOverScreen,
                            scale=0.1,
                            pos=(0, 0, 0.2),
                            text_font=self.font,
                            relief=None)

        btn = DirectButton(text="Restart",
                           command=self.startGame,
                           pos=(-0.3, 0, -0.2),
                           parent=self.gameOverScreen,
                           scale=0.07,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

        btn = DirectButton(text="Quit",
                           command=self.quit,
                           pos=(0.3, 0, -0.2),
                           parent=self.gameOverScreen,
                           scale=0.07,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    # Add a task to keep updating the terrain
    def updateTerrain(self, task):
        self.terrain.update()
        return task.cont

    def updateCurvTor(self, task):
        """ Movement bases on curvature and torsion """
        if self.keyMap["tor+"]:
            self.plane.tau += self.SCALE
        if self.keyMap["tor-"]:
            self.plane.tau -= self.SCALE
        if self.keyMap["curv+"]:
            self.plane.kappa += self.SCALE
        if self.keyMap["curv-"]:
            self.plane.kappa -= self.SCALE
        if self.keyMap["curv0"]:
            self.plane.kappa = 0
        if self.keyMap["tor0"]:
            self.plane.tau = 0

        sol = solve_frenet_serre(self.plane.getPos(), self.plane.getT(), self.plane.getN(), self.plane.getB(),
                                 self.plane.kappa, self.plane.tau, self.INTERVAL)

        self.draw_curve(sol[:, 0], sol[:, 1], sol[:, 2])

        index = 1
        self.plane.setPos(sol[index, 0], sol[index, 1], sol[index, 2])
        self.plane.setT(sol[index, 3], sol[index, 4], sol[index, 5])
        self.plane.setN(sol[index, 6], sol[index, 7], sol[index, 8])
        self.plane.setB(sol[index, 9], sol[index, 10], sol[index, 11])

        self.plane.setHpr(tangent_to_hpr(self.plane.getT(), self.plane.getN(), self.plane.getB()))

        self.camPos(20)
        self.camera.lookAt(self.floater)

        return task.cont

    def camPos(self, scale):
        x = self.plane.getPos()[0] - scale * self.plane.getT()[0]
        y = self.plane.getPos()[1] - scale * self.plane.getT()[1]
        z = self.plane.getPos()[2] - scale * self.plane.getT()[2] + 10

        self.camera.setPos(x, y, z)

    def updateText(self, task):
        pos_str = "Plane Pos: " + self.strVector(self.plane.getPos())
        tanjent_str = "Tangent: " + self.strVector(self.plane.getT())
        normal_str = "Normal: " + self.strVector(self.plane.getN())
        binormal_str = "Binormal: " + self.strVector(self.plane.getB())
        kappa_str = "Curvature: " + str(round(self.plane.kappa, 4))
        tau_str = "Torsion: " + str(round(self.plane.tau, 4))

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
        self.prev_np.append(NodePath(self.prev_node))
        self.prev_np[-1].reparentTo(render)

    def updateCollisionDetection(self, task):
        plane_x, plane_y, plane_z = self.plane.getPos()

        if plane_z <= self.root.getSz() * self.terrain.getElevation(plane_x, plane_y):
            self.plane.setT(0, 0, 0)
            self.plane.setN(0, 0, 0)
            self.plane.setB(0, 0, 0)

            if self.gameOverScreen.isHidden():
                self.gameOverScreen.show()

        return task.cont

    @staticmethod
    def strVector(vector):
        digits = 2

        return "(" + str(round(vector[0], digits)) + ", " + str(round(vector[1], digits)) \
               + ", " + str(round(vector[2], digits)) + ")"


app = MyApp()
app.run()