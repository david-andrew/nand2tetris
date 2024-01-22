from dataclasses import dataclass


@dataclass
class Ref[T]:
    value: T
