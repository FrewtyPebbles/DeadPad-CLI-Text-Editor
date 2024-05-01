import sys
import termios
import time
import tty
from deadpad.parts.input_handler import BaseInputHandler

def getch():
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)

    tty.setcbreak(fd)
    inp = sys.stdin.read(1)
    if inp == "\x1b":# if it is an escape code read the rest of the bytes
        inp += (ch2 := sys.stdin.read(1))
        if ch2 == '[':
            # escape sequence
            while not (chn := sys.stdin.read(1)).isalpha():
                inp += chn
            else:
                inp += chn
    termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    return inp.encode()
    

class InputHandler(BaseInputHandler):

    def _detect_keys(self):
        while self.checking_for_input:
            if self.input_queue.full():
                self.input_queue.get(False)
                self.input_queue.get(False)
            if sys.stdin.isatty():
                self.input_queue.put(self.filter_key(getch()), False)


if __name__ == "__main__":
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)
    ih = InputHandler()
    ih.start()
    sys.stdout.write("\x1b[?1003h\x1b[?1015h\x1b[?1006h")
    while True:
        if (char := ih.get()) != None:
            print(repr(char))
            if char == b'~':
                break
        time.sleep(0.1)
    sys.stdout.write("\x1b[?1000l")
    ih.stop()
    termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
        