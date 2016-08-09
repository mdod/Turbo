import configparser

from .exceptions import FatalError


class Config:

    def __init__(self):
        config = configparser.ConfigParser(interpolation=None)
        if not config.read('config/config.ini', encoding='utf-8'):
            raise FatalError(
                "The configuration file does not exist: {}".format('config/config.ini'))
        config.read('config/config.ini', encoding='utf-8')

        self.token = config.get('Auth', 'Token', fallback=ConfigDefaults.token)
        self.bot = config.getboolean(
            'Auth', 'Bot', fallback=ConfigDefaults.bot)

        self.prefix = config.get(
            'Options', 'Prefix', fallback=ConfigDefaults.prefix)


class ConfigDefaults:
    token = None
    bot = False

    prefix = '$'
