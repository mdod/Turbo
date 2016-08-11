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
from colorama import Fore
from functools import wraps
from discord.ext.commands.bot import _get_variable

from .exceptions import FatalError, printError
from .config import Config


class Turbo(discord.Client):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self._reload()

        self.max_messages = self.config.messages

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
            return
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
                        Fore.YELLOW, message.author, Fore.RESET, r))
                    await self.safe_send_message(message.channel, responses[r])

    async def on_ready(self):
        """
        Called when the bot is connected successfully
        """
        if self.user.bot:
            print(Fore.YELLOW + """Warning: Detected you are running this bot on an oAuth account
While not intended, it is possible for this bot to run on these accounts.
Some commands may work weird, and additionally, they can be triggered by everyone""" + Fore.RESET)
        print('Logged in as {}\n'.format(self.user))

    async def on_message(self, message):
        """
        Called when any message is sent that the client can see
        """
        await self.wait_until_ready()  # Ensure that the client is ready

        if message.author != self.user:
            if not message.channel.is_private:
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
            Fore.YELLOW, message.author, Fore.RESET, content))

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
        if not self.user.bot:
            return await self.safe_edit_message(msgobj, str_to_send, delete_after)
        else:
            return await self.safe_send_message(msgobj.channel, str_to_send, delete_after)

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
        response = ":information_source: Posted by **{}** in <#{}> at `{}`\n――――――――――――――――――――――――\n{}".format(msg.author, msg.channel.id, msg.timestamp, msg.content)
        return await self._check_bot(message, response)

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
        try:
            await self.edit_server(server, **kwargs)
            return True
        except discord.Forbidden:
            printError("No permission to edit: {}".format(server))
            return False
        except discord.NotFound:
            printError("Server wasn't found while trying to edit it: {}".format(server))
            return False
        except discord.HTTPException:
            printError("Editing the server failed: {}".format(server))
            return False

    async def cmd_region(self, message, server, region):
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
