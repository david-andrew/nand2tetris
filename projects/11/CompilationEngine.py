from utils import Ref
from JackTokenizer import Token
from SymbolTable import SymbolTable
from VMWriter import VMWriter

##
import pdb


# TODO: remove this eventually
XML = None


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
    """('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody"""

    # ('constructor' | 'function' | 'method')
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value not in ["constructor", "function", "method"]:
        return False

    # set up the symbol table for this subroutine
    subroutine_symbols = SymbolTable()
    if tokens_ref.value[0].value == "method":
        subroutine_symbols.insert("this", class_name, "argument")

    tokens_ref.value = tokens_ref.value[1:]

    # ('void' | type)
    if not is_type(tokens_ref.value[0]) and tokens_ref.value[0].type != "keyword" and tokens_ref.value[0].value != "void":
        raise ValueError(f"Invalid program. Expected type or 'void', got {tokens_ref.value[0]}")

    # return_type = tokens_ref.value[0].value
    return_void = tokens_ref.value[0].value == "void"
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected subroutineName, got {tokens_ref.value[0]}")

    subroutine_name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # create the initial label for the subroutine
    writer.write_function(f"{class_name}.{subroutine_name}", subroutine_symbols.var_count("local"))

    # '('
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

    # branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # parameterList
    if not compile_parameter_list(tokens_ref, subroutine_symbols):
        raise ValueError(f"Invalid program. Expected parameterList, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    # subroutineBody
    if not compile_subroutine_body(tokens_ref, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected subroutineBody, got {tokens_ref.value[0]}")

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


def compile_subroutine_body(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'{' varDec* statements '}'"""

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        return False

    tokens_ref.value = tokens_ref.value[1:]

    # varDec*
    while compile_var_dec(tokens_ref, subroutine_symbols):
        ...

    # statements
    if not compile_statements(tokens_ref, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        pdb.set_trace()
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

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


def compile_statements(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """statement*"""

    # statement*
    while compile_do(tokens_ref, class_symbols, subroutine_symbols, writer) or \
            compile_let(tokens_ref, class_symbols, subroutine_symbols, writer) or \
            compile_while(tokens_ref, class_symbols, subroutine_symbols, writer) or \
            compile_return(tokens_ref, class_symbols, subroutine_symbols, writer) or \
            compile_if(tokens_ref, class_symbols, subroutine_symbols, writer):
        ...

    return True


def compile_do(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'do' subroutineCall ';'"""

    # 'do'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "do":
        return False

    tokens_ref.value = tokens_ref.value[1:]

    # subroutineCall
    if not compile_subroutine_call(tokens_ref, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected subroutineCall, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    # throw away the return value
    writer.write_pop("temp", 0)

    return True


def compile_let(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
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

    # ('[' expression ']')?
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == "[":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "]":
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

    # '='
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "=":
        raise ValueError(f"Invalid program. Expected '=', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        pdb.set_trace()
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    writer.write_push("local", subroutine_symbols.index_of(var_name))

    return True


def compile_while(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'while' '(' expression ')' '{' statements '}'"""

    # 'while'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "while":
        return False

    branch = XML("whileStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
        raise ValueError(
            f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["{"]:
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # statements
    if not compile_statements(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["}"]:
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_return(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'return' expression? ';'"""

    # 'return'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "return":
        return False

    tokens_ref.value = tokens_ref.value[1:]

    # expression?
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        if not compile_expression(tokens_ref, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    writer.write_return()

    return True


def compile_if(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""

    # 'if'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "if":
        return False

    branch = XML("ifStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
        raise ValueError(
            f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["{"]:
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # statements
    if not compile_statements(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["}"]:
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # ('else' '{' statements '}')?
    if tokens_ref.value[0].tag == "keyword" and tokens_ref.value[0].children == ["else"]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["{"]:
            raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_statements(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["}"]:
            raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_expression(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """term (op term)*"""

    # term
    if not compile_term(tokens_ref, class_symbols, subroutine_symbols, writer):
        return False

    # (op term)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value in "+-*/&|<>=":
        operator = tokens_ref.value[0].value
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, class_symbols, subroutine_symbols, writer):
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


def compile_term(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term"""

    # varName '[' expression ']'   # needs to be before varName
    if tokens_ref.value[0].type == "identifier" and tokens_ref.value[1].type == "symbol" and tokens_ref.value[1].value == "[":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].children != ["]"]:
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # subroutineCall    # needs to be before varName
    if compile_subroutine_call(tokens_ref, class_symbols, subroutine_symbols, writer):
        root.append_child(branch)
        return True

    # integerConstant
    if tokens_ref.value[0].type == "integerConstant":
        writer.write_push("constant", tokens_ref.value[0].value)
        tokens_ref.value = tokens_ref.value[1:]

        return True

    # stringConstant
    if tokens_ref.value[0].type == "stringConstant":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # keywordConstant
    if tokens_ref.value[0].type == "keyword" and tokens_ref.value[0].children in [["true"], ["false"], ["null"], ["this"]]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # varName
    if tokens_ref.value[0].type == "identifier":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # '(' expression ')'
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == "(":
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

        tokens_ref.value = tokens_ref.value[1:]

        return True

    # unaryOp term
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].children in [["-"], ["~"]]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

        root.append_child(branch)
        return True

    return False


def compile_subroutine_call(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> bool:
    """subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'"""

    # subroutineName '(' expressionList ')'
    if tokens_ref.value[0].type == "identifier" and tokens_ref.value[1].type == "symbol" and tokens_ref.value[1].value == "(":
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression_list(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected expressionList, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
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
            writer.write_push(parent_symbol.kind, parent_symbol.index)
            pdb.set_trace()
            call_label = f"{parent_symbol.type}.{method_name}"
            nArgs += 1

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "(":
            raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

        tokens_ref.value = tokens_ref.value[1:]

        nArgs += compile_expression_list(tokens_ref, class_symbols, subroutine_symbols, writer)

        if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ")":
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

        tokens_ref.value = tokens_ref.value[1:]

        writer.write_call(call_label, nArgs)

        return True

    return False


def compile_expression_list(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable, subroutine_symbols: SymbolTable, writer: VMWriter) -> int:
    """(expression (',' expression)*)?"""
    nArgs = 0
    # (expression (',' expression)*)?
    if tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ")":
        return nArgs  # empty expression list

    # expression
    if not compile_expression(tokens_ref, class_symbols, subroutine_symbols, writer):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")
    nArgs += 1

    # (',' expression)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, class_symbols, subroutine_symbols, writer):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        nArgs += 1

    return nArgs
