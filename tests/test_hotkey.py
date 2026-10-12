from voice_changer.hotkey import from_key_sequence, to_key_sequence

assert from_key_sequence("Ctrl+Alt+V") == "<ctrl>+<alt>+v"
assert from_key_sequence("Meta+Shift+F9") == "<cmd>+<shift>+<f9>"
assert to_key_sequence("<ctrl>+<alt>+v") == "Ctrl+Alt+V"
assert to_key_sequence(from_key_sequence("Ctrl+Shift+F12")) == "Ctrl+Shift+F12"
for invalid in ("", "Ctrl+Bogus"):
    try:
        from_key_sequence(invalid)
        raise AssertionError(f"accepted {invalid!r}")
    except ValueError:
        pass
print("ok")
