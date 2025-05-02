import os

from typing import List
from pathlib import Path
import subprocess
from models import Relation
from database import get_db
import tempfile
import logging

logger = logging.getLogger()
PATH = Path("./notes")


def get_all() -> List[str]:
    """get all notes"""
    return os.listdir(PATH)


def open_editor(path: Path):
    global PATH
    return subprocess.run(["nvim", path])


def write_note(name: str):
    """
    Open a editor window
    write Note to database
    """

    with open(PATH / name, "r") as f:
        result = open_editor(PATH / name)


def create_table():
    """Create Table in DB"""
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    if not get_all():
        with open(PATH / "one.txt", "+w") as file:
            file.write("Welcome")


def add_item(name: str, note: str):
    """add a new idtem to database"""
    with open(PATH / name, "+w") as file:
        file.write(note)


def remove_item(name: str):
    """add a new idtem to database"""
    file = PATH / name
    file.unlink()


def update_name(old_name: str, new_name: str):
    """Update name by id in database"""
    old_path = PATH / old_name
    old_path.rename(PATH / new_name)


def update_note(name: str, note: str):
    """Update note content by id"""
    logger.info(f"[update_note] : {note}")
    with open(PATH / name, "+w") as file:
        file.write(note)


def toggle_done(id: int):
    """toggle if note/todo is done"""
    try:
        with get_db() as con:
            con.sql(query="UPDATE Notes SET done = NOT done WHERE id=?", params=(id,))
    except Exception as e:
        logger.warning(f"[toggle_done] failed for {id=} : {e}")


def filter(done: bool) -> List[tuple]:
    """Filter notes by done or not done"""
    with get_db() as con:
        result = con.sql("SELECT * FROM Notes WHERE done=?", params=(done,)).fetchall()
    return result


def get_by_id(id: int) -> List[tuple]:
    """get a note by id"""
    with get_db() as con:
        result = con.sql("SELECT * FROM Notes WHERE id=?", params=(id,)).fetchall()
    return result


def parse_one(data: tuple) -> Relation:
    """get a reletion class for the db return object"""
    if data:
        return Relation(id=data[0], name=data[1], note=data[2], done=data[3])
    else:
        raise Exception("Cannot parse Empty DB return")


def parse_all(liast_data: List[tuple]) -> List[Relation]:
    """parse list of db returns"""
    return [parse_one(data) for data in liast_data]
