from typing import List
from backend import (
    get_all,
    parse_all,
    toggle_done,
    write_note,
    remove_item,
    add_item,
    update_name,
)
from models import Relation
import curses
import logging
import os

logger = logging.getLogger()


class Pointer:
    def __init__(self, max: int) -> None:
        self.selected: int = 0
        self.string: str = ">"
        self.max: int = max
        self.done: str = "[•]"
        self.not_done: str = "[ ]"

    def up(self):
        if self.selected > 0:
            self.selected -= 1
        else:
            self.selected = self.max

    def down(self):
        if self.selected < self.max:
            self.selected += 1
        else:
            self.selected = 0


class Notes_list:
    def __init__(self) -> None:
        self.items: List[Relation] = parse_all(get_all())
        self.pointer: Pointer = Pointer(len(self.items) - 1)

    def print_items(self, stdscr):
        logger.info(self.pointer.selected)
        for idx, i in enumerate(self.items):
            point = " "
            if idx == self.pointer.selected:
                point = self.pointer.string
            if i.done:
                status = self.pointer.done
            else:
                status = self.pointer.not_done
            stdscr.addstr(idx, 0, f"{point}{status} {i.name}")

    def check(self, key):
        if key == curses.KEY_UP:
            self.pointer.up()
        elif key == curses.KEY_DOWN:
            self.pointer.down()

    def update(self, stdscr, key):
        if key == ord("a"):
            pos_y = self.pointer.max + 1
            name = input_box(stdscr, notes=self, pos_y=pos_y, prompt=">[n] ")
            if not name:
                return
            add_item(name=name, note="Welcome")
            stdscr.clear()
            self.refresh()
            return
        if not self.items:
            return
        if key == ord(" "):
            id = self.items[self.pointer.selected].id
            toggle_done(id)
        if key in (curses.KEY_ENTER, 10, 13):
            relation = self.items[self.pointer.selected]
            curses.endwin()
            write_note(data=relation)
            curses.doupdate()
        if key == ord("d"):
            id = self.items[self.pointer.selected].id
            remove_item(id)
            if self.pointer.selected == self.pointer.max:
                self.pointer.selected -= 1
            stdscr.clear()
        if key == ord("e"):
            pos_y = self.pointer.selected
            item = self.items[pos_y]
            name = input_box(
                stdscr, notes=self, pos_y=pos_y, prefill=item.name, prompt=">[e] "
            )
            if not name:
                return
            update_name(id=item.id, name=name)
            stdscr.clear()
            self.refresh()

        self.refresh()

    def refresh(self):
        self.items = parse_all(get_all())
        self.pointer.max = len(self.items) - 1


def input_box(
    stdscr, notes: Notes_list, pos_y: int, prompt: str = ">[ ] ", prefill: str = ""
):
    if not prefill:
        notes.pointer.selected = notes.pointer.max + 1

    logger.info(f"Position of line is {pos_y=}")
    curses.curs_set(1)

    input_win = curses.newwin(1, curses.COLS - len(prompt), pos_y, len(prompt))
    input_win.keypad(True)
    buffer = list(prefill)
    cursor_pos = len(prefill)

    stdscr.addstr(pos_y, 0, prompt)
    stdscr.refresh()
    while True:
        input_win.erase()
        input_win.addstr("".join(buffer))
        input_win.move(0, cursor_pos)
        input_win.refresh()

        key = input_win.getch()
        if key in (curses.KEY_ENTER, 10, 13):  # Enter key
            break
        elif key in (curses.KEY_BACKSPACE, 127):
            if cursor_pos > 0:
                cursor_pos -= 1
                buffer.pop(cursor_pos)
        elif key == curses.KEY_LEFT:
            if cursor_pos > 0:
                cursor_pos -= 1
        elif key == curses.KEY_RIGHT:
            if cursor_pos < len(buffer):
                cursor_pos += 1
        elif 32 <= key <= 126:  # Printable characters
            buffer.insert(cursor_pos, chr(key))
            cursor_pos += 1

    curses.curs_set(0)

    return "".join(buffer)


def draw_window(win):
    win.clear()
    win.box()
    win.addstr(1, 2, "This is a new window!")
    win.refresh()


def footer(stdscr, height: int, width: int):
    stdscr.addstr(height - 1, width - 20, "SPACE : toggle")
    stdscr.addstr(height - 1, width - 40, "ENTER: open")
    stdscr.addstr(height - 1, width - 64, "E: edit name")
    stdscr.addstr(height - 1, width - 80, "A: Add")
    stdscr.addstr(height - 1, width - 100, "D: Delete")


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)
    notes = Notes_list()
    win = curses.newwin(10, 40, 5, 10)
    while True:
        height, width = stdscr.getmaxyx()
        footer(stdscr, height, width)
        notes.print_items(stdscr)
        key = stdscr.getch()
        if key == ord("q"):
            break
        notes.check(key=key)
        notes.update(stdscr, key=key)
        stdscr.refresh()
        # draw_window(win)
