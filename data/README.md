# User-supplied Space Invaders ROM

Game ROMs are not included. Obtain ROMs you are legally entitled to use.

The emulator expects exactly 8192 bytes at `data/invaders.rom`, consisting of four 2048-byte files in this order: `invaders.h`, `invaders.g`, `invaders.f`, `invaders.e`.

Place those four files in this directory, then run this command from the project root (requires Python 3; use `python` instead of `python3` where appropriate):

```sh
python3 -c "from pathlib import Path; p=Path('data'); parts=[(p/n).read_bytes() for n in ('invaders.h','invaders.g','invaders.f','invaders.e')]; assert all(len(b)==2048 for b in parts), 'Each input ROM must be 2048 bytes'; (p/'invaders.rom').write_bytes(b''.join(parts))"
```

ROMs are ignored by Git. Do not force-add them or include them in distributed builds. Start the emulator from the project root so its relative asset paths work.
