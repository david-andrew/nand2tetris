from pathlib import Path
from utils import Ref
from JackTokenizer import Token
from dataclasses import dataclass

##
import pdb


# TODO: remove this eventually
XML = None


@dataclass
class Symbol:
    # name: str # key in the symbol table
    type: str
    kind: str
    index: int


class SymbolTable(dict[str, Symbol]):
    def insert(self, name: str, type: str, kind: str) -> None:
        self[name] = Symbol(type, kind, self.var_count(kind))

    def var_count(self, kind: str) -> int:
        return len([symbol for symbol in self.values() if symbol.kind == kind])

    def __str__(self) -> str:
        """nice table printout"""
        name_width = max(*(len(name) for name in self.keys()), len("name"))
        type_width = max(*(len(symbol.type) for symbol in self.values()), len("type"))
        kind_width = max(*(len(symbol.kind) for symbol in self.values()), len("kind"))
        index_width = max(*(len(str(symbol.index)) for symbol in self.values()), len("#"))

        header = f"{'name':<{name_width}} │ {'type':<{type_width}} │ {'kind':<{kind_width}} │ {'#':<{index_width}}"
        lines = [header]
        lines.append(f"{'─' * name_width}─┼─{'─' * type_width}─┼─{'─' * kind_width}─┼─{'─' * index_width}─")
        for name, symbol in self.items():
            lines.append(f"{name:<{name_width}} │ {symbol.type:<{type_width}} │ {
                         symbol.kind:<{kind_width}} │ {symbol.index:<{index_width}}")
        return "\n".join(lines)


def compile(tokens: list[Token]) -> str:
    tokens_ref = Ref(tokens)

    vmcode = compile_class(tokens_ref)
    if vmcode is None:
        raise ValueError(f"Invalid program. Remaining tokens: {tokens_ref.value}")

    return vmcode


def compile_class(tokens_ref: Ref[list[Token]]) -> str | None:
    """'class' className '{' classVarDec* subroutineDec* '}'"""

    # 'class'
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value != "class":
        return False

    class_symbols = SymbolTable()

    # root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # className
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected className, got {tokens_ref.value[0]}")

    # root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "{":
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")

    # root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # classVarDec*
    while compile_class_var_dec(tokens_ref, class_symbols):
        ...
    pdb.set_trace()

    # subroutineDec*
    while compile_subroutine(tokens_ref):
        ...

    # '}'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != "}":
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    # root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    return True


def is_type(token: Token) -> bool:
    """'int' | 'char' | 'boolean' | className"""
    if token.type == "keyword" and token.value in ["int", "char", "boolean"]:
        return True
    if token.type == "identifier":
        return True


def compile_class_var_dec(tokens_ref: Ref[list[Token]], class_symbols: SymbolTable) -> bool:
    """('static' | 'field') type varName (',' varName)* ';'"""

    # ('static' | 'field')
    if tokens_ref.value[0].type != "keyword" or tokens_ref.value[0].value not in ["static", "field"]:
        return False

    decl0_kind = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")

    decl0_type = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].type != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

    name = tokens_ref.value[0].value
    tokens_ref.value = tokens_ref.value[1:]

    # insert the first variable
    class_symbols.insert(name, decl0_type, decl0_kind)

    # (',' varName)*
    while tokens_ref.value[0].type == "symbol" and tokens_ref.value[0].value == ",":
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].type != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

        name = tokens_ref.value[0].value
        class_symbols.insert(name, decl0_type, decl0_kind)
        tokens_ref.value = tokens_ref.value[1:]

    # ';'
    if tokens_ref.value[0].type != "symbol" or tokens_ref.value[0].value != ";":
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    tokens_ref.value = tokens_ref.value[1:]

    return True


def compile_subroutine(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody"""

    # ('constructor' | 'function' | 'method')
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children not in [["constructor"], ["function"], ["method"]]:
        return False

    branch = XML("subroutineDec", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # ('void' | type)
    if not is_type(tokens_ref.value[0]) and tokens_ref.value[0].tag != "keyword" and tokens_ref.value[0].children != ["void"]:
        raise ValueError(f"Invalid program. Expected type or 'void', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineName
    if tokens_ref.value[0].tag != "identifier":
        raise ValueError(f"Invalid program. Expected subroutineName, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # parameterList
    if not compile_parameter_list(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected parameterList, got {tokens_ref.value[0]}")

    # ')'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
        raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineBody
    if not compile_subroutine_body(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected subroutineBody, got {tokens_ref.value[0]}")

    root.append_child(branch)
    return True


def compile_parameter_list(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """((type varName) (',' type varName)*)?"""

    # ((type varName) (',' type varName)*)?
    if tokens_ref.value[0].tag not in ["keyword", "identifier"]:
        root.append_child(XML("parameterList", []))
        return True  # empty parameter list

    branch = XML("parameterList", [])

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].tag != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # (',' type varName)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [","]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        # type
        if not is_type(tokens_ref.value[0]):
            raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        # varName
        if tokens_ref.value[0].tag != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_subroutine_body(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'{' varDec* statements '}'"""

    # '{'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["{"]:
        return False

    branch = XML("subroutineBody", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # varDec*
    while compile_var_dec(tokens_ref, branch):
        ...

    # statements
    if not compile_statements(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected statements, got {tokens_ref.value[0]}")

    # '}'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["}"]:
        pdb.set_trace()
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_var_dec(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'var' type varName (',' varName)* ';'"""

    # 'var'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["var"]:
        return False

    branch = XML("varDec", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # type
    if not is_type(tokens_ref.value[0]):
        raise ValueError(f"Invalid program. Expected type, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].tag != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # (',' varName)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [","]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].tag != "identifier":
            raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

    # ';'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [";"]:
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_statements(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """statement*"""

    branch = XML("statements", [])

    # statement*
    while compile_do(tokens_ref, branch) or \
            compile_let(tokens_ref, branch) or \
            compile_while(tokens_ref, branch) or \
            compile_return(tokens_ref, branch) or \
            compile_if(tokens_ref, branch):
        ...

    root.append_child(branch)
    return True


def compile_do(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'do' subroutineCall ';'"""

    # 'do'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["do"]:
        return False

    branch = XML("doStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # subroutineCall
    if not compile_subroutine_call(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected subroutineCall, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [";"]:
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_let(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'let' varName ('[' expression ']')? '=' expression ';'"""

    # 'let'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["let"]:
        return False

    branch = XML("letStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # varName
    if tokens_ref.value[0].tag != "identifier":
        raise ValueError(f"Invalid program. Expected varName, got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # ('[' expression ']')?
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == ["["]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["]"]:
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

    # '='
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["="]:
        raise ValueError(f"Invalid program. Expected '=', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # expression
    if not compile_expression(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [";"]:
        pdb.set_trace()
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_while(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'while' '(' expression ')' '{' statements '}'"""

    # 'while'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["while"]:
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


def compile_return(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'return' expression? ';'"""

    # 'return'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["return"]:
        return False

    branch = XML("returnStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # expression?
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [";"]:
        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # ';'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [";"]:
        raise ValueError(f"Invalid program. Expected ';', got {tokens_ref.value[0]}")

    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    root.append_child(branch)
    return True


def compile_if(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""

    # 'if'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["if"]:
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


def compile_expression(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """term (op term)*"""

    branch = XML("expression", [])

    # term
    if not compile_term(tokens_ref, branch):
        return False

    # (op term)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children in [["+"], ["-"], ["*"], ["/"], ["&"], ["|"], ["<"], [">"], ["="]]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

    root.append_child(branch)
    return True


def compile_term(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term"""

    branch = XML("term", [])

    # varName '[' expression ']'   # needs to be before varName
    if tokens_ref.value[0].tag == "identifier" and tokens_ref.value[1].tag == "symbol" and tokens_ref.value[1].children == ["["]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["]"]:
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # subroutineCall    # needs to be before varName
    if compile_subroutine_call(tokens_ref, branch):
        root.append_child(branch)
        return True

    # integerConstant
    if tokens_ref.value[0].tag == "integerConstant":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # stringConstant
    if tokens_ref.value[0].tag == "stringConstant":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # keywordConstant
    if tokens_ref.value[0].tag == "keyword" and tokens_ref.value[0].children in [["true"], ["false"], ["null"], ["this"]]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # varName
    if tokens_ref.value[0].tag == "identifier":
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # '(' expression ')'
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == ["("]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(branch)
        return True

    # unaryOp term
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children in [["-"], ["~"]]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

        root.append_child(branch)
        return True

    return False


def compile_subroutine_call(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'"""

    # subroutineName '(' expressionList ')'
    if tokens_ref.value[0].tag == "identifier" and tokens_ref.value[1].tag == "symbol" and tokens_ref.value[1].children == ["("]:
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
    if tokens_ref.value[0].tag == "identifier" and tokens_ref.value[1].tag == "symbol" and tokens_ref.value[1].children == ["."]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].tag != "identifier":
            raise ValueError(f"Invalid program. Expected subroutineName, got {tokens_ref.value[0]}")

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
            raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression_list(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected expressionList, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    return False


def compile_expression_list(tokens_ref: Ref[list[XML | str]], root: XML) -> bool:
    """(expression (',' expression)*)?"""

    branch = XML("expressionList", [])

    # (expression (',' expression)*)?
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [")"]:
        root.append_child(branch)
        return True  # empty expression list

    # expression
    if not compile_expression(tokens_ref, branch):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # (',' expression)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [","]:
        branch.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, branch):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    root.append_child(branch)
    return True
