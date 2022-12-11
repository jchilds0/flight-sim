from abc import ABC, abstractmethod
from collections import deque
from direct.gui.DirectGui import *
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import GeoMipTerrain, TextureStage, TexGenAttrib, PointLight, LineSegs, NodePath, PandaNode, \
    TextNode

from src.curves import solve_frenet_serre, tangent_to_hpr
from src.plane import Plane


class World(ABC):
    INTERVAL = 150
    SCALE = 0.001

    def __init__(self, parent):
        self.parent = parent

        # Create Terrain
        self.terrain = GeoMipTerrain("myDynamicTerrain")
        self.root = self.terrain.getRoot()

        self.terrainGenerate()

        # Skybox
        self.sphere = loader.loadModel("models/skysphere/InvertedSphere.egg")

        self.skyboxGenerate()

        # Plane
        self.plane = Plane()

        # Text Nodes
        self.text = ['Pos', 'Tangent', 'Normal', 'Binormal', 'kappa', 'tau']
        self.textObject = [
            OnscreenText(pos=(-1.7, -0.4 - i / 10), scale=0.07, align=TextNode.ALeft, fg=(255, 255, 255, 1))
            for i in range(len(self.text))]

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane.model)
        self.floater.setZ(5)

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

        self.buttonImages = (
            loader.loadTexture("ui/UIButton.png"),
            loader.loadTexture("ui/UIButtonPressed.png"),
            loader.loadTexture("ui/UIButtonHighlighted.png"),
            loader.loadTexture("ui/UIButtonDisabled.png")
        )

        self.gameOverScreen = DirectDialog(frameSize=(-0.7, 0.7, -0.7, 0.7),
                                           fadeScreen=0.4,
                                           relief=DGG.FLAT,
                                           frameTexture="ui/stoneFrame.png")
        self.gameoverScreenGenerate()

        self.titleScreen = DirectDialog(frameSize=(-0.7, 0.7, -0.7, 0.7),
                                        fadeScreen=0.4,
                                        relief=DGG.FLAT,
                                        frameTexture="ui/stoneFrame.png")
        self.title = self.desc = self.titleBtn = None
        self.titleScreenGenerate()

    @abstractmethod
    def start(self):
        """ Run the program """
        pass

    def drawModels(self):
        """ Draw all models and initialise cameras"""
        self.parent.setWindowSize(1920, 1080)
        self.root.reparentTo(render)
        self.sphere.reparentTo(render)
        self.plane.model.reparentTo(render)

    def startUpdaters(self):
        """ Add tasks to task manager """
        self.run()
        taskMgr.add(self.updateCollisionDetection, "updateCol")
        taskMgr.add(self.updateCurvTor, "updatePos")
        taskMgr.add(self.updateText, "updateText")

    def run(self):
        """ Reset variables to rerun the program """
        # Hide Gameover Screen
        if not self.gameOverScreen.isHidden():
            self.gameOverScreen.hide()

        if not self.titleScreen.isHidden():
            self.titleScreen.hide()

        # Initialise Plane
        self.plane.start(p0=(50, 50, 30))

        # Clear Lines
        self.clearCurve()

    @staticmethod
    def stopUpdaters():
        """ Stop tasks """
        taskMgr.remove("updateCol")
        taskMgr.remove("updatePos")
        taskMgr.remove("updateText")

    def clean(self):
        self.gameOverScreen.hide()
        self.titleScreen.hide()
        self.clearText()
        self.clearCurve()
        self.root.detachNode()
        self.sphere.detachNode()
        self.plane.model.detachNode()

        self.stopUpdaters()

    def menu(self):
        self.clean()
        self.parent.menu()

    @abstractmethod
    def level(self):
        """ Handle passing between levels """
        pass

    def terrainGenerate(self):
        self.terrain.setHeightfield("terrain/heightmap_2049.png")

        # Set terrain properties
        self.terrain.setBlockSize(1024)
        # self.terrain.setNear(40)
        # self.terrain.setFar(1000)
        # self.terrain.setFocalPoint(base.camera)

        # Store the root NodePath for convenience
        terrainNormal = loader.loadTexture("terrain/base_color_darker_2049.png")
        self.root.setTexture(terrainNormal)
        self.root.setSz(75)
        self.root.setSx(0.1)
        self.root.setSy(0.1)

        # Generate it.
        self.terrain.generate()
        # taskMgr.add(self.updateTerrain, "updateTer")

    def skyboxGenerate(self):
        # Load a sphere with a radius of 1 unit and the faces directed inward.
        self.sphere.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        self.sphere.setTexProjector(TextureStage.getDefault(), render, self.sphere)
        self.sphere.setTexPos(TextureStage.getDefault(), 0, 0, 0)
        self.sphere.setTexScale(TextureStage.getDefault(), .5)

        tex = loader.loadCubeMap("models/skysphere/BlueGreenNebula_#.png")
        self.sphere.setTexture(tex)
        self.sphere.setLightOff()
        self.sphere.setScale(1000)

    def drawText(self):
        for i, string in enumerate(self.text):
            self.textObject[i] = OnscreenText(text=string, pos=(-1.6, 0, -0.3 - i / 10), scale=0.07)

    def clearText(self):
        for i, string in enumerate(self.text):
            self.textObject[i].setText("")

    def updateTerrain(self, task):
        self.terrain.update()
        return task.cont

    def updateCurvTor(self, task):
        """ Movement bases on curvature and torsion """
        if self.parent.keyMap["tor+"]:
            self.plane.tau += self.SCALE
        if self.parent.keyMap["tor-"]:
            self.plane.tau -= self.SCALE
        if self.parent.keyMap["curv+"]:
            self.plane.kappa += self.SCALE
        if self.parent.keyMap["curv-"]:
            self.plane.kappa -= self.SCALE
        if self.parent.keyMap["curv0"]:
            self.plane.kappa = 0
        if self.parent.keyMap["tor0"]:
            self.plane.tau = 0
        if self.parent.keyMap["esc"]:
            self.menu()

        sol = solve_frenet_serre(self.plane.getPos(), self.plane.getT(), self.plane.getN(), self.plane.getB(),
                                 self.plane.kappa, self.plane.tau, self.INTERVAL)

        self.drawCurve(sol[:, 0], sol[:, 1], sol[:, 2])

        index = 1
        self.plane.setPos(sol[index, 0], sol[index, 1], sol[index, 2])
        self.plane.setT(sol[index, 3], sol[index, 4], sol[index, 5])
        self.plane.setN(sol[index, 6], sol[index, 7], sol[index, 8])
        self.plane.setB(sol[index, 9], sol[index, 10], sol[index, 11])

        self.plane.setHpr(tangent_to_hpr(self.plane.getT(), self.plane.getN(), self.plane.getB()))

        self.camPos(20)
        self.parent.lookAtCamera(self.floater)

        return task.cont

    def camPos(self, scale):
        x = self.plane.getPos()[0] - scale * self.plane.getT()[0]
        y = self.plane.getPos()[1] - scale * self.plane.getT()[1]
        z = self.plane.getPos()[2] - scale * self.plane.getT()[2] + 10

        self.parent.setCameraPos(x, y, z)

    def updateText(self, task):
        pos_str = "Plane Pos: " + self.strVector(self.plane.getPos())
        tanjent_str = "Tangent: " + self.strVector(self.plane.getT())
        normal_str = "Normal: " + self.strVector(self.plane.getN())
        binormal_str = "Binormal: " + self.strVector(self.plane.getB())
        kappa_str = "Curvature: " + str(round(self.plane.kappa, 4))
        tau_str = "Torsion: " + str(round(self.plane.tau, 4))

        self.textObject[0].setText(pos_str)
        self.textObject[1].setText(tanjent_str)
        self.textObject[2].setText(normal_str)
        self.textObject[3].setText(binormal_str)
        self.textObject[4].setText(kappa_str)
        self.textObject[5].setText(tau_str)

        return task.cont

    def drawCurve(self, x, y, z):
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

    def clearCurve(self):
        if self.prev_np is not None:
            n = len(self.prev_np)
            for _ in range(n):
                self.prev_np.pop().detach_node()

            self.prev_np.clear()

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

    def gameoverScreenGenerate(self):
        font = loader.loadFont("fonts/Wbxkomik.ttf")

        self.gameOverScreen.hide()

        title = DirectLabel(text="You Crashed!",
                            parent=self.gameOverScreen,
                            scale=0.1,
                            pos=(0, 0, 0.2),
                            text_font=font,
                            relief=None)

        btn = DirectButton(text="Restart",
                           command=self.run,
                           pos=(-0.3, 0, -0.2),
                           parent=self.gameOverScreen,
                           scale=0.07,
                           text_font=font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

        btn = DirectButton(text="Menu",
                           command=self.menu,
                           pos=(0.3, 0, -0.2),
                           parent=self.gameOverScreen,
                           scale=0.07,
                           text_font=font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def titleScreenGenerate(self):
        font = loader.loadFont("fonts/Wbxkomik.ttf")

        self.titleScreen.hide()

        self.title = DirectLabel(text="",
                                 parent=self.titleScreen,
                                 scale=0.1,
                                 pos=(0, 0, 0.2),
                                 text_font=font,
                                 relief=None)

        self.desc = DirectLabel(text="This is a description",
                                parent=self.titleScreen,
                                scale=0.05,
                                pos=(0, 0, 0),
                                text_font=font,
                                relief=None)

        self.titleBtn = DirectButton(text="Start",
                                     command=self.level,
                                     pos=(-0.3, 0, -0.2),
                                     parent=self.titleScreen,
                                     scale=0.07,
                                     text_font=font,
                                     clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                                     frameTexture=self.buttonImages,
                                     frameSize=(-4, 4, -1, 1),
                                     text_scale=0.75,
                                     relief=DGG.FLAT,
                                     text_pos=(0, -0.2))
        self.titleBtn.setTransparency(True)

        btn = DirectButton(text="Menu",
                           command=self.menu,
                           pos=(0.3, 0, -0.2),
                           parent=self.titleScreen,
                           scale=0.07,
                           text_font=font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def setTitle(self, text: str):
        self.title.setText(text)


class SandBox(World):
    def start(self):
        self.drawModels()
        self.startUpdaters()

    def level(self):
        pass


class Tutorial(World):
    def __init__(self, parent):
        World.__init__(self, parent)

        self.levelNum = 0

        self.levelText = [
            "Level 0: Circles",
            "",
        ]

    def start(self):
        self.drawModels()
        self.setTitle(self.levelText[0])
        self.titleScreen.show()

    def level(self):
        if self.levelNum == 0:
            self.startUpdaters()
