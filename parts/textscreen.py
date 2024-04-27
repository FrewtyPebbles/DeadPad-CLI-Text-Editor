from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum
import math
import sys
import time
import shutil
from typing import TYPE_CHECKING
from parts.document import Document
from parts.windows_input import InputHandler
if TYPE_CHECKING:
    from deadpad import Editor

def move_cursor(y:int, x:int):
    return "\033[%d;%dH" % (y, x)

def line_len(row:list[str]):
    leng = 0
    for char in row:
        if char == None:
            break
        leng += 1
    return leng

height_offset = 2

class TextScreen:
    def __init__(self, master:Editor, width:int, height:int, document:Document) -> None:
        self.width = width - 2
        self.height = height-height_offset
        self._y_pos = 0
        self.document = document
        """
        This is a reference to the document we are editing.

        Any changes to the state will be rendered onto the document's matrix at the state's position on the document.
        Rendering to the document will happen either on save or when the state's position on the document changes.
        """

        self.cursor = '✍ '
        self.state:list[list[None|bytes]] = [[] for _ in range(self.height)]

        self.footer_string = document.file_path
        self.edit_mode = True
        self.running = True
        self.master = master

    @property
    def y_pos(self):
        return self._y_pos
    
    @y_pos.setter
    def y_pos(self, val:int):
        self._y_pos = max(val, 0)
        

    @property
    def cursor_x(self):
        "The screen space x position of the cursor"
        return self.document.cursor.x % self.width
    
    @property
    def cursor_y(self):
        "The screen space y position of the cursor"
        return self.document.cursor.y - self.y_pos + math.floor(self.document.cursor.x / self.width)

    def render(self, new_width:int = None, new_height:int = None) -> str:
        # Resize terminal
        dim_changed = self.width != (new_width - 2) or self.height != (new_height - height_offset)
        self.width = new_width - 2 if new_width else self.width
        self.height = new_height - height_offset if new_height else self.height
        if dim_changed:
            self.state = [[] for _ in range(self.height)]
            
            self.document.render_width = self.width
            self.document.update_state()
            sys.stdout.write("\033c")

        # render the screen

        screen = ""
        doc_state = self.document.state[max(self.y_pos, 0):min(self.y_pos + self.height, self.document.height)]

        for ln, line in enumerate(doc_state):
            self.state[ln] = [char for char in line[:self.width]]
            
            while len(self.state[ln]) != self.width:
                self.state[ln].append(None)
            

        for y, row in enumerate(self.state):
            for x, col in enumerate(row):
                if col != None:
                    if y == self.cursor_y and x == self.cursor_x:
                        if col == '\n':
                            screen += self.cursor
                        else:
                            screen += self.cursor + col
                    elif col == '\n':
                        screen += '¶' if self.master.settings["show_paragraphs"] else ''
                    else:
                        screen += col
                elif y == self.cursor_y and x == self.cursor_x:
                    screen += self.cursor
            if col != '\n':
                screen += '\n'

        footer_bg = "❚" * (self.width - len(self.footer_string)-5)
        padding = ' ' if self.footer_string != "" else ''
        return f"{screen}\033[K💀 ❚{padding}{self.footer_string}{padding}{footer_bg}\n\033[K"
    
    def handle_key(self, key:bytes):
        if self.edit_mode:
            self.footer_string = self.document.file_path if self.footer_string in {"COMMAND MODE",self.document.file_path} else self.footer_string
            if self.document._recording_arrow:
                # move y_pos if y is at the bottom or top
                match key:
                    case b'H': # up
                        if self.cursor_y == 0:
                            self.y_pos -= 1
                    case b'P': # down
                        if self.cursor_y == self.height:
                            self.y_pos += 1
            else:
                match key:
                    case b'\x17': # ctrl w
                        self.footer_string = f"Last saved to '{self.document.file_path}' at {datetime.datetime.now()}. 📀"
                    case b'\x1b': # esc
                        self.footer_string = f"EXITING"
                        self.running = False
                    case b'\n': # enter
                        if self.cursor_y == self.height:
                            self.y_pos += 1
                    case b'\x08': # enter
                        if self.cursor_y == 0:
                            self.y_pos -= 1
                    case b'\x1c': # ctrl \
                        self.edit_mode = False
                        self.footer_string = "COMMAND MODE"
                        return
            self.document.handle_key(key)
        else:
            # this is for doing commands
            self.master.run_command(input("=☠ |"))
            sys.stdout.write("\033c")
            self.edit_mode = True