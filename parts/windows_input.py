import msvcrt as ms
import sys
import threading as th
from queue import Queue
from parts.input_handler import BaseInputHandler

class InputHandler(BaseInputHandler):
    def _detect_keys(self):
        while self.checking_for_input:
            if ms.kbhit():
                self.input_queue.put(self.filter_key(ms.getch()), False)