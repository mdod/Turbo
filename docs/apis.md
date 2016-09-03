# :rocket: List of APIs
This is a list of the APIs that Turbo uses and their specific options that are available in the `config.ini` file.

## HolidayAPI
> Data obtained from [HolidayAPI](https://holidayapi.com/)

Options:
* `Key` - Obtained from [HolidayAPI](https://holidayapi.com/)
* `Country` - Default country code to use in queries (full list at site above)

## GitHub API v3
> Data obtained from [GitHub](https://github.com/).

Limited to 60 requests/hour for unauthenticated users. After that, you'll receive `HTTP Error 403: Forbidden`.

## UINames API
> Data obtained from [UINames](http://uinames.com/).

## Overwatch API
> Data obtained from [OWApi](https://owapi.net/).

## Steam API
> Data obtained from [Steam](https://developer.valvesoftware.com/wiki/Steam_Web_API) and [SteamAPI](https://github.com/smiley/steamapi).

## WeatherUnderground API
> Data obtained from [Weather Underground](https://www.wunderground.com/weather/api/)

## Joke API
> Data obtained from [Joke API](http://tambal.azurewebsites.net/joke/random)

## Yomama API
> Data obtained from [Y Momma](http://yomomma.info)

## Mashape
These APIs are used through a service called [Mashape](https://market.mashape.com/). You should create an account there. Afterwards, replace `<name>` in this URL with your username and go to it:

```
https://market.mashape.com/<name>/applications/default-application
```

Afterwards, click **GET THE KEYS** at the top-right, select **Production** from the drop-down menu, and copy your key. This key is universal and will be used for every API under this section.

Place it in `config.ini` under the **[Mashape]** section.

### Hearthstone API
> Data obtained from [Mashape](https://market.mashape.com/omgvamp/hearthstone).

### Urban Dictionary API
> Data obtained from [Mashape](https://market.mashape.com/community/urban-dictionary)

### Quote API
> Data obtained from [Mashape](https://market.mashape.com/andruxnet/random-famous-quotes)
