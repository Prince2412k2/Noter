import curses
from frontend.curse import main
import logging
from backend import create_table

logging.basicConfig(filename="debug.log", level=logging.INFO)

if __name__ == "__main__":
    create_table()
    curses.wrapper(main)
