import sys
from pathlib import Path
from typing import Literal


# global reference to the input filename
filepath: Path = None

def main():
    """main entrypoint for the vm translator"""

    # read in the filename and save it as a global variable
    global filepath
    assert len(sys.argv) == 2, "Usage: python vm.py <filename.vm>"
    filepath = Path(sys.argv[1])
    assert filepath.exists(), f"Invalid filename: \"{filepath}\". File does not exist"
    assert filepath.suffix == '.vm', f"Invalid filename: \"{filepath}\". Expected a .vm file"

    # read in the lines of the program
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # filter out whitespace and comments
    vm_lines = filter_whitespace(lines)

    # translate the program into assembly
    asm_lines = []
    for line in vm_lines:
        asm_lines.extend([f'// {line}', *translate(line), ''])

    # write the program to the output file
    with open(filepath.with_suffix('.asm'), 'w') as f:
        f.write('\n'.join(asm_lines))


def filter_whitespace(lines:list[str]) -> list[str]:
    """filter out whitespace and comments from the vm program"""
    prog_lines = []

    for line in lines:
        # remove leading/trailing whitespace
        line = line.strip()

        # skip empty lines and comments
        if line == '' or line.startswith('//'):
            continue

        # split code from any trailing comments
        line = line.split('//')[0].strip()

        # add to list of program lines
        prog_lines.append(line)

    return prog_lines


def translate(line:str) -> list[str]:
    """translate a vm line into one or more asm lines"""

    if line.startswith('push'):
        return push(line)
    elif line.startswith('pop'):
        return pop(line)
    elif line == 'add':
        return add()
    elif line == 'sub':
        return sub()
    elif line == 'neg':
        return neg()
    elif line == 'eq':
        return eq()
    elif line == 'gt':
        return gt()
    elif line == 'lt':
        return lt()
    elif line == 'and':
        return and_()
    elif line == 'or':
        return or_()
    elif line == 'not':
        return not_()
    else:
        raise ValueError(f"Invalid vm command: \"{line}\"")


def push(line:str) -> list[str]:
    """translate a push command into one or more asm lines"""

    # verify the command starts with push and has a segment and index
    assert line.startswith('push'), f"Invalid push command: \"{line}\". expected `push <segment> <index>`"

    # separate out the segment/index and convert index to int
    _, segment, index = line.split()
    index = int(index)

    # handle the constant segment
    if segment == 'constant':
        return push_constant(index)
    elif segment == 'local':
        return push_variable('LCL', index)
    elif segment == 'argument':
        return push_variable('ARG', index)
    elif segment == 'this':
        return push_variable('THIS', index)
    elif segment == 'that':
        return push_variable('THAT', index)
    elif segment == 'temp':
        assert index in range(8), f"Invalid push command: \"{line}\". Temp index must be in range 0-7"
        return [
            f'@{5+index}',
            'D=M',
            *push_D(),
        ]
    elif segment == 'static':
        return [
            f'@{filepath.stem}.{index}',
            'D=M',
            *push_D(),
        ]
    elif segment == 'pointer':
        assert index in (0, 1), f"Invalid push command: \"{line}\". Pointer index must be 0 or 1"
        return [
            f'@{3+index}',
            'D=M',
            *push_D(),
        ]
    else:
        raise ValueError(f"Invalid push command: \"{line}\". Unknown segment: \"{segment}\"")



def pop(line:str) -> list[str]:
    """translate a pop command into one or more asm lines"""

    # verify the command starts with pop and has a segment and index
    assert line.startswith('pop'), f"Invalid pop command: \"{line}\". expected `pop <segment> <index>`"

    # separate out the segment/index and convert index to int
    _, segment, index = line.split()
    index = int(index)

    assert segment != 'constant', f"Invalid pop command: \"{line}\". Cannot pop to constant segment"

    if segment == 'local':
        return pop_variable('LCL', index)
    elif segment == 'argument':
        return pop_variable('ARG', index)
    elif segment == 'this':
        return pop_variable('THIS', index)
    elif segment == 'that':
        return pop_variable('THAT', index)
    elif segment == 'temp':
        assert index in range(8), f"Invalid pop command: \"{line}\". Temp index must be in range 0-7"
        return [
            *pop_D(),
            f'@{5+index}',
            'M=D',
        ]
    elif segment == 'static':
        return [
            *pop_D(),
            f'@{filepath.stem}.{index}',
            'M=D',
        ]
    elif segment == 'pointer':
        assert index in (0, 1), f"Invalid pop command: \"{line}\". Pointer index must be 0 or 1"
        return [
            *pop_D(),
            f'@{3+index}',
            'M=D',
        ]
    else:
        raise ValueError(f"Invalid pop command: \"{line}\". Unknown segment: \"{segment}\"")



def push_D() -> list[str]:
    """push the value in D to the stack"""
    return [
        '@SP',
        'A=M',
        'M=D',
        '@SP',
        'M=M+1',
    ]

def pop_D() -> list[str]:
    """pop the value from the stack into D"""
    return [
        '@SP',
        'M=M-1',
        'A=M',
        'D=M',
    ]

def push_constant(index:int) -> list[str]:
    """push the given constant value to the stack"""
    return [
        f'@{index}',
        'D=A',
        *push_D(),
    ]

def push_variable(varname:str, offset:int) -> list[str]:
    """push the value of the given variable + (optional) offset to the stack"""
    return [
        f'@{varname}',
        'D=M',
        f'@{offset}',
        'A=D+A',
        'D=M',
        *push_D(),
    ]

def pop_variable(varname:str, offset:int=0) -> list[str]:
    """pop the top value from the stack into the given variable + (optional) offset"""
    return [
        f'@{varname}',
        'D=M',
        f'@{offset}',
        'D=D+A',
        '@R13', # stash the address in R13 since D will be overwritten
        'M=D',
        *pop_D(),
        '@R13',
        'A=M',
        'M=D',
    ]

def add() -> list[str]:
    """add the top two values on the stack"""
    return [
        *pop_D(),
        'A=A-1',
        'M=M+D',
    ]

def sub() -> list[str]:
    """subtract the top two values on the stack"""
    return [
        *pop_D(),
        'A=A-1',
        'M=M-D',
    ]

def neg() -> list[str]:
    """negate the top value on the stack"""
    return [
        '@SP',
        'A=M-1',
        'M=-M',
    ]

_counter = 0
def compare(op:Literal['LT', 'GT', 'EQ']) -> list[str]:
    """compare the top two values on the stack according to the given operator (LT, GT, EQ). 0 if false, -1 if true"""
    global _counter
    _counter += 1
    return [
        *pop_D(),
        'A=A-1',
        'D=M-D',
        f'@{op}_{_counter}',
        f'D;J{op}',
        '@SP',
        'A=M-1',
        'M=0',
        f'@END_{_counter}',
        '0;JMP',
        f'({op}_{_counter})',
        '@SP',
        'A=M-1',
        'M=-1',
        f'(END_{_counter})',
    ]

def eq() -> list[str]:
    """compare the top two values on the stack for equality. 0 if false, -1 if true"""
    return compare('EQ')

def gt() -> list[str]:
    """compare the top two values on the stack for greater than. 0 if false, -1 if true"""
    return compare('GT')

def lt() -> list[str]:
    """compare the top two values on the stack for less than. 0 if false, -1 if true"""
    return compare('LT')

def and_() -> list[str]:
    """bitwise and the top two values on the stack"""
    return [
        *pop_D(),
        'A=A-1',
        'M=M&D',
    ]

def or_() -> list[str]:
    """bitwise or the top two values on the stack"""
    return [
        *pop_D(),
        'A=A-1',
        'M=M|D',
    ]

def not_() -> list[str]:
    """bitwise not the top value on the stack"""
    return [
        '@SP',
        'A=M-1',
        'M=!M',
    ]



if __name__ == '__main__':
    main()