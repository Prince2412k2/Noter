import curses
from frontend.curse import main
import logging

logging.basicConfig(filename="debug.log", level=logging.INFO)

if __name__ == "__main__":
    curses.wrapper(main)
