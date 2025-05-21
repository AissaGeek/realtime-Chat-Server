"""Module to create chat channel between clients"""
import sys

from ui import ChatApp

if __name__ == "__main__":
    try:
        app = ChatApp(sys.argv)
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
