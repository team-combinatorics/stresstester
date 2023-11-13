from configparser import ConfigParser

from stresstester import StressTesterApp


def get_locale_windows():
    import locale
    import ctypes

    windll = ctypes.windll.kernel32
    return locale.windows_locale[windll.GetUserDefaultUILanguage()]


def use_english():
    try:
        _locale = get_locale_windows()
        if _locale.startswith("zh"):
            print("Using zh_CN locale:", _locale)
            return False
        print("Using en_US locale:", _locale)
        return True
    except:
        return False


if __name__ == '__main__':
    _conf = ConfigParser()
    _conf.read(['config.ini', 'text_en.ini' if use_english() else 'text.ini'])
    app = StressTesterApp(_conf)
    app.run()
