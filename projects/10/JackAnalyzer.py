from pathlib import Path
import sys
from dataclasses import dataclass
from argparse import ArgumentParser

import pdb





"""
import xml.etree.ElementTree as ET

# Create the root element
tokens = ET.Element("tokens")

# Define a list of tuples with tag and text
elements = [
    ("keyword", "if"),
    ("symbol", "("),
    ("identifier", "x"),
    ("symbol", "&lt;"),
    ("integerConstant", "0"),
    ("symbol", ")"),
    ("symbol", "{"),
    ("keyword", "let"),
    ("identifier", "sign"),
    ("symbol", "="),
    ("stringConstant", "negative"),
    ("symbol", ";"),
    ("symbol", "}")
]

# Iterate over the tuples and add them as children to the root element
for tag, text in elements:
    child = ET.SubElement(tokens, tag)
    child.text = text

# Convert the XML structure to a string and write it to a file
tree = ET.ElementTree(tokens)
tree.write('tokens.xml', encoding='utf-8', xml_declaration=True)
"""


keywords = {
    "class",
    "constructor",
    "function",
    "method",
    "field",
    "static",
    "var",
    "int",
    "char",
    "boolean",
    "void",
    "true",
    "false",
    "null",
    "this",
    "let",
    "do",
    "if",
    "else",
    "while",
    "return"
}

symbols = {*"{}()[].,;+-*/&|<>=~"}

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
    token_path = file_path.with_suffix("T.xml")
    parse_path = file_path.with_suffix(".xml")
    tokenize(file_path, token_path)
    compile(token_path, parse_path)

def tokenize(inpath:Path, outpath:Path):
    pdb.set_trace()

def compile(inpath:Path, outpath:Path):
    pdb.set_trace()

@dataclass
class XML:
    tag:str
    children:list['XML|str']

    def __str__(self, depth=0):
        tab = "    "

        if len(self.children) == 0:
            return f"{tab*depth}<{self.tag}/>\n"
        elif len(self.children) == 1 and isinstance(self.children[0], str):
            return f"{tab*depth}<{self.tag}> {self.children[0]} </{self.tag}>\n"


        s = f"{tab*depth}<{self.tag}>\n"
        for child in self.children:
            if isinstance(child, str):
                s += tab*(depth+1) + child + "\n"
            else:
                s += child.__str__(depth+1)
        s += f"{tab*depth}</{self.tag}>\n"
        return s

    def __repr__(self):
        s = f'XML(tag="{self.tag}", children=['
        c = [f'"{child}"' if isinstance(child, str) else child.__repr__() for child in self.children]
        s += ", ".join(c)
        s += "])"
        return s

test = XML('tokens', [
    XML("keyword", ["if"]),
    XML("symbol", ["("]),
    XML("identifier", ["x"]),
    XML("symbol", ["&lt;"]),
    XML("integerConstant", ["0"]),
    XML("symbol", [")"]),
    XML("symbol", ["{"]),
    XML("keyword", ["let"]),
    XML("identifier", ["sign"]),
    XML("symbol", ["="]),
    XML("stringConstant", ["negative"]),
    XML("symbol", [";"]),
    XML("symbol", ["}"])
])

# def to_xml()



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to a .jack file or directory")
    args = parser.parse_args()
    
    main(args.path)