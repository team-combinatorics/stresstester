import os

from . import BatteryInfo

if __name__ == '__main__':
    t = BatteryInfo()
    print(t.run_sync())

    with open(os.path.join(t.path,'battery.csv'), 'r') as f:
        print(f.read())