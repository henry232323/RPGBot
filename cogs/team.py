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

from discord.ext import commands
import discord

from random import randint

from .utils import checks
from .utils.translation import _


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @checks.no_pm()
    async def team(self, ctx, *, character: str):
        """Check a character's team"""

        try:
            team = await self.bot.di.get_team(ctx.guild, character)
            all_chars = await self.bot.di.get_guild_characters(ctx.guild)
            chobj = all_chars[character]
        except KeyError:
            await ctx.send(await _(ctx, "That character doesn't exist!"))
            return

        embed = discord.Embed(title=f"{character} Pokemon", color=randint(0, 0xFFFFFF))
        embed.set_author(name=character, icon_url=chobj.meta.get("image", discord.Embed.Empty))

        for pokemon in team:
            stats = "\n\t".join(f"{x}: {y}" for x, y in pokemon.stats.items())
            meta = "\n\t".join(f"{x}: {y}" for x, y in pokemon.meta.items())
            fmt = (await _(ctx, "ID: {}\nSpecies: {}\nStats:\n\t{}\nAdditional Info:\n\t{}")).format(pokemon.id,
                                                                                                     pokemon.type,
                                                                                                     stats,
                                                                                                     meta)
            embed.add_field(name=pokemon.name, value=fmt)

        await ctx.send(embed=embed)

    @team.command(aliases=["addmember"])
    @checks.no_pm()
    async def add(self, ctx, character: str, id: int):
        """Add a Pokemon to a character's team"""
        try:
            chobj = (await self.bot.di.get_guild_characters(ctx.guild))[character]
            if chobj.owner != ctx.author.id:
                await ctx.send(await _(ctx, "You do not own this character!"))
                return
            if id in chobj.team:
                await ctx.send(await _(ctx, "That Pokemon is already a part of the team!"))
                return
            await self.bot.di.add_to_team(ctx.guild, character, id)
            await ctx.send(await _(ctx, "Added to team!"))
        except KeyError:
            await ctx.send("That character does not exist!")

    @team.command(aliases=["removemember"])
    @checks.no_pm()
    async def remove(self, ctx, character: str, id: int):
        """Remove a Pokemon from a character's team"""
        try:
            chobj = (await self.bot.di.get_guild_characters(ctx.guild))[character]
            if chobj.owner != ctx.author.id:
                await ctx.send(await _(ctx, "You do not own this character!"))
                return

            await self.bot.di.remove_from_team(ctx.guild, character, id)
            await ctx.send(await _(ctx, "Successfully removed Pokemon!"))
        except KeyError:
            await ctx.send(await _(ctx, "That character does not exist!"))
