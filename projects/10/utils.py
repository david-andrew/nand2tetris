from dataclasses import dataclass


@dataclass
class Ref[T]:
    value:T


@dataclass
class XML:
    tag:str
    children:list['XML|str']

    def append_child(self, child:'XML|str'): 
        self.children.append(child)
    
    def __str__(self, depth=0):
        tab = "    "

        if len(self.children) == 0:
            return f"{tab*depth}<{self.tag}>\n{tab*depth}</{self.tag}>\n"
        elif len(self.children) == 1 and isinstance(self.children[0], str):
            return f"{tab*depth}<{self.tag}> {XML.escape(self.children[0])} </{self.tag}>\n"

        s = f"{tab*depth}<{self.tag}>\n"
        for child in self.children:
            if isinstance(child, str):
                s += tab*(depth+1) + XML.escape(child) + "\n"
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
    
    @staticmethod
    def escape(s:str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    @staticmethod
    def unescape(s:str) -> str:
        return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    
    @staticmethod
    def from_string(src:str) -> 'XML':
        
        def eat_whitespace(src:Ref[str]) -> str|None:
            i = 0
            while i < len(src.value) and src.value[i].isspace():
                i += 1
            if i == 0: return None
            whitespace, src.value = src.value[:i], src.value[i:]
            return whitespace
        
        def eat_opening_tag(src:Ref[str]) -> str|None:
            if src.value[0] != "<": return None
            i = 1
            while i < len(src.value) and src.value[i] != ">":
                i += 1
            assert i < len(src.value), f"Unclosed tag {src.value}"
            tag, src.value = src.value[1:i], src.value[i+1:]
            return tag
        
        def eat_closing_tag(src:Ref[str], tag:str) -> str|None:
            if src.value[:2] != "</": return None
            i = 2
            while i < len(src.value) and src.value[i] != ">":
                i += 1
            assert i < len(src.value), f"Unclosed tag {src.value}"
            assert src.value[2:i] == tag, "Mismatched tags"
            tag, src.value = src.value[2:i], src.value[i+1:]
            return tag
    
        def eat_text(src:Ref[str]) -> str | None:
            i = 0
            while i < len(src.value) and src.value[i] != "<":
                i += 1
            if i == 0: return None
            text, src.value = src.value[:i], src.value[i:]
            return XML.unescape(text.strip())
        
        stack: list[XML] = []
        src: Ref[str] = Ref(src.strip())
        root_tag = eat_opening_tag(src)
        assert root_tag is not None, "No root tag"
        root = XML(root_tag, [])
        stack.append(root)

        while src.value:
            if eat_whitespace(src) is not None: continue
            
            if eat_closing_tag(src, stack[-1].tag) is not None:
                stack.pop()
                continue

            if (tag := eat_opening_tag(src)) is not None:
                xml = XML(tag, [])
                stack[-1].append_child(xml)
                stack.append(xml)
                continue
            
            if (text := eat_text(src)) is not None:
                stack[-1].append_child(text)
                continue

            assert False, f"Invalid XML: {src.value}"

        assert len(stack) == 0, f"Unclosed tags on stack {[xml.tag for xml in stack]}"

        return root








def main():
    from pathlib import Path
    import pdb
    test = Path("ArrayTest/Main.xml").read_text()
    test = XML.from_string(test)

    pdb.set_trace()


    test = XML('tokens', [
        XML("keyword", ["if"]),
        XML("symbol", ["("]),
        XML("identifier", ["x"]),
        XML("symbol", ["<"]),
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