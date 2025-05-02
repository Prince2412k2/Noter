# def get_db() -> duckdb.DuckDBPyConnection:
# return duckdb.connect("./database/duck.db")

from pathlib import Path
from typing import Dict, List


def create_table(db: Db):
    """Create a json file in PATH if doesnt exist"""
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    if not get_all(db):
        with open(PATH / "one.txt", "+w") as file:
            file.write("Welcome")
    if not os.path.exists(PATH / "database" / "data.json"):
        os.makedirs(PATH / "database", exist_ok=True)
        with open(PATH / "database" / "data.json", "wb") as file:
            file.write(orjson.dumps({"one": False}))


class Db:
    path: Path
    file: Dict[str, bool] = field(init=False)

    def __post_init__(self):
        create_table(self)
        with open(self.path, "rb") as file:
            self.file = orjson.loads(file.read())
