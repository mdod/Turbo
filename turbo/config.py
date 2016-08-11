import configparser

from .exceptions import FatalError
from colorama import Fore


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
        self.messages = config.getint(
            'Options', 'Messages', fallback=ConfigDefaults.messages)
        self.flip = config.get(
            'Options', 'Flip', fallback=ConfigDefaults.flip)
        self.autorespond = config.getboolean(
            'Options', 'Autorespond', fallback=ConfigDefaults.autorespond)

        self.moderator = config.get(
            'Permissions', 'Moderator', fallback=ConfigDefaults.moderator)

        self.validate()

    def validate(self):
        """
        Validates the configuration options
        """
        if self.messages < 100:
            print("{}Messages amount in config must be 100 or higher. Defaulting to {}{}".format(Fore.YELLOW, ConfigDefaults.messages, Fore.RESET))
            self.messages = ConfigDefaults.messages

        self.flip = self.handle_comma_list(self.flip)
        self.moderator = self.handle_comma_list(self.moderator)

    def handle_comma_list(self, data):
        """
        Utility function for handling comma seperated lists
        """
        newlist = []
        for l in data.split(','):
            # Remove dodgy whitespace at the beginning of strings
            l = l.lstrip()
            newlist.append(l)
        return newlist


class ConfigDefaults:
    token = None
    bot = False

    prefix = '$'
    messages = 5000
    flip = "Heads, Tails"

    moderator = []
