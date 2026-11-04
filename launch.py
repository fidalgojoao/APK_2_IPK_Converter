"""Double click on systems with Python/Tk installed, or run python launch.py."""
import sys
from apk2ipk.gui import launch, smoke_test

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        smoke_test()
    else:
        launch()
