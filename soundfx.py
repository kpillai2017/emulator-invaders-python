# Python port of the C++ SoundFX class
from core.sound import Sound

SOUND_CH_UNDEF = -2

class SoundFX:
    def __init__(self):
        self.coin = Sound()
        self.baseHit = Sound()
        self.invHit = Sound()
        self.shot = Sound()
        self.ufo = Sound()
        self.ufoHit = Sound()
        self.walk1 = Sound()
        self.walk2 = Sound()
        self.walk3 = Sound()
        self.walk4 = Sound()
        self.beginPlay = Sound()
        self.extraLife = Sound()
        self.ufoChannel = SOUND_CH_UNDEF

    def init(self):
        try:
            if not self.coin.load("data/coin.wav"): return False
            if not self.baseHit.load("data/basehit.wav"): return False
            if not self.invHit.load("data/invhit.wav"): return False
            if not self.shot.load("data/shot.wav"): return False
            if not self.ufo.load("data/ufo.wav"): return False
            if not self.ufoHit.load("data/ufohit.wav"): return False
            if not self.walk1.load("data/walk1.wav"): return False
            if not self.walk2.load("data/walk2.wav"): return False
            if not self.walk3.load("data/walk3.wav"): return False
            if not self.walk4.load("data/walk4.wav"): return False
            if not self.beginPlay.load("data/beginplay.wav"): return False
            if not self.extraLife.load("data/extralife.wav"): return False
            return True
        except Exception:
            return False

    def play(self):
        self.baseHit.play(0)

    def play_coin(self):
        self.coin.play(0)

    def play_base_hit(self):
        self.baseHit.play(0)

    def play_inv_hit(self):
        self.invHit.play(0)

    def play_shot(self):
        self.shot.play(0)

    def start_ufo(self):
        if self.ufoChannel == SOUND_CH_UNDEF:
            self.ufoChannel = self.ufo.play(-1)

    def stop_ufo(self):
        if self.ufoChannel != SOUND_CH_UNDEF:
            self.ufo.halt(self.ufoChannel)
        self.ufoChannel = SOUND_CH_UNDEF

    def play_ufo_hit(self):
        self.ufoHit.play(0)

    def play_walk1(self):
        self.walk1.play(0)

    def play_walk2(self):
        self.walk2.play(0)

    def play_walk3(self):
        self.walk3.play(0)

    def play_walk4(self):
        self.walk4.play(0)

    def play_begin_play(self):
        self.beginPlay.play(0)

    def play_extra_life(self):
        self.extraLife.play(0)

    def free(self):
        self.coin.free()
        self.baseHit.free()
        self.invHit.free()
        self.shot.free()
        self.ufo.free()
        self.ufoHit.free()
        self.walk1.free()
        self.walk2.free()
        self.walk3.free()
        self.walk4.free()
        self.beginPlay.free()
        self.extraLife.free()
