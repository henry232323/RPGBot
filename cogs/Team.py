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


class Team(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    async def box(self, ctx, member: discord.Member=None):
        """Check the pokemon in your box"""
        if member is None:
            member = ctx.author
        box = await self.bot.di.get_box(member)

        pokemon = [f"{x.id}: **{x.name}**" for x in box]
        description = "\n".join(pokemon)
        embed = discord.Embed(description=description, title=f"{member.display_name}'s Pokemon")
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, no_pm=True)
    async def team(self, ctx, character: str):
        """Check a character's team"""
        team = await self.bot.di.get_team(ctx.guild, character)
        all_chars = await self.bot.di.get_guild_characters()
        chobj = all_chars[character]

        embed = discord.Embed(title=f"{character}'s Pokemon")
        embed.set_author(name=character, icon_url=chobj.meta.get("image"))

        for pokemon in team:
            stats = "\n\t".join(f"{x}: {y}" for x,y in pokemon.stats.items())
            meta = "\n\t".join(f"{x}: {y}" for x, y in pokemon.meta.items())
            fmt = f"ID: {pokemon.id}\nSpecies: {pokemon.type}\nStats:\n\t{stats}\nAdditional Info:\n\t{meta}"
            embed.add_field(name=pokemon.name, value=fmt)

        await ctx.send(embed=embed)

    @team.command(aliases=["addmember"], no_pm=True)
    async def add(self, ctx, character, id):
        await self.bot.di.add_to_team(ctx.guild, character, id)

    @team.command(aliases=["removemember"], no_pm=True)
    async def remove(self, ctx, character, id):
        await self.bot.di.remove_from_team(ctx.guild, character, id)

