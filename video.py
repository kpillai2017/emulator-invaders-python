# Python port of the C++ Video class
import re
import pygame
from core.graphics import Graphics
from core.outline_font import OutlineFont
from memory import Memory

SPIN_SCREEN_W = 224 * 2
SPIN_SCREEN_H = 256 * 2

class Video:
    def __init__(self):
        self.X = 20
        self.Y = 40
        self.gVideo = None
        self.videoOutlineFont = OutlineFont()
        self.videoMemory = None
        self.videoMemoryPtr = None
        self.color = [[0, 0] for _ in range(32)]
        self.color2 = [[0, 0] for _ in range(32)]

    def init(self, g: Graphics, m: Memory):
        self.X = 20
        self.Y = 40
        self.gVideo = g
        self.videoMemory = m
        self.videoMemoryPtr = m.get_memory_ptr()
        for i in range(32):
            self.color[i][0] = 0x000000
            self.color2[i][0] = 0x444444
            if 26 <= i <= 27:
                self.color[i][1] = 0xFF0000
                self.color2[i][1] = 0xAA0000
            elif 2 <= i <= 7:
                self.color[i][1] = 0x00FF00
                self.color2[i][1] = 0x00AA00
            else:
                self.color[i][1] = 0xFFFFFF
                self.color2[i][1] = 0xAAAAAA
        self._build_lookup_tables()
        if not self.videoOutlineFont.load("fonts/blitz.fon", 14):
            return False
        return True

    def _build_lookup_tables(self):
        """
        Precompute the RGB bytes for every (colour band, VRAM byte) pair.

        Each VRAM byte holds 8 vertical pixels. On screen every pixel is drawn
        2 rows high (bright colour, then the dimmer colour2 row above it), so
        one byte expands to 16 RGB pixels = 48 bytes. Bytes are laid out in
        "bottom-to-top" order so that a whole emulated column can be built by
        simple concatenation and then rotated into place (see copy_screen).
        """
        def rgb(c):
            return bytes(((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF))

        self._lut = []
        for i in range(32):
            on1, off1 = rgb(self.color[i][1]), rgb(self.color[i][0])
            on2, off2 = rgb(self.color2[i][1]), rgb(self.color2[i][0])
            band = []
            for v in range(256):
                parts = []
                for bit in range(8):
                    if (v >> bit) & 1:
                        parts.append(on1)
                        parts.append(on2)
                    else:
                        parts.append(off1)
                        parts.append(off2)
                band.append(b"".join(parts))
            self._lut.append(band)

        # The original renderer only drew even screen columns; odd ones stay black
        self._black_column = bytes(SPIN_SCREEN_H * 3)

    def draw(self):
        self.gVideo.clear(0, 0, 0)
        self.draw_outline_font("Space Invaders emulator started.", 0, 0, 255, 255, 255)
        self.draw_controls_panel()
        self.copy_screen()
        self.gVideo.draw_line(self.X-1, self.Y-1, self.X+SPIN_SCREEN_W+1, self.Y-1, 200, 200, 200)
        self.gVideo.draw_line(self.X-1, self.Y+SPIN_SCREEN_H, self.X+SPIN_SCREEN_W, self.Y+SPIN_SCREEN_H, 200, 200, 200)
        self.gVideo.draw_line(self.X-1, self.Y-1, self.X-1, self.Y+SPIN_SCREEN_H, 200, 200, 200)
        self.gVideo.draw_line(self.X+SPIN_SCREEN_W, self.Y-1, self.X+SPIN_SCREEN_W, self.Y+SPIN_SCREEN_H, 200, 200, 200)

    # Right-hand help panel. Each section is (title, credits_needed, rows) where a
    # row is either a plain string (word-wrapped to the panel width) or an
    # (action, key) pair (drawn as an aligned two-column table).
    # credits_needed: the section is highlighted as READY when no game is in
    # progress and at least this many credits are inserted (None = never).
    # Keep keys in sync with iohandler.py.
    HELP_SECTIONS = (
        ("1 PLAYER GAME", 1, (
            "1. Press 3 (or 5) once to insert a coin.",
            "2. Press 1 to start.",
        )),
        ("2 PLAYER GAME", 2, (
            "1. Press 3 (or 5) twice to insert 2 coins. CREDIT must show 02.",
            "2. Press 2 to start.",
            "Players take turns: Player 2 plays when Player 1 loses a life.",
            "Both players use the same keys.",
        )),
        ("CONTROLS", None, (
            ("Move left", "LEFT arrow"),
            ("Move right", "RIGHT arrow"),
            ("Fire", "SPACE"),
            ("Tilt", "T"),
            ("Quit", "ESCAPE"),
        )),
    )

    TITLE_COLOR = (0, 255, 0)
    TEXT_COLOR = (200, 200, 200)
    KEY_COLOR = (255, 255, 0)
    READY_TITLE_COLOR = (255, 255, 255)
    READY_BAR_COLOR = (0, 110, 0)
    READY_SUFFIX = "  << READY"
    # The READY marker blinks: shown for READY_BLINK_FRAMES frames, hidden for
    # the next READY_BLINK_FRAMES (20 frames at 60 FPS = 1.5 blinks per second).
    # The highlight bar and title stay steady.
    READY_BLINK_FRAMES = 20

    # Space Invaders RAM locations used to drive the panel highlight
    RAM_CREDITS = 0x20EB    # number of credits, BCD
    RAM_GAME_MODE = 0x20EF  # 0 = attract/demo mode, 1 = game in progress

    def game_state(self):
        """Return (credits, game_in_progress) read from the emulated RAM."""
        mem = self.videoMemoryPtr
        if mem is None:
            return 0, False
        bcd = mem[self.RAM_CREDITS]
        return (bcd >> 4) * 10 + (bcd & 0x0F), mem[self.RAM_GAME_MODE] != 0

    def draw_controls_panel(self):
        # Panel sits in the empty area to the right of the emulated screen
        if getattr(self, "_panel_ops", None) is None:
            self._panel_ops = self._layout_help_panel()
        credits, in_game = self.game_state()
        frame = getattr(self, "_panel_frame", 0)
        self._panel_frame = frame + 1
        show_marker = (frame // self.READY_BLINK_FRAMES) % 2 == 0
        bar_height = self._line_height() + 2
        bar_width = self._panel_right - self._panel_x + 8
        for text, x, y, (r, g, b), needed in self._panel_ops:
            if needed is not None and not in_game and credits >= needed:
                # Section can be started right now: highlight its title
                br, bg, bb = self.READY_BAR_COLOR
                self.gVideo.fill_rect(x - 4, y - 1, bar_width, bar_height, br, bg, bb)
                r, g, b = self.READY_TITLE_COLOR
                if show_marker:
                    text += self.READY_SUFFIX
            self.draw_outline_font(text, x, y, r, g, b)

    def _layout_help_panel(self):
        """Compute (text, x, y, colour, credits_needed) draw operations for the help panel once."""
        font = getattr(self.videoOutlineFont, "font", None)
        width_of = (lambda s: font.size(s)[0]) if font else (lambda s: len(s) * 8)

        x = self.X + SPIN_SCREEN_W + 20
        backbuffer = self.gVideo.get_backbuffer() if self.gVideo else None
        right = (backbuffer.get_width() if backbuffer else 800) - 10
        indent = 8
        line = self._line_height() + 4
        self._panel_x, self._panel_right = x, right

        # Align the key column of every (action, key) table across sections
        labels = [row[0] for _, _, rows in self.HELP_SECTIONS for row in rows if isinstance(row, tuple)]
        key_x = x + indent + (max(width_of(a) for a in labels) if labels else 0) + 16

        ops = []
        y = self.Y
        for title, needed, rows in self.HELP_SECTIONS:
            ops.append((title, x, y, self.TITLE_COLOR, needed))
            y += line + 2
            for row in rows:
                if isinstance(row, tuple):
                    action, key = row
                    ops.append((action, x + indent, y, self.TEXT_COLOR, None))
                    ops.append((key, key_x, y, self.KEY_COLOR, None))
                    y += line
                else:
                    # Numbered steps ("1. ...") get a hanging indent so wrapped
                    # lines line up with the step text, not with the number
                    match = re.match(r"^(\d+\.\s+)(.*)$", row)
                    prefix, body = (match.group(1), match.group(2)) if match else ("", row)
                    text_x = x + indent + (width_of(prefix) if prefix else 0)
                    if prefix:
                        ops.append((prefix.rstrip(), x + indent, y, self.TEXT_COLOR, None))
                    for wrapped in self._wrap_text(body, right - text_x, width_of):
                        ops.append((wrapped, text_x, y, self.TEXT_COLOR, None))
                        y += line
            y += line  # blank line between sections
        return ops

    @staticmethod
    def _wrap_text(text, max_width, width_of):
        """Greedy word-wrap of text into lines no wider than max_width pixels."""
        lines, current = [], ""
        for word in text.split():
            candidate = word if not current else current + " " + word
            if width_of(candidate) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _line_height(self):
        # Height of one text line in the banner font (fallback if the font isn't loaded)
        font = getattr(self.videoOutlineFont, "font", None)
        return font.get_linesize() if font else 18

    def draw_outline_font(self, text, x, y, r, g, b):
        self.videoOutlineFont.draw(text, x, y, r, g, b, self.gVideo)

    def build_frame_bytes(self):
        """
        Build the emulated screen as raw RGB bytes.

        The buffer is SPIN_SCREEN_H (512) pixels wide and SPIN_SCREEN_W (448)
        pixels tall: buffer row 2*j is emulated column j (pixels bottom-to-top),
        buffer row 2*j+1 is black. Rotating it 90 degrees counter-clockwise
        gives exactly the upright image the per-pixel renderer used to draw.
        """
        mem = self.videoMemoryPtr
        lut = self._lut
        black = self._black_column
        rows = []
        append = rows.append
        for j in range(224):
            base = 0x2400 + (j << 5)
            append(b"".join([band[v] for band, v in zip(lut, mem[base:base + 32])]))
            append(black)
        return b"".join(rows)

    def copy_screen(self):
        # One buffer build + one rotate + one blit per frame, instead of
        # ~115,000 individual draw_pixel calls.
        frame = pygame.image.frombuffer(self.build_frame_bytes(), (SPIN_SCREEN_H, SPIN_SCREEN_W), "RGB")
        upright = pygame.transform.rotate(frame, 90)
        self.gVideo.get_backbuffer().blit(upright, (self.X, self.Y))

    # Upright view reversed (previously commented out in the per-pixel renderer):
    # use pygame.transform.flip(upright, True, False) before blitting.

    def free(self):
        self.videoOutlineFont.free()

    def get_video_outline_font(self):
        return self.videoOutlineFont
