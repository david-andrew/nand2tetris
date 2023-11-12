from pathlib import Path
from argparse import ArgumentParser

from utils import Ref, XML

import pdb




def main(path:Path):
    if path.is_dir():
        analyze_dir(path)
    elif path.is_file():
        analyze_file(path)
    else:
        raise Exception(f"Invalid path: {path}")


def analyze_dir(dir_path:Path):
    for file_path in dir_path.iterdir():
        if file_path.suffix == ".jack":
            analyze_file(file_path)


def analyze_file(file_path:Path):
    if file_path.suffix != ".jack":
        raise Exception(f"Invalid file: {file_path}")

    token_path = file_path.with_name(file_path.stem + 'TTT').with_suffix(".xml")
    tokenize(file_path, token_path)

    parse_path = file_path.with_name(file_path.stem + 'PPP').with_suffix(".xml")
    compile(token_path, parse_path)


#### Testing helper functions
import subprocess

def compare(path:Path):
    if path.is_dir():
        compare_dir(path)
    elif path.is_file():
        compare_file(path)
    else:
        raise Exception(f"Invalid path: {path}")

def compare_dir(dir_path:Path):
    done = set()
    for file_path in dir_path.iterdir():
        if file_path.stem.endswith("TTT") or file_path.stem.endswith("PPP"):
            answer_path = file_path.with_name(file_path.stem[:-2]).with_suffix(".xml")
            done.add(file_path)
            compare_file(file_path, answer_path)

def compare_file(test_path:Path, answer_path:Path):
    assert test_path.exists(), f"File does not exist: {test_path}"
    assert answer_path.exists(), f"File does not exist: {answer_path}"

    # run bash ../../tools/TextComparer.sh
    res = subprocess.run(["bash", "../../tools/TextComparer.sh", str(test_path), str(answer_path)], capture_output=True)
    if res.returncode == 0:
        print(f"[Success] comparing {test_path} to {answer_path}")
    else:
        print(f"[Failure] comparing {test_path} to {answer_path}")

#################################### TOKENIZER ####################################

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



#################################### COMPILER ####################################

def compile(inpath:Path, outpath:Path):
    # pdb.set_trace()
    ...
    print('compilation not implemented yet')












if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to a .jack file or directory")
    parser.add_argument("--compare", action="store_true", help="Test a <file>TTT.xml against <file>T.xml using TextComparer.sh")
    args = parser.parse_args()
    
    if args.compare:
        compare(args.path)
    else:
        main(args.path)