from dataclasses import dataclass


@dataclass
class Relation:
    id: int
    name: str
    note: str
    done: bool
