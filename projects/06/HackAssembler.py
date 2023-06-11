def assemble(path: str):
    """assembles a .asm file into a .hack file. For input file is xxx.asm, output file will be xxx.hack"""

    assert path.endswith('.asm'), 'Input file must be a .asm file'
    
    # read the raw source code
    with open(path, 'r') as f:
        src = f.read()

    # split the source code into lines
    lines = src.splitlines()

    # remove whitespace and comments
    lines = remove_all_whitespace(lines)
    
    # initialize the symbol table
    symbols = generate_symbol_table(lines)

    # remove the labels from the code
    lines = [line for line in lines if not line.startswith('(')]

    # convert each line to its binary representation
    lines = [binarize_line(line, symbols) for line in lines]

    # write the binary code to a .hack file
    out_path = path.replace('.asm', '.hack')
    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f'wrote to {out_path}')
    

def remove_all_whitespace(lines: list[str]) -> list[str]:
    """removes whitespace and comments from a list of raw assembly code lines"""
    lines = [remove_line_whitespace(line) for line in lines]
    lines = [line for line in lines if line]
    return lines

def remove_line_whitespace(line: str) -> str:
    """removes whitespace and comments from a line of assembly code"""

    #remove comments
    if '//' in line:
        line, comment = line.split('//', maxsplit=1)
    
    #remove any remaining whitespace in the line
    line = line.replace(' ', '') .strip()

    return line


def generate_symbol_table(lines: list[str]) -> dict[str, int]:
    """
    generates a symbol table from a list of assembly code lines
    assumes all whitespace and comments have been removed
    """

    #default symbol table values
    symbols = {
        'SP': 0,
        'LCL': 1,
        'ARG': 2,
        'THIS': 3,
        'THAT': 4,
        **{f'R{i}': i for i in range(0, 16)},
        'SCREEN': 16384,
        'KBD': 24576,
    }

    #add the labels to the symbol table
    i = 0
    for line in lines:
        if line.startswith('(') and line.endswith(')'):
            symbols[line[1:-1]] = i
        else:
            i += 1

    #add the variables to the symbol table
    address = 16
    for i, line in enumerate(lines):
        if line.startswith('@') and not line[1:].isdigit() and line[1:] not in symbols:
            symbols[line[1:]] = address
            address += 1

    # print(f'symbols: {symbols}')
    
    return symbols


def binarize_line(line: str, symbols: dict[str, int]) -> str:
    """converts a line of assembly code to its binary representation"""
    if line.startswith('@'):
        return binarize_a_instruction(line, symbols)
    else:
        return binarize_c_instruction(line)
    
def binarize_a_instruction(line: str, symbols: dict[str, int]) -> str:
    """converts an A-instruction to its binary representation"""
    if line[1:].isdigit():
        return f'0{int(line[1:]):015b}'
    else:
        return f'0{symbols[line[1:]]:015b}'
    
COMP = {
      '0': '0101010',
      '1': '0111111',
     '-1': '0111010',
      'D': '0001100',
      'A': '0110000',   'M': '1110000',
     '!D': '0001101',
     '!A': '0110001',  '!M': '1110001',
     '-D': '0001111',
     '-A': '0110011',  '-M': '1110011',
    'D+1': '0011111',
    'A+1': '0110111', 'M+1': '1110111',
    'D-1': '0001110',
    'A-1': '0110010', 'M-1': '1110010',
    'D+A': '0000010', 'D+M': '1000010',
    'D-A': '0010011', 'D-M': '1010011',
    'A-D': '0000111', 'M-D': '1000111',
    'D&A': '0000000', 'D&M': '1000000',
    'D|A': '0010101', 'D|M': '1010101',
}

DEST = {
    'null': '000',
    'M':    '001',
    'D':    '010',
    'MD':   '011',
    'A':    '100',
    'AM':   '101',
    'AD':   '110',
    'AMD':  '111',
}

JUMP = {
    'null': '000',
    'JGT':  '001',
    'JEQ':  '010',
    'JGE':  '011',
    'JLT':  '100',
    'JNE':  '101',
    'JLE':  '110',
    'JMP':  '111',
}

def binarize_c_instruction(line: str) -> str:
    """converts a C-instruction to its binary representation"""
    if '=' in line:
        dest, comp = line.split('=')
    else:
        dest = 'null'
        comp = line
    if ';' in comp:
        comp, jump = comp.split(';')
    else:
        jump = 'null'
    return f'111{COMP[comp]}{DEST[dest]}{JUMP[jump]}'


if __name__ == '__main__':
    import sys
    assert len(sys.argv) == 2, 'Usage: python HackAssembler.py <input file>'
    assemble(sys.argv[1])