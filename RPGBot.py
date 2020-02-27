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

import asyncio
import datetime
import logging
import os
import sys
import ujson as json
from io import BytesIO
from collections import Counter, defaultdict
from random import choice, sample, seed

import aiohttp
import discord
import psutil
from datadog import ThreadStats
from datadog import initialize as init_dd
from discord.ext import commands

from pyhtml import server
import cogs
from cogs.utils import db, data
from cogs.utils.translation import _

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    uvloop = None

if os.name == "nt":
    sys.argv.append("debug")
if os.getcwd().endswith("rpgtest"):
    sys.argv.append("debug")


class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, game=discord.Game(name="rp!help for help!"), **kwargs)
        self.prefixes = {}
        self.owner_id = 122739797646245899
        self.lounge_id = 166349353999532035
        self.uptime = datetime.datetime.utcnow()
        self.commands_used = Counter()
        self.server_commands = Counter()
        self.socket_stats = Counter()
        self.shutdowns = []
        self.lotteries = dict()
        self.in_character = defaultdict(lambda: defaultdict(str))

        self.logger = logging.getLogger('discord')  # Discord Logging
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename=os.path.join('resources', 'discord.log'), encoding='utf-8',
                                           mode='w')
        self.handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(self.handler)

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.shutdowns.append(self.shutdown)

        with open("resources/auth") as af:
            self._auth = json.loads(af.read())

        with open("resources/dnditems.json", 'r') as dndf:
            self.dnditems = json.loads(dndf.read())

        with open("resources/dnditems.json", 'r') as dndf2:
            self.dndmagic = json.loads(dndf2.read())

        with open("resources/pokemonitems.json", 'r') as dndf3:
            self.pokemonitems = json.loads(dndf3.read())

        with open("resources/starwars.json", 'r') as swf:
            self.switems = json.loads(swf.read())

        if 'debug' not in sys.argv:
            self.httpserver = server.API(self)
            self.loop.create_task(self.httpserver.host())

        self.db: db.Database = db.Database(self)
        self.di: data.DataInteraction = data.DataInteraction(self)
        self.default_udata = data.default_user
        self.default_servdata = data.default_server
        self.rnd = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        with open("resources/patrons.json") as pj:
            self.patrons = {int(k): v for k, v in json.loads(pj.read()).items()}

        with open("resources/newtranslations.json", 'rb') as trf:
            self.translations = json.loads(trf.read().decode())
        self.languages = ["en", "fr", "de", "ru", "es"]

        with open("resources/blacklist.json") as blf:
            self.blacklist = json.loads(blf.read())

        with open("savedata/prefixes.json") as prf:
            self.prefixes = json.loads(prf.read())

        icogs = [
            cogs.admin.Admin(self),
            cogs.team.Team(self),
            cogs.economy.Economy(self),
            cogs.inventory.Inventory(self),
            cogs.settings.Settings(self),
            cogs.misc.Misc(self),
            cogs.characters.Characters(self),
            cogs.pets.Pets(self),
            cogs.groups.Groups(self),
            cogs.user.User(self),
            cogs.salary.Salary(self),
            cogs.map.Mapping(self),
            cogs.backups.Backups(self),
        ]
        for cog in icogs:
            self.add_cog(cog)

        # self.loop.create_task(self.start_serv())

        init_dd(self._auth[3], self._auth[4])
        self.stats = ThreadStats()
        self.stats.start()

        self._first = True

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        if self._first:
            self.loop.create_task(self.update_stats())
            self._first = False

    async def on_message(self, msg):
        if msg.author.id not in self.blacklist:
            """
            if False and msg.guild:
                prefixes = await self.di.get_cmd_prefixes(msg.guild)
                for cmd, prefix in prefixes.items():
                    if msg.content.startswith(prefix):
                        msg.content = msg.content.replace(prefix, "rp!" + (cmd.replace(".", " ")) + " ", 1)
                        break
            """

            ctx = await self.get_context(msg)
            await self.invoke(ctx)

            if ctx.command is None and ctx.guild:
                if ctx.guild.id in self.in_character:
                    if ctx.author.id in self.in_character[ctx.guild.id]:
                        char = self.in_character[ctx.guild.id][ctx.author.id]
                        hooks = await ctx.guild.webhooks()
                        hook = discord.utils.get(hooks, name=char)
                        if hook is None:
                            # await ctx.send(await _(ctx, "Webhook missing!"))
                            del self.in_character[ctx.guild.id][ctx.author.id]
                            return
                        content = msg.content
                        files = msg.attachments
                        dfiles = []
                        for f in files:
                            dio = BytesIO()
                            await f.save(dio)
                            dfiles.append(discord.File(dio, f.filename, spoiler=f.is_spoiler()))
                        embeds = msg.embeds
                        if hook.channel.id != msg.channel.id:
                            await hook.delete()
                            hook = await msg.channel.create_webhook(name=char)
                        await msg.delete()
                        url = (await self.di.get_character(ctx.guild, char)).meta.get("icon")
                        await hook.send(content, avatar_url=url,
                                        files=dfiles, embeds=embeds)

    async def update_stats(self):
        url = "https://bots.discord.pw/api/bots/{}/stats".format(self.user.id)
        while not self.is_closed():
            payload = json.dumps(dict(server_count=len(self.guilds))).encode()
            headers = {'authorization': self._auth[1], "Content-Type": "application/json"}

            async with self.session.post(url, data=payload, headers=headers) as response:
                await response.read()

            url = "https://discordbots.org/api/bots/{}/stats".format(self.user.id)
            payload = json.dumps(dict(server_count=len(self.guilds))).encode()
            headers = {'authorization': self._auth[2], "Content-Type": "application/json"}

            async with self.session.post(url, data=payload, headers=headers) as response:
                await response.read()

            await asyncio.sleep(14400)

    async def on_command(self, ctx):
        self.stats.increment("RPGBot.commands", tags=["RPGBot:commands"], host="scw-8112e8")
        self.stats.increment(f"RPGBot.commands.{str(ctx.command).replace(' ', '.')}", tags=["RPGBot:commands"],
                             host="scw-8112e8")
        self.commands_used[ctx.command] += 1
        if self.commands_used[ctx.command] % 100 == 0:
            seed(self.socket_stats["PRESENCE_UPDATE"])
        if isinstance(ctx.author, discord.Member):
            self.server_commands[ctx.guild.id] += 1
            if ctx.guild.id not in self.patrons:
                if (self.server_commands[ctx.guild.id] % 50) == 0:
                    await ctx.send(await _(ctx,
                                           "This bot costs $300/yr to run. If you like the utilities it provides,"
                                           " consider buying me a coffee <https://ko-fi.com/henrys>"
                                           " or subscribe as a Patron <https://www.patreon.com/henry232323>"
                                           " Also consider upvoting the bot to help us grow <https://discordbots.org/bot/305177429612298242>"
                                           ))

            if await self.di.get_exp_enabled(ctx.guild):
                add = choice([0, 0, 0, 0, 0, 1, 1, 2, 3])
                fpn = ctx.command.full_parent_name.lower()
                if fpn:
                    values = {
                        "character": 2,
                        "inventory": 1,
                        "economy": 1,
                        "pet": 2,
                        "guild": 2,
                        "team": 1,
                    }
                    add += values.get(fpn, 0)

                if add:
                    await asyncio.sleep(4)
                    r = await self.di.add_exp(ctx.author, add)
                    if r is not None:
                        await ctx.message.add_reaction("\u23EB")
            time = await self.di.get_delete_time(ctx.guild)
            if time:
                await asyncio.sleep(time)
                await ctx.message.delete()

    async def on_member_join(self, member):
        amount = await self.di.get_guild_start(member.guild)
        if amount:
            await self.di.set_eco(member, amount)

    async def on_member_remove(self, member):
        setting = await self.di.get_leave_setting(member.guild)
        if setting:
            await self.db.update_user_data(member, {})

    async def on_command_error(self, ctx, exception):
        self.stats.increment("RPGBot.errors", tags=["RPGBot:errors"], host="scw-8112e8")
        logging.info(f"Exception in {ctx.command} {ctx.guild}:{ctx.channel} {exception}")
        try:
            if isinstance(exception, commands.MissingRequiredArgument):
                await ctx.send(f"```{exception}```")
            elif isinstance(exception, TimeoutError):
                await ctx.send(await _(ctx, "This operation ran out of time! Please try again"))
            elif isinstance(exception, discord.Forbidden):
                await ctx.send(await _(ctx, "Error: This command requires the bot to have permission to send links."))
            else:
                await ctx.send(f"`{exception} If this is unexpected, please report this to the bot creator`")
        except discord.Forbidden:
            pass

    async def on_guild_join(self, guild):
        if guild.id in self.blacklist:
            await guild.leave()

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
        return f"{mem.used / 0x40_000_000:.2f}/{mem.total / 0x40_000_000:.2f}GB ({mem.percent}%)"

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
        if not len(print_string):
            return
        print_string = print_string[:-3]

        # Print the actual data
        fin = []
        for i, line in enumerate(lines):
            fin.append(print_string.format(*line))
            if i == 0 and separate_head:
                fin.append("-" * (sum(widths) + 3 * (len(widths) - 1)))

        return "\n".join(fin)

    async def shutdown(self):
        with open("savedata/prefixes.json", 'w') as prf:
            json.dump(self.prefixes, prf)

        await self.session.close()


prefixes = ['rp!', 'pb!', '<@305177429612298242> ', 'Rp!'] if "debug" not in sys.argv else 'rp$'
invlink = "https://discordapp.com/oauth2/authorize?client_id=305177429612298242&scope=bot&permissions=322625"
servinv = "https://discord.gg/UYJb8fQ"
sourcelink = "https://github.com/henry232323/RPGBot"
tutoriallink = "https://github.com/henry232323/RPGBot/blob/master/tutorial.md"
description = f"A Bot for assisting with RPG made by Henry#6174," \
              " with a working inventory, market and economy," \
              " team setups and characters as well. Each user has a server unique inventory and balance." \
              " Players may list items on a market for other users to buy." \
              " Users may create characters with teams from pets. " \
              "Server administrators may add and give items to the server and its users.```\n" \
              f"**Add to your server**: <{invlink}>\n" \
              f"**Support Server**: {servinv}\n" \
              f"**Command List**: <{sourcelink}>\n" \
              f"**Tutorial**: <{tutoriallink}>\n" \
              "**Support Me on Patreon**: <https://www.patreon.com/henry232323>\n```"

with open("resources/auth") as af:
    _auth = json.loads(af.read())


async def prefix(bot, msg):
    if msg.guild:
        # prefix = await bot.db.guild_item(msg.guild, "prefix")
        prefix = bot.prefixes.get(str(msg.guild.id), [])
        if isinstance(prefix, str):
            return prefixes + [prefix]
        else:
            return prefixes + prefix
    else:
        return prefixes


"""
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
"""

if "debug" in sys.argv:
    prefix = "rp$"

prp = Bot(command_prefix=prefix, description=description, pm_help=True, shard_count=7)
prp.run(_auth[0])
