from direct.gui.DirectGui import *
from panda3d.core import TextNode, PandaNode, NodePath


class Menu:
    def __init__(self, parent):
        self.font = loader.loadFont("fonts/Wbxkomik.ttf")
        self.parent = parent

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
        self.title = DirectLabel(text="Flight Simulator",
                                 scale=0.125,
                                 pos=(0, 0, 0.65),
                                 parent=self.titleMenu,
                                 relief=None,
                                 text_font=self.font,
                                 text_fg=(1, 1, 1, 1))
        self.homeScreen = DirectFrame()
        self.controlScreenText = PandaNode("controlScreen")
        self.controlScreenButton = DirectFrame()
        self.controlNodes = []

        self.titleScreenCreate()
        self.controlScreenCreate()

        self.clean()

    def showHome(self):
        """ Method for starting the main home screen"""
        self.parent.setWindowSize(800, 600)
        self.homeScreen.show()
        self.titleMenu.show()
        self.titleMenuBackdrop.show()

    def clean(self):
        """ Remove the main home screen from view"""
        self.homeScreen.hide()
        self.titleMenu.hide()
        self.titleMenuBackdrop.hide()

    def quitMenu(self):
        """ End game """
        base.userExit()

    def titleScreenCreate(self):
        """ Create the buttons for the main home screen """
        btn = DirectButton(text="Tutorial",
                           command=self.parent.startTutorial,
                           pos=(0, 0, 0.3),
                           parent=self.homeScreen,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

        btn = DirectButton(text="Sandbox",
                           command=self.parent.startSandbox,
                           pos=(0, 0, 0),
                           parent=self.homeScreen,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

        btn = DirectButton(text="Controls",
                           command=self.controlShow,
                           pos=(0, 0, -0.3),
                           parent=self.homeScreen,
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
                           command=self.quitMenu,
                           pos=(0, 0, -0.6),
                           parent=self.homeScreen,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def controlScreenCreate(self):
        """ Initialise Controls Screen """
        controls = [
            "W + S: Torsion",
            "A + D: Curvature",
            "Q: Set Curvature to 0",
            "E: Set Torsion to 0",
            "Esc: Restart"
        ]

        for i, string in enumerate(controls):
            node = TextNode(str(i))
            self.controlScreenText.addChild(node)
            np = NodePath(node)
            np.setScale(0.07)
            np.setPos(-0.4, 0, 0.35 - i / 6)
            node.setText(string)
            node.setFont(self.font)
            node.setTextColor(255, 255, 255, 1)
            self.controlNodes.append((node, np))

        btn = DirectButton(text="Menu",
                           command=self.controlClear,
                           pos=(0, 0, -0.6),
                           parent=self.controlScreenButton,
                           scale=0.1,
                           text_font=self.font,
                           clickSound=loader.loadSfx("sounds/UIClick.ogg"),
                           frameTexture=self.buttonImages,
                           frameSize=(-4, 4, -1, 1),
                           text_scale=0.75,
                           relief=DGG.FLAT,
                           text_pos=(0, -0.2))
        btn.setTransparency(True)

    def controlShow(self):
        """ Show the control screen """
        self.homeScreen.hide()
        self.title.setText("Controls")
        NodePath(self.controlScreenText).reparentTo(aspect2d)
        self.controlScreenButton.show()

    def controlClear(self):
        """ Remove control screen from view"""
        NodePath(self.controlScreenText).detachNode()
        self.controlScreenButton.hide()
        self.title.setText("Flight Simulator")
        self.showHome()
