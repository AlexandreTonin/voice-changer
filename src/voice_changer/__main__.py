import os
import sys

from voice_changer.config import APPLIO_DIR, applio_env


def main():
    os.environ.update(applio_env())
    os.chdir(APPLIO_DIR)
    sys.path.insert(0, str(APPLIO_DIR))

    from PySide6.QtWidgets import QApplication

    from voice_changer.app import App

    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)
    app = App(qt_app)
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
