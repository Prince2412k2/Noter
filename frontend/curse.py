# TODO: versdion control
"""
git log --pretty=format:'{%n  "hash": "%H",%n  "author": "%an",%n  "email": "%ae",%n  "date": "%ad",%n  "message": "%s"%n},'
"""

import subprocess
import json
from typing import List, Optional
import time
from backend import (
    get_all,
    parse_all,
    toggle_done,
    write_note,
    remove_item,
    add_item,
    update_name,
    Relation,
    PATH,
    Db,
    Commits,
    Commit,
)

import curses
import logging

import pyperclip


logger = logging.getLogger()
db = Db(PATH)


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
        self.items: List[Relation] = parse_all(db)
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

        name = self.items[self.pointer.selected].name
        if name:
            name = name.strip()
        else:
            return
        if key == ord("a"):
            pos_y = self.pointer.max + 1
            name = input_box(stdscr, pos_y=pos_y, prompt=" │>[n] ")
            if not name:
                return
            if add_item(name=name, note="Welcome", db=db):
                commit_file(".")
                time.sleep(0.05)
                notify(f"note : {name} created")

            else:
                notify(f"{name.capitalize()} already exists")
                return
            self.refresh()
            return
        if not self.items:
            return
        if key == ord(" "):
            if name:
                toggle_done(name, db)
        if key in (curses.KEY_ENTER, 10, 13):
            curses.endwin()
            write_note(name)
            commit_file(".")
            curses.doupdate()
        if key == ord("d"):
            # TODO: implement double "d" for delete
            if name:
                if remove_item(name, db):
                    commit_file(".")
                    notify(f"note : {name} deleted", 2)
                else:
                    notify(f"{name} does not exist")
                    return
            if self.pointer.selected == self.pointer.max:
                self.pointer.selected -= 1
        if key == ord("e"):
            name = edit_note(stdscr, note=self)
        if key == ord("h"):
            draw_footer(stdscr, view_footer)
        if key == ord("g"):
            jump_to(stdscr, self)
        self.refresh()

    def refresh(self):
        self.items = parse_all(db)
        self.pointer.max = len(self.items) - 1


def edit_note(stdscr, note: NotesList):
    pos_y = note.pointer.selected
    old_name = note.items[pos_y].name
    assert old_name
    name = input_box(stdscr=stdscr, pos_y=pos_y, prefill=old_name, prompt=" │>[e] ")
    if not name:
        return
    if update_name(old_name, name, db):
        commit_file(".")
        notify(f"{name} updated")
    else:
        notify(f"{name} does not exist")

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


def draw_commit_window(win, height, width, commits):
    win.resize(height - 2, width // 2 - 2)
    win.mvwin(0, 0)
    win.erase()
    print_items(commits, win)
    win.box()
    win.refresh()


def view_footer(win, height: int, width: int):
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
        ("  V   -> Version Control", white),
    ):
        win.addstr(count + 2, 4, tag[0], tag[1])
        count += space
    win.box()
    win.refresh()


def git_footer(win, height: int, width: int):
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
    for tag in (("c -> coppy version to clipboard", white),):
        win.addstr(count + 2, 4, tag[0], tag[1])
        count += space
    win.box()
    win.refresh()


def draw_footer(stdscr, footer):
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
    assert rel.note
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
    win.addstr(
        2,
        int(width * 0.5) - len(msg) + 5,
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


def get_single_commit(item: dict) -> Commit:
    return Commit(**item)


def get_all_commits(file: str) -> Commits:
    result = subprocess.run(
        [
            "git",
            "log",
            "--follow",
            '--pretty=format:{%n  "hash": "%H",%n  "author": "%an",%n  "email": "%ae",%n  "date": "%ad",%n  "message": "%s"%n},',
            "--",
            file,
        ],
        cwd=PATH,
        capture_output=True,
        text=True,
    )
    out = f"[{result.stdout[:-1]}]"
    jout = json.loads(out)
    return Commits(commits=[get_single_commit(i) for i in jout])


def get_file_with_hash(hash: str, name: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "show",
                f"{hash}:{name}",
            ],
            cwd=PATH,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            return None


def commit_file(name: str):
    try:
        today = time.strftime("%d-%m-%y")

        out1 = subprocess.run(["git", "add", name], check=True, capture_output=True)
        out2 = subprocess.run(
            ["git", "commit", "-m", today], check=True, capture_output=True
        )
        logger.info("\n--------------\n")
        logger.info(out1)
        logger.info("\n--------------\n")
        logger.info(out2)
    except subprocess.CalledProcessError as e:
        logger.info("\n--------------\n")
        logger.info(e)
        logger.info("\n--------------\n")
        if e.returncode == 128:
            notify(f"failed to commit{name if name != '.' else '*'}")
            return None


def version_control(
    stdscr, git_win, view_win, notes: NotesList, key, height, width, count
):
    if key == ord("v"):
        file = notes.items[notes.pointer.selected].name
        assert file
        commits: Commits = get_all_commits(file)
        assert file
        while True:
            com = commits.get()
            if not com:
                break
            content = get_file_with_hash(com.hash, file)
            draw_commit_window(git_win, height, width, commits)
            draw_view_window(
                view_win,
                height,
                width,
                content=content,
            )
            handle_notification(width, count)
            key1 = stdscr.getch()
            if key1 == curses.KEY_UP:
                commits.up()
            if key1 == curses.KEY_DOWN:
                commits.down()
            if key1 == ord("c"):
                logger.info("CUSRED ROUTE")
                pyperclip.copy(content if content else "")
                notify("Content coppied to clipboard")
            if key1 == ord("h"):
                draw_footer(stdscr, git_footer)
            if key1 == ord("q"):
                break
            time.sleep(0.05)


def print_items(commits: Commits, win):
    for idx, i in enumerate(commits.commits):
        point = " "
        color = curses.color_pair(1) | curses.A_DIM
        if idx == commits.pointer:
            color = curses.color_pair(1) | curses.A_STANDOUT | curses.A_BOLD
        win.addstr(idx + 1, 1, f"{idx + 1}│{point}{i.date}", color)


NOTIFICATION = Notification()


def main(stdscr):
    init_color()

    height, width = stdscr.getmaxyx()
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    notes = NotesList()

    if not get_all(db):
        add_item("welcome", "welcome", db)

    view_win = curses.newwin((height) - 1, (width // 2) - 2, 0, width // 2)
    git_win = curses.newwin((height) - 1, (width // 2) - 2, 0, 0)
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
        version_control(stdscr, git_win, view_win, notes, key, height, width, count)
        notes.update(stdscr, key=key)
        time.sleep(0.005)
        stdscr.refresh()
