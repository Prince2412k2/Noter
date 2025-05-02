import os

from typing import List, Dict, Optional
from pathlib import Path
import subprocess

import logging
from dataclasses import dataclass

import orjson

logger = logging.getLogger()
PATH = Path("./notes")


class Db:
    def __init__(self, path: Path):
        self.path = path
        self.file: Dict[str, bool]
        try:
            with open(self.path / "database" / "data.json", "rb") as file:
                cont = orjson.loads(file.read())
        except Exception as e:
            cont = handle_empty_file()
            logger.warning(f"creating a new file {e}")
        self.file = cont
        create_table()

    def dump(self):
        with open(self.path / "database" / "data.json", "+wb") as file:
            file.write(orjson.dumps(self.file))


@dataclass
class Commit:
    hash: str
    author: str
    email: str
    date: str
    message: str


@dataclass
class Commits:
    commits: List[Commit]
    pointer: int = 0

    def up(self):
        if self.pointer > 0:
            self.pointer -= 1
        return self.commits[self.pointer]

    def down(self):
        if self.pointer < len(self.commits) - 1:
            self.pointer += 1
        return self.commits[self.pointer]

    def get(self):
        if len(self.commits) < 1:
            return None
        return self.commits[self.pointer]


@dataclass
class Relation:
    name: Optional[str]
    note: Optional[str]

    done: bool


def get_all(db: Db) -> List[str]:
    """get all notes"""
    return list(db.file.keys())


def write_note(name: str):
    """
    Open a editor window
    write Note to database
    """
    try:
        subprocess.run(["nvim", PATH / name])
    except Exception as e:
        logger.warning(f"[write_note] nvim failed to load : {e}")


def handle_empty_file() -> Dict[str, bool]:
    with open(PATH / "one", "+w") as file:
        file.write("Welcome")
    return {"one": False}


def create_table():
    """Create a json file in PATH if doesnt exist"""
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    if not os.path.exists(PATH / "database" / "data.json"):
        os.makedirs(PATH / "database", exist_ok=True)
        with open(PATH / "database" / "data.json", "wb") as file:
            file.write(orjson.dumps({"one": False}))


def add_item(name: str, note: str, db: Db) -> Optional[bool]:
    """add a new item to database"""
    if name in db.file:
        return
    db.file[name] = False
    with open(PATH / name, "+w") as file:
        file.write(note)
    db.dump()
    return True


def remove_item(name: str, db: Db) -> Optional[bool]:
    """add a new idtem to database"""
    if name not in db.file:
        return None
    del db.file[name]
    file = PATH / name
    file.unlink()
    db.dump()
    return True


def update_name(old_name: str, new_name: str, db: Db) -> bool:
    """Update name by id in database"""
    if new_name in db.file:
        return False
    db.file[new_name] = db.file[old_name]
    del db.file[old_name]
    old_path = PATH / old_name
    old_path.rename(PATH / new_name)
    db.dump()
    return True


def update_note(name: str, note: str, db: Db) -> Optional[bool]:
    """Update note content by id"""
    if name not in db.file:
        return None

    with open(PATH / name, "+w") as file:
        file.write(note)
    return True


def toggle_done(name: str, db: Db) -> Optional[bool]:
    """toggle if note/todo is done"""
    if name not in db.file:
        return None
    db.file[name] = not (db.file[name])
    db.dump()
    return True


def filter(done: bool, db: Db) -> List[str]:
    """Filter notes by done or not done"""
    if len(db.file) < 1:
        return []
    return [i for i, j in db.file.items() if j == done]


def get_by_id(name: str, db: Db) -> Optional[str]:
    """get a note by id"""
    if name not in db.file:
        return None
    with open(PATH / name, "r") as file:
        content = file.read()
    return content


def parse_one(name: Optional[str], content: Optional[str], done: bool) -> Relation:
    """get a reletion class for the db return object"""
    return Relation(name=name, note=content, done=done)


def parse_all(db: Db) -> List[Relation]:
    """parse list of db returns"""
    return [parse_one(k, get_by_id(k, db), v) for k, v in db.file.items()]


def main():
    db = Db(PATH / "database" / "data.json")
    print(get_all(db))


if __name__ == "__main__":
    main()
