from dataclasses import dataclass


@dataclass
class Ref[T]:
    value:T


@dataclass
class XML:
    tag:str
    children:list['XML|str']

    def append(self, child:'XML|str'):
        self.children.append(child)
    
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

def main():
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

    print(test)


if __name__ == "__main__":
    main()