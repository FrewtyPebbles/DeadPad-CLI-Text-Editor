from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum
import json
import math
import sys
import time
import shutil
from typing import TYPE_CHECKING
from parts.document import Document, str_weight
from parts.themes import RESET_STYLE, get_style
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
width_offset = 6

class TextScreen:
    def __init__(self, master:Editor, width:int, height:int, document:Document) -> None:
        self.width = width - width_offset
        self.height = height-height_offset
        self._y_pos = 0
        self.document = document
        """
        This is a reference to the document we are editing.

        Any changes to the state will be rendered onto the document's matrix at the state's position on the document.
        Rendering to the document will happen either on save or when the state's position on the document changes.
        """

        self.state:list[list[None|bytes]] = [[] for _ in range(self.height)]

        self.footer_string = document.file_path
        self.edit_mode = True
        self.running = True
        self.master = master
        self.theme_data = json.load(f_p:=open(self.master.settings["theme"], "r", encoding="utf8"))
        f_p.close()
    
    def open_document(self, path:str):
        self._y_pos = 0
        self.document = Document(self.master, self.width, path)
        self.state = [[] for _ in range(self.height)]
        self.footer_string = self.document.file_path
        sys.stdout.write("\033c")
    
    def refresh(self):
        self.theme_data = json.load(f_p:=open(self.master.settings["theme"], "r", encoding="utf8"))
        f_p.close()

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
        dim_changed = self.width != (new_width - width_offset) or self.height != (new_height - height_offset)
        self.width = new_width - width_offset if new_width else self.width
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
            self.state[ln] = [char for char in line]
            
            # add spaces to rhs of text accounting for tabs
            while str_weight(self.state[ln]) < self.width:
                self.state[ln].append(None)
            

        for y, row in enumerate(self.state):
            if self.master.settings["line_numbers"]:

                screen += f"{get_style(bg=self.theme_data['line_number_bg'])}{(y+self.y_pos+1):^4}{get_style(bg=self.theme_data['editor_bg'])}|"
            for x, col in enumerate(row):
                if col != None:
                    if y == self.cursor_y and x == self.cursor_x:
                        if col in {'\n', ' '}:
                            screen += self.theme_data["cursor_sym"]
                        elif col == '\t':
                            screen += self.theme_data["cursor_sym"] + self.theme_data["tab_sym"][1:len(self.theme_data["tab_sym"])] if self.master.settings["show_tabs"] else self.theme_data["cursor_sym"] + (' ' * (len(self.theme_data["tab_sym"])-1))
                        else:
                            screen += self.theme_data["cursor_sym"] + col
                    else:
                        match col:
                            case '\n':
                                screen += self.theme_data["paragraph_sym"] if self.master.settings["show_paragraphs"] else ''

                            case '\t':
                                screen += self.theme_data["tab_sym"] if self.master.settings["show_tabs"] else (' ' * len(self.theme_data["tab_sym"]))

                            case _:
                                screen += col
                elif y == self.cursor_y and x == self.cursor_x:
                    screen += self.theme_data["cursor_sym"]
                else:
                    screen += ' '
            if col != '\n':
                screen += f'\n{RESET_STYLE}'

        bchar = self.theme_data['CLI_bar_filler_char']
        footer_bg = bchar * (self.width - len(self.footer_string)-5)
        padding = ' ' if self.footer_string != "" else ''
        return f"{screen}\033[K{self.theme_data['emblem']} {bchar}{padding}{self.footer_string}{padding}{footer_bg}\n\033[K"
    
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
            self.master.run_command(input(self.theme_data['CLI_prefix']))
            sys.stdout.write("\033c")
            self.edit_mode = True