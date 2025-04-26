from typing import List
import time
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


logger = logging.getLogger()


def init_color():
    # curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)

    # HEADING1
    curses.init_pair(11, curses.COLOR_BLACK, 224)  # Light red-like
    # HEADING2
    curses.init_pair(12, curses.COLOR_BLACK, 225)  # Light magenta/pink
    # HEADING3
    curses.init_pair(13, curses.COLOR_BLACK, 229)  # Light yellow
    # HEADING4
    curses.init_pair(14, curses.COLOR_BLACK, 152)  # Light green
    # HEADING5
    curses.init_pair(15, curses.COLOR_BLACK, 153)  # Light blue
    # HEADING6
    curses.init_pair(16, curses.COLOR_BLACK, 195)
    # CODE
    curses.init_pair(17, curses.COLOR_CYAN, -1)
    # list
    curses.init_pair(18, 229, -1)


class Notification:
    def __init__(self, msg="") -> None:
        self.msg: str = msg
        self.color = 1
        self.life: float = 0.0
        self.wid = len(self.msg) + 10
        self.changed = True

    def deduct(self, deduction_ammout: float):
        if self.life > 0:
            self.life -= deduction_ammout

    def set_msg(self, msg, color_code=1):
        self.color = color_code
        self.wid = len(msg) + 20
        self.msg = msg
        self.life = time.perf_counter() + 5
        self.changed = True
        return self


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
                color = curses.color_pair(1) | curses.A_STANDOUT | curses.A_BOLD
            if i.done:
                status = self.pointer.done
            else:
                status = self.pointer.not_done
            stdscr.addstr(idx, 0, f"{idx + 1}│{point}{status} {i.name}", color)
            stdscr.refresh()

    # def check(self, key):
    def update(self, stdscr, key):
        if key == curses.KEY_UP:
            self.pointer.up()
        if key == curses.KEY_DOWN:
            self.pointer.down()

        if key == ord("a"):
            pos_y = self.pointer.max + 1
            name = input_box(stdscr, pos_y=pos_y, prompt=" │>[n] ")
            if not name:
                return
            add_item(name=name, note="Welcome")
            notify(f"note : {name} created")
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
            item = self.items[self.pointer.selected]
            remove_item(item.id)
            if self.pointer.selected == self.pointer.max:
                self.pointer.selected -= 1
            notify(f"note : {item.name} deleted", 2)
        if key == ord("e"):
            name = edit_note(stdscr, note=self)
        if key == ord("h"):
            draw_footer(stdscr)
        if key == ord("g"):
            jump_to(stdscr, self)
        self.refresh()

    def refresh(self):
        self.items = parse_all(get_all())
        self.pointer.max = len(self.items) - 1


def edit_note(stdscr, note: NotesList):
    pos_y = note.pointer.selected
    item = note.items[pos_y]
    name = input_box(stdscr=stdscr, pos_y=pos_y, prefill=item.name, prompt=" │>[e] ")
    if not name:
        return
    update_name(id=item.id, name=name)
    note.refresh()


def input_box(stdscr, pos_y: int, prompt: str = " │>[ ] ", prefill: str = "", max=None):
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
        if not max:
            continue
        elif len(buffer) >= max:
            curses.curs_set(0)
            return "".join(buffer)

    curses.curs_set(0)
    return "".join(buffer)


def print_in_win(win, content: List[str]):
    space = len(str(len(content)))
    for line, i in enumerate(content):
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
        ("  G   -> GoTo", white),
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

    return result[: hight - 4]


def get_note_content(notes_list: NotesList) -> str:
    pointer = notes_list.pointer.selected
    rel = notes_list.items[pointer]
    return rel.note.strip("\n").strip()


def go_to_index(note: NotesList, index: int):
    if index > len(note.items):
        notify(f"<{index}> is out of range", 2)
        return
    note.pointer.selected = index - 1


def jump_to(stdscr, note: NotesList):
    num_items = len(note.items) + 1
    index = input_box(
        stdscr=stdscr, pos_y=stdscr.getmaxyx()[0] - 1, prompt="g~ ", max=num_items
    )
    if index.isnumeric():
        index = int(index)
        go_to_index(note, index)
    else:
        notify(f"<{index}> is not a valid num", 2)


def generate_notification(win: curses.window, msg: str, width, pos_y, pos_x, color):
    win.resize(5, width)
    win.mvwin(pos_y, pos_x)
    win.erase()
    logger.info(color)
    win.addstr(
        2,
        int(width * 0.5) - len(msg) + 4,
        msg,
        curses.color_pair(color) | curses.A_BOLD,
    )
    win.attron(curses.color_pair(4))
    win.box()
    win.addstr(
        0,
        int(width * 0.5) - 12 - 4,
        "Notification",
        curses.color_pair(3) | curses.A_ITALIC | curses.A_BOLD,
    )
    win.refresh()


def handle_notification(width, count):
    if NOTIFICATION.changed and not count:
        count = time.perf_counter()
        NOTIFICATION.changed = False
    if NOTIFICATION.life > 0 and count:
        wid = NOTIFICATION.wid
        pos_y = 0
        pos_x = width - wid - 2

        win = curses.newwin(
            5,
            wid,
            0,
            width - wid - 1,
        )
        generate_notification(
            win=win,
            msg=NOTIFICATION.msg,
            width=wid,
            pos_y=pos_y,
            pos_x=pos_x,
            color=NOTIFICATION.color,
        )
        NOTIFICATION.life = NOTIFICATION.life - count

    else:
        count = None
        NOTIFICATION.msg = ""


def notify(msg, color=1):
    NOTIFICATION.set_msg(msg, color)


NOTIFICATION = Notification()


def main(stdscr):
    init_color()

    height, width = stdscr.getmaxyx()
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    notes = NotesList()

    if not get_all():
        add_item("welcome", "welcome")

    view_win = curses.newwin((height) - 1, (width // 2) - 2, 0, width // 2)
    count = None
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        help_bar(stdscr, height, width)
        notes.print_items(stdscr)
        draw_view_window(
            view_win,
            height,
            width,
            content=get_note_content(notes),
        )
        handle_notification(width, count)
        key = stdscr.getch()
        if key == ord("q"):
            break
        notes.update(stdscr, key=key)
        time.sleep(0.005)
        stdscr.refresh()
