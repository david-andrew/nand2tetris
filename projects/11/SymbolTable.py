from dataclasses import dataclass
from typing import Literal
##
import pdb


@dataclass
class Symbol:
    # name: str # key in the symbol table
    type: str
    kind: Literal['static', 'field', 'argument', 'local']
    index: int


class SymbolTable(dict[str, Symbol]):
    def insert(self, name: str, type: str, kind: str) -> None:
        self[name] = Symbol(type, kind, self.var_count(kind))

    def var_count(self, kind: str) -> int:
        return len([symbol for symbol in self.values() if symbol.kind == kind])

    def __str__(self) -> str:
        """nice table printout"""
        name_width = max([*(len(name) for name in self.keys()), len("name")])
        type_width = max([*(len(symbol.type) for symbol in self.values()), len("type")])
        kind_width = max([*(len(symbol.kind) for symbol in self.values()), len("kind")])
        index_width = max([*(len(str(symbol.index)) for symbol in self.values()), len("#")])

        header = f"{'name':<{name_width}} │ {'type':<{type_width}} │ {'kind':<{kind_width}} │ {'#':<{index_width}}"
        lines = [header]
        lines.append(f"{'─' * name_width}─┼─{'─' * type_width}─┼─{'─' * kind_width}─┼─{'─' * index_width}─")
        for name, symbol in self.items():
            lines.append(f"{name:<{name_width}} │ {symbol.type:<{type_width}} │ {
                         symbol.kind:<{kind_width}} │ {symbol.index:<{index_width}}")
        return "\n".join(lines)
