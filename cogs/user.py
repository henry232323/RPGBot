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

from .utils import checks, data
from .utils.data import chain
from .utils.translation import _


class User(commands.Cog):
    """Commands for guild management"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.command(name="userinfo", aliases=["ui"])
    async def ui(self, ctx, *, user: discord.Member = None):
        """Get info on a user"""
        dest = ctx.channel
        if user is None:
            user = ctx.author
        gd = await self.bot.db.get_guild_data(ctx.guild)
        try:
            is_mod = checks.role_or_permissions(ctx,
                                                lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False

        hide = gd.get("hideinv", False)

        if not is_mod and hide:
            user = ctx.author

        if hide:
            dest = ctx.author

        embed = discord.Embed(color=randint(0, 0xFFFFFF))
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)

        ud = await self.bot.db.get_user_data(user)
        gd = await self.bot.db.get_guild_data(ctx.guild)
        hide = gd.get("hideinv", False)

        pet = [f"{x[0]}: **{x[1]}**" for x in ud["box"]]
        pl = len(pet)
        if pl > 20:
            pet = pet[20:]
            pet.append((await _(ctx, "\nand {} more...")).format(pl - 20))
        boxitems = "\n".join(pet)

        characters = [x for x, y in gd["characters"].items() if y[1] == user.id]
        if characters:
            embed.add_field(name=await _(ctx, "Characters"), value="\n".join(characters))

        if not hide or is_mod:
            imap = [f"{x[0]} x{x[1]}" for x in ud["items"].items()]
            il = len(imap)
            if il > 20:
                imap = imap[:20]
                imap.append((await _(ctx, "\nand {} more...")).format(il - 20))
            invitems = "\n".join(imap) or await _(ctx, "No Items")

            embed.add_field(name=await _(ctx, "Items"), value=invitems)
            embed.add_field(name=await _(ctx, "Balance"), value=f"{ud['money']} {gd.get('currency', 'dollars')}")
            if user == ctx.author:
                embed.add_field(name=await _(ctx, "Bank"), value=f"{ud.get('bank', 0)} {gd.get('currency', 'dollars')}")
                embed.add_field(name=await _(ctx, "Total Money"),
                                value=f"{ud.get('bank', 0) + ud['money']} {gd.get('currency', 'dollars')}")

        embed.add_field(name=await _(ctx, "Guild"), value=ud.get("guild", await _(ctx, "None")))
        embed.add_field(name=await _(ctx, "Box"), value=boxitems) if boxitems else None
        embed.add_field(name=await _(ctx, "Experience"),
                        value=(await _(ctx, "Level: {}\nExperience: {}/{}")).format(ud.get('level', 1),
                                                                                    ud.get('exp', 0),
                                                                                    self.bot.get_exp(
                                                                                        ud.get('level', 1))))

        await dest.send(embed=embed)

    @commands.group(aliases=["exp"], invoke_without_command=True)
    async def experience(self, ctx, member: discord.Member = None):
        """Get your or another user's level information. Help on this command for experience subcommands
        EXP is calculated using a 0.1x^2+5x+4 where x is equal to the user's current level
        Spamming commands or messages will not earn more exp!"""
        if member is None:
            member = ctx.author

        ulvl, uexp = await self.bot.di.get_user_level(member)
        embed = discord.Embed(
            description=(await _(ctx, "Level: {}\nExperience: {}/{}")).format(ulvl, uexp, self.bot.get_exp(ulvl)),
            color=randint(0, 0xFFFFFF), )
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @checks.mod_or_permissions()
    @experience.command(aliases=["set"])
    async def setlevel(self, ctx, level: data.IntConverter, *members: data.MemberConverter):
        """Set the given members level"""
        members = chain(members)
        for member in members:
            await self.bot.di.set_level(member, level, 0)
        await ctx.send(await _(ctx, "Set level for members"))

    @checks.mod_or_permissions()
    @experience.command()
    async def add(self, ctx, amount: data.IntConverter, *members: data.MemberConverter):
        """Give the given members an amount of experience"""
        amount = abs(amount)
        members = chain(members)
        for member in members:
            await self.bot.di.add_exp(member, amount)

        await ctx.send(await _(ctx, "Gave experience to members"))

    @checks.mod_or_inv()
    @commands.command()
    async def giveexp(self, ctx, amount: data.IntConverter):
        """Give the yourself an amount of experience"""
        amount = abs(amount)
        await self.bot.di.add_exp(ctx.author, amount)

        await ctx.send(await _(ctx, "Experience given!"))

    @checks.mod_or_inv()
    @commands.command()
    async def givelevel(self, ctx, level: data.IntConverter):
        """Set yourself to a certain level"""
        await self.bot.di.set_level(ctx.author, level, 0)
        await ctx.send(await _(ctx, "Level set!"))

    @experience.command()
    @checks.mod_or_permissions()
    async def enable(self, ctx):
        """Enable EXP settings for a guild"""
        await self.bot.di.set_exp_enabled(ctx.guild, True)
        await ctx.send(await _(ctx, "Successfully changed EXP setting"))

    @experience.command()
    @checks.mod_or_permissions()
    async def disable(self, ctx):
        """Disable EXP settings for a guild"""
        await self.bot.di.set_exp_enabled(ctx.guild, False)
        await ctx.send(await _(ctx, "Successfully changed EXP setting"))
