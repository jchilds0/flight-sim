from abc import ABC, abstractmethod
from math import sin, cos, pi, fabs

import numpy as np
from direct.gui.DirectGui import *
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import GeoMipTerrain, TextureStage, TexGenAttrib, PointLight, LineSegs, NodePath, PandaNode, \
    TextNode
from typing import Tuple

from src.curves import solve_frenet_serre, tangent_to_hpr
from src.plane import Plane


class World(ABC):
    INTERVAL = 150
    SCALE = 0.001

    def __init__(self, parent):
        self.parent = parent
        self.font = loader.loadFont("fonts/Wbxkomik.ttf")

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
        self.textObject = [TextNode(string) for string in self.text]

        self.nodeHUD = PandaNode("HUD")
        self.npHUD = NodePath(self.nodeHUD)

        for i, node in enumerate(self.textObject):
            np = NodePath(node)
            np.setPos(-1.7, 0, -0.4 - i / 10)
            np.setScale(0.07)
            self.nodeHUD.addChild(node)
            node.setTextColor(255, 255, 255, 1)

        # Floater for camera
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.plane.model)
        self.floater.setZ(5)

        # Curve
        self.line = LineSegs()
        self.line.setThickness(4)
        self.prev_line = LineSegs()
        self.prev_line.setThickness(4)

        self.curves = PandaNode('Curve')
        self.lineAhead = PandaNode('lineAhead')
        self.lineBehind = PandaNode('lineBehind')
        NodePath(self.lineAhead).reparentTo(NodePath(self.curves))
        NodePath(self.lineBehind).reparentTo(NodePath(self.curves))

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
        NodePath(self.curves).reparentTo(render)

    def startUpdaters(self):
        """ Add tasks to task manager """
        self.run()
        self.npHUD.reparentTo(aspect2d)
        taskMgr.add(self.updateCollisionDetection, "updateCol")
        taskMgr.add(self.updateCurvTor, "updatePos")
        taskMgr.add(self.updateHUD, "updateHUD")

    def run(self):
        """ Reset variables to rerun the program """
        # Hide Gameover Screen
        if not self.gameOverScreen.isHidden():
            self.gameOverScreen.hide()

        # Initialise Plane
        self.plane.start(p0=(10, 40, 40))

        # Clear Lines
        self.lineAhead.removeAllChildren()
        self.lineBehind.removeAllChildren()

    @staticmethod
    def stopUpdaters():
        """ Stop tasks """
        taskMgr.remove("updateCol")
        taskMgr.remove("updatePos")
        taskMgr.remove("updateHUD")

    def clean(self):
        self.gameOverScreen.hide()
        self.npHUD.detachNode()
        self.root.detachNode()
        self.sphere.detachNode()
        self.plane.model.detachNode()
        NodePath(self.curves).detachNode()

        self.stopUpdaters()

    def menu(self):
        self.clean()
        self.parent.menu()

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

    def updateHUD(self, task):
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
        self.lineAhead.removeAllChildren()

        self.prev_line.moveTo(x[0], y[0], z[0])
        self.prev_line.drawTo(x[1], y[1], z[1])

        for i in range(len(x) - 1):
            self.line.drawTo(x[i + 1], y[i + 1], z[i + 1])

        NodePath(self.line.create()).reparentTo(NodePath(self.lineAhead))

        for i in range(len(x) - 1):
            self.line.setVertexColor(i, 255, 255, 0, 1)

        NodePath(self.prev_line.create()).reparentTo(NodePath(self.lineBehind))

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
        self.gameOverScreen.hide()

        title = DirectLabel(text="You Crashed!",
                            parent=self.gameOverScreen,
                            scale=0.1,
                            pos=(0, 0, 0.2),
                            text_font=self.font,
                            relief=None)

        btn = DirectButton(text="Restart",
                           command=self.run,
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

        btn = DirectButton(text="Menu",
                           command=self.menu,
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


class SandBox(World):
    def start(self):
        self.drawModels()
        self.startUpdaters()

    def level(self):
        pass


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


class Tutorial(World, ABC):
    def __init__(self, parent):
        super().__init__(parent)

        self.titleScreen = DirectDialog(frameSize=(-0.7, 0.7, -0.7, 0.7),
                                        fadeScreen=0.4,
                                        relief=DGG.FLAT,
                                        frameTexture="ui/stoneFrame.png")
        self.title = self.desc = self.titleBtn = None
        self.titleScreenGenerate()

        self.levelCompleteScreen = DirectDialog(frameSize=(-0.7, 0.7, -0.7, 0.7),
                                                fadeScreen=0.4,
                                                relief=DGG.FLAT,
                                                frameTexture="ui/stoneFrame.png")
        self.levelCompleteScreenGenerate()

        self.levelLineNode = PandaNode('levelLineNode')
        NodePath(self.levelLineNode).reparentTo(NodePath(self.curves))

    @abstractmethod
    def levelStart(self):
        pass

    @abstractmethod
    def levelComplete(self):
        pass

    @abstractmethod
    def nextLevel(self):
        pass

    def titleScreenGenerate(self):
        self.titleScreen.hide()

        self.title = DirectLabel(text="",
                                 parent=self.titleScreen,
                                 scale=0.1,
                                 pos=(0, 0, 0.2),
                                 text_font=self.font,
                                 relief=None)

        self.desc = DirectLabel(text="",
                                parent=self.titleScreen,
                                scale=0.05,
                                pos=(0, 0, 0),
                                text_font=self.font,
                                relief=None)

        self.titleBtn = DirectButton(text="Start",
                                     command=self.levelStart,
                                     pos=(-0.3, 0, -0.2),
                                     parent=self.titleScreen,
                                     scale=0.07,
                                     text_font=self.font,
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
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def levelCompleteScreenGenerate(self):
        self.levelCompleteScreen.hide()

        title = DirectLabel(text="Level Complete!",
                            parent=self.levelCompleteScreen,
                            scale=0.1,
                            pos=(0, 0, 0.2),
                            text_font=self.font,
                            relief=None)

        btn = DirectButton(text="Next Level",
                           command=self.nextLevel,
                           pos=(-0.3, 0, -0.2),
                           parent=self.levelCompleteScreen,
                           scale=0.07,
                           text_font=self.font,
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
                           parent=self.levelCompleteScreen,
                           scale=0.07,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)


class TutorialLevel1(Tutorial):
    def __init__(self, parent):
        super().__init__(parent)
        self.ring = None
        self.ringLines = []

    def start(self):
        self.drawModels()
        self.title.setText("Level 1: Circles")
        self.desc.setText("Set a positive curvature to make a circle")
        self.titleScreen.show()

    def run(self):
        super().run()

        self.ring = 0

        self.ringLines[0].setColor(1)
        for ring in self.ringLines[1:]:
            ring.setColor(0)

    def clean(self):
        self.titleScreen.hide()
        self.levelCompleteScreen.hide()
        self.levelLineNode.removeAllChildren()
        super().clean()

    def levelStart(self):
        if not self.titleScreen.isHidden():
            self.titleScreen.hide()

        # Draw Circles + Color them
        self.drawCircles()
        # Start Game Updaters
        taskMgr.add(self.updateLevel, "level")
        self.startUpdaters()

    def updateLevel(self, task):
        if self.ringLines[self.ring].isInsideRing(self.plane.getPos()):
            self.ringLines[self.ring].setColor(2)
            self.ring += 1

            # Check if all rings have been completed
            if self.ring == len(self.ringLines):
                taskMgr.remove("level")
                self.levelComplete()
            else:
                self.ringLines[self.ring].setColor(1)

        return task.cont

    def drawCircles(self):
        outerCenter, outerRadius = (110, 110, 40), 100
        numSegs = 12

        angles = [pi - 2 * pi * i / numSegs for i in range(numSegs - 3)]

        innerRadius = 10
        self.ringLines = [TorusCircle(theta, innerRadius, outerCenter, outerRadius, self.levelLineNode) for theta in
                          angles]
        self.ringLines[0].setColor(1)
        self.ring = 0

    def levelComplete(self):
        self.plane.setT(0, 0, 0)
        self.plane.setN(0, 0, 0)
        self.plane.setB(0, 0, 0)
        self.levelCompleteScreen.show()

    def nextLevel(self):
        self.clean()
        self.parent.tutorial2.start()
