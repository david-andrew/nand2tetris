from pathlib import Path
from utils import XML, Ref

import pdb



def compile(inpath:Path, outpath:Path):
    xml = XML.from_string(inpath.read_text())
    tokens: list[XML] = xml.children
    tokens_ref = Ref(tokens)
    
    root = XML("class", [])

    if not compile_class(tokens_ref, root):
        raise ValueError(f"Invalid program. Remaining tokens: {tokens_ref.value}")

    outpath.write_text(str(root))
    print(f'Wrote parse to {outpath}')



def compile_class(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """'class' className '{' classVarDec* subroutineDec* '}'"""
    
    # 'class'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["class"]:
        return False

    root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # className
    if tokens_ref.value[0].tag != "identifier":
        raise ValueError(f"Invalid program. Expected className, got {tokens_ref.value[0]}")

    root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '{'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["{"]:
        raise ValueError(f"Invalid program. Expected '{{', got {tokens_ref.value[0]}")

    root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # classVarDec*
    while compile_class_var_dec(tokens_ref, root):
        ...

    # subroutineDec*
    while compile_subroutine(tokens_ref, root):
        ...

    # '}'
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["}"]:
        raise ValueError(f"Invalid program. Expected '}}', got {tokens_ref.value[0]}")

    root.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    return True


def is_type(token:XML) -> bool:
    """'int' | 'char' | 'boolean' | className"""
    if token.tag == "keyword" and token.children in [["int"], ["char"], ["boolean"]]:
        return True
    if token.tag == "identifier":
        return True

def compile_class_var_dec(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """('static' | 'field') type varName (',' varName)* ';'"""
    
    # ('static' | 'field')
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children not in [["static"], ["field"]]:
        return False

    branch = XML("classVarDec", [])
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


def compile_subroutine(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_parameter_list(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """((type varName) (',' type varName)*)?"""
    
    # ((type varName) (',' type varName)*)?
    if tokens_ref.value[0].tag not in ["keyword", "identifier"]:
        return True # empty parameter list

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


def compile_subroutine_body(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_var_dec(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_statements(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """statement*"""
    
    # statement*
    while compile_do(tokens_ref, root) or \
          compile_let(tokens_ref, root) or \
          compile_while(tokens_ref, root) or \
          compile_return(tokens_ref, root) or \
          compile_if(tokens_ref, root):
        ...


    return True




def compile_do(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_let(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_while(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """'while' '(' expression ')' '{' statements '}'"""
    
    # 'while'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["while"]:
        return False

    branch = XML("whileStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

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


def compile_return(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_if(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""
    
    # 'if'
    if tokens_ref.value[0].tag != "keyword" or tokens_ref.value[0].children != ["if"]:
        return False
    

    branch = XML("ifStatement", [])
    branch.append_child(tokens_ref.value[0])
    tokens_ref.value = tokens_ref.value[1:]

    # '('
    if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["("]:
        raise ValueError(f"Invalid program. Expected '(', got {tokens_ref.value[0]}")

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

def compile_expression(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """term (op term)*"""
    
    # term
    if not compile_term(tokens_ref, root):
        return False

    # (op term)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children in [["+"], ["-"], ["*"], ["/"], ["&"], ["|"], ["<"], [">"], ["="]]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")

    return True


def compile_term(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
    """integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term"""
    
    # varName '[' expression ']'   # needs to be before varName
    if tokens_ref.value[0].tag == "identifier" and tokens_ref.value[1].tag == "symbol" and tokens_ref.value[1].children == ["["]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != ["]"]:
            raise ValueError(f"Invalid program. Expected ']', got {tokens_ref.value[0]}")

        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    # subroutineCall    # needs to be before varName
    if compile_subroutine_call(tokens_ref, root):
        return True

    # integerConstant
    if tokens_ref.value[0].tag == "integerConstant":
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    # stringConstant
    if tokens_ref.value[0].tag == "stringConstant":
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    # keywordConstant
    if tokens_ref.value[0].tag == "keyword" and tokens_ref.value[0].children in [["true"], ["false"], ["null"], ["this"]]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    # varName
    if tokens_ref.value[0].tag == "identifier":
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True

    # '(' expression ')'
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == ["("]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")
        
        if tokens_ref.value[0].tag != "symbol" or tokens_ref.value[0].children != [")"]:
            raise ValueError(f"Invalid program. Expected ')', got {tokens_ref.value[0]}")
        
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]
        return True
    
    # unaryOp term
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children in [["-"], ["~"]]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_term(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected term, got {tokens_ref.value[0]}")
        return True
    
    return False


def compile_subroutine_call(tokens_ref:Ref[list[XML|str]], root:XML) -> bool:
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


def compile_expression_list(tokens_ref:Ref[list[XML|str]], root:XML) -> bool: 
    """(expression (',' expression)*)?"""
    
    # (expression (',' expression)*)?
    if tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [")"]:
        return True # empty expression list

    # expression
    if not compile_expression(tokens_ref, root):
        raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    # (',' expression)*
    while tokens_ref.value[0].tag == "symbol" and tokens_ref.value[0].children == [","]:
        root.append_child(tokens_ref.value[0])
        tokens_ref.value = tokens_ref.value[1:]

        if not compile_expression(tokens_ref, root):
            raise ValueError(f"Invalid program. Expected expression, got {tokens_ref.value[0]}")

    return True


