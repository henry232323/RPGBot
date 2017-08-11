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

from .utils import checks, data


class User(object):
    """Commands for guild management"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", aliases=["ui"])
    @checks.no_pm()
    async def ui(self, ctx, *, user: discord.Member=None):
        """Get info on a user"""
        if user is None:
            user = ctx.author

        embed = discord.Embed()
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)

        ud = await self.bot.db.get_user_data(user)

        pokemon = [f"{x[0]}: **{x[1]}**" for x in ud["box"]]
        pl = len(pokemon)
        if pl > 20:
            pokemon = pokemon[20:]
            pokemon.append(f"\nand {pl-20} more...")
        boxitems = "\n".join(pokemon)

        imap = [f"{x[0]} x{x[1]}" for x in ud["items"].items()]
        il = len(imap)
        if il > 20:
            imap = imap[20:]
            imap.append(f"\nand {il-20} more...")
        invitems = "\n".join(imap) or "No Items"

        embed.add_field(name="Balance", value=f"${ud['money']}")
        embed.add_field(name="Guild", value=ud.get("guild", "None"))
        embed.add_field(name="Items", value=invitems)
        embed.add_field(name="Box", value=boxitems) if boxitems else None
        embed.add_field(name="Experience", value=f"Level: {ud.get('level', 1)}\nExperience: {ud.get('exp', 0)}/{self.bot.get_exp(ud.get('level', 1))}")

        await ctx.send(embed=embed)

    @checks.no_pm()
    @checks.mod_or_permissions()
    @commands.group(aliases=["exp"], invoke_without_command=True)
    async def experience(self, ctx, member: discord.Member=None):
        """Get your or another user's level information. Help on this command for experience subcommands
        EXP is calculated using a 0.1x^2+5x+4 where x is equal to the user's current level
        Spamming commands or messages will not earn more exp!"""
        if not member:
            member = ctx.author

        ulvl, uexp = await self.bot.di.get_user_level(ctx.author)
        embed = discord.Embed(description=f"Level: {ulvl}\nExperience: {uexp}/{self.bot.get_exp(ulvl)}")
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @checks.no_pm()
    @checks.mod_or_permissions()
    @experience.command(aliases=["set"])
    async def setlevel(self, ctx, level: data.NumberConverter, *members: data.MemberConverter):
        """Set the given members level"""
        if "everyone" in members:
            members = ctx.guild.members
        for member in members:
            await self.bot.di.set_level(member, level, 0)
        await ctx.send("Set level for members")

    @checks.no_pm()
    @checks.mod_or_inv()
    @experience.command()
    async def add(self, ctx, amount: data.NumberConverter, *members: data.MemberConverter):
        """Give the given members an amount of experience"""
        if "everyone" in members:
            members = ctx.guild.members
        for member in members:
            await self.bot.di.add_exp(member, amount)

        await ctx.send("Gave experience to members")