# Python port of the C++ Io class
import pygame
from core.input import Input
from soundfx import SoundFX
from util import BIT0, BIT1, BIT2, BIT3, BIT4, BIT5, BIT6, BIT7

class Io:
    def __init__(self):
        self.IoSoundFX = None
        self.IoInput = None
        self.OUT_PORT2 = 0
        self.OUT_PORT3 = 0
        self.OUT_PORT4LO = 0
        self.OUT_PORT4HI = 0
        self.OUT_PORT5 = 0
        self.IN_PORT1 = 0
        self.IN_PORT2 = 0

    def init(self, in_obj: Input, sfx: SoundFX):
        self.IoSoundFX = sfx
        self.IoInput = in_obj
        self.IN_PORT2 = 0
        self.IN_PORT2 |= (BIT0 | BIT1)
        self.IN_PORT2 |= BIT7

    def update(self):
        self.IN_PORT1 &= ~(BIT0 | BIT1 | BIT2 | BIT4 | BIT5 | BIT6)
        self.IN_PORT2 &= ~(BIT2 | BIT4 | BIT5 | BIT6)
        if self.IoInput.key_down(pygame.K_1): self.IN_PORT1 |= BIT2
        if self.IoInput.key_down(pygame.K_2): self.IN_PORT1 |= BIT1
        if self.IoInput.key_down(pygame.K_t): self.IN_PORT2 |= BIT2
        if self.IoInput.key_down(pygame.K_LEFT):
            self.IN_PORT1 |= BIT5
            self.IN_PORT2 |= BIT5
        if self.IoInput.key_down(pygame.K_RIGHT):
            self.IN_PORT1 |= BIT6
            self.IN_PORT2 |= BIT6
        if self.IoInput.key_down(pygame.K_SPACE):
            self.IN_PORT1 |= BIT4
            self.IN_PORT2 |= BIT4
        if self.IoInput.key_down(pygame.K_3) or self.IoInput.key_down(pygame.K_5):
            self.IN_PORT1 |= BIT0
            self.IoSoundFX.play_coin()

    def output_port(self, port, value):
        if port == 2:
            self.OUT_PORT2 = value
        elif port == 3:
            if value & BIT0:
                self.IoSoundFX.start_ufo()
            else:
                self.IoSoundFX.stop_ufo()
            if (value & BIT1) and not (self.OUT_PORT3 & BIT1): self.IoSoundFX.play_shot()
            if (value & BIT2) and not (self.OUT_PORT3 & BIT2): self.IoSoundFX.play_base_hit()
            if (value & BIT3) and not (self.OUT_PORT3 & BIT3): self.IoSoundFX.play_inv_hit()
            if (value & BIT4) and not (self.OUT_PORT3 & BIT4): self.IoSoundFX.play_extra_life()
            if (value & BIT5) and not (self.OUT_PORT3 & BIT5): self.IoSoundFX.play_begin_play()
            self.OUT_PORT3 = value
        elif port == 4:
            self.OUT_PORT4LO = self.OUT_PORT4HI
            self.OUT_PORT4HI = value
        elif port == 5:
            if (value & BIT0) and not (self.OUT_PORT5 & BIT0): self.IoSoundFX.play_walk1()
            if (value & BIT1) and not (self.OUT_PORT5 & BIT1): self.IoSoundFX.play_walk2()
            if (value & BIT2) and not (self.OUT_PORT5 & BIT2): self.IoSoundFX.play_walk3()
            if (value & BIT3) and not (self.OUT_PORT5 & BIT3): self.IoSoundFX.play_walk4()
            if (value & BIT4) and not (self.OUT_PORT5 & BIT4): self.IoSoundFX.play_ufo_hit()
            self.OUT_PORT5 = value

    def input_port(self, port):
        if port == 1:
            return self.IN_PORT1
        elif port == 2:
            return self.IN_PORT2
        elif port == 3:
            return (((self.OUT_PORT4HI << 8) | self.OUT_PORT4LO) << self.OUT_PORT2) >> 8
        return 0
