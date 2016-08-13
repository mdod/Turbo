"""
    Turbo is a Discord selfbot created by Jayden Bailey
    While designed for personal use, it is open-source.
    Feel free to create a fork of this project.
    Please read the LICENSE.md file for further information.
"""

import discord
import asyncio
import traceback
import inspect
import datetime
import json
import os
import random
import urllib.request
from colorama import Fore
from functools import wraps
from discord.ext.commands.bot import _get_variable

from .exceptions import FatalError, printError
from .utils import load_file, VERSION
from .config import Config


class Turbo(discord.Client):

    def __init__(self):
        print("{}Turbo - Version {} - jaydenkieran.com/turbo{}".format(Fore.GREEN, VERSION, Fore.RESET))
        super().__init__()
        self.config = Config()
        self._reload()

        self.max_messages = self.config.messages
        self.blacklist = set(load_file('config/blacklist.txt'))
        self.disabled = False

        self.timers = []
        self.timer_failure = ":warning: Provide time in a format such as **01:00** for one minute"

        self.holidays_countries = ['BE', 'BG', 'BR', 'CA', 'CZ', 'DE', 'ES', 'FR', 'GB',
                                   'GT', 'HR', 'HU', 'ID', 'IN', 'IT', 'NL', 'NO', 'PL', 'PR', 'SI', 'SK', 'US']

        self.name_genders = ['male', 'female']

        self.color = self.config.color

    def no_private(func):
        """
        Decorator to disallow using a command in a PrivateChannel
        """
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            msg = _get_variable('message')

            if not msg or not msg.channel.is_private:
                return await func(self, *args, **kwargs)
            else:
                return False
        return wrapper

    def _reload(self, save=False):
        """
        Reloads required files
        """
        if save:
            self.save_json('config/responses.json', self.responses)
            self.save_json('config/tags.json', self.tags)
        self.responses = self.load_json('config/responses.json')
        self.tags = self.load_json('config/tags.json')

    def load_json(self, file):
        """
        Safely load a JSON file
        """
        if not os.path.isfile(file):
            printError("Failed loading JSON: {}".format(file))
            return {}
        with open(file, encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, file, data):
        """
        Safely save a JSON file
        """
        if not os.path.isfile(file):
            printError("Failed saving JSON to: {}".format(file))
            return False
        with open(file, 'w', encoding="utf-8") as f:
            return json.dump(data, f, indent=4, sort_keys=True)

    def run(self):
        """
        Send authentication to Discord and start bot
        """
        print("Authenticating...")
        try:
            super().run(self.config.token, bot=self.config.bot)
        except discord.errors.LoginFailure as e:
            raise FatalError("Failed to authenticate: {}".format(e))

    async def _delete_msg(self, msg, delete):
        """
        Handler function for deleting messages after a period of time
        """
        await asyncio.sleep(delete)
        await self.safe_delete_message(msg)

    async def safe_edit_message(self, message, content, delete_after=0):
        """
        Allows editing a message safely
        """
        try:
            msg = await self.edit_message(message, content)
            if msg and delete_after:
                asyncio.ensure_future(self._delete_msg(msg, delete_after))
            return msg
        except discord.HTTPException:
            printError("Failed editing message: {}".format(message.id))

    async def safe_delete_message(self, message):
        """
        Allows deleting a message safely
        """
        try:
            await self.delete_message(message)
        except discord.HTTPException:
            printError("Failed deleting message: {}".format(message.id))
        except discord.Forbidden:
            printError(
                "No permission to delete message: {}".format(message.id))

    async def safe_send_message(self, dest, content, delete_after=0):
        """
        Allows sending a message safely
        """
        try:
            msg = await self.send_message(dest, content)
            if msg and delete_after:
                asyncio.ensure_future(self._delete_msg(msg, delete_after))
            return msg
        except discord.HTTPException:
            printError("Failed sending message to: {}".format(dest.name))
        except discord.Forbidden:
            printError(
                "No permission to send message to: {}".format(dest.name))
        except discord.NotFound:
            printError(
                "Cannot send message to invalid destination: {}".format(dest.name))

    async def _handle_autoresponses(self, message):
        """
        Handler function for autoresponses
        """
        if message.channel.id in self.responses.keys():
            responses = self.responses[str(message.channel.id)]
            for r in responses:
                if r in message.content:
                    print("{0}{1.name} ({1.id}) {2}Response: {0}{3}".format(
                        self.color, message.author, Fore.RESET, r))
                    await self.safe_send_message(message.channel, responses[r])

    async def on_ready(self):
        """
        Called when the bot is connected successfully
        """
        if self.user.bot:
            print(self.color + """Warning: Detected you are running this bot on an oAuth account
While not intended, it is possible for this bot to run on these accounts.
Some commands may work weird, and additionally, they can be triggered by everyone""" + Fore.RESET)
        print('Logged in as {}'.format(self.user))
        if self.config.moderator:
            mods = []
            for u in self.config.moderator:
                user = discord.utils.get(self.get_all_members(), id=u)
                if user:
                    name = "{}#{}".format(user.name, user.discriminator)
                    mods.append(name)
                else:
                    mods.append(id)
            mods = ', '.join(mods)
            print('{}Moderators: {}{}'.format(self.color, mods, Fore.RESET))
        if self.blacklist:
            blacklist = []
            for u in self.blacklist:
                user = discord.utils.get(self.get_all_members(), id=u)
                if user:
                    name = "{}#{}".format(user.name, user.discriminator)
                    blacklist.append(name)
                else:
                    blacklist.append(id)
            blacklist = ', '.join(blacklist)
            print('{}Blacklisted: {}{}'.format(
                self.color, blacklist, Fore.RESET))
        print()

    async def on_message(self, message):
        """
        Called when any message is sent that the client can see
        """
        await self.wait_until_ready()  # Ensure that the client is ready

        if self.disabled:
            if message.author == self.user and message.content == "{}enable".format(self.config.prefix):
                # Don't do anything if the bot is disabled
                await self.cmd_enable(message)
            return

        if message.author.id in self.blacklist:
            # Don't do anything if the user is blacklisted
            return

        if message.content == "{}disable".format(self.config.prefix):
            if message.author == self.user or message.author.id in self.config.moderator:
                await self.cmd_disable(message)
                return

        if message.author != self.user:
            if not message.channel.is_private and self.config.autorespond:
                await self._handle_autoresponses(message)
            # Don't do anything else if the message wasn't sent by the user
            if not self.user.bot:
                return

        content = message.content.strip()
        if not content.startswith(self.config.prefix):
            # Don't do anything else if the message doesn't have the prefix
            return

        command, *args = content.split()
        command = command[len(self.config.prefix):].lower().strip()

        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            return  # If the command isn't actually a command, do nothing

        print("{0}{1.name} ({1.id}) {2}{3}".format(
            self.color, message.author, Fore.RESET, content))

        argspec = inspect.signature(handler)
        params = argspec.parameters.copy()

        # noinspection PyBroadException
        try:
            handler_kwargs = {}
            if params.pop('message', None):
                handler_kwargs['message'] = message

            if params.pop('channel', None):
                handler_kwargs['channel'] = message.channel

            if params.pop('author', None):
                handler_kwargs['author'] = message.author

            if params.pop('server', None):
                handler_kwargs['server'] = message.server

            if params.pop('player', None):
                handler_kwargs['player'] = await self.get_player(message.channel)

            if params.pop('user_mentions', None):
                handler_kwargs['user_mentions'] = list(
                    map(message.server.get_member, message.raw_mentions))

            if params.pop('channel_mentions', None):
                handler_kwargs['channel_mentions'] = list(
                    map(message.server.get_channel, message.raw_channel_mentions))

            if params.pop('voice_channel', None):
                handler_kwargs[
                    'voice_channel'] = message.server.me.voice_channel

            if params.pop('leftover_args', None):
                handler_kwargs['leftover_args'] = args

            args_expected = []
            for key, param in list(params.items()):
                doc_key = '[%s=%s]' % (
                    key, param.default) if param.default is not inspect.Parameter.empty else key
                args_expected.append(doc_key)

                if not args and param.default is not inspect.Parameter.empty:
                    params.pop(key)
                    continue

                if args:
                    arg_value = args.pop(0)
                    handler_kwargs[key] = arg_value
                    params.pop(key)

            if params:
                await self._check_bot(message, ":warning: Invalid usage: `{}{}`".format(self.config.prefix, command), delete_after=10)
                return

            response = await handler(**handler_kwargs)
        except Exception:
            traceback.print_exc()

    async def _check_bot(self, msgobj, str_to_send, delete_after=0):
        if not self.user.bot and msgobj.author == self.user:
            return await self.safe_edit_message(msgobj, str_to_send, delete_after)
        else:
            return await self.safe_send_message(msgobj.channel, str_to_send, delete_after)

    def _time_since(self, time1, time2):
        """
        Helper function to display a prettier output of how much time has passed
        """
        rawdiff = time1 - time2
        time = ""
        secdiff = int(rawdiff.seconds%60)
        mindiff = int(rawdiff.seconds/60%60)
        hourdiff = int(rawdiff.seconds/60/60)
        if hourdiff > 0:
            if hourdiff == 1:
                time += "{} hour and ".format(hourdiff)
            else:
                time += "{} hours and ".format(hourdiff)
        if mindiff > 0:
            if mindiff == 1:
                time += "{} minute and ".format(mindiff)
            else:
                time += "{} minutes and ".format(mindiff)
        if secdiff == 1:
            time += "{} second".format(secdiff)
        else:
            time += "{} seconds".format(secdiff)
        return time


    async def cmd_eval(self, message, args, leftover_args):
        """
        Evaluates code
        """
        starttime = datetime.datetime.now()
        args = ' '.join([args, *leftover_args])
        try:
            result = eval(args)
            if inspect.isawaitable(result):
                result = await result
        except SyntaxError:
            try:
                result = exec(args)
            except Exception:
                result = traceback.format_exc()
        except Exception:
            result = traceback.format_exc()
        endtime = datetime.datetime.now()
        diff = endtime - starttime
        return await self._check_bot(message, "```python\n# Input\n{}\n# Output\n{}\n```\n:stopwatch: Time taken: `{}`".format(args, result, diff))

    async def cmd_discrim(self, message, discrim):
        """
        Shows all visible members that have matching discriminator
        For farming discriminator changes
        """
        matches = []
        for m in self.get_all_members():
            if m.discriminator == discrim and m != self.user:
                if m.name not in matches:
                    matches.append(m.name)
        if not matches:
            return await self._check_bot(message, ":warning: No names found with discriminator **{}**".format(discrim), delete_after=30)
        matches = '`, `'.join(matches)
        return await self._check_bot(message, ":label: Names with discriminator **{}**\n`{}`".format(discrim, matches))

    async def cmd_emoji(self, message, name):
        """
        Shows information about a custom emoji
        """
        emoji = discord.utils.get(self.get_all_emojis(), name=name)
        if not emoji:
            return await self._check_bot(message, ":warning: No emoji found with name **{}**".format(name), delete_after=30)
        servers = []
        for s in self.servers:
            semoji = discord.utils.get(s.emojis, name=name)
            if semoji:
                servers.append(s.name)
        servers = '`, `'.join(servers)
        response = ":performing_arts: **{0.name}**\nServers: `{1}`\n{0.url}".format(
            emoji, servers)
        return await self._check_bot(message, response)

    async def cmd_snowflake(self, message, id):
        """
        Shows the creation time in UTC of a Discord ID
        """
        time = discord.utils.snowflake_time(id)
        if not time:
            return await self._check_bot(message, ":warning: No user found with ID **{}**".format(id), delete_after=30)
        user = discord.utils.get(self.get_all_members(), id=id)
        if user:
            return await self._check_bot(message, ":snowflake: {0.name}#{0.discriminator} (**{0.id}**) was created at: `{1}`".format(user, time))
        else:
            return await self._check_bot(message, ":snowflake: **{}** was created at: `{}`".format(id, time))

    async def cmd_status(self, message, status, leftover_args):
        """
        Changes the user's status
        """
        status = ' '.join([status, *leftover_args])
        try:
            await self.change_status(game=discord.Game(name=status))
        except discord.InvalidArgument:
            printError(
                'Invalid argument when changing status to: {}'.format(status))
        return await self._check_bot(message, ":speech_left: Status set to **{}**".format(status), delete_after=30)

    async def cmd_strike(self, message, content, leftover_args):
        """
        Helper command to strike through text
        """
        content = ' '.join([content, *leftover_args])
        return await self._check_bot(message, "~~{}~~".format(content))

    async def cmd_italics(self, message, content, leftover_args):
        """
        Helper command to italicalize text
        """
        content = ' '.join([content, *leftover_args])
        return await self._check_bot(message, "*{}*".format(content))

    async def cmd_bold(self, message, content, leftover_args):
        """
        Helper command to strike through text
        """
        content = ' '.join([content, *leftover_args])
        return await self._check_bot(message, "**{}**".format(content))

    async def _check_for_key(self, data, key):
        """
        Checks a dictionary for a key
        """
        for k in data.keys():
            if k == key:
                return k
        return

    async def cmd_tag(self, message, tag, leftover_args):
        """
        Trigger a tag
        """
        tag = ' '.join([tag, *leftover_args])
        key = await self._check_for_key(self.tags, tag)
        if key:
            response = self.tags[tag]
            return await self._check_bot(message, response)
        return await self._check_bot(message, ":warning: No tag found: **{}**".format(tag), delete_after=30)

    @no_private
    async def cmd_reload(self, message):
        """
        Reloads the bot's files
        """
        self._reload()
        return await self._check_bot(message, ":package: Reloaded", delete_after=5)

    async def cmd_echo(self, message, id):
        """
        Tries to obtain a message via ID and send it
        This will fail if the client receives a lot of messages
        By default, discord.py stores 5000 messages
        """
        msg = discord.utils.get(self.messages, id=id)
        if not msg:
            return await self._check_bot(message, ":warning: Can't find message: **{}**".format(id), delete_after=30)
        now = datetime.datetime.utcnow()
        time = self._time_since(now, msg.timestamp)
        response = ":information_source: Posted by **{}** in <#{}> `{} ago`\n――――――――――――――――――――――――\n{}".format(msg.author, msg.channel.id, time, msg.content)
        return await self._check_bot(message, response)

    async def cmd_msginfo(self, message, id):
        """
        Tries to show different information about a message
        This will fail if the client recieves a lot of messages
        """
        msg = discord.utils.get(self.messages, id=id)
        if not msg:
            return await self._check_bot(message, ":warning: Can't find message: **{}**".format(id), delete_after=30)
        if msg.channel.is_private:
            server = "Private message"
        else:
            server = msg.server.name
        if not msg.channel.name:
            channel = msg.channel.user
        else:
            channel = "<#{}>".format(msg.channel.id)
        return await self._check_bot(message, ":information_source: Here's the info on that message:\nServer: {}\nChannel: {}\nAuthor: {}\nTime sent in UTC: {}\nContent:\n{}".format(server, channel, msg.author, msg.timestamp, msg.clean_content))

    async def cmd_flip(self, message):
        """
        Flips an imaginary object
        """
        return await self._check_bot(message, ":trophy: **{}** wins!".format(random.choice(self.config.flip)))

    async def cmd_random(self, message, number):
        """
        Returns a random number between 1 and the number given
        """
        try:
            number = int(number)
        except ValueError:
            return await self._check_bot(message, ":warning: **{}** could not be converted to a number".format(number), delete_after=30)

        rand = range(number)
        return await self._check_bot(message, ":trophy: Number generated: **{}**".format(int(random.choice(rand) + 1)))

    async def cmd_removetag(self, message, name):
        """
        Removes a tag with specified name
        """
        if name not in self.tags.keys():
            return await self._check_bot(message, ":warning: The tag **{}** doesn't exist".format(name), delete_after=30)
        del self.tags[name]
        self._reload(save=True)
        return await self._check_bot(message, ":white_check_mark: Removed tag **{}**".format(name))

    async def cmd_cleartags(self, message):
        """
        Clears the entire list of tags
        Destructive - will not ask for confirmation
        """
        self.tags.clear()
        self._reload(save=True)
        return await self._check_bot(message, ":white_check_mark: Cleared all tags")

    async def safe_edit_server(self, server, **kwargs):
        """
        Safely edit a server
        """
        try:
            await self.edit_server(server, **kwargs)
            return True
        except discord.Forbidden:
            printError("No permission to edit: {}".format(server))
            return False
        except discord.NotFound:
            printError(
                "Server wasn't found while trying to edit it: {}".format(server))
            return False
        except discord.HTTPException:
            printError("Editing the server failed: {}".format(server))
            return False

    @no_private
    async def cmd_serverregion(self, message, server, region):
        """
        Switches server region to given region
        """
        regionattr = getattr(discord.ServerRegion, region, None)
        if not regionattr:
            regions = []
            for i in dir(discord.ServerRegion):
                if "__" in i:
                    continue
                regions.append(i)
            regions = '`, `'.join(regions)
            return await self._check_bot(message, ":warning: Invalid region. Valid regions are:\n`{}`".format(regions))
        edit = await self.safe_edit_server(server, region=region)
        if not edit:
            return await self._check_bot(message, ":warning: Problem editing server region to **{}**".format(region), delete_after=30)
        return await self._check_bot(message, ":white_check_mark: Changed server region to **{}**".format(region))

    @no_private
    async def cmd_servername(self, message, server, name, leftover_args):
        """
        Renames a server
        """
        name = ' '.join([name, *leftover_args])
        edit = await self.safe_edit_server(server, name=name)
        if not edit:
            return await self._check_bot(message, ":warning: Problem changing server name to **{}**".format(name), delete_after=30)
        return await self._check_bot(message, ":white_check_mark: Changed server name to **{}**".format(name))

    async def cmd_disable(self, message):
        """
        Disables the bot temporarily
        """
        self.disabled = True
        print(self.color + "{} disabled the bot".format(message.author))
        return await self._check_bot(message, ":white_check_mark:", delete_after=5)

    async def cmd_enable(self, message):
        """
        Re-enables the bot (when disabled)
        """
        self.disabled = False
        print(self.color + "{} enabled the bot".format(message.author))
        return await self._check_bot(message, ":white_check_mark:", delete_after=5)

    async def _handle_timer(self, timer_dict):
        """
        Handler for the timer command
        """
        await asyncio.sleep(int(timer_dict['totalseconds']))
        if timer_dict['author'] != self.user:
            await self.safe_send_message(timer_dict['channel'], ":stopwatch: {}, your `{}:{}` timer finished".format(timer_dict['author'].mention, timer_dict['minutes'], timer_dict['seconds']))
        else:
            await self.safe_send_message(timer_dict['channel'], ":stopwatch: `{}:{}` timer finished".format(timer_dict['minutes'], timer_dict['seconds']))
        self.timers.remove(timer_dict)

    async def cmd_timer(self, message, time):
        """
        Sets a timer, which will send another message in the channel when complete
        """
        if ":" not in time:
            return await self._check_bot(message, self.timer_failure, delete_after=30)
        minutes = time.rpartition(':')[0]
        seconds = time.split(":", 1)[1]
        if ":" in minutes or ":" in seconds:
            return await self._check_bot(message, self.timer_failure, delete_after=30)
        try:
            minutes = int(minutes)
            seconds = int(seconds)
        except ValueError:
            return await self._check_bot(message, self.timer_failure, delete_after=30)

        time_to_wait = datetime.timedelta(minutes=minutes, seconds=seconds)
        totalseconds = time_to_wait.total_seconds()
        timer_dict = {'author': message.author, 'channel': message.channel, 'server': message.server,
                      'timestamp': message.timestamp, 'minutes': minutes, 'seconds': seconds, 'totalseconds': totalseconds}
        self.timers.append(timer_dict)
        asyncio.ensure_future(self._handle_timer(timer_dict))
        return await self._check_bot(message, ":white_check_mark: Timer set for **{}** minutes, **{}** seconds".format(minutes, seconds))

    async def cmd_listtimers(self, message):
        """
        Provides a list of all active timers
        """
        response = ":stopwatch: All **running** timers\n```"
        if self.timers:
            for t in self.timers:
                response += "\n{} - {}:{} - {}/{} - {}".format(
                    t['author'], t['minutes'], t['seconds'], t['server'], t['channel'], t['timestamp'])
        else:
            response += "\nNone"
        response += "\n```"
        return await self._check_bot(message, response)

    def _get_json_from_url(self, url):
        """
        Utility function for getting JSON from a URL
        """
        response = urllib.request.urlopen(url).read()
        data = json.loads(response.decode('utf-8'))
        return data

    async def cmd_cat(self, message):
        """
        Pastes the link to a random cat picture
        Uses random.cat API
        """
        data = self._get_json_from_url('http://random.cat/meow')
        url = data['file']
        return await self._check_bot(message, url)

    def _get_config_attr(self, attribute):
        attr = getattr(self.config, attribute, None)
        return attr

    async def cmd_holidays(self, message, country=None):
        """
        Returns information about upcoming holidays
        Uses the HolidayApi
        """
        if not self._get_config_attr('holidays_key'):
            return await self._check_bot(message, ":warning: You must specify an API key in the config", delete_after=30)

        now = datetime.datetime.now()
        if country:
            country = country.upper()
            if country not in self.holidays_countries:
                valid = '`, `'.join(self.holidays_countries)
                return await self._check_bot(message, ":warning: Invalid country. Valid countries are: `{}`".format(valid), delete_after=30)
        else:
            country = self.config.holidays_country
        data = self._get_json_from_url('https://holidayapi.com/v1/holidays?country={}&year={}&month={}&day={}&upcoming=True&key={}'.format(
            country, now.year, now.month, now.day, self.config.holidays_key))
        if data['status'] != 200:
            printError(
                "Couldn't get holiday info, returned {}".format(data['status']))
            return await self._check_bot(message, ":warning: An error occurred while obtaining holidays: {}".format(data['status']), delete_after=30)
        response = "Upcoming holidays for **{}**\n".format(
            country)
        for h in data['holidays']:
            if h['public']:
                holiday_type = 'Public holiday'
            else:
                holiday_type = 'Holiday'
            response += ":island: **{}** - {} - *{}*".format(
                h['name'], h['date'], holiday_type)
        return await self._check_bot(message, response)

    async def cmd_responses(self, message):
        """
        Returns a list of all autoresponses that have been set up
        """
        if not self.config.autorespond:
            return await self._check_bot(message, ":warning: Autoresponses have been disabled in the config", delete_after=30)
        if not self.responses:
            return await self._check_bot(message, ":warning: No autoresponses have been setup", delete_after=30)
        response = ":information_source: List of **autoresponses**"
        for c in self.responses.keys():
            channel = discord.utils.get(self.get_all_channels(), id=c)
            if not channel:
                channel = c
            else:
                channel = '<#{}> on {}'.format(channel.id, channel.server)
            response += "\n{}: ".format(channel)
            if not self.responses[c].keys():
                response += "None"
            else:
                channel_list = []
                for r in self.responses[c].keys():
                    channel_list.append(r)
                channel_list = '`, `'.join(channel_list)
                response += "`{}`".format(channel_list)
        return await self._check_bot(message, response)

    async def cmd_tags(self, message):
        """
        Returns a list of all tags that have been set up
        """
        if not self.tags:
            return await self._check_bot(message, ":warning: No tags have been setup", delete_after=30)
        response = ":information_source: List of **tags**"
        if not self.tags.keys():
            response += "\nNone"
        else:
            tags = []
            for i in self.tags.keys():
                tags.append(i)
            tags = '`, `'.join(tags)
            response += "\n`{}`".format(tags)
        return await self._check_bot(message, response)

    async def cmd_addtag(self, message, name, leftover_args):
        """
        Adds a tag with specified name and content
        """
        if not leftover_args:
            return await self._check_bot(message, ":warning: You must specify content for your tag **{}**".format(name))
        content = ' '.join([*leftover_args])
        if name in self.tags.keys():
            return await self._check_bot(message, ":warning: A tag with the name **{}** already exists".format(name), delete_after=30)
        self.tags[name] = content
        self._reload(save=True)
        return await self._check_bot(message, ":white_check_mark: Added tag **{}**".format(name))

    async def cmd_githubuser(self, message, name):
        """
        Get information about a GitHub user
        Uses the GitHub API v3
        """
        try:
            data = self._get_json_from_url('https://api.github.com/users/{}'.format(name))
        except urllib.error.HTTPError as e:
            return await self._check_bot(message, ":warning: Problem getting GitHub info for **{}**: `{}`".format(name, e))
        response = "```py\nUsername: {}\nName: {}\nWebsite: {}\nLocation: {}\nPublic repos: {}\nPublic gists: {}\nFollowers: {}\nFollowing: {}".format(
            data['login'], data['name'], data['blog'], data['location'], data['public_repos'], data['public_gists'], data['followers'], data['following'])
        response += "\n```\n{}".format(data['html_url'])
        return await self._check_bot(message, response)

    async def cmd_generatename(self, message, gender=None):
        """
        Generate a random name. Takes an optional gender.
        Uses the UINames API
        """
        if gender:
            gender = gender.lower()
            if gender not in self.name_genders:
                return await self._check_bot(message, ":warning: Invalid gender")
        if gender:
            data = self._get_json_from_url('http://uinames.com/api/?gender={}'.format(gender))
        else:
            data = self._get_json_from_url('http://uinames.com/api/')

        response = "**{} {}** - Gender: `{}` - Region: `{}`".format(data['name'], data['surname'], data['gender'], data['region'])
        return await self._check_bot(message, response)
