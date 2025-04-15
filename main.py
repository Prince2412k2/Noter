from __future__ import annotations
import curses


def c_main(stdscr: curses._CursesWindow) -> int:
    stdscr.clear()
    stdscr.addstr(0, 0, "hello world")
    stdscr.refresh()

    # Wait for a key press

    stdscr.getch()
    return 0


# def main() -> int:
#    return curses.wrapper(c_main)


if __name__ == "__main__":
    from backend.crud import main

    main()
