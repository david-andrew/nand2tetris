from utils import Ref
from JackTokenizer import Token
from SymbolTable import SymbolTable
from VMWriter import VMWriter

##
import pdb


def compile(tokens: list[Token]) -> str:
    tokens_ref = Ref(tokens)
    writer = VMWriter()

    if not compile_class(tokens_ref, writer):
        raise ValueError(f"Invalid program. Remaining tokens: {tokens_ref.value}")

    return writer.__str__()


def compile_class(tokens_ref: Ref[list[Token]], writer: VMWriter) -> bool:
    """'class' className '{' classVarDec* subroutineDec* '}'"""

    # 'class'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "class":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    class_symbols = SymbolTable()

    # className
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected className, got {tokens_ref.value[0]}")
    class_name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # classVarDec*
    while compile_class_var_dec(tokens_ref, class_symbols):
        ...

    # subroutineDec*
    while compile_subroutine(tokens_ref, class_name, class_symbols, writer):
        ...

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    return True


def is_type(token: Token) -> bool:
    """'int' | 'char' | 'boolean' | className"""
    if token.type == "keyword" and token.value in ["int", "char", "boolean"]:
        return True
    if token.type == "identifier":
        return True
    return False


def compile_class_var_dec(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable) -> bool:
    """('static' | 'field') type varName (',' varName)* ';'"""

    # ('static' | 'field')
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value not in ["static", "field"]:
        return False
    kind = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")
    type = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
    name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # insert the first variable
    class_symbols.insert(name, type, kind)

    # (',' varName)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].type != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

        name = tokens_ref.value[0].value
        class_symbols.insert(name, type, kind)
        tokens_ref.value = tokens_ref.value[1:]

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    return True


def compile_subroutine(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, writer: VMWriter) -> bool:
    """('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' '{' varDec* statements '}'"""

    # ('constructor' | 'function' | 'method')
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value not in ["constructor", "function", "method"]:
        return False
    subroutine_type = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # set up the symbol table for this subroutine
    subroutine_symbols = SymbolTable()

    if subroutine_type == "method":
        subroutine_symbols.insert("this", class_name, "argument")

    # ('void' | type)
    if not is_type(tokens_ref.value[0]) and tokens_ref.value[0].type != "keyword" and tokens_ref.value[0].value != "void":
        raise ValueError(f"Invalid program. Expected type or 'void', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected subroutineName, got {tokens_ref.value[0]}")
    subroutine_name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # parameterList
    if not compile_parameter_list(tokens_ref, subroutine_symbols):
        raise ValueError(f"Invalid program. Expected parameterList, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # varDec*
    while compile_var_dec(tokens_ref, subroutine_symbols):
        ...

    # now that we know how many locals there are, we can create the function entry label
    writer.write_function(f"{class_name}.{subroutine_name}", subroutine_symbols.var_count("local"))

    # if a method, add `this` as the first argument, and set the base address to `this` object
    if subroutine_type == "method":
        writer.write_push("argument", 0)
        writer.write_pop("pointer", 0)
    elif subroutine_type == "constructor":
        writer.write_push("constant", class_symbols.var_count("field"))
        writer.write_call("Memory.alloc", 1)
        writer.write_pop("pointer", 0)

    # statements
    if not compile_statements(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    return True


def compile_parameter_list(tokens_ref: Ref[list[Token]], subroutine_symbols: SymbolTable) -> bool:
    """((type varName) (',' type varName)*)?"""
    # ((type varName) (',' type varName)*)?
    if tokens_ref.value[0].type not in ["keyword", "identifier"]:
        return True  # empty parameter list

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")
    type = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
    name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # insert the first variable
    subroutine_symbols.insert(name, type, "argument")

    # (',' type varName)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        # type
        if not is_type(tokens_ref.value[0]):
            raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")
        type = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        # varName
        if tokens_ref.value[0].type != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
        name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        subroutine_symbols.insert(name, type, "argument")

    return True


def compile_var_dec(tokens_ref: Ref[list[Token]], subroutine_symbols: SymbolTable) -> bool:
    """'var' type varName (',' varName)* ';'"""

    # 'var'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "var":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")
    type = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
    name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # insert the first variable
    subroutine_symbols.insert(name, type, "local")

    # (',' varName)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].type != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
        name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        subroutine_symbols.insert(name, type, "local")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    return True


def compile_statements(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """statement*"""

    # statement*
    while compile_do(tokens_ref, class_name, class_symbols, subroutine_symbols, writer) or \
            compile_let(tokens_ref, class_name, class_symbols, subroutine_symbols, writer) or \
            compile_while(tokens_ref, class_name, class_symbols, subroutine_symbols, writer) or \
            compile_return(tokens_ref, class_name, class_symbols, subroutine_symbols, writer) or \
            compile_if(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        ...

    return True


def compile_do(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'do' subroutineCall ';'"""

    # 'do'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "do":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineCall
    if not compile_subroutine_call(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected subroutineCall, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # throw away the return value
    writer.write_pop("temp", 0)

    return True


def compile_let(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'let' varName ('[' expression ']')? '=' expression ';'"""

    # 'let'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "let":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")
    var_name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # get the symbol associated with this variable
    symbol = subroutine_symbols.get(var_name, None) or class_symbols.get(var_name, None)
    assert symbol is not None, f"Variable {var_name} not found. Expected local or class variable."

    # ('[' expression ']')?
    is_array_assignment = False
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == "[":
        tokens_ref.value = tokens_ref.value[1:]
        is_array_assignment = True

        # push the base address of the array
        writer.write_push(symbol.kind, symbol.index)

        if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "]":
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        # add the index to the base address
        writer.write_arithmetic("add")

    # '='
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "=":
        raise ValueError(f"Invalid program. Expected '=', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    if is_array_assignment:
        writer.write_pop("temp", 0)
        writer.write_pop("pointer", 1)
        writer.write_push("temp", 0)
        writer.write_pop("that", 0)
    elif symbol.kind == "field":
        writer.write_pop("this", symbol.index)
    else:
        writer.write_pop(symbol.kind, symbol.index)

    return True


while_label_count = 0


def compile_while(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'while' '(' expression ')' '{' statements '}'"""

    # 'while'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "while":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    global while_label_count
    L1 = f"WHILE{while_label_count}"
    L2 = f"WHILE_END{while_label_count}"
    while_label_count += 1
    writer.write_label(L1)

    # '('
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    writer.write_arithmetic("not")
    writer.write_if(L2)

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # statements
    if not compile_statements(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    writer.write_goto(L1)
    writer.write_label(L2)

    return True


def compile_return(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'return' expression? ';'"""

    # 'return'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "return":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    # expression?
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")
    else:
        writer.write_push("constant", 0)

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    writer.write_return()

    return True


if_label_count = 0


def compile_if(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""

    # 'if'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "if":
        return False
    tokens_ref.value = tokens_ref.value[1:]

    global if_label_count
    L1 = f"IF_FALSE{if_label_count}"
    L2 = f"IF_END{if_label_count}"
    if_label_count += 1

    # '('
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    writer.write_arithmetic("not")
    writer.write_if(L1)

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    # statements
    if not compile_statements(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")
    tokens_ref.value = tokens_ref.value[1:]

    writer.write_goto(L2)
    writer.write_label(L1)

    # ('else' '{' statements '}')?
    if tokens_ref.value[0].type == "keyword" and tokens_ref.value[0].value == "else":
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
            raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_statements(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
            raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

    writer.write_label(L2)

    return True


def compile_expression(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """term (op term)*"""

    # term
    if not compile_term(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        return False

    # (op term)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value in "+-*/&|<>=":
        operator = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

        if operator == "+":
            writer.write_arithmetic("add")
        elif operator == "-":
            writer.write_arithmetic("sub")
        elif operator == "*":
            writer.write_call("Math.multiply", 2)
        elif operator == "/":
            writer.write_call("Math.divide", 2)
        elif operator == "&":
            writer.write_arithmetic("and")
        elif operator == "|":
            writer.write_arithmetic("or")
        elif operator == "<":
            writer.write_arithmetic("lt")
        elif operator == ">":
            writer.write_arithmetic("gt")
        elif operator == "=":
            writer.write_arithmetic("eq")
        else:
            raise ValueError(f"Invalid operator: {operator}")

    return True


def compile_term(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term"""

    # varName '[' expression ']'   # needs to be before varName
    if tokens_ref.value[0].type == "identifier" and tokens_ref.value[1].type == "symbol" and tokens_ref.value[1].value == "[":
        var_name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[2:]

        # push the base address of the array
        symbol = subroutine_symbols.get(var_name, None) or class_symbols.get(var_name, None)
        assert symbol is not None, f"Variable {var_name} not found. Expected local or class variable."
        writer.write_push(symbol.kind, symbol.index)

        if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "]":
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        # add the index to the base address
        writer.write_arithmetic("add")
        writer.write_pop("pointer", 1)

        # push the value of the array
        writer.write_push("that", 0)

        return True

    # subroutineCall    # needs to be before varName
    if compile_subroutine_call(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        return True

    # integerConstant
    if tokens_ref.value[0].type == "integerConstant":
        writer.write_push("constant", tokens_ref.value[0].value)
        tokens_ref.value = tokens_ref.value[1:]

        return True

    # stringConstant
    if tokens_ref.value[0].type == "stringConstant":
        string = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        writer.write_push("constant", len(string))
        writer.write_call("String.new", 1)
        for char in string:
            writer.write_push("constant", ord(char))
            writer.write_call("String.appendChar", 2)

        return True

    # keywordConstant
    if tokens_ref.value[0].type == "keyword" and tokens_ref.value[0].value in ["true", "false", "null", "this"]:
        if tokens_ref.value[0].value == "true":
            writer.write_push("constant", 1)
            writer.write_arithmetic("neg")
        elif tokens_ref.value[0].value == "false":
            writer.write_push("constant", 0)
        elif tokens_ref.value[0].value == "null":
            writer.write_push("constant", 0)
        elif tokens_ref.value[0].value == "this":
            writer.write_push("pointer", 0)
        else:
            raise ValueError(f"Invalid keyword: {tokens_ref.value[0].value}")
        tokens_ref.value = tokens_ref.value[1:]

        return True

    # varName
    if tokens_ref.value[0].type == "identifier":
        name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        symbol = subroutine_symbols.get(name, None) or class_symbols.get(name, None)
        assert symbol is not None, f"Variable {name} not found. Expected local or class variable."
        if symbol.kind == "field":
            writer.write_push("this", symbol.index)
        else:
            writer.write_push(symbol.kind, symbol.index)

        return True

    # '(' expression ')'
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == "(":
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        return True

    # unaryOp term
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value in "-~":
        operator = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

        if operator == "-":
            writer.write_arithmetic("neg")
        elif operator == "~":
            writer.write_arithmetic("not")
        else:
            raise ValueError(f"Invalid operator: {operator}")
        return True

    return False


def compile_subroutine_call(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'"""

    # subroutineName '(' expressionList ')'
    if tokens_ref.value[0].type == "identifier" and tokens_ref.value[1].type == "symbol" and tokens_ref.value[1].value == "(":
        nArgs = 0
        subroutine_name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[2:]

        # push this as the first argument
        writer.write_push("pointer", 0)
        nArgs += 1

        # expressionList
        nArgs += compile_expression_list(tokens_ref, class_name, class_symbols, subroutine_symbols, writer)

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        writer.write_call(f"{class_name}.{subroutine_name}", nArgs)

        return True

    # (className | varName) '.' subroutineName '(' expressionList ')'
    if tokens_ref.value[0].type == "identifier" and tokens_ref.value[1].type == "symbol" and tokens_ref.value[1].value == ".":
        nArgs = 0
        parent_name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[2:]

        if tokens_ref.value[0].type != "identifier":
            raise ValueError(f"Invalid program. Expected subroutineName, got {tokens_ref.value[0]}")
        method_name = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        call_label = f"{parent_name}.{method_name}"

        parent_symbol = subroutine_symbols.get(parent_name, None) or class_symbols.get(parent_name, None)
        if parent_symbol is not None:
            if parent_symbol.kind == "field":
                writer.write_push("this", parent_symbol.index)
            else:
                writer.write_push(parent_symbol.kind, parent_symbol.index)
            call_label = f"{parent_symbol.type}.{method_name}"
            nArgs += 1

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
            raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        # expressionList
        nArgs += compile_expression_list(tokens_ref, class_name, class_symbols, subroutine_symbols, writer)

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
        tokens_ref.value = tokens_ref.value[1:]

        writer.write_call(call_label, nArgs)

        return True

    return False


def compile_expression_list(tokens_ref: Ref[list[Token]], class_name: str, class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> int:
    """(expression (',' expression)*)?"""
    nArgs = 0
    # (expression (',' expression)*)?
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ")":
        return nArgs  # empty expression list

    # expression
    if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")
    nArgs += 1

    # (',' expression)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, class_name, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        nArgs += 1

    return nArgs
