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
from models import Relation, relation
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


class NotesList:
    def __init__(self) -> None:
        self.items: List[Relation] = parse_all(get_all())
        self.pointer: Pointer = Pointer(len(self.items) - 1)

    def print_items(self, stdscr):
        for idx, i in enumerate(self.items):
            point = " "
            color = curses.color_pair(1) | curses.A_DIM
            if idx == self.pointer.selected:
                point = self.pointer.string
                color = (
                    curses.color_pair(1) | curses.A_STANDOUT | curses.A_BOLD
                    # | curses.A_REVERSE
                )
            if i.done:
                status = self.pointer.done
            else:
                status = self.pointer.not_done
            stdscr.addstr(idx, 0, f"{point}{status} {i.name}", color)
            stdscr.refresh()

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
            # stdscr.erase()
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
            # stdscr.erase()
        if key == ord("e"):
            pos_y = self.pointer.selected
            item = self.items[pos_y]
            name = input_box(
                stdscr, notes=self, pos_y=pos_y, prefill=item.name, prompt=">[e] "
            )
            if not name:
                return
            update_name(id=item.id, name=name)
            # stdscr.erase()
            self.refresh()
        if key == ord("h"):
            draw_footer(stdscr)
        self.refresh()

    def refresh(self):
        self.items = parse_all(get_all())
        self.pointer.max = len(self.items) - 1


def input_box(
    stdscr, notes: NotesList, pos_y: int, prompt: str = ">[ ] ", prefill: str = ""
):
    if not prefill:
        notes.pointer.selected = notes.pointer.max + 1

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


def print_in_win(win, content: List[str]):
    space = len(str(len(content)))
    for line, i in enumerate(content):
        # leading_space=" "*(space-len(str(line+1)))
        # prefix_zero="0"*(space-len(str(line+1)))
        win.addstr(line + 1, 1, f"{'0' * (space - len(str(line + 1)))}{line + 1} │ {i}")


def draw_view_window(win, height, width, content):
    chunked = chunk_content(content=content, hight=height, width=width)

    win.resize(height - 2, width // 2 - 2)
    win.mvwin(0, width // 2)
    win.erase()
    print_in_win(win, content=chunked)
    win.box()
    win.refresh()


def footer(win, height: int, width: int):
    space = 2
    if height // 2 < 12:
        space = 1
    if (height // 2) < 10:
        win.erase()
        return

    win.resize(height // 2, width // 2)
    win.mvwin(height // 4, width // 4)
    win.erase()
    count = 1
    white = curses.color_pair(1) | curses.A_BOLD
    blue = curses.color_pair(4) | curses.A_BOLD | curses.A_DIM
    red = curses.color_pair(2) | curses.A_BOLD
    for tag in (
        ("Space -> Toggle Done and Undone", white),
        ("Enter -> Open in Neovim", blue),
        ("  E   -> Edit name of the note", white),
        ("  A   -> New Note", white),
        ("  D   -> Delete Note", red),
    ):
        win.addstr(count + 2, 4, tag[0], tag[1])
        count += space
    win.box()
    win.refresh()


def draw_footer(stdscr):
    height, width = stdscr.getmaxyx()
    win = curses.newwin(height // 2, width // 2, height // 2, width // 2)

    while True:
        footer(win, height, width)
        temp_key = stdscr.getch()
        if temp_key:
            break
    win.clear()


def help_bar(stdscr, height, width):
    if width < 20:
        return
    stdscr.addstr(height - 1, 2, "H : HELP ", curses.color_pair(3))
    stdscr.addstr(height - 1, width - 10, "Q : Quit ", curses.color_pair(3))


def split_content_by_width(content, width):
    return [content[i : i + width] for i in range(0, len(content), width)]


def chunk_content(content: str, width: int, hight: int) -> list[str]:
    result = []
    for i in content.split("\n"):
        if i:
            result.extend(split_content_by_width(i, width))
        else:
            result.append("")

    return result[: hight - 1]


def get_note_content(notes_list: NotesList) -> str:
    pointer = notes_list.pointer.selected
    rel = notes_list.items[pointer]
    return rel.note.strip("\n").strip()


def init_color():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)


def main(stdscr):
    init_color()
    height, width = stdscr.getmaxyx()
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)
    notes = NotesList()
    view_win = curses.newwin((height) - 1, (width // 2) - 2, 0, width // 2)
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        help_bar(stdscr, height, width)
        notes.print_items(stdscr)
        draw_view_window(
            view_win,
            height,
            width,
            content=get_note_content(notes),
        )
        key = stdscr.getch()
        if key == ord("q"):
            break
        notes.check(key=key)
        notes.update(stdscr, key=key)
        stdscr.refresh()
