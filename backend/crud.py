from typing import List
from pathlib import Path
import subprocess
from models import Relation
from database import get_db
import tempfile

PATH = Path("./notes")


def open_editor(path: str):
    global PATH
    return subprocess.run(["vi", path])


def write_note(data: Relation):
    """
    Open a editor window
    write Note to database
    """
    print(data.note)

    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
        tf.write(data.note)
        tf.flush()
        temp_path = tf.name
    with open(temp_path, "r") as f:
        result = open_editor(temp_path)
        update_note(data.id, f.read())

    if result.returncode == 0:
        pass
    # print("file written")


def create_table():
    """Create Table in DB"""
    with get_db() as con:
        con.sql("""
        CREATE SEQUENCE IF NOT EXISTS id_sequence START 1;
        CREATE TABLE IF NOT EXISTS Notes (
            id INTEGER DEFAULT nextval('id_sequence'),
            name TEXT,
            note TEXT,
            done BOOLEAN
            );
        """)


def add_item(name: str, note: str):
    """add a new idtem to database"""
    with get_db() as con:
        con.sql(
            """
            INSERT INTO Notes (name, note, done)
            VALUES (?, ?, FALSE)
            """,
            params=(name, note),
        )


def update_name(id: int, name: str, con=get_db()):
    """Update name by id in database"""
    with get_db() as con:
        con.sql(
            "UPDATE Notes SET name=? WHERE id=?",
            params=(name, id),
        )


def update_note(id: int, note: str):
    """Update note content by id"""
    with get_db() as con:
        con.sql(
            "UPDATE Notes SET note=? WHERE id=?",
            params=(
                note,
                id,
            ),
        )


def toggle_done(id: int):
    """toggle if note/todo is done"""
    with get_db() as con:
        con.sql(query="UPDATE Notes SET done = NOT done WHERE id=?", params=(id,))


def filter(done: bool) -> List[tuple]:
    """Filter notes by done or not done"""
    with get_db() as con:
        result = con.sql("SELECT * FROM Notes WHERE done=?", params=(done,)).fetchall()
    return result


def get_all() -> List[tuple]:
    """get all notes"""
    with get_db() as con:
        result = con.sql("SELECT * FROM Notes").fetchall()
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


def main():
    create_table()
    print(get_all())

    write_note(data=parse_all(get_by_id(id=6))[0])
    print(parse_all(get_all()))
