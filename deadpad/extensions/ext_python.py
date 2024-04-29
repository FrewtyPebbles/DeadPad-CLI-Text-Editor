from dataclasses import dataclass
from enum import Enum
import sys
from typing import Generic, Iterable, TypeVar

FILE_EXT = "py"

class TokType(Enum):
    kw_def = "def"
    kw_if = "if"
    kw_elif = "elif"
    kw_else = "else"
    kw_finally = "finally"
    kw_try = "try"
    kw_class = "class"
    kw_except = "except"
    kw_import = "import"
    kw_from = "from"
    kw_as = "as"
    label = 1
    op_nonlocal = "nonlocal"
    op_global = "global"
    op_raise = "raise"
    op_add = "+"
    op_sub = "-"
    op_mul = "*"
    op_div = "/"
    op_matmul = "@"
    op_bitor = "|"
    op_bitnot = "~"
    op_bitand = "&"
    op_mod = "%"
    op_or = "or"
    op_and = "and"
    op_not = "not"
    op_in = "in"
    op_assign = "="
    op_del = "del"
    op_eq = "=="
    op_gt = ">"
    op_lt = "<"
    op_lte = "<="
    op_gte = ">="
    op_neq = "!="
    op_is = "is"
    op_dot = "."
    string = 4
    integer = 5
    float = 6
    format_string = 7
    byte_string = 8
    raw_string = 9
    bool_true = "True"
    bool_false = "False"
    sqr_bracket_start = "["
    sqr_bracket_end = "]"
    cur_bracket_start = "{"
    cur_bracket_end = "}"
    parentheses_start = "("
    parentheses_end = ")"
    semi_colon = ":"
    type_str = "str"
    type_int = "int"
    type_float = "float"
    type_bool = "bool"
    type_bytes = "bytes"
    type_list = "list"
    type_set = "set"
    type_dict = "dict"
    type_tuple = "tuple"
    type = "type"
    module = "module"
    comment = 11
    space = " "
    tab = "\t"
    newline = "\n"
    backslash = "\\"

class PyExcept:
    def __init__(self, typ:str, description:str, metadata:dict[str,any] = None):
        self.type = typ
        self.description = description
        self.metadata = metadata
    
    def __repr__(self):
        return f"e'{self.type[:3]}'"

    def __str__(self):
        return f"{self.type}"

class Token:
    def __init__(self, tok_type:TokType, tok_value, col_num:int, line_num:int):
        self.tok_type = tok_type
        self.tok_value = tok_value
        self.col_num = col_num
        self.line_num = line_num
        self.exception = None
    

    def __repr__(self):
        return f"t'{self.tok_value}'"

    def __str__(self):
        return f"(STRING)\"{self.tok_value}\"" if self.tok_type == TokType.string else f"{self.tok_value}"

    @classmethod
    def from_raw(cls, raw_str:str, col_num:int, line_num:int, override_type:TokType = None):
        # str and bytes literals are handled by override_type
        if override_type:
            return Token(override_type, raw_str, col_num, line_num)
        
        try:
            return Token(TokType(raw_str), raw_str, col_num, line_num)
        except ValueError:
            
            # This is where we will do type parsing
            assume_num_str = raw_str.lstrip("-")
            if assume_num_str.isdigit():
                # now that we know the string is all integers, check if it isa valid integer
                if assume_num_str[0] == '0':
                    return PyExcept("SyntaxError", "Integers cannotbegin with a leading 0.")
                else:
                    # valid integer
                    return Token(TokType.integer, int(raw_str), col_num, line_num)
            else:
                try:
                    val = float(raw_str)
                    return Token(TokType.float, val, col_num, line_num)
                except ValueError:
                    return Token(TokType.label, raw_str, col_num, line_num)

T = TypeVar('T')

class Src(Generic[T]):
    def __init__(self, collection:Iterable[T]) -> None:
        self.iter = iter(collection)
        self.l_n = 1
        self.c_n = 1

    def __iter__(self):
        return self.iter

class Parser:

    def __init__(self, src:str, master = None):
        """
        This parses the src str into a python astso it can be used for syntax highlighting and other tooling.
        """
        self.src = src
        self.master = master

    def tokenize(self, src:str):
        # This function returns a list of `Token`s
        src:Src[str] = Src(src)
        tokens:list[Token] = []
        self.tokenize_code_context(tokens, src)
        
        return tokens
    
    def tokenize_code_context(self, tokens:list[Token], src:Src[str]):
        tok_buff = ""
        for char in src:
            match char:
                case '\r':
                    pass
                case '+'|'-'|'*'|'/'|'@'|'='|'~'|'(' \
                |')'|'{'|'}'|'['|']'|':'|'.'|'&'|' '|'\t'|'\\':
                    append_tok(tokens, src.c_n, src.l_n, tok_buff=tok_buff)
                    tok_buff = ""
                    append_tok(tokens, src.c_n, src.l_n, char)
                case '"'|'\'':
                    append_tok(tokens, src.c_n, src.l_n, tok_buff=tok_buff)
                    tok_buff = ""
                    self.tokenize_str_context(tokens, src, char)
                case '\n':
                    append_tok(tokens, src.c_n, src.l_n, tok_buff=tok_buff)
                    tok_buff = ""
                    append_tok(tokens, src.c_n, src.l_n, '\n')
                    src.c_n = 1
                    src.l_n += 1
                case _:
                    tok_buff += char

            src.c_n += 1
    
    def tokenize_str_context(self, tokens:list[Token], src:Src[str], str_tok:str):
        tok_buff = ""
        escape=False
        for char in src:
            match char:
                case '\''|'"':
                    # end string
                    if char == str_tok and not escape:
                        tokens.append(Token.from_raw(tok_buff, src.c_n, src.l_n, TokType.string))
                        return
                    else:
                        tok_buff += char
                        escape = False
                case '\n':
                    tok_buff += char
                    escape = False
                    src.c_n = 1
                    src.l_n += 1
                case _:
                    if char == '\\':
                        # TODO BUG escape not working
                        escape = not escape
                    elif escape:
                        escape = False
                    tok_buff += char

            src.c_n += 1


def append_tok(tokens:list[Token], c_n:int, l_n:int, tok_str:str = None, tok_buff:str = ""):
    if tok_str == None:
        if tok_buff != "":
            tokens.append(Token.from_raw(tok_buff, c_n, l_n))
    else:
        tokens.append(Token.from_raw(tok_str, c_n, l_n))


if __name__ == "__main__":
    src_file = open(sys.argv[1])
    parser = Parser(src_file.read())
    src_file.close()
    print("".join([str(tok) for tok in parser.tokenize(parser.src)]))



