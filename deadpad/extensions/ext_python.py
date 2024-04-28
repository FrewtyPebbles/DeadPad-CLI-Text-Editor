from enum import Enum
import sys

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
        return f"{self.tok_value}"

    @classmethod
    def from_raw(cls, raw_str:str, col_num:int, line_num:int, override_type:TokType = None):
        try:
            return Token(TokType(raw_str), raw_str, col_num, line_num)
        except ValueError:
            # str and bytes literals are handled by override_type
            if override_type != None:
                return Token(override_type, raw_str, col_num, line_num)
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



class Parser:

    def __init__(self, src:str, master = None):
        """
        This parses the src str into a python astso it can be used for syntax highlighting and other tooling.
        """
        self.src = src
        self.master = master

    def tokenize(self, src:str):
        # This function returns a list of `Token`s
        lines = enumerate(src.splitlines())
        tokens:list[Token] = []
        tok_buff = ""
        
        l_n = 0
        c_n = 0

        def append_tok(tok_str:str = None):
            nonlocal tok_buff
            if tok_str == None:
                if len(tok_buff) != 0:
                    tokens.append(Token.from_raw(tok_buff, c_n, l_n))
                    tok_buff = ""
            else:
                tokens.append(Token.from_raw(tok_str, c_n, l_n))
                
        for l_n, line in lines:
            for c_n, char in enumerate(line):
                match char:
                    case '+'|'-'|'*'|'/'|'@'|'='|'~'|'(' \
                    |')'|'{'|'}'|'['|']'|':'|'.'|'&'|' '|'\t'|'\\':
                        append_tok()
                        append_tok(char)
                    case '"'|'\'':
                        pass # TODO make string parsing context
                        # will likely need to move this loop to its own context so that we can use it again for format strings.
                    case _:
                        tok_buff += char
            append_tok()
            append_tok('\n')
        return tokens




if __name__ == "__main__":
    src_file = open(sys.argv[1])
    parser = Parser(src_file.read())
    src_file.close()
    print("".join([str(tok) for tok in parser.tokenize(parser.src)]))



