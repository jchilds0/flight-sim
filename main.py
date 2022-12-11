from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, WindowProperties

from src.game import SandBox, Tutorial
from src.menu import Menu


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.props = WindowProperties()
        self.sandbox = SandBox(self)
        self.tutorial = Tutorial(self)
        self.menuObject = Menu(self)

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
        self.accept("escape", self.updateKeyMap, ["esc", True])
        self.accept("escape-up", self.updateKeyMap, ["esc", False])

        self.menu()

    def startSandbox(self):
        self.menuObject.clean()
        self.sandbox.start()

    def startTutorial(self):
        self.menuObject.clean()
        self.tutorial.start()

    def menu(self):
        self.menuObject.showHome()

    def setWindowSize(self, x: int, y: int):
        self.props.setSize(x, y)
        base.win.requestProperties(self.props)

    def updateKeyMap(self, controlName, controlState):
        self.keyMap[controlName] = controlState

    def setCameraPos(self, x, y, z):
        self.camera.setPos(x, y, z)

    def lookAtCamera(self, obj):
        self.camera.lookAt(obj)


app = MyApp()
app.run()