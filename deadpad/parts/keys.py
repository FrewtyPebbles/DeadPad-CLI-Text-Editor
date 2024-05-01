import platform


opsys = platform.system()

LEFT = b'\x1b[D' if opsys == 'Linux' else b'\xe0K'
RIGHT = b'\x1b[C' if opsys == 'Linux' else b'\xe0M'
UP = b'\x1b[A' if opsys == 'Linux' else b'\xe0H'
DOWN = b'\x1b[B' if opsys == 'Linux' else b'\xe0P'
HOME = b'\x1b[H' if opsys == 'Linux' else b'\xe0G'
END = b'\x1b[F' if opsys == 'Linux' else b'\xe0O'
ESC = b'\x1b\x1b' if opsys == 'Linux' else b'\x1b'
BACKSPACE = b'\x7f' if opsys == 'Linux' else b'\x08'
CTRL_O = b'\x0f' if opsys == 'Linux' else b'\x0f'
CTRL_W = b'\x17' if opsys == 'Linux' else b'\x17'