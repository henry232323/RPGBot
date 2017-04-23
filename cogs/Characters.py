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
from .utils.data import Character

class Characters(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, aliases=["chars"])
    async def characters(self, ctx):
        """List all your characters"""
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        characters = [x for x in characters.values() if x.owner == ctx.author.id]
        if not characters:
            await ctx.send("User has no characters to display")
            return

        embed = discord.Embed(description="\n".join(characters))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(no_pm=True)
    async def allchars(self, ctx):
        """List all your characters"""
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        if not characters:
            await ctx.send("No characters to display")

        embed = discord.Embed()
        words = dict()
        for x in characters.keys():
            if x[0].lower() in words:
                words[x[0].lower()].append(x)
            else:
                words[x[0].lower()] = [x]

        for key, value in words.items():
            if value:
                embed.add_field(name=key.upper(), value="\n".join(value))

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.group(no_pm=True, invoke_without_command=True, aliases=["c", "char"])
    async def character(self, ctx, *, name: str):
        """Get info on a character"""
        try:
            char = await self.bot.di.get_guild_characters(ctx.guild)[name]
        except KeyError:
            await ctx.send("Character does not exist!")
            return

        owner = discord.utils.get(ctx.guild.members, id=char.owner)
        embed = discord.Embed(description=char.description)
        embed.set_author(name=char.name, icon_url=char.meta.get("image") or owner.avatar_url)
        embed.add_field(name="Name", value=char.name)
        embed.add_field(name="Owner", value=str(owner))
        embed.add_field(name="Level", value=char.level)
        team = await self.bot.di.get_team(ctx.guild, char.name)
        tfmt = "\n".join(p.name for p in team)
        embed.add_field(name="Team", value=tfmt)
        mfmt = "\n".join(f"{x}: {y}" for x, y in char.meta.items())
        embed.add_field(name="Additional Info", value=mfmt)

        await ctx.send(embed=embed)

    @character.command(no_pm=True, aliases=["new"])
    async def create(self, ctx, *, name: str):
        """Create a new character"""
        check = lambda x: x.channel is ctx.channel and x.author is ctx.author
        character = dict(name=name, owner=ctx.author.id, meta=dict())
        await ctx.send("Describe the character (Relevent character sheet)")
        response = await self.bot.wait_for("message", check=check, timeout=60)
        character["description"] = response.content
        await ctx.send("What level is the character?")
        response = await self.bot.wait_for("message", timeout=30, check=check)
        character["level"] = int(response.content)
        await ctx.send("Any additional info? (Add a character image using the image keyword. Formats use regular syntax i.e "
                       "`image: http://image.com/, hair_color: blond, nickname: Kevin`")
        while True:
            response = await self.bot.wait_for("message", check=check, timeout=60)
            try:
                for val in response.content.split(", "):
                    key, value = val.split(": ")
                    key = key.strip().lower()
                    character["meta"][key] = value
                else:
                    break
            except:
                await ctx.send("Invalid formatting! Try again")
                continue

        await self.bot.di.add_character(ctx.guild, Character(**character))