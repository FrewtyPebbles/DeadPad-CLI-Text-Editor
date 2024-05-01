from __future__ import annotations
from enum import Enum
import sys
import datetime
from typing import TYPE_CHECKING

from deadpad.parts import keys
if TYPE_CHECKING:
    from deadpad.parts.textscreen import TextScreen
    from deadpad import Editor

# TODO Add line class to keep track of line numbers (should have all string functions implemented)


def chrweight(char:str):
    match char:
        case "\t":
            return 3
        case None: # equivalent of space in textscreen
            return 1
        case _:
            return 1
        
def str_weight(string:str):
    weight = 0
    for char in string:
        weight += chrweight(char)
    return weight

def chunk_str_by_weight(string:str, chunk_size:int):
    chunks:list[str] = []
    str_buff = ""
    chr_ind = 0
    while chr_ind < len(string):
        str_buff = ""
        while (str_weight(str_buff) + chrweight(string[chr_ind])) < chunk_size \
        if chr_ind < len(string) else False:
            str_buff += string[chr_ind]
            chr_ind += 1
        chunks.append(str_buff)
        
    return chunks

def newline_chunkstring(string:str, length:int):
    
    ret:list[str] = []
    for chunk in string.splitlines(True):
        # TODO split into chunks based on actual size since tabs are bigger
        chunks = []
        if str_weight(chunk) > length:
            chunks = chunk_str_by_weight(chunk, length)
        else:
            chunks = [chunk]
        for sub_chunk in chunks:
            ret.append(sub_chunk)
    return ret

if __name__ == "__main__":
    for chunk in newline_chunkstring("\t\t\twjdkjwkj       djk wdja hwhdgjiwa dj \t \t\twjdjwkjdkk\n", 20):
        print(repr(chunk))

class CursorPosition:
    def __init__(self, x:int, y:int, owner:Document) -> None:
        self._x = x
        self._y = y
        self.owner = owner

    @property
    def x(self):
        return self._x
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, val:int):
        h = self.owner.height-1
        state = self.owner.state
        if val < 0:
            self._y = 0
        elif val > h:
            self._y = h-1
        else:
            self._y = val
        # reset the x cursor to its position
        self.x = min(len(state[self.y])-1, self.x)

    @x.setter
    def x(self, val:int):
        h = self.owner.height
        state = self.owner.state
        while (val >= len(state[self.y])) if self.y < h else False:
            val -= len(state[self.y])
            self.y += 1
        
        
        while val < 0:
            self.y -= 1
            val += len(state[self.y])

        self._x = val

escapes = b''.join([chr(char).encode() for char in range(1, 32)])

class Document:
    def __init__(self, master:Editor, render_width:int, file_path:str) -> None:
        self.file_path = file_path
        self.state:list[str] = [""]
        self.cursor = CursorPosition(0,0,self)
        self._recording_arrow = False
        self.render_width = render_width - 2
        self.file = open(self.file_path, "r+", encoding="utf8")
        t_str_state = self.file.read()
        if t_str_state == "":
            self.str_state = "\n"
        else:
            self.str_state = t_str_state if t_str_state[-1] == "\n" else t_str_state + "\n"
        self.state = newline_chunkstring(self.str_state, self.render_width)
        self.master = master
        self.updated = True


    def __del__(self):
        self.file.close()

    def save(self):
        "Saves the document."
        self.file.seek(0)
        self.file.write(self.str_state)
        self.file.truncate()
        self.updated = True

    def update_state(self):
        self.str_state = "".join(self.state)
        self.str_state = self.str_state if self.str_state[-1] == "\n" else self.str_state + "\n"
        self.state = newline_chunkstring(self.str_state, self.render_width)
        self.updated = True

    @property
    def height(self):
        return len(self.state)
    
    def check_update(self):
        updated = self.updated
        self.updated = False
        return updated

    def handle_key(self, key:bytes):
        if key != None:
            
            match key:
                case keys.UP: # up
                    self.cursor.y -= 1
                case keys.DOWN: # down
                    if not (self.cursor.y == len(self.state)-1):
                        self.cursor.y += 1
                case keys.LEFT: # left
                    if not (self.cursor.x == 0 and \
                    self.cursor.y == 0):
                        self.cursor.x -= 1
                case keys.RIGHT: # right
                    if not (self.cursor.x == len(self.state[-1])-1 and \
                    self.cursor.y == len(self.state)-1):
                        self.cursor.x += 1
                    
                case keys.CTRL_W: # ctrl w
                    self.save()
                case b'\n': # enter
                    # TODO Make it drop text to the next line
                    self._insert_character(key, self.cursor.x, self.cursor.y)
                    if self.cursor.x == len(self.state[-1])-2 and \
                    self.cursor.y == len(self.state)-1:
                        self.update_state()
                        self.cursor.x += 1
                    else:
                        self.cursor.x = 0
                        self.cursor.y += 1
                        self.update_state()
                case keys.BACKSPACE: # backspace
                    if self.cursor.x == 0 and self.cursor.y == 0:
                        pass
                    elif self.cursor.x == 0:
                        line_len = len(self.state[self.cursor.y])
                        self.state[self.cursor.y-1] = self.state[self.cursor.y-1][:-1]
                        
                        self.update_state()
                        self.cursor.x -= line_len
                    else:
                        self.state[self.cursor.y] = self.state[self.cursor.y][:self.cursor.x-1] + self.state[self.cursor.y][self.cursor.x:]
                        self.cursor.x -= 1
                        self.update_state()
                case b'\t':
                    
                    self._insert_character(self.master.settings["tab"].encode(), self.cursor.x, self.cursor.y)
                    self.cursor.x += len(self.master.settings["tab"])
                    self.update_state()
                case _:
                    try:
                        
                        key = key.translate(None, escapes)
                        self._insert_character(key, self.cursor.x, self.cursor.y)
                        self.cursor.x += 1
                        self.update_state()
                    except UnicodeDecodeError:
                        pass
            
            
        
    def _insert_character(self, char:bytes, x:int, y:int):
        """
        inserts a character at the provided position in the state
        """
        
        self.state[y] = self.state[y][:x] + char.decode() + self.state[y][x:]