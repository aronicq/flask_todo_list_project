import os

from test.tests import ServerTest, Test

if __name__ == '__main__':
    ServerTest().run_tests()
    Test().run_tests()

    try:
        os.remove("instance/sqlite.db")
    except Exception:
        ...
