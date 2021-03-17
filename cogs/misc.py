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

import psutil
import discord
from discord.ext import commands

import os
import io
import inspect
import datetime
from time import monotonic
from itertools import chain
from collections import Counter
from random import randint, choice

from .utils import checks
from .utils.translation import _


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["rollthedice", "dice", "roll"])
    async def rtd(self, ctx, *dice: str):
        """Roll a number of dice with given sides (ndx notation)
        Example: rp!rtd 3d7 2d4
        Optional Additions:
            Test for success by adding a >/<#
            Grab the top n rolls by adding ^n
            Grab the bottom n rolls by adding _n
            Add to the final roll by just adding a number (pos or neg)
            
            Examples of all:
                rp!rtd 8d8 -12 15 ^4 >32
                
                -> Roll failed (30 > 32) ([8 + 7 + 6 + 6] + -12 + 15) (Grabbed top 4 out of 8)"""
        try:
            dice = list(dice)
            rolls = dict()
            add = []
            rel = None
            pp = None
            pp2 = None

            for die in dice:
                try:
                    number, sides = die.split("d")
                    number, sides = int(number or "1"), int(sides)
                    if number > 10:
                        await ctx.send(await _(ctx, "Too many dice! Cant roll that many!"))
                        return
                    if sides > 1000:
                        await ctx.send(await _(ctx, "That die has much too many sides!"))
                        return

                    rolls[sides] = [randint(1, sides) for _ in range(number)]
                except ValueError:
                    try:
                        die = die.strip("+")
                        if len(die) <= 5:
                            add.append(int(die))
                        else:
                            await ctx.send(await _(ctx, "{} is too big a number!".format(die)))
                            return
                    except:
                        if die.startswith((">", "<")):
                            rel = die
                            _dir = rel.strip("<>")
                            if len(_dir) > 5:
                                await ctx.send(await _(ctx, "{} is too big a number!").format(_dir))
                                return
                            val = int(_dir)
                            type = rel[0]
                        elif die.startswith("^"):
                            _cur = die.strip("^")
                            if len(_cur) > 5:
                                await ctx.send((await _(ctx, "{} is too big a number!")).format(_cur))
                                return
                            pp = int(_cur)
                        elif die.startswith("_"):
                            _cur = die.strip("_")
                            if len(_cur) > 5:
                                await ctx.send((await _(ctx, "{} is too big a number!")).format(_cur))
                                return
                            pp2 = int(_cur)

            if pp:
                s = list(chain(*rolls.values()))
                rolls.clear()
                rolls[0] = list()
                for d in range(pp):
                    mx = max(s)
                    s.remove(mx)
                    rolls[0].append(mx)

            if pp2:
                s = list(chain(*rolls.values()))
                rolls.clear()
                rolls[0] = list()
                for d in range(pp2):
                    mn = min(s)
                    s.remove(mn)
                    rolls[0].append(mn)

            total = sum(sum(x) for x in rolls.values()) + sum(add)

            if rel is not None:
                if type == "<":
                    if total < val:
                        succ = await _(ctx, "succeeded")
                    else:
                        succ = await _(ctx, "failed")
                else:
                    if total > val:
                        succ = await _(ctx, "succeeded")
                    else:
                        succ = await _(ctx, "failed")

                fmt = "{roll} **{0}** ({1} {2} {3}) ([{4}] + {5})" if add else "{roll} **{0}** ({1} {2} {3}) ([{4}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(succ, total, type, val, all, " + ".join(map(lambda x: str(x), add)),
                                 roll=await _(ctx, "Roll"))
            else:
                fmt = "{roll} **{0}** ([{1}] + {2})" if add else "{roll} **{0}** ([{1}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(total, all, " + ".join(map(lambda x: str(x), add)), roll=await _(ctx, "Roll"))

            if pp:
                msg += (await _(ctx, " (Grabbed top {} out of {})")).format(pp, len(s) + pp)

            await ctx.send(f"<@{ctx.author.id}> rolled {msg}")
        except:
            from traceback import print_exc
            print_exc()
            await ctx.send(await _(ctx, "Invalid syntax!"))

    @commands.command()
    async def ping(self, ctx):
        """Test the bot's connection ping"""
        a = monotonic()
        await (await ctx.bot.shards[getattr(ctx.guild, "shard_id", 0)].ws.ping())
        b = monotonic()
        ping = "{:.3f}ms".format((b - a) * 1000)
        msg = f"P{choice('aeiou')}ng {ping}"
        await ctx.send(msg)

    @commands.command()
    async def info(self, ctx):
        """Bot Info"""
        me = self.bot.user if not ctx.guild else ctx.guild.me
        appinfo = await self.bot.application_info()
        embed = discord.Embed(color=randint(0, 0xFFFFFF), )
        embed.set_author(name=me.display_name, icon_url=appinfo.owner.avatar_url,
                         url="https://github.com/henry232323/RPGBot")
        embed.add_field(name=await _(ctx, "Author"), value='Henry#6174 (Discord ID: 122739797646245899)')
        embed.add_field(name=await _(ctx, "Library"), value='discord.py (Python)')
        embed.add_field(name=await _(ctx, "Uptime"), value=await self.bot.get_bot_uptime())
        embed.add_field(name=await _(ctx, "Servers"), value=(await _(ctx, "{} servers")).format(len(self.bot.guilds)))
        embed.add_field(name=await _(ctx, "Commands Run"),
                        value=(await _(ctx, '{} commands')).format(sum(self.bot.commands_used.values())))

        total_members = sum(len(s.members) for s in self.bot.guilds)
        total_online = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        unique_members = set(map(lambda x: x.id, self.bot.get_all_members()))
        channel_types = Counter(isinstance(c, discord.TextChannel) for c in self.bot.get_all_channels())
        voice = channel_types[False]
        text = channel_types[True]
        embed.add_field(name=await _(ctx, "Total Members"),
                        value=(await _(ctx, '{} ({} online)')).format(total_members, total_online))
        embed.add_field(name=await _(ctx, "Unique Members"), value='{}'.format(len(unique_members)))
        embed.add_field(name=await _(ctx, "Channels"),
                        value=(await _(ctx, '{} text channels, {} voice channels')).format(text, voice))
        embed.add_field(name=await _(ctx, "Shards"),
                        value=(await _(ctx, 'Currently running {} shards. This server is on shard {}')).format(
                            ctx.bot.shard_count, getattr(ctx.guild, "shard_id", 0)))

        # a = monotonic()
        # await (await ctx.bot.shards[getattr(ctx.guild, "shard_id", 0)].ws.ping())
        # b = monotonic()
        # ping = "{:.3f}ms".format((b - a) * 1000)

        embed.add_field(name=await _(ctx, "CPU Percentage"), value="{}%".format(psutil.cpu_percent()))
        embed.add_field(name=await _(ctx, "Memory Usage"), value=self.bot.get_ram())
        embed.add_field(name=await _(ctx, "Observed Events"), value=sum(self.bot.socket_stats.values()))
        # embed.add_field(name=await _(ctx, "Ping"), value=ping)

        embed.add_field(name=await _(ctx, "Source"), value="[Github](https://github.com/henry232323/RPGBot)")

        embed.set_footer(text=await _(ctx, 'Made with discord.py'), icon_url='http://i.imgur.com/5BFecvA.png')
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(delete_after=60, embed=embed)

    @commands.command()
    async def totalcmds(self, ctx):
        """Get totals of commands and their number of uses"""
        embed = discord.Embed(color=randint(0, 0xFFFFFF), )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        for val in self.bot.commands_used.most_common(25):
            embed.add_field(name=val[0], value=val[1])
        embed.set_footer(text=str(ctx.message.created_at))
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you have to separate it by
        periods, e.g. tag.create for the create subcommand of the tag command.
        """
        source_url = 'https://github.com/henry232323/RPGBot'
        if command is None:
            await ctx.send(source_url)
            return

        code_path = command.split('.')
        obj = self.bot
        for cmd in code_path:
            try:
                obj = obj.get_command(cmd)
                if obj is None:
                    await ctx.send(await _(ctx, 'Could not find the command ') + cmd)
                    return
            except AttributeError:
                await ctx.send((await _(ctx, '{0.name} command has no subcommands')).format(obj))
                return

        # since we found the command we're looking for, presumably anyway, let's
        # try to access the code itself
        src = obj.callback.__code__

        if not obj.callback.__module__.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(src.co_filename).replace('\\', '/')
            final_url = '<{}/tree/master/{}#L{}>'.format(source_url, location, src.co_firstlineno)
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            base = 'https://github.com/Rapptz/discord.py'
            final_url = '<{}/blob/master/{}#L{}>'.format(base, location, src.co_firstlineno)

        await ctx.send(final_url)

    @commands.command()
    async def donate(self, ctx):
        """Donation information"""
        await ctx.send(await _(ctx, "Keeping the bots running takes money, "
                                    "if several people would buy me a coffee each month, "
                                    "I wouldn't have to worry about it coming out of my pocket. "
                                    "If you'd like, you can subscribe to my Patreon here: https://www.patreon.com/henry232323, "
                                    "or try `.donate` in the support server to support me through the Donate Bot"))

    @commands.command()
    async def feedback(self, ctx, *, feedback):
        """Give me some feedback on the bot"""
        await ctx.send(await _(ctx, "This command is deprecated. If you need help or want to provide feedback, please"
                                    " ask in our support server https://discord.gg/UYJb8fQ"))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def socketstats(self, ctx):
        delta = datetime.datetime.utcnow() - self.bot.uptime
        minutes = delta.total_seconds() / 60
        total = sum(self.bot.socket_stats.values())
        cpm = total / minutes

        fmt = '%s socket events observed (%.2f/minute):\n%s'
        await ctx.send(fmt % (total, cpm, self.bot.socket_stats))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def makedoc(self, ctx):
        cogs = {name: {} for name in ctx.bot.cogs.keys()}

        all_commands = []
        for command in ctx.bot.commands:
            all_commands.append(command)
            if isinstance(command, commands.Group):
                all_commands.extend(command.commands)

        for c in all_commands:
            if c.cog_name not in cogs or c.help is None or c.hidden:
                continue
            if c.qualified_name not in cogs[c.cog_name]:
                skip = False
                for ch in c.checks:
                    if 'is_owner' in repr(ch):  # mine. don't put on docs
                        skip = True
                if skip:
                    continue
                help = c.help.replace('\n\n', '\n>')
                cogs[c.cog_name][
                    c.qualified_name] = f'#### {c.qualified_name}\n>**Description:** {help}\n\n>**Usage:** `{ctx.prefix + c.signature}`'

        index = '\n\n# Commands\n\n'
        data = ''

        for cog in sorted(cogs):
            index += '- [{0} Commands](#{1})\n'.format(cog, (cog + ' Commands').replace(' ', '-').lower())
            data += '## {0} Commands\n\n'.format(cog)
            extra = inspect.getdoc(ctx.bot.get_cog(cog))
            if extra is not None:
                data += '#### ***{0}***\n\n'.format(extra)

            for command in sorted(cogs[cog]):
                index += '  - [{0}](#{1})\n'.format(command, command.replace(' ', '-').lower())
                data += cogs[cog][command] + '\n\n'

        fp = io.BytesIO((index.rstrip() + '\n\n' + data.strip()).encode('utf-8'))
        await ctx.author.send(file=discord.File(fp, 'commands.md'))
