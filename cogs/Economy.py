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
from .utils.data import Converter
from .utils import checks

class Economy(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["bal", "balance", "eco", "e"], no_pm=True, invoke_without_command=True)
    async def economy(self, ctx, member: discord.Member=None):
        if member is None:
            member = ctx.author

        bal = await self.bot.di.get_balance(member)

        await ctx.send(f"{member.display_name} has {bal} Pokédollars")

    @checks.mod_or_permissions()
    @economy.command(aliases=["set"], no_pm=True)
    async def setbalance(self, ctx, amount: int, *members: Converter):
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.set_eco(member, amount)

        await ctx.send("Balances changed")

    @checks.mod_or_permissions()
    @economy.command(aliases=["give"], no_pm=True)
    async def givemoney(self, ctx, amount: int, *members: Converter):
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.add_eco(member, amount)

        await ctx.send("Money given")

    @commands.command(no_pm=True)
    async def pay(self, ctx, amount: int, member: discord.Member):
        amount = abs(amount)
        await self.bot.di.add_eco(ctx.author, -amount)
        await self.bot.di.add_eco(member, amount)
        await ctx.send(f"Successfully paid {amount} Pokédollars to {member}")