from pathlib import Path
from utils import XML, Ref


keywords = {
    "class", "constructor", "function", "method", "field", "static", "var", 
    "int", "char", "boolean", "void", "true", "false", "null", "this", "let", 
    "do", "if", "else", "while", "return"
}

symbols = {*"{}()[].,;+-*/&|<>=~"}


def tokenize(inpath:Path, outpath:Path):
    src = Ref(inpath.read_text())
    xml = XML("tokens", [])
    while len(src.value) > 0:
        if eat_comments(src): continue
        if eat_whitespace(src): continue
        if eat_keyword(src, xml): continue
        if eat_symbol(src, xml): continue
        if eat_integer_constant(src, xml): continue
        if eat_string_constant(src, xml): continue
        if eat_identifier(src, xml): continue
        pdb.set_trace()
        raise Exception(f"Invalid token: '{src.value}'")

    outpath.write_text(str(xml))
    print(f'Wrote tokens to {outpath}')

def eat_keyword(src:Ref[str], xml:XML) -> bool:
    for keyword in keywords:
        if src.value.startswith(keyword) and (len(src.value) == len(keyword) or not src.value[len(keyword)].isalnum()):
            xml.append(XML("keyword", [keyword]))
            src.value = src.value[len(keyword):]
            return True
    return False

def eat_symbol(src:Ref[str], xml:XML) -> bool:
    if src.value[0] in symbols:
        xml.append(XML("symbol", [src.value[0]]))
        src.value = src.value[1:]
        return True
    return False

def eat_integer_constant(src:Ref[str], xml:XML) -> bool:
    if src.value[0].isdigit():
        i = 1
        while i < len(src.value) and src.value[i].isdigit():
            i += 1
        xml.append(XML("integerConstant", [src.value[:i]]))
        src.value = src.value[i:]
        return True
    return False

def eat_string_constant(src:Ref[str], xml:XML) -> bool:
    if src.value[0] == '"':
        i = 1
        while i < len(src.value) and src.value[i] != '"':
            i += 1
        xml.append(XML("stringConstant", [src.value[1:i]]))
        src.value = src.value[i+1:]
        return True
    return False

def eat_identifier(src:Ref[str], xml:XML) -> bool:
    if src.value[0].isalpha() or src.value[0] == "_":
        i = 1
        while i < len(src.value) and (src.value[i].isalnum() or src.value[i] == "_"):
            i += 1
        
        if src.value[:i] in keywords: return False # keywords are not identifiers
        
        xml.append(XML("identifier", [src.value[:i]]))
        src.value = src.value[i:]
        return True
    return False

def eat_whitespace(src:Ref[str]) -> bool:
    if src.value[0].isspace():
        i = 1
        while i < len(src.value) and src.value[i].isspace():
            i += 1
        src.value = src.value[i:]
        return True
    return False


def eat_comments(src:Ref[str]) -> bool:
    if src.value.startswith("//"):
        i = 2
        while i < len(src.value) and src.value[i] != "\n":
            i += 1
        src.value = src.value[i:]
        return True
    if src.value.startswith("/*"):
        i = 2
        while  i < len(src.value) and not src.value[i:].startswith("*/"):
            i += 1
        assert src.value[i:].startswith("*/"), "Unclosed comment"
        src.value = src.value[i+2:]
        return True
    return False

