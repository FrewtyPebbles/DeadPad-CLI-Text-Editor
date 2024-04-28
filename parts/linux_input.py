import sys
import termios
import threading as th
from queue import Queue
import tty
from parts.input_handler import BaseInputHandler


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
 
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch.encode()

class InputHandler(BaseInputHandler):

    def _detect_keys(self):
        while self.checking_for_input:
            self.input_queue.put(self.filter_key(getch()), False)
