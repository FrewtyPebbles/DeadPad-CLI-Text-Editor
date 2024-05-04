import sys
import termios
import time
import tty
from deadpad.parts.input.input_handler import BaseInputHandler, InputEvent
import os
import io



def getch():
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)
    
    try:
        tty.setcbreak(fd)
        sys.stdout.write("\x1b[?1000h\x1b[?1003h\x1b[?1015h\x1b[?1006h") # enable mouse mode
        sys.stdout.flush()
        inp = sys.stdin.read(1)
        if inp == "\x1b":# if it is an escape code read the rest of the bytes
            inp += (ch2 := sys.stdin.read(1))
            if ch2 == '[':
                # escape sequence
                while not (chn := sys.stdin.read(1)).isalpha():
                    inp += chn
                else:
                    inp += chn
        sys.stdin.flush()
        sys.stdout.write("\x1b[?1000l\x1b[?1003l\x1b[?1015l\x1b[?1006l") # stop mouse mode
        sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    return inp
    

class InputHandler(BaseInputHandler):

    def start(self):
        # disable stdin echo
        fd = sys.stdin.fileno()
        new_term_attr = termios.tcgetattr(fd)
        new_term_attr[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new_term_attr)
        # end disable stdin echo
        #sys.stdout.write("\x1b[?1000h\x1b[?1003h\x1b[?1015h\x1b[?1006h") # enable mouse mode
        #sys.stdout.flush()
        super().start()

    def stop(self):
        sys.stdout.write("\x1b[?1000l\x1b[?1003l\x1b[?1015l\x1b[?1006l") # stop mouse mode
        sys.stdout.flush()
        super().stop()

    def _detect_keys(self):
        while self.checking_for_input:
            if self.input_queue.full():
                self.input_queue.get(False)
                self.input_queue.get(False)
            if sys.stdin.isatty():
                key = getch()
                if key:
                    self.input_queue.put(InputEvent(key), False)
            



if __name__ == "__main__":
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)
    ih = InputHandler()
    ih.start()
    while True:
        if (char := ih.get()) != None:
            print(repr(char))
            if char == b'~':
                break
        time.sleep(0.1)
    ih.stop()
    termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
        
