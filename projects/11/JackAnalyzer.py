from pathlib import Path
from argparse import ArgumentParser
import subprocess

from JackTokenizer import tokenize
from CompilationEngine import compile

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




################## Testing helper functions ##################

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
            chop_length = 2 if file_path.stem.endswith("TTT") else 3 # i.e. compare MainTTT.xml to MainT.xml, and MainPPP.xml to Main.xml
            answer_path = file_path.with_name(file_path.stem[:-chop_length]).with_suffix(".xml")
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
        print(res.stdout.decode())
        print(res.stderr.decode())





if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to a .jack file or directory")
    parser.add_argument("--compare", action="store_true", help="Test a <file>TTT.xml against <file>T.xml using TextComparer.sh")
    args = parser.parse_args()
    
    if args.compare:
        compare(args.path)
    else:
        main(args.path)