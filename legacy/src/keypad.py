import pygame
from pynput import keyboard

class GameBoyAdvanceKeypad:
    def __init__(self):
        self.KEYCODE_LEFT = 37
        self.KEYCODE_UP = 38
        self.KEYCODE_RIGHT = 39
        self.KEYCODE_DOWN = 40
        self.KEYCODE_START = 13
        self.KEYCODE_SELECT = 220
        self.KEYCODE_A = 90
        self.KEYCODE_B = 88
        self.KEYCODE_L = 65
        self.KEYCODE_R = 83

        self.GAMEPAD_LEFT = 14
        self.GAMEPAD_UP = 12
        self.GAMEPAD_RIGHT = 15
        self.GAMEPAD_DOWN = 13
        self.GAMEPAD_START = 9
        self.GAMEPAD_SELECT = 8
        self.GAMEPAD_A = 1
        self.GAMEPAD_B = 0
        self.GAMEPAD_L = 4
        self.GAMEPAD_R = 5
        self.GAMEPAD_THRESHOLD = 0.2

        self.A = 0
        self.B = 1
        self.SELECT = 2
        self.START = 3
        self.RIGHT = 4
        self.LEFT = 5
        self.UP = 6
        self.DOWN = 7
        self.R = 8
        self.L = 9

        self.currentDown = 0x03ff
        self.eatInput = False

        self.gamepads = []

        self.remappingKeyId = ""

        self.keyboard_listener = None

    def on_press(self, key):
        try:
            key_code = key.value.vk
        except AttributeError:
            key_code = key.value.data

        self.keyboardHandler(key_code)

    def on_release(self, key):
        try:
            key_code = key.value.vk
        except AttributeError:
            key_code = key.value.data

        self.keyboardHandler(key_code)

    def keyboardHandler(self, key_code):
        toggle = 0

        # Check for a remapping
        if self.remappingKeyId != "":
            self.remapKeycode(self.remappingKeyId, key_code)
            self.remappingKeyId = ""
            return

        if key_code == self.KEYCODE_START:
            toggle = self.START
        elif key_code == self.KEYCODE_SELECT:
            toggle = self.SELECT
        elif key_code == self.KEYCODE_A:
            toggle = self.A
        elif key_code == self.KEYCODE_B:
            toggle = self.B
        elif key_code == self.KEYCODE_L:
            toggle = self.L
        elif key_code == self.KEYCODE_R:
            toggle = self.R
        elif key_code == self.KEYCODE_UP:
            toggle = self.UP
        elif key_code == self.KEYCODE_RIGHT:
            toggle = self.RIGHT
        elif key_code == self.KEYCODE_DOWN:
            toggle = self.DOWN
        elif key_code == self.KEYCODE_LEFT:
            toggle = self.LEFT
        else:
            return

        toggle = 1 << toggle
        if key_code == pygame.KEYDOWN:
            self.currentDown &= ~toggle
        else:
            self.currentDown |= toggle

        if self.eatInput:
            return

    def gamepadHandler(self, gamepad):
        value = 0
        if gamepad.get_button(self.GAMEPAD_LEFT):
            value |= 1 << self.LEFT
        if gamepad.get_button(self.GAMEPAD_UP):
            value |= 1 << self.UP
        if gamepad.get_button(self.GAMEPAD_RIGHT):
            value |= 1 << self.RIGHT
        if gamepad.get_button(self.GAMEPAD_DOWN):
            value |= 1 << self.DOWN
        if gamepad.get_button(self.GAMEPAD_START):
            value |= 1 << self.START
        if gamepad.get_button(self.GAMEPAD_SELECT):
            value |= 1 << self.SELECT
        if gamepad.get_button(self.GAMEPAD_A):
            value |= 1 << self.A
        if gamepad.get_button(self.GAMEPAD_B):
            value |= 1 << self.B
        if gamepad.get_button(self.GAMEPAD_L):
            value |= 1 << self.L
        if gamepad.get_button(self.GAMEPAD_R):
            value |= 1 << self.R

        self.currentDown = ~value & 0x3ff

    def gamepadConnectHandler(self, gamepad):
        self.gamepads.append(gamepad)

    def gamepadDisconnectHandler(self, gamepad):
        self.gamepads = [other for other in self.gamepads if other != gamepad]

    def pollGamepads(self):
        pygame.event.get()
        self.gamepads = []

        for i in range(pygame.joystick.get_count()):
            gamepad = pygame.joystick.Joystick(i)
            gamepad.init()
            self.gamepads.append(gamepad)

        if len(self.gamepads) > 0:
            self.gamepadHandler(self.gamepads[0])

    def registerHandlers(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.keyboard_listener.start()

        pygame.init()
        pygame.joystick.init()

    def initKeycodeRemap(self, keyId):
        validKeyIds = ["A", "B", "SELECT", "START", "RIGHT", "LEFT", "UP", "DOWN", "R", "L"]
        if keyId in validKeyIds:
            self.remappingKeyId = keyId

    def remapKeycode(self, keyId, keycode):
        if keyId == "A":
            self.KEYCODE_A = keycode
        elif keyId == "B":
            self.KEYCODE_B = keycode
        elif keyId == "SELECT":
            self.KEYCODE_SELECT = keycode
        elif keyId == "START":
            self.KEYCODE_START = keycode
        elif keyId == "RIGHT":
            self.KEYCODE_RIGHT = keycode
        elif keyId == "LEFT":
            self.KEYCODE_LEFT = keycode
        elif keyId == "UP":
            self.KEYCODE_UP = keycode
        elif keyId == "DOWN":
            self.KEYCODE_DOWN = keycode
        elif keyId == "R":
            self.KEYCODE_R = keycode
        elif keyId == "L":
            self.KEYCODE_L = keycode