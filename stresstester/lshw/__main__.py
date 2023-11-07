from . import LSHW

if __name__ == '__main__':
    t = LSHW()
    print(t.run_sync())