import sys
from pathlib import Path
from typing import Literal



# hidden global variables. Access via functions
_function_name: str = None    # name of the current function being translated
_counter = 0                 # counter for generating unique labels

def get_current_function_name() -> str:
    """return the name of the current function"""
    if _function_name is not None:
        return _function_name
    else:
        return 'global'

def set_current_function_name(name: str):
    """set the name of the current function"""
    global _function_name
    _function_name = name

def get_next_counter() -> int:
    """return the next value of the counter"""
    global _counter
    _counter += 1
    return _counter

def main():
    """main entrypoint for the vm translator"""

    # get the file or list of files to translate and the output asm filepath
    assert len(sys.argv) == 2, "Usage: python vm.py <filename.vm> or <directory>"
    filepath = Path(sys.argv[1])
    assert filepath.exists(), f"Invalid path: \"{filepath}\" does not exist"
    
    
    if filepath.is_dir():
        files = [*filepath.glob('*.vm')] # get all .vm files in the directory
        outpath = filepath / f'{filepath.name}.asm'
        INCLUDE_BOOTSTRAP = True # for directory programs, don't skip the bootstrap code
    else:
        files = [filepath]
        outpath = filepath.with_suffix('.asm')
        INCLUDE_BOOTSTRAP = False # for single file programs, skip the bootstrap code


    # array to save the translated asm lines
    asm_lines = []



    # add the bootstrap code to the beginning of the program
    if INCLUDE_BOOTSTRAP:
        asm_lines.extend(['// bootstrap code', *bootstrap(), ''])


    # translate each vm file and insert into the output asm file
    for file in files:
        # save the base filename for use in generating unique labels
        global basename
        basename = file.stem

        # read in the lines of the program
        with open(file, 'r') as f:
            lines = f.readlines()

        # filter out whitespace and comments
        vm_lines = filter_whitespace(lines)

        # translate the file into assembly
        for line in vm_lines:
            asm_lines.extend([f'// {line}', *translate(line), ''])


    # write the final program to the output file
    with open(outpath, 'w') as f:
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
    elif line.startswith('label'):
        return label(line)
    elif line.startswith('goto'):
        return goto(line)
    elif line.startswith('if-goto'):
        return if_goto(line)
    elif line.startswith('function'):
        return function_(line)
    elif line.startswith('call'):
        return call(line)
    elif line == 'return':
        return return_()
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


def bootstrap() -> list[str]:
    """bootstrap code to initialize the vm"""

    return [
        '//set SP=256',
        '@256',
        'D=A',
        '@SP',
        'M=D',
        
        '// For easier debugging: set pointers to known illegal values: LCL=-4242, ARG=-4243, THIS=-4244, THAT=-4245',
        '@4242',
        'D=A',
        '@LCL',
        'M=0',
        'M=M-D',
        '@4243',
        'D=A',
        '@ARG',
        'M=0',
        'M=M-D',
        '@4244',
        'D=A',
        '@THIS',
        'M=0',
        'M=M-D',
        '@4245',
        'D=A',
        '@THAT',
        'M=0',
        'M=M-D',

        '//call Sys.init',
        *call('call Sys.init 0')
    ]

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
        return push_from_variable('LCL', index)
    elif segment == 'argument':
        return push_from_variable('ARG', index)
    elif segment == 'this':
        return push_from_variable('THIS', index)
    elif segment == 'that':
        return push_from_variable('THAT', index)
    elif segment == 'temp':
        assert index in range(8), f"Invalid push command: \"{line}\". Temp index must be in range 0-7"
        return [
            f'@{5+index}',
            'D=M',
            *push_D(),
        ]
    elif segment == 'static':
        return [
            f'@{basename}.{index}',
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
        return pop_to_variable('LCL', index)
    elif segment == 'argument':
        return pop_to_variable('ARG', index)
    elif segment == 'this':
        return pop_to_variable('THIS', index)
    elif segment == 'that':
        return pop_to_variable('THAT', index)
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
            f'@{basename}.{index}',
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

def push_constant(value:int) -> list[str]:
    """push the given constant value to the stack"""
    return [
        f'@{value}',
        'D=A',
        *push_D(),
    ]

def push_from_variable(varname:str, offset:int=0) -> list[str]:
    """push the value of the given variable + (optional) offset to the stack"""
    return [
        f'@{varname}',
        'D=M',
        f'@{offset}',
        'A=D+A',
        'D=M',
        *push_D(),
    ]

def pop_to_variable(varname:str, offset:int=0) -> list[str]:
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

def push_named_variable(varname:Literal['SP', 'LCL', 'ARG', 'THIS', 'THAT']) -> list[str]:
    """push the current value of the given variable to the stack"""
    return [
        f'@{varname}',
        'D=M',
        *push_D(),
    ]

def pop_named_variable(varname:Literal['SP', 'LCL', 'ARG', 'THIS', 'THAT']) -> list[str]:
    """pop the top value from the stack into the address of the given variable"""
    return [
        *pop_D(),
        f'@{varname}',
        'M=D',
    ]



def label(line:str) -> list[str]:
    """translate a label command into one or more asm lines"""

    # verify the command starts with label and has a labelname
    assert line.startswith('label'), f"Invalid label command: \"{line}\". expected `label <labelname>`"

    # separate out the labelname
    _, label_name = line.split()

    return [
        f'({get_current_function_name()}${label_name})',
    ]

def goto(line:str) -> list[str]:
    """translate a goto command into one or more asm lines"""

    # verify the command starts with goto and has a labelname
    assert line.startswith('goto'), f"Invalid goto command: \"{line}\". expected `goto <labelname>`"

    # separate out the labelname
    _, label_name = line.split()

    return [
        f'@{get_current_function_name()}${label_name}',
        '0;JMP',
    ]

def if_goto(line:str) -> list[str]:
    """translate an if-goto command into one or more asm lines"""

    # verify the command starts with if-goto and has a labelname
    assert line.startswith('if-goto'), f"Invalid if-goto command: \"{line}\". expected `if-goto <labelname>`"

    # separate out the labelname
    _, label_name = line.split()

    return [
        *pop_D(),
        f'@{get_current_function_name()}${label_name}',
        'D;JNE',
    ]

def function_(line:str) -> list[str]:
    """translate a function command into one or more asm lines"""

    # verify the command starts with function and has a function name and local variable count
    assert line.startswith('function'), f"Invalid function command: \"{line}\". expected `function <functionname> <localcount>`"

    # separate out the function name and local variable count
    _, function_name, local_count = line.split()
    local_count = int(local_count)
    
    # save the function name globally for use in label/goto/if-goto commands
    set_current_function_name(function_name)

    # return the asm lines
    return [
        f'({function_name})',
        *(push_constant(0) * local_count),
    ]

def call(line:str) -> list[str]:
    """translate a call command into one or more asm lines"""

    # verify the command starts with call and has a function name and argument count
    assert line.startswith('call'), f"Invalid call command: \"{line}\". expected `call <functionname> <argcount>`"

    # separate out the function name and argument count
    _, function_name, arg_count = line.split()
    arg_count = int(arg_count)

    # generate a unique return address label
    return_address = f'return_{get_next_counter()}'

    # push the return address
    return [
        *push_constant(return_address),
        *push_named_variable('LCL'),
        *push_named_variable('ARG'),
        *push_named_variable('THIS'),
        *push_named_variable('THAT'),
        # ARG = SP - arg_count - 5
        '@SP',
        'D=M',
        f'@{arg_count}',
        'D=D-A',
        '@5',
        'D=D-A',
        '@ARG',
        'M=D',
        # LCL = SP
        '@SP',
        'D=M',
        '@LCL',
        'M=D',
        # goto function
        f'@{function_name}',
        '0;JMP',
        # return address label
        f'({return_address})',
    ]

# def return_() -> list[str]:
#     """translate a return command into one or more asm lines"""

#     return [
#         # save the end frame: endFrame = LCL
#         '@LCL',
#         'D=M',
#         '@endFrame',
#         'M=D',
#         # save the return address: retAddr = *(endFrame - 5)
#         '@5',
#         'D=D-A',
#         'A=D',
#         'D=M',
#         '@retAddr',
#         'M=D',
#         # put the return value at the top of the caller's stack: *ARG = pop()
#         *pop_D(),
#         '@ARG',
#         'A=M',
#         'M=D',
#         # restore SP of the caller: SP = ARG + 1
#         '@ARG',
#         'D=M+1',
#         '@SP',
#         'M=D',
#         # restore THAT of the caller: THAT = *(endFrame - 1)
#         '@endFrame',
#         'D=M-1',
#         'A=D',
#         'D=M',
#         '@THAT',
#         'M=D',
#         # restore THIS of the caller: THIS = *(endFrame - 2)
#         '@endFrame',
#         'D=M',
#         '@2',
#         'D=D-A',
#         'A=D',
#         'D=M',
#         '@THIS',
#         'M=D',
#         # restore ARG of the caller: ARG = *(endFrame - 3)
#         '@endFrame',
#         'D=M',
#         '@3',
#         'D=D-A',
#         'A=D',
#         'D=M',
#         '@ARG',
#         'M=D',
#         # restore LCL of the caller: LCL = *(endFrame - 4)
#         '@endFrame',
#         'D=M',
#         '@4',
#         'D=D-A',
#         'A=D',
#         'D=M',
#         '@LCL',
#         'M=D',
#         # goto return address
#         '@retAddr',
#         'A=M',
#         '0;JMP',
#     ]
# BROKEN: tried to make return_() more compact...
def return_() -> list[str]:
    """translate a return command into one or more asm lines"""

    return [
        # save the return value retVal = pop()
        *pop_D(),
        '@retVal',
        'M=D',

        # save SP of the caller (without the return value): savedSP = ARG
        '@ARG',
        'D=M',
        '@savedSP',
        'M=D',

        # set the stack pointer to LCL so we can pop the saved LCL, ARG, THIS, and THAT
        '@LCL',
        'D=M',
        '@SP',
        'M=D',
       
        *pop_named_variable('THAT'),
        *pop_named_variable('THIS'),
        *pop_named_variable('ARG'),
        *pop_named_variable('LCL'),

        # save the return address: retAddr = pop()
        *pop_D(),
        '@retAddr',
        'M=D',
        
        # restore SP of the caller: SP = savedSP
        '@savedSP',
        'D=M',
        '@SP',
        'M=D',

        # push the return value onto the stack
        '@retVal',
        'D=M',
        *push_D(),

        # goto return address
        '@retAddr',
        'A=M',
        '0;JMP',
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

def compare(op:Literal['LT', 'GT', 'EQ']) -> list[str]:
    """compare the top two values on the stack according to the given operator (LT, GT, EQ). 0 if false, -1 if true"""
    counter = get_next_counter()
    return [
        *pop_D(),
        'A=A-1',
        'D=M-D',
        f'@{op}_{counter}',
        f'D;J{op}',
        '@SP',
        'A=M-1',
        'M=0',
        f'@END_{counter}',
        '0;JMP',
        f'({op}_{counter})',
        '@SP',
        'A=M-1',
        'M=-1',
        f'(END_{counter})',
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