from typing import List
import duckdb
from pathlib import Path
import subprocess

from models.relation import Relation
from database.database import get_db
import os

os.mkdir("./notes")
PATH = Path("./notes")

con = get_db()


def open_editor():
    global PATH
    return subprocess.run(["nvim", PATH / "temp"])


def write_note(data: Relation, con=con):
    """
    Open a editor window
    write Note to database
    """
    result = open_editor()

    with open(PATH / data.name, "+r") as content:
        update_note(con, data.id, content.read())
    (PATH / data.name).unlink()
    if result.returncode == 0:
        print("file written")


def create_table(con):
    """Create Table in DB"""
    con.sql("""
    CREATE SEQUENCE IF NOT EXISTS id_sequence START 1;
    CREATE TABLE IF NOT EXISTS Notes (
            id INTEGER DEFAULT nextval('id_sequence'),
            name TEXT,
            note TEXT,
            done BOOLEAN
        );
    """)


def add_item(con, name: str, note: str):
    """add a new idtem to database"""
    con.sql(
        """
        INSERT INTO Notes (name, note, done)
        VALUES (?, ?, FALSE)
    """,
        (name, note),
    )


def update_name(con, id: int, name: str):
    """Update name by id in database"""
    con.sql(
        """
            UPDATE Notes SET name=? WHERE id=?
            """,
        (name, id),
    )


def update_note(con, id: int, note: str):
    """Update note content by id"""
    con.sql(
        "UPDATE Notes SET note=? WHERE id=?",
        params=(
            note,
            id,
        ),
    )


def toggle_done(con, id: int):
    """toggle if note/todo is done"""
    con.sql(query="UPDATE Notes SET done = NOT done WHERE id=?", params=(id,))


def filter(con, done: bool):
    """Filter notes by done or not done"""
    return con.sql("SELECT * FROM Notes WHERE done=?", params=(done,))


def get_all():
    """get all notes"""
    return con.sql("SELECT * FROM Notes")


def get_by_id(con: duckdb.DuckDBPyConnection, id: int):
    """get a note by id"""
    return con.sql("SELECT * FROM Notes WHERE id=?", params=(id,))


def parse_one(relation: duckdb.DuckDBPyRelation) -> Relation:
    """get a reletion class for the db return object"""
    all_data = relation.fetchall()
    if len(all_data) == 1:
        data = all_data[0]
        return Relation(id=data[0], name=data[1], note=data[2], done=data[3])
    else:
        raise Exception("No output for parsing")


def parse_all(relations: List[duckdb.DuckDBPyRelation]) -> List[Relation]:
    """parse list of db returns"""
    return [parse_one(relation) for relation in relations]


create_table(con)
print(get_all())


write_note(data=parse_one(get_by_id(6)))
print(get_all())
