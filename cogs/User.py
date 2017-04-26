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


class User(object):
    """Commands for guild management"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", aliases=["ui"], no_pm=True)
    async def ui(self, ctx, user: discord.Member=None):
        if user is None:
            user = ctx.author

        embed = discord.Embed()
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)

        ud = self.bot.db.get_user_data(user)

        pokemon = [f"{x.id}: **{x.name}**" for x in ud["box"]]
        boxitems = "\n".join(pokemon)

        imap = [f"{x[0]} x{x[1]}" for x in ud["items"].items()]
        invitems = "\n".join(imap)

        embed.add_field(name="Balance", value=f"{ud['money']} Pokédollars")
        embed.add_field(name="Guild", value=ud["guild"] or "None")
        embed.add_field(name="Items", value=invitems)
        embed.add_field(name="Box", value=boxitems)

        await ctx.send(embed)