import sys

from .application import Application

if __name__ == "__main__":
    app = Application()
    sys.exit(app.run(sys.argv))
