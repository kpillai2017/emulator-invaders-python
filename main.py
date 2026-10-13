# Python port of the C++ main.cpp
from emulator import Emulator

if __name__ == "__main__":
    emulator = Emulator()
    if not emulator.init():
        emulator.free()
    else:
        emulator.run()
