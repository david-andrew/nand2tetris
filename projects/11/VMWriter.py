

class VMWriter(list[str]):
    def __str__(self) -> str:
        return "\n".join(self)