import datetime
import platform
import sys
try:
    from parts.windows_input import InputHandler
except ModuleNotFoundError:
    from parts.linux_input import InputHandler
from parts.textscreen import TextScreen
import shutil
from parts.document import Document

opsys = platform.system()



class Editor:
    "The main class for the python based CLI text editor Dead Pad"
    def __init__(self) -> None:
        self.in_handler = InputHandler()
        self.term_size = shutil.get_terminal_size()
        self.settings = {
            # Toggleables
            "show_paragraphs": False,
            "show_tabs": False,
            "line_numbers": True,
            # General config
            "theme": "./themes/default.json",
            "tab_replace": "\t",
        }

        self.screen = TextScreen(self, self.term_size.columns, self.term_size.lines, Document(self, self.term_size.columns, sys.argv[1]))

    def run_command(self, command_str:str):
        tokens = self.get_tokens(command_str)
        if len(tokens) > 0:
            match tokens[0]: # command name
                case "set": # changes a setting
                    self.settings[tokens[1]] = (val:=self.parse_literal(tokens[2]))
                    self.screen.footer_string = f"Set {tokens[1]} to {repr(val)}"
                case "toggle": # toggles a setting
                    self.settings[tokens[1]] = not self.settings[tokens[1]]
                case "exit":
                    self.screen.footer_string = f"EXITING"
                    self.screen.running = False
                case "save":
                    self.screen.footer_string = f"Last saved to '{self.screen.document.file_path}' at {datetime.datetime.now()}. 📀"
                    self.screen.document.save()
                case "refresh":
                    self.screen.refresh()
                    self.screen.footer_string = f"Dead Pad Themes, Plugins, and Config refreshed."
                case "edit":
                    self.screen.open_document(tokens[1])
                case _:
                    self.screen.footer_string = f"Unknown command \"{tokens[0]}\""
                    

    def parse_literal(self, tok:str):
        if tok == "true":
            return True
        if tok == "false":
            return False
        if tok.isdigit():
            return int(tok)
        try:
            return float(tok)
        except ValueError:
            pass

        return tok
    
    def get_tokens(self, command_str:str):
        tok_buffer = ""
        tokens = []
        is_str = ""
        escape = False

        def push_tok(tok:str):
            nonlocal tok_buffer
            if tok_buffer != "":
                tokens.append(tok)
                tok_buffer = ""

        for char in command_str:
            if is_str != "":
                if char == is_str and not escape:
                    is_str = ""
                    push_tok(tok_buffer)
                else:
                    match char:
                        case '\\':
                            if not escape:
                                escape = True
                            else:
                                tok_buffer += char
                        case '"':
                            tok_buffer += char
                            escape = False
                        case '\'':
                            tok_buffer += char
                            escape = False
                        case 'n':
                            if escape:
                                tok_buffer += "\n"
                                escape = False
                            else:
                                tok_buffer += char
                        case 't':
                            if escape:
                                tok_buffer += "\t"
                                escape = False
                            else:
                                tok_buffer += char
                        case 'b':
                            if escape:
                                tok_buffer += "\b"
                                escape = False
                            else:
                                tok_buffer += char
                        case 'r':
                            if escape:
                                tok_buffer += "\r"
                                escape = False
                            else:
                                tok_buffer += char
                        case _:
                            tok_buffer += char
                    
            else:
                match char:
                    case '"'|'\'':
                        is_str = char
                    case ' '|'\t':
                        push_tok(tok_buffer)
                    case _:
                        tok_buffer += char

        push_tok(tok_buffer)
        return tokens

        
    def run(self):
        try:
            import termios
            orig = termios.tcgetattr(sys.stdin.fileno())
        except ModuleNotFoundError:
            pass
        self.in_handler.start()
        while self.screen.running:
            self._run_update()
        self.in_handler.stop()
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, orig)
        except UnboundLocalError:
            pass
        sys.stdout.write("\033c")
        
    def _run_update(self):
        self.screen.handle_key(self.in_handler.get())
        term_size = shutil.get_terminal_size()
        if self.screen.check_update()\
         or term_size.lines != self.term_size.lines\
         or term_size.columns != self.term_size.columns:
            self.term_size = term_size
            clear_str = "\033[F\033[K" * (self.term_size.lines)
            self.screen.render(self.term_size.columns, self.term_size.lines)
            sys.stdout.write(f"{clear_str}{self.screen.render(self.term_size.columns, self.term_size.lines)}")

if __name__ == "__main__":
    editor = Editor()
    editor.run()
