from . import Prime95

if __name__ == '__main__':
    t = Prime95()
    print(t.run_sync())