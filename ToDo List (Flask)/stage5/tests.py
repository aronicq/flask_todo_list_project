import os

from test.tests import ServerTest

if __name__ == '__main__':
    try:
        os.remove("instance/sqlite.db")
    except Exception:
        ...
    ServerTest().run_tests()
