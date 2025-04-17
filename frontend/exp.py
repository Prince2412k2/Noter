from pynput import keyboard
from pynput.keyboard import Key


def on_press(key):
    if key == Key.up:
        print("↑ Up arrow pressed")
    elif key == Key.down:
        print("↓ Down arrow pressed")
    elif key == Key.left:
        print("← Left arrow pressed")
    elif key == Key.right:
        print("→ Right arrow pressed")
    elif key == Key.esc:
        print("Exiting...")
        return False  # Stop listener
    else:
        try:
            print(f"Key pressed: {key.char}")
        except AttributeError:
            print(f"Special key pressed: {key}")


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

