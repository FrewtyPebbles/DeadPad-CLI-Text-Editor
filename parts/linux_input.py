import sys
import termios
import time
import tty
try:
    from parts.input_handler import BaseInputHandler
except ModuleNotFoundError:
    from input_handler import BaseInputHandler

def getch():
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)

    tty.setcbreak(fd)
    ch = sys.stdin.read(1).encode()
    if ch == b"\x1b":# if it is an arrow key read the rest of the bytes
        ch += sys.stdin.read(2).encode()
    termios.tcsetattr(fd, termios.TCSAFLUSH, orig)
    return ch
    

class InputHandler(BaseInputHandler):

    def _detect_keys(self):
        while self.checking_for_input:
            if self.input_queue.full():
                self.input_queue.get(False)
                self.input_queue.get(False)
            if sys.stdin.isatty():
                self.input_queue.put(self.filter_key(getch()), False)


if __name__ == "__main__":
    ih = InputHandler()
    ih.start()
    while True:
        if (char := ih.get()) != None:
            print(repr(char))
            if char == b'~':
                break
        time.sleep(0.1)
    ih.stop()
        