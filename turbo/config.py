import configparser
import os
import shutil

from .exceptions import FatalError, printError
from colorama import Fore


class Config:

    def __init__(self):
        restart_required = False
        files = ['blacklist.txt', 'config.ini', 'responses.json', 'tags.json']
        for f in files:
            if not os.path.isfile('config/{}'.format(f)):
                print("{}Can't find file: config/{}".format(Fore.YELLOW, f))
                source = 'config/examples/{}'.format(f)
                if os.path.isfile(source):
                    shutil.copy(source, 'config/{}'.format(f))
                    print("{}Copied file: {} to config/{}{}".format(Fore.GREEN, source, f, Fore.RESET))
                else:
                    raise FatalError("Example file: {} doesn't exist. Can't copy. Please redownload.".format(
                        source))
                restart_required = True
        if restart_required:
            print("\n{}Please configure the options in the /config folder and run the bot again.{}".format(Fore.YELLOW, Fore.RESET))
            os._exit(1)


        config = configparser.ConfigParser(interpolation=None)
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
        self.color = config.get(
            'Options', 'Color', fallback=ConfigDefaults.color)

        self.moderator = config.get(
            'Permissions', 'Moderator', fallback=ConfigDefaults.moderator)

        self.holidays_key = config.get(
            'Holidays', 'Key', fallback=ConfigDefaults.holidays_key)
        self.holidays_country = config.get(
            'Holidays', 'Country', fallback=ConfigDefaults.holidays_country)

        self.mashape = config.get(
            'Mashape', 'Key', fallback=ConfigDefaults.mashape)

        self.validate()

    def validate(self):
        """
        Validates the configuration options
        """
        self.color = self.color.upper()
        if self.color not in ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE']:
            self.color = getattr(Fore, ConfigDefaults.color)
            print("{}Specified color not found as a supported logging color. Defaulting to {}{}".format(self.color, ConfigDefaults.color, Fore.RESET))
        else:
            self.color = getattr(Fore, self.color)

        if self.messages < 100:
            print("{}Messages amount in config must be 100 or higher. Defaulting to {}{}".format(self.color, ConfigDefaults.messages, Fore.RESET))
            self.messages = ConfigDefaults.messages

        if self.flip:
            self.flip = self.handle_comma_list(self.flip)
        if self.moderator:
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
    autorespond = False
    color = "YELLOW"

    moderator = []

    holidays_key = None
    holidays_country = "US"

    mashape = None
