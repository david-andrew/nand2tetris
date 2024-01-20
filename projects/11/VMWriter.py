from typing import Literal


class VMWriter(list[str]):
    def write_push(self, segment: Literal['CONST', 'ARG', 'LOCAL', 'STATIC', 'THIS', 'THAT', 'POINTER', 'TEMP'], index: int) -> None:
        self.append(f"push {segment} {index}")

    def write_pop(self, segment: Literal['CONST', 'ARG', 'LOCAL', 'STATIC', 'THIS', 'THAT', 'POINTER', 'TEMP'], index: int) -> None:
        self.append(f"pop {segment} {index}")

    def write_arithmetic(self, command: Literal['ADD', 'SUB', 'NEG', 'EQ', 'GT', 'LT', 'AND', 'OR', 'NOT']) -> None:
        self.append(command)

    def write_label(self, label: str) -> None:
        self.append(f"label {label}")

    def write_goto(self, label: str) -> None:
        self.append(f"goto {label}")

    def write_if(self, label: str) -> None:
        self.append(f"if-goto {label}")

    def write_call(self, name: str, nArgs: int) -> None:
        self.append(f"call {name} {nArgs}")

    def write_function(self, name: str, nLocals: int) -> None:
        self.append(f"function {name} {nLocals}")

    def write_return(self) -> None:
        self.append("return")

    def __str__(self) -> str:
        return "\n".join(self)
