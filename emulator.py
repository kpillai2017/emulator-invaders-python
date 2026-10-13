# Python port of the C++ Emulator class
import pygame

from core.game import Game
from memory import Memory
from iohandler import Io
from cpu import Cpu
from soundfx import SoundFX
from video import Video

class Emulator(Game):
    def __init__(self):
        super().__init__()
        self.emulIO = Io()
        self.emulMemory = Memory()
        self.emulCpu = Cpu()
        self.emulSoundFX = SoundFX()
        self.emulVideo = Video()
        self.mapX = 0
        self.mapY = 0
        self.SCROLL_SPEED = 10

    def init(self):
        if not self.init_system("Space Invaders Emulator", 800, 600, False):
            return False
        if not self.emulMemory.init("data/invaders.rom"):
            return False
        if not self.emulCpu.init(self.get_memory(), self.get_io()):
            return False
        if not self.emulSoundFX.init():
            return False
        if not self.emulVideo.init(self.get_graphics(), self.get_memory()):
            return False
        self.emulIO.init(self.get_input(), self.get_soundfx())
        self.set_fps(60)
        self.get_graphics().clear(0, 0, 0)
        return True

    def update(self):
        in_obj = self.get_input()
        # if in_obj.key_down('escape'):
        if in_obj.key_down(pygame.K_ESCAPE):
            self.end()
        self.emulIO.update()
        tmp_buf = "-> " + self.emulCpu.get_debug_output()
        self.emulVideo.draw_outline_font(tmp_buf, 0, 20, 255, 255, 255)
        self.emulCpu.run()
        self.emulVideo.draw()

    def draw(self, g):
        pass

    def get_soundfx(self):
        return self.emulSoundFX

    def get_memory(self):
        return self.emulMemory

    def get_video(self):
        return self.emulVideo

    def get_io(self):
        return self.emulIO

    def free(self):
        self.emulVideo.free()
        self.emulCpu.free()
        self.emulSoundFX.free()
        self.emulMemory.free()
        self.free_system()
