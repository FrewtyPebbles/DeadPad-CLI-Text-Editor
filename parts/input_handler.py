import threading as th
from queue import Queue

class BaseInputHandler:
    def __init__(self) -> None:
        self._processing_thread = th.Thread(target=self._detect_keys, daemon=True)
        self.checking_for_input = True
        self.input_queue:Queue[bytes] = Queue()

    def _detect_keys(self):
        "While true and queue keys."

    def filter_key(self, key:bytes):
        k_filter = {
            b'\r':b'\n'
        }
        return (k_filter)[key] if key in k_filter.keys() else key

    def start(self):
        "Start recording inputs."
        self.checking_for_input = True
        self._processing_thread.start()

    def stop(self):
        "Stop recording inputs."
        self.checking_for_input = False

    def get(self):
        "Get the next input in the input queue"
        if not self.input_queue.empty():
            return self.input_queue.get(False)