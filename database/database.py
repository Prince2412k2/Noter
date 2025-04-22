# def get_db() -> duckdb.DuckDBPyConnection:
# return duckdb.connect("./database/duck.db")

import duckdb
from contextlib import contextmanager
from typing import Generator


@contextmanager
def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    con = duckdb.connect("./database/duck.db")
    try:
        yield con
    finally:
        con.close()
