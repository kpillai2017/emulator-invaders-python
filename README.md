# Space Invaders Emulator

This project is a Python emulator for the classic Space Invaders arcade game. It aims to faithfully reproduce the gameplay, graphics, and sound of the original game.

---

## Game Instructions

**Objective:**
- Defend your base from waves of descending alien invaders.
- Shoot all invaders before they reach the bottom of the screen.
- Earn points for each invader destroyed. Bonus points for shooting the UFO.

**Starting a game:**

| Mode | Steps |
|---|---|
| 1 player | Press `3` (or `5`) once to insert a coin, then press `1`. |
| 2 players | Press `3` (or `5`) twice to insert 2 coins (CREDIT shows `02`), then press `2`. |

In 2-player mode the players take turns, as on the original cabinet: Player 2 plays when Player 1 loses a life. Both players use the same keys.

The help panel on the right of the window shows these steps. When enough credits are inserted (and no game is running) the matching section is highlighted with a blinking `<< READY` marker.

**Controls:**

| Action | Key |
|---|---|
| Insert coin | `3` or `5` |
| 1 player start | `1` |
| 2 player start | `2` |
| Move left | `Left Arrow` |
| Move right | `Right Arrow` |
| Fire | `Space` |
| Tilt | `T` |
| Quit | `Escape` |

**Gameplay:**
- You have a limited number of lives.
- Aliens move faster as their numbers decrease.
- Shields provide temporary protection but degrade when hit.
- The game ends when all lives are lost or invaders reach the bottom.

---

## Setup Instructions

1. **Clone the Repository**
   ```sh
   git clone https://github.com/kpillai2017/emulator-invaders-python.git
   cd emulator-invaders-python
   ```

2. **Install Python 3.10+**
   - Ensure you have Python 3.10 or newer installed.

3. **(Optional) Create a Virtual Environment**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Dependencies**
   - The emulator needs [pygame](https://www.pygame.org) (graphics, sound and keyboard), listed in `requirements.txt`:
     ```sh
     pip install -r requirements.txt
     ```

5. **Supply Your Own ROM**
   - Game ROMs are not included. Obtain ROMs you are legally entitled to use and place the combined 8192-byte ROM at `data/invaders.rom`.
   - Combine the four 2048-byte ROM files in this order: `invaders.h`, `invaders.g`, `invaders.f`, `invaders.e`. See [data/README.md](data/README.md) for a cross-platform command.
   - ROMs and their backup/test variants are ignored by Git. Do not force-add them or include them in distributed builds.
   - Sound effects (`data/*.wav`) and the font (`fonts/blitz.fon`) are included. The C++ version uses the same assets.

6. **Run the Emulator** (from the `emulator-invaders-python` folder, so `data/` and `fonts/` are found)
   ```sh
   python main.py
   ```

---

## Code Overview

The emulator is organized into several modules, each responsible for a different aspect of the game:

### Top-Level Files
- `main.py`: Entry point. Initializes and runs the emulator.
- `emulator.py`: Coordinates CPU, memory, video, and input/output.
- `cpu.py`: Emulates the Intel 8080 CPU, including instruction decoding and execution.
- `memory.py`: Handles memory mapping, ROM loading, and RAM operations.
- `video.py`: Renders the game graphics, including the display buffer and screen updates.
- `iohandler.py`: Manages user input (keyboard) and hardware I/O ports.
- `soundfx.py`: Handles sound effects and music playback.
- `util.py`: Utility functions used throughout the emulator.

### `core/` Directory
- `audio.py`, `music.py`, `sound.py`: Audio and music playback logic.
- `game.py`: Base game-loop framework (start-up, per-frame update/draw, frame timing, shut-down) that `Emulator` extends.
- `graphics.py`, `image.py`: Window, back buffer and drawing helpers (pixels, lines, rectangles, images).
- `input.py`: Input abstraction and mapping.
- `outline_font.py`, `raster_font.py`: Font rendering for on-screen text.

### `data/` Directory
- `invaders.rom`: your locally supplied ROM; not included in this repository.
- `*.wav`: sound effects.

### `fonts/` Directory
- `blitz.fon`: the font used for on-screen text.

---

## How the Emulator Works

1. **Initialization**
   - Loads ROM files into memory.
   - Sets up CPU, memory, video, and sound subsystems.

2. **Main Loop**
   - Emulates CPU cycles, executing instructions from the loaded ROM.
   - Handles user input and updates game state.
   - Renders graphics to the screen.
   - Plays sound effects as triggered by game events.

3. **Input/Output**
   - Maps keyboard input to arcade controls.
   - Emulates hardware I/O ports for communication between CPU and peripherals.

4. **Graphics**
   - Reads video RAM (`0x2400`–`0x3FFF`) every frame and turns it into a rotated, colour-banded image, as on the original cabinet's colour overlay.
   - Draws the banner and the help panel next to the game screen.

5. **Sound**
   - Watches the sound output ports and plays the matching `.wav` file for each effect.

6. **Game Logic**
   - Scoring, lives, invader movement, collisions and level progression all run inside the original game code in the ROM. The emulator only runs the CPU and handles the I/O around it.

---

## Recent Changes

**Bug fix: the game ignored player input** (`cpu.py`)
- The Python version rendered correctly, but the player could not move. The cause was a CPU emulation bug, not the keyboard code.
- `perform_inc` (the 8080 `INR` instruction) set the Zero flag by testing only the low 4 bits (`value & 0x0F`) instead of the whole byte (`value & 0xFF`). Space Invaders' player-movement code relies on that flag, so the ship never moved.
- Other CPU differences from the C/C++ version were fixed at the same time:
  - `execute_ral` (`RAL`) did not shift the accumulator left.
  - `add_hl` (`DAD`) could never set the Carry flag.
  - `execute_adc` (`ADC`) now passes the carry separately, so the Half-carry flag is correct.
- Smaller fixes:
  - Escape quits while held, as in the C/C++ version.
  - Window close is handled in the same frame.
  - `Input.kill()` resets its event store to the correct type.

**Performance: now runs at full speed (60 FPS)**
- `video.py`: the screen used to be drawn with about 115,000 `draw_pixel` calls per frame. That took about 35 ms in Python alone, more than twice the 16.7 ms budget for one frame at 60 FPS.
  - The screen is now built from a lookup table that turns each video-RAM byte directly into RGB bytes.
  - The frame is converted with `pygame.image.frombuffer`, rotated with `pygame.transform.rotate`, and blitted once.
  - The output is pixel-for-pixel identical to the old renderer.
- `cpu.py`: opcodes are decoded through a 256-entry dispatch table instead of a long `if/elif` chain, and parity uses a lookup table.
  - Emulation is unchanged: memory and registers matched the old CPU on every frame of a scripted test game.
- `core/outline_font.py`: rendered text is cached instead of re-rendered every frame.
- Result: a full frame (CPU, video, text, flip) takes about 2 ms.

**On-screen help panel** (`video.py`)
- The banner now reads "Space Invaders emulator started."
- A panel to the right of the game explains 1- and 2-player mode step by step and lists the controls.
- The panel content is defined in one list, `Video.HELP_SECTIONS`. Text wraps to the panel width, and numbered steps get a hanging indent.
- When enough credits are inserted, the matching section is highlighted with a blinking `<< READY` marker. The credit count and game-in-progress flag are read from the game's RAM (`0x20EB` and `0x20EF`).

---

## Troubleshooting
- Ensure all required ROM and sound files are present in the `data/` directory.
- Run with Python 3.10+ for best compatibility.
- For issues, check for error messages in the terminal and verify file paths.

---

## License
This project is for educational purposes. Space Invaders is © Taito. You must legally own the original ROMs to use them with this emulator.
