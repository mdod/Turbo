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
from colorama import Fore

from .exceptions import FatalError, printError
from .config import Config


class Turbo(discord.Client):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self._reload()

    def _reload(self):
        """
        Reloads required files
        """
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

    async def safe_send_message(self, dest, content, tts=False, delete_after=0):
        """
        Allows sending a message safely
        """
        try:
            msg = await self.send_message(dest, content, tts=tts)
            if msg and delete_after:
                asyncio.ensure_future(self._delete_msg(msg, delete_after))
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
        print('Logged in as {}\n'.format(self.user))

    async def on_message(self, message):
        """
        Called when any message is sent that the client can see
        """
        await self.wait_until_ready()  # Ensure that the client is ready

        if message.channel.is_private:
            return  # Don't do anything else if the channel is private

        if message.author != self.user:
            await self._handle_autoresponses(message)
            # Don't do anything else if the message wasn't sent by the user
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
                await self.safe_edit_message(message, ":warning: Invalid usage: `{}{}`".format(self.config.prefix, command), delete_after=10)
                return

            response = await handler(**handler_kwargs)
        except Exception:
            traceback.print_exc()

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
        await self.safe_edit_message(message, "```python\n# Input\n{}\n# Output\n{}\n```\n:stopwatch: Time taken: `{}`".format(args, result, diff))

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
            return await self.safe_edit_message(message, ":warning: No names found with discriminator **{}**".format(discrim), delete_after=30)
        matches = '`, `'.join(matches)
        await self.safe_edit_message(message, ":label: Names with discriminator **{}**\n`{}`".format(discrim, matches))

    async def cmd_emoji(self, message, name):
        """
        Shows information about a custom emoji
        """
        emoji = discord.utils.get(self.get_all_emojis(), name=name)
        if not emoji:
            return await self.safe_edit_message(message, ":warning: No emoji found with name **{}**".format(name), delete_after=30)
        servers = []
        for s in self.servers:
            semoji = discord.utils.get(s.emojis, name=name)
            if semoji:
                servers.append(s.name)
        servers = '`, `'.join(servers)
        response = ":performing_arts: **{0.name}**\nServers: `{1}`\n{0.url}".format(
            emoji, servers)
        await self.safe_edit_message(message, response)

    async def cmd_snowflake(self, message, id):
        """
        Shows the creation time in UTC of a Discord ID
        """
        time = discord.utils.snowflake_time(id)
        if not time:
            return await self.safe_edit_message(message, ":warning: No user found with ID **{}**".format(id), delete_after=30)
        user = discord.utils.get(self.get_all_members(), id=id)
        if user:
            await self.safe_edit_message(message, ":snowflake: {0.name}#{0.discriminator} (**{0.id}**) was created at: `{1}`".format(user, time))
        else:
            await self.safe_edit_message(message, ":snowflake: **{}** was created at: `{}`".format(id, time))

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
        await self.safe_edit_message(message, ":speech_left: Status set to **{}**".format(status), delete_after=30)

    async def cmd_strike(self, message, content, leftover_args):
        """
        Helper command to strike through text
        """
        content = ' '.join([content, *leftover_args])
        await self.safe_edit_message(message, "~~{}~~".format(content))

    async def cmd_italics(self, message, content, leftover_args):
        """
        Helper command to italicalize text
        """
        content = ' '.join([content, *leftover_args])
        await self.safe_edit_message(message, "*{}*".format(content))

    async def cmd_bold(self, message, content, leftover_args):
        """
        Helper command to strike through text
        """
        content = ' '.join([content, *leftover_args])
        await self.safe_edit_message(message, "**{}**".format(content))

    async def cmd_tag(self, message, tag, leftover_args):
        """
        Trigger a tag
        """
        tag = ' '.join([tag, *leftover_args])
        if tag in self.tags.keys():
            response = self.tags[tag]
            await self.safe_edit_message(message, response)
        else:
            await self.safe_edit_message(message, ":warning: No tag found: **{}**".format(tag), delete_after=30)

    async def cmd_reload(self, message):
        """
        Reloads the bot's files
        """
        self._reload()
        await self.safe_edit_message(message, ":package: Reloaded", delete_after=5)
