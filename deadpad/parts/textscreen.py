from __future__ import annotations
from dataclasses import dataclass
import datetime
from enum import Enum
import json
import math
import sys
import time
import shutil
from typing import TYPE_CHECKING, Callable
from deadpad.parts import keys
from deadpad.parts.document import Document, str_weight
from deadpad.parts.themes import RESET_STYLE, get_style
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

escapes = b''.join([chr(char).encode() for char in range(1, 32)])

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
        self.theme_data = json.load(f_p:=open(f"{self.master.themes_path}{self.master.settings['theme']}.json", "r", encoding="utf8"))
        f_p.close()
        self.updated = True
        
        self.state = [[] for _ in range(self.height)]    
        self.document.render_width = self.width
        self.document.update_state()
        sys.stdout.write("\033c")
        self.get_extensions()
        

    def check_update(self):
        updated = self.updated or self.document.updated
        self.updated = False
        self.document.updated = False
        return updated
    
    def open_document(self, path:str):
        self._y_pos = 0
        self.document = Document(self.master, self.width, path)
        self.state = [[] for _ in range(self.height)]
        self.footer_string = self.document.file_path
        sys.stdout.write("\033c")
        self.updated = True
        self.get_extensions()
        
    def get_extensions(self):
        self.highlight:Callable[[str], str] = lambda src: src
        "The current active syntax highlighter."

        file_ext = self.document.file_path.split(".")[-1]
        for extension in self.master.extensions.values():
            if extension.FILE_EXT == file_ext:
                if extension.parser:
                    self.highlight = extension.parser.highlight
                    
    
    def refresh(self):
        # TODO: make theme_data an attribute of Editor instead.
        self.theme_data = json.load(f_p:=open(f"{self.master.themes_path}{self.master.settings['theme']}.json", "r", encoding="utf8"))
        f_p.close()
        self.updated = True

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
        doc_state = self.document.state

        ln = 0
        for dsln in range(max(self.y_pos, 0), min(self.y_pos + self.height, self.document.height)):
            line = doc_state[dsln]
            self.state[ln] = [char for char in line]
            
            # add spaces to rhs of text accounting for tabs
            
            self.state[ln].extend([None for _ in range(self.width - str_weight(self.state[ln]))])
            ln += 1
            

        for y, row in enumerate(self.state):
            src_line = ""
            for x, col in enumerate(row):
                if col != None:
                    if y == self.cursor_y and x == self.cursor_x:
                        if col in {'\n', ' '}:
                            src_line += self.theme_data["cursor_sym"]
                        elif col == '\t':
                            src_line += self.theme_data["cursor_sym"] + self.theme_data["tab_sym"][1:len(self.theme_data["tab_sym"])] if self.master.settings["show_tabs"] else self.theme_data["cursor_sym"] + (' ' * (len(self.theme_data["tab_sym"])-1))
                        else:
                            src_line += self.theme_data["cursor_sym"] + col
                    else:
                        match col:
                            case '\n':
                                src_line += self.theme_data["paragraph_sym"] if self.master.settings["show_paragraphs"] else ''

                            case '\t':
                                src_line += self.theme_data["tab_sym"] if self.master.settings["show_tabs"] else (' ' * len(self.theme_data["tab_sym"]))
                            case _:
                                src_line += col
                elif y == self.cursor_y and x == self.cursor_x:
                    src_line += self.theme_data["cursor_sym"]
            screen += src_line
            if col != '\n':
                screen += f'\n'
    
        screen = self.highlight(screen).replace(" ", " ")
        screen = self._render_second_pass(screen)

        # command bar
        bchar = self.theme_data['CLI_bar_filler_char']
        footer_bg = bchar * (self.width - len(self.footer_string)-5)
        padding = ' ' if self.footer_string != "" else ''
        
        return f"{screen}\033[K{self.theme_data['emblem']} {bchar}{padding}{self.footer_string}{padding}{footer_bg}\n\033[K{' '*self.width}"

    def _render_second_pass(self, src:str):
        lines = src.split('\n')
        lines.pop()
        ret_screen = ""
        for l_n, line in enumerate(lines):
            if self.master.settings["line_numbers"]:
                ret_screen += f"{get_style(bg=self.theme_data['line_number_bg'])}{(l_n+self.y_pos+1):^4}{RESET_STYLE}|"
            ret_screen += line + '\n'
        return ret_screen + RESET_STYLE

    def handle_key(self, key:bytes):
        if key != None:
            self.updated = True
        if self.edit_mode:
            self.footer_string = self.document.file_path if self.footer_string in {"COMMAND MODE",self.document.file_path} else self.footer_string
            
            match key:
                case keys.CTRL_W: # ctrl w
                    # TODO make save message show maximum ammount of characters in file path.
                    flpw = math.floor(self.width/8)
                    filep = (self.document.file_path[:flpw]+'...') if len(self.document.file_path) > (flpw+3) else self.document.file_path    
                    self.footer_string = f"Last saved '{filep}' at {datetime.datetime.now()}. 📀"
                case keys.ESC: # esc
                    self.footer_string = f"EXITING"
                    self.running = False
                case b'\n': # enter
                    if self.cursor_y == self.height:
                        self.y_pos += 1
                case keys.BACKSPACE: # backspace
                    if self.cursor_y == 0:
                        self.y_pos -= 1
                case keys.CTRL_O: # ctrl \
                    self.edit_mode = False
                    self.footer_string = "COMMAND MODE"
                    return
                case keys.UP: # up
                    if self.cursor_y == 0:
                        self.y_pos -= 1
                case keys.DOWN: # down
                    if self.cursor_y == self.height:
                        self.y_pos += 1
            self.document.handle_key(key)
        else:
            sys.stdout.write(f"\r\033[K{self.theme_data['CLI_prefix']}{' ' * (self.width - len(self.theme_data['CLI_prefix']))}")
            sys.stdout.flush()
            # this is for doing commands
            command = b""
            cursor_pos = 0
            while (curr_key := self.master.in_handler.get()) != b'\n':
                if curr_key != None:
                    match curr_key:
                        case keys.BACKSPACE:
                            command = command[:cursor_pos-1] + command[cursor_pos:]
                            cursor_pos = max(cursor_pos-1, 0)
                        case keys.LEFT:
                            cursor_pos = max(cursor_pos-1, 0)
                        case keys.RIGHT:
                            cursor_pos = min(cursor_pos+1, len(command))
                        case keys.UP | keys.DOWN:
                            pass
                        case _:
                            try:
                                curr_key = curr_key.translate(None, escapes)
                                command = command[:cursor_pos] + curr_key + command[cursor_pos:]
                                cursor_pos = min(cursor_pos+1, len(command))
                            except UnicodeDecodeError:
                                pass
                    com_dec = command.decode()
                    lhs_str = f"{self.theme_data['CLI_prefix']}{com_dec[:cursor_pos]}{self.theme_data['cursor_sym']}{com_dec[cursor_pos:]}"
                    padding = ' ' * (self.width - len(lhs_str))
                    sys.stdout.write(f"\r\033[K{lhs_str}{padding}")
                    sys.stdout.flush()
            self.master.run_command(command.decode())
            sys.stdout.write("\033c")
            self.edit_mode = True
            self.updated = True

