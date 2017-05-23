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
import ujson as json
import logging
import discord
import psutil
import datetime
import aiohttp
import asyncio
from random import choice, sample
from discord.ext import commands
from collections import Counter

from kyoukai import Kyoukai
from kyoukai.asphalt import HTTPRequestContext, Response
from werkzeug.exceptions import HTTPException

from datadog import ThreadStats
from datadog import initialize as init_dd

import cogs
from cogs.utils import db, data

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

if os.name == "nt":
    sys.argv.append("debug")
if os.getcwd().endswith("rpgtest"):
    sys.argv.append("debug")


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, game=discord.Game(name="rp!help for help!"), **kwargs)
        self.owner_id = 122739797646245899
        self.lounge_id = 166349353999532035
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = Counter()
        self.server_commands = Counter()
        self.socket_stats = Counter()
        self.shutdowns = []
        self.lotteries = dict()

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
            "Pokemon": cogs.Pokemon.Pokemon(self),
            "Groups": cogs.Groups.Groups(self),
            "User": cogs.User.User(self)
        }

        self.db = db.Database(self)
        self.di = data.DataInteraction(self)
        self.default_udata = data.default_user
        self.default_servdata = data.default_server
        self.rnd = "1234567890abcdefghijklmnopqrstuvwxyz"

        init_dd(self._auth[3], self._auth[4])
        self.stats = ThreadStats()
        self.stats.start()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        self.loop.create_task(self.start_serv())
        # self.remove_command("help")

        await self.db.connect()

        for cog in self._cogs.values():
            self.add_cog(cog)

        await self.update_stats()

    async def update_stats(self):
        url = "https://bots.discord.pw/api/bots/{}/stats".format(self.user.id)
        payload = json.dumps(dict(server_count=len(self.guilds))).encode()
        headers = {'authorization': self._auth[1], "Content-Type": "application/json"}

        async with self.session.post(url, data=payload, headers=headers) as response:
            await response.read()

        url = "https://discordbots.org/api/bots/{}/stats".format(self.user.id)
        payload = json.dumps(dict(server_count=len(self.guilds))).encode()
        headers = {'authorization': self._auth[2], "Content-Type": "application/json"}

        async with self.session.post(url, data=payload, headers=headers) as response:
            await response.read()

        self.loop.call_later(14400, lambda: asyncio.ensure_future(self.update_stats()))

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_command(self, ctx):
        self.stats.increment("RPGBot.commands", tags=["RPGBot:commands"], host="scw-8112e8")
        self.stats.increment(f"RPGBot.commands.{str(ctx.command).replace(' ', '.')}", tags=["RPGBot:commands"], host="scw-8112e8")
        self.commands_used[ctx.command] += 1
        if isinstance(ctx.author, discord.Member):
            self.server_commands[ctx.guild.id] += 1
            if not (self.server_commands[ctx.guild.id] % 50):
                await ctx.send(
                    "This bot costs $130/yr to run. If you like the utilities it provides, consider buying me a coffee https://ko-fi.com/henrys"
                )

            add = choice([0, 0, 0, 0, 0, 0, 1, 1, 2])
            fpn = ctx.command.full_parent_name
            if fpn:
                if fpn == "settings":
                    return
                elif fpn == "character":
                    add += 2
                elif fpn == "inventory":
                    add += 1
                elif fpn == "economy":
                    add += 1
                elif fpn == "pokemon":
                    add += 2
                elif fpn == "guild":
                    add += 2

            if add:
                await asyncio.sleep(3)
                r = await self.di.add_exp(ctx.author, add)
                if r is not None:
                    await ctx.send(f"{ctx.author.mention} is now level {r}!")

    async def on_command_error(self, ctx, exception):
        self.stats.increment("RPGBot.errors", tags=["RPGBot:errors"], host="scw-8112e8")
        logging.info(f"Exception in {ctx.command} {ctx.guild}:{ctx.channel} {exception}")
        if isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send(f"`{exception}`")
        else:
            await ctx.send(f"`{exception}`")

    async def on_guild_join(self, guild):
        if sum(1 for m in guild.members if m.bot) / guild.member_count >= 3/4:
            try:
                await guild.default_channel.send("This server has too many bots! I'm just going to leave if thats alright")
            finally:
                await guild.leave()
        else:
            self.stats.increment("RPGBot.guilds", tags=["RPGBot:guilds"], host="scw-8112e8")

    async def on_guild_leave(self, guild):
        self.stats.increment("RPGBot.guilds", -1, tags=["RPGBot:guilds"], host="scw-8112e8")

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

    def randsample(self):
        return "".join(sample(self.rnd, 6))

    @staticmethod
    def get_exp(level):
        return int(0.1 * level ** 2 + 5 * level + 4)

    @staticmethod
    def get_ram():
        """Get the bot's RAM usage info."""
        mem = psutil.virtual_memory()
        return f"{mem.used:.2f}/{mem.total:.2f}GB ({mem.percent}%)"

    @staticmethod
    def format_table(lines, separate_head=True):
        """Prints a formatted table given a 2 dimensional array"""
        # Count the column width
        widths = []
        for line in lines:
            for i, size in enumerate([len(x) for x in line]):
                while i >= len(widths):
                    widths.append(0)
                if size > widths[i]:
                    widths[i] = size

        # Generate the format string to pad the columns
        print_string = ""
        for i, width in enumerate(widths):
            print_string += "{" + str(i) + ":" + str(width) + "} | "
        if (len(print_string) == 0):
            return
        print_string = print_string[:-3]

        # Print the actual data
        fin = []
        for i, line in enumerate(lines):
            fin.append(print_string.format(*line))
            if (i == 0 and separate_head):
                fin.append("-" * (sum(widths) + 3 * (len(widths) - 1)))

        return "\n".join(fin)

    async def shutdown(self):
        self.session.close()

    async def start_serv(self):
        self.webapp = Kyoukai(__name__)

        @self.webapp.route("/servers/<int:snowflake>/", methods=["GET"])
        async def getservinfo(ctx: HTTPRequestContext, snowflake: int):
            try:
                snowflake = int(snowflake)
                req = f"""SELECT info FROM servdata WHERE UUID = {snowflake};"""
                async with self.db._conn.acquire() as connection:
                    response = await connection.fetchval(req)
                return Response(response if response else json.dumps(self.default_servdata, indent=4), status=200)
            except:
                return HTTPException("Invalid snowflake!", Response("Failed to fetch info!", status=400))

        @self.webapp.route("/users/<int:snowflake>/", methods=["GET"])
        async def getuserinfo(ctx: HTTPRequestContext, snowflake: int):
            try:
                snowflake = int(snowflake)
                req = f"""SELECT info FROM userdata WHERE UUID = {snowflake};"""
                async with self.db._conn.acquire() as connection:
                    response = await connection.fetchval(req)
                return Response(response if response else json.dumps(self.default_udata, indent=4), status=200)
            except:
                return HTTPException("Invalid snowflake!", Response("Failed to fetch info!", status=400))

        await self.webapp.start('0.0.0.0', 1441)

prefix = ['rp!', 'pb!', '<@305177429612298242> '] if "debug" not in sys.argv else 'rp$'
invlink = "https://discordapp.com/oauth2/authorize?client_id=305177429612298242&scope=bot&permissions=322625"
servinv = "https://discord.gg/UYJb8fQ"
sourcelink = "https://github.com/henry232323/RPGBot"
description = f"RPGBot, a little discord bot by Henry#6174\n**Add to your server**: {invlink}\n**Support Server**: {servinv}\n**Source**: {sourcelink}"

with open("resources/auth") as af:
    _auth = json.loads(af.read())

prp = Bot(command_prefix=prefix, description=description, pm_help=True)
prp.run(_auth[0])
