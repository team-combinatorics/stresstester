from . import LogViewer
import sys

if __name__ == '__main__':
    t = LogViewer()
    files = sys.argv[1:]
    t.run_sync(files)