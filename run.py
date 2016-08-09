import aiohttp
import traceback
from colorama import init, Fore
init()

print('\x1b[2J')

try:
    from turbo import Turbo
    bot = Turbo()
    print("Starting...")
    bot.run()
except aiohttp.errors.ClientOSError as e:
    print(Fore.RED + "Problem connecting to Discord: {}".format(e))
except Exception as e:
    if hasattr(e, '__module__') and e.__module__ == 'turbo.exceptions':
        name = e.__class__.__name__
        if name == "FatalError":
            print("{}{}".format(Fore.RED, e.message))
    else:
        traceback.print_exc()
