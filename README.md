# :rocket: Turbo - Discord Bot
> **Note:** Turbo works as a selfbot or a regular bot, however it doesn't allow configuring permissions (e.g who can use commands). To use it as a standalone bot, create an [oAuth application](https://discordapp.com/developers/applications/me) and set `bot=True` in `config.ini`.

Turbo is a Discord bot powered by [discord.py](http://github.com/Rapptz/discord.py), which runs alongside your user account to help you perform many functions, including easily evaluating Python code, checking the servers that an emoji is on, getting all users with a certain discriminator, and much more!

**Please note that I did not create this bot. [jaydenkieran](https://github.com/jaydenkieran) is the original creator of [Turbo](https://github.com/jaydenkieran/Turbo). I have only modified and added to his bot.**

#Easy Install
> Run these commands in a **Command Prompt / Terminal** application 

* Clone the bot using **Git**:
```
git clone https://github.com/mdod/Turbo.git -b master
```
* Install required dependencies:
```
python -m pip install -r requirements.txt
```
* Copy all of the files from `/config/examples` to `/config`

    In the `config.ini` file:
    * Insert you or your Bot's token
    * If you are using a bot account, set `Bot = ` to `yes`
    * **[Optional]** Set your preferred command prefix (Default is **$**)
    * **[Optional]** Obtain API Keys for any APIs you would like to use with Turbo
    
    **[Optional]** In the `responses.json` file:
    * Add responses (If `Autoresponses = yes` in `config.ini`, a message will be sent by the bot each time a trigger message is sent by a user.)

        Responses are set like this:
        ```
        "Channel ID": {
            "Trigger": "Response"
        }
        ```
        **More info about responses can be found a little further down**

    **[Optional]** In the `tags.json` file:
    * Add tags (Responses sent by the bot each time a user sends `$tag <tag name>` in chat)
    
        Tags are set like this:
        ```
        {
            "tag name": "response"
        }
        ```
* Run the bot:
    * On **Windows**: Open `run.bat` (this will set console to UTF-8, fixing unicode encoding)
    * On **Linux**: Run `python run.py`

# Requirements
* [Python 3.5](http://python.org)

The following are Python dependencies, inside `requirements.txt`:

* [discord.py](http://github.com/Rapptz/discord.py)
* [colorama](https://pypi.python.org/pypi/colorama)
* [requests](https://github.com/kennethreitz/requests)
* [steamapi](https://github.com/mdod/steamapi)
* [easy_date](https://pypi.python.org/pypi/easy-date/0.1.3)

You can install them using:
```
python -m pip install -r requirements.txt
```

If you're on **Windows**, you can run `update_deps.bat` instead.

# Installation
Clone the bot using **Git**:
```
git clone https://github.com/mdod/Turbo.git -b master
```

Run the bot:
* On **Windows**: Open `run.bat` (this will set console to UTF-8, fixing unicode encoding)
* On **Linux**: Run `python run.py`

# Usage
**Start by copying all of the files from `/config/examples` to `/config`. The bot does this automatically if the files don't exist**

In the configuration file (`config.ini`), change the `Token` to your account's token. As you **should** be using your own account, your token is obtainable via `localStorage.token` in the Web Inspector (CTRL + SHIFT + I) on the Discord client.

The `Bot` boolean determines whether you are using a user account or a bot account. This should be `no`, but if you decide to use the bot standalone (see warning at the top of this file), this will be `yes`.

Other options:
* `Prefix` - The prefix used before all of the bot's commands
* `Messages` - The amount of messages for the client to cache (for use in `$echo`)
* `Flip` - Comma seperated list of possible responses to the `$flip` command
* `Color` - A color for Colorama to use for logging
* `Autorespond` - Boolean for if the bot's autoresponding feature is enabled or not
* `Moderator` - Comma seperated list of user IDs that can use the `$disable` command in emergencies
* **For API-specific options**, see [apis.md](docs/apis.md).

There are two files in JSON format which allow for adding tags and autoresponses. Bare in mind: Autoresponses are bad practice in selfbots and should not be used in a public server, only private ones. Either of these files **can** be deleted and the bot will function fine without them, though the `$tag` command won't work if `tags.json` is deleted, and autoresponses will never be triggered if `responses.json` doesn't exist.

To add autoresponses, use `responses.json`. Add the channel ID to send the message in as an object, and then the autoreponse's trigger and response. To add multiple autorespones for a channel, just put a `,` at the end of the line before making a new one. Example below.

```json
{
    "84319995256905728": {
        "trigger": "response",
        "trigger2": "response2"
    }
}
```

To add tags, use `tags.json`. An example tag is already in the file when you downloaded the bot, which should make it easy for you to tell how to create more.

You can also blacklist user IDs from triggering autoresponses (or using the bot, if using it as a standalone one) by putting an ID on a new line in the `blacklist.txt` file.

# Commands
* :paperclip: `$tag <name>` - Triggers a tag
* :pencil2: `$addtag <name> <content>` - Adds a new tag
* :pencil2: `$removetag <name>` - Removes a tag with given name
* :pencil2: `$cleartags` - Removes all tags
* :pencil2: `$tags` - Lists all tags
* :pencil2: `$responses` - Lists all autoresponses
* :floppy_disk: `$eval <code>` - Allows you to evaluate Python code
* :hammer: `$discrim <discrim>` - Displays all visible users with discriminator given
* :couple: `$emoji <emoji as string>` - Displays information about a custom emoji
* :snowflake: `$snowflake <id>` - Get the creation time in UTC of a Discord ID
* :thought_balloon: `$status <status>` - Change the user's status
* :abc: `$strike <text>` - Strikes out text (replica of using `~~text~~`)
* :abc: `$bold <text>` - Bolds text (replica of using `**text**`)
* :abc: `$italics <text>` - Italicalises text (replica of using `*text*`)
* :speech_balloon: `$quote` - Returns a random famous quote
* :woman: `$yomama` - Returns a random yomama joke
* :black_joker: `$joke` - Returns a random joke
* :open_book: `$urbandictionary <word>` - Returns the definition of the given word on Urban Dictionary
* :repeat: `$reload` - Reloads the bot's JSON files (`tags.json` and `responses.json`)
* :mega: `$echo <id>` - Echos a message via it's ID (must be saved in cache)
* :mega: `$messageinfo <id>` - Shows information about a message
* :arrows_clockwise: `$flip` - Flips an imaginary object
* :game_die: `$random <number>` - Returns a random number between 1 and the number given
* :partly_sunny: `$weather <zipcode>` - Get the current weather for a certain zipcode
* :earth_americas: `$serverregion <region>` - Switch the server to a different region
* :name_badge: `$servername <name>` - Rename the server
* :no_entry_sign: `$disable` - Disables the bot temporarily
* :white_check_mark: `$enable` - Re-enables the bot
* :hourglass: `$timer <minutes:seconds>` - Starts a timer
* :alarm_clock: `$listtimers` - Returns a list of all running timers
* :watch: `$time` - Returns the current time
* :calendar: `$date` - Returns the current date
* :cat: `$cat` - Sends a random cat picture
* :balloon: `$holidays [country code]` - Gets upcoming holiday info for country
* :electric_plug: `$githubuser <username>` - Gets information about a GitHub user
* :performing_arts: `$generatename [gender]` - Generates a random name
* :video_game: `$hearthinfo` - Get information about the latest version of Hearthstone
* :video_game: `$owplayer <battletag>` - Gets stats for an Overwatch player
* :video_game: `$steamuser <steamid>` - Gets information about a Steam user

# Development
You can fork this project and change things to make it your own, using the foundations that it is built upon. You should read the [documentation](http://discordpy.readthedocs.io/en/latest/api.html#client) for discord.py to learn more about the methods that can be used.

These methods exist to compliment various built-in discord.py methods:
* `safe_send_message(msg, content, delete_after)` - Allows safe sending of a message. Checks for various exceptions. Can allow for deleting messages after a certain time.
* `safe_edit_message(msg, content, delete_after)` - Allows safe editing of a message. Checks for various exceptions. Can allow for deleting messages after a certain time.
* `safe_delete_message(msg)` - Allows safe deleting of a message. Checks for various exceptions.
* `safe_edit_server(server, **kwargs)` - Allows safe editing of a server. Checks for various exceptions.

These methods are utility functions:
* `_check_bot(msg, str)` - Checks if the bot is running on a bot account or user account. If user account, assume selfbot and edit the message. If oauth, assume standalone and send a message to the channel instead.
* `_delete_msg(msg, time)` - Deletes a message after a period of time (in seconds)
* `_request(url, **kwargs)` - Sends a HTTP request to a URL

The following decorators can be used:
* `@no_private` - Disallows a command being used in a [PrivateChannel](http://discordpy.readthedocs.io/en/latest/api.html#discord.PrivateChannel)
* `@mashape` - Wrapper for commands that require the [Mashape](https://market.mashape.com/) API key set in the config

These exceptions can be raised:
* `FatalError` - Raised when the bot encounters an error that means it cannot continue

# License
This project is licensed under the **MIT License**. It is available in [LICENSE.md](LICENSE.md).

For API-specific credits, see [apis.md](docs/apis.md).
