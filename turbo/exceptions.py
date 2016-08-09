from colorama import Fore


class TurboException(Exception):

    def __init__(self, message):
        self._message = message

    @property
    def message(self):
        return self._message


class FatalError(TurboException):

    def __init__(self, issue):
        self.issue = issue

    @property
    def message(self):
        return "\n###### A fatal error occurred while running Turbo ######\n{}\n".format(self.issue)


def printError(error):
    print(Fore.RED + "{}".format(error) + Fore.RESET)
