# Python port of the C++ Memory class
import sys


class Memory:
    ROM_SIZE = 8192

    def __init__(self):
        self.memoryPtr = bytearray(0x8000)

    def init(self, rom_path):
        try:
            with open(rom_path, 'rb') as f:
                rom = f.read(self.ROM_SIZE + 1)
        except OSError as exc:
            print(f"Cannot load ROM '{rom_path}': {exc}. Supply your own legally obtained 8192-byte Space Invaders ROM; see README.md.", file=sys.stderr)
            return False
        if len(rom) != self.ROM_SIZE:
            print(f"Invalid ROM '{rom_path}': expected exactly {self.ROM_SIZE} bytes; see README.md.", file=sys.stderr)
            return False
        self.memoryPtr[:self.ROM_SIZE] = rom
        return True

    def get_memory_ptr(self):
        return self.memoryPtr

    def free(self):
        self.memoryPtr = None
