import os
from typing import Optional
from pynput import keyboard
from pynput.keyboard import Key


class Inputs:
    def __init__(self) -> None:
        self.up: bool = False
        self.down: bool = False

    def set_up(self):
        self.up = True
        self.down = False

    def set_down(self):
        self.up = False
        self.down = True


inputs = Inputs()


def on_press(key):
    global inputs
    try:
        if key.char == Key.up:
            inputs.set_up()
            print("up")
        if key.char == Key.down:
            inputs.set_down()
            print("down")
    except AttributeError:
        print("wrong key")
    # Handle special keys (e.g., arrow keys)


class Pointer:
    def __init__(self, max: int, keys: Inputs) -> None:
        self.selected: int = 0
        self.string: str = ">"
        self.max: int = max
        self.keys: Inputs = keys

    def up(self):
        if self.selected > 0:
            self.selected += 1

    def down(self):
        if self.selected < self.max:
            self.selected += 1


class Notes_list:
    def __init__(self, items: list) -> None:
        global inputs
        self.items: list = items
        self.pointer: Pointer = Pointer(len(self.items), inputs)

    def print_items(self):
        for idx, i in enumerate(self.items):
            if idx == self.pointer.selected:
                print(self.pointer.string, end="")
            else:
                print(" ", end="")
            print(i)

    def check(self):
        if self.pointer.keys.up:
            self.pointer.up()
        if self.pointer.keys.down:
            self.pointer.down()


def clear():
    """clear screen"""
    os.system("clear")


def start_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener


def main():
    notes = Notes_list(["hellow", "world", "who is you"])
    while True:
        print("on")  # Main TUI loop for output display
    # clear()
    # notes.print_items()
    # notes.check()


if __name__ == "__main__":
    listener = start_listener()  # Start listening to the keyboard
    try:
        main()
    finally:
        listener.stop()
