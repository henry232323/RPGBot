#!/usr/bin/env python3
# Copyright (c) 2016-2017, henry232323
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import sys
import json
import logging
import discord
import psutil
import datetime
import aiohttp
import asyncio
import asyncpg
from discord.ext import commands
from collections import Counter

import cogs
from cogs.utils import db, data

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

if os.name == "nt":
    sys.argv.append("debug")
if os.getcwd().endswith("poketest"):
    sys.argv.append("debug")

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner_id = 122739797646245899
        self.lounge_id = 166349353999532035
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = Counter()
        self.server_commands = Counter()
        self.socket_stats = Counter()
        self.shutdowns = []

        self.logger = logging.getLogger('discord')  # Discord Logging
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename=os.path.join('resources', 'discord.log'), encoding='utf-8', mode='w')
        self.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(self.handler)

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.shutdowns.append(self.shutdown)

        with open("resources/auth", 'r') as af:
            self._auth = json.loads(af.read())

        self._cogs = {
            "Admin": cogs.Admin.Admin(self),
            "Team": cogs.Team.Team(self),
            "Economy": cogs.Economy.Economy(self),
            "Inventory": cogs.Inventory.Inventory(self),
            "Settings": cogs.Settings.Settings(self),
            "Misc": cogs.Misc.Misc(self),
            "Characters": cogs.Characters.Characters(self),
            "Pokemon": cogs.Pokemon.Pokemon(self)
        }

        self.db = db.Database(self)
        self.di = data.DataInteraction(self)
        self.default_udata = data.default_user
        self.default_servdata = data.default_server

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        # self.remove_command("help")

        await self.db.connect()

        for cog in self._cogs.values():
            self.add_cog(cog)

        # await self.change_presence(game=discord.Game(name="pb!help for help!"))

        url = "https://bots.discord.pw/api/bots/{}/stats".format(self.user.id)
        payload = json.dumps(dict(server_count=len(self.guilds))).encode()
        headers = {'authorization': self._auth[1], "Content-Type": "application/json"}

        async with self.session.post(url, data=payload, headers=headers) as response:
            await response.read()

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_command_error(self, exception, ctx):
        if isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send(f"`{exception}`")
        else:
            await ctx.send(f"`{exception}`")

    async def on_socket_response(self, msg):
        self.socket_stats[msg.get('t')] += 1

    async def get_bot_uptime(self):
        """Get time between now and when the bot went up"""
        now = datetime.datetime.utcnow()
        delta = now - self.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if days:
            fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h} hours, {m} minutes, and {s} seconds'

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @staticmethod
    async def get_ram():
        """Get the bot's RAM usage info."""
        mu = psutil.Process(os.getpid()).memory_info().rss
        return mu / 1_000_000

    async def shutdown(self):
        self.session.close()

prefix = ['pb!'] if 'debug' not in sys.argv else ['pb$']
invlink = "https://discordapp.com/oauth2/authorize?client_id=305177429612298242&scope=bot&permissions=322625"
servinv = "https://discord.gg/UYJb8fQ"
description = "PokeRP Bot, a little discord bot by Henry#6174\n**Add to your server**: {}\n**Support Server**: {}".format(invlink, servinv)

with open("resources/auth") as af:
    _auth = json.loads(af.read())

prp = Bot(command_prefix=prefix, description=description, pm_help=True)
prp.run(_auth[0])
