import msvcrt as ms
import sys
import threading as th
from queue import Queue
import time
from deadpad.parts.input.input_handler import BaseInputHandler, InputEvent, InputType

import deadpad.parts.input.wininp_c.wininp as c_inp


class InputHandler(BaseInputHandler):
    
    def _detect_keys(self):
        while self.checking_for_input:
            if self.input_queue.full():
                self.input_queue.get(False)
                self.input_queue.get(False)
            raw_inp = c_inp.get_key()
            sys.stdin.flush()
            if raw_inp:
                self.input_queue.put(InputEvent(raw_inp), False)
        
if __name__ == "__main__":
    def t1():
        ih = InputHandler()
        ih.start()
        while True:
            if (char := ih.get()) != None:
                print(repr(char))
                if char == b'~':
                    break
            time.sleep(0.1)
        ih.stop()

    def t2():
        while True:
            if (m_tup := c_inp.get_mouse()) != None:
                print(m_tup)
            time.sleep(0.1)
    t2()
        