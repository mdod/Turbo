from .exceptions import printError

VERSION = "2.0_nightly_130816"


# Bork's nice method for loading files
def load_file(filename, skip_commented_lines=True, comment_char='#'):
    try:
        with open(filename, encoding='utf8') as f:
            results = []
            for line in f:
                line = line.strip()

                if line and not (skip_commented_lines and line.startswith(comment_char)):
                    results.append(line)

            return results

    except IOError as e:
        printError("Error loading {}: {}".format(filename, e))
        return []


class ApiBase:
    cat = "http://random.cat/meow"
    holidays = "https://holidayapi.com/v1/holidays"
    github = "https://api.github.com/"
    names = "http://uinames.com/api/"
    hearthstone = "https://omgvamp-hearthstone-v1.p.mashape.com/"
    overwatch = "https://owapi.net/api/v2/u/"
    steam = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="
    weather = "http://api.wunderground.com/api/"
    quote = "https://andruxnet-random-famous-quotes.p.mashape.com/?cat=famous"
    joke = "http://tambal.azurewebsites.net/joke/random"
    yomama = "http://api.yomomma.info"
    urbandictionary = "https://mashape-community-urban-dictionary.p.mashape.com/define?term="
