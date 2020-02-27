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
import csv

from discord.ext import commands
import discord
import asyncio

from random import randint

from io import BytesIO, StringIO

from .utils.data import ServerItem, NumberConverter, create_pages
from .utils import checks
from .utils.translation import _


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.group()
    async def items(self, ctx, letter: str = None):
        """See all items for a server"""
        items = await self.bot.di.get_guild_items(ctx.guild)

        if not items:
            await ctx.send(await _(ctx, "No items to display"))
            return

        words = dict()
        for x in sorted(items.keys()):
            if x[0].casefold() in words:
                words[x[0].casefold()].append(x)
            else:
                words[x[0].casefold()] = [x]

        desc = await _(ctx, "\u27A1 to see the next page"
                            "\n\u2B05 to go back"
                            "\n\u274C to exit")

        if letter is not None:
            if letter in words:
                words = {letter: words[letter]}
            else:
                await ctx.send(await _(ctx, "No entries found for that letter"))

        def lfmt(v):
            return "\n".join(v)

        await create_pages(ctx, list(words.items()), lfmt, description=desc, title=await _(ctx, "Server Items"),
                           author=ctx.guild.name, author_url=ctx.guild.icon_url,
                           thumbnail="https://mir-s3-cdn-cf.behance.net/project_modules/disp/196b9d18843737.562d0472d523f.png",
                           footer=str(ctx.message.created_at), chunk=4)

    @items.command()
    async def info(self, ctx, *, item: str):
        """Get info on a server item"""
        items = await self.bot.di.get_guild_items(ctx.guild)
        item = items.get(item)
        if not item:
            await ctx.send(await _(ctx, "Item doesnt exist!"))
            return
        if hasattr(item, "description"):
            embed = discord.Embed(title=item.name, description=item.description, color=randint(0, 0xFFFFFF),)
        else:
            embed = discord.Embed(title=item.name, color=randint(0, 0xFFFFFF),)

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name=await _(ctx, "Name"), value=item.name)
        img = item.meta.get("image")
        embed.set_thumbnail(url=str(img)) if img else None
        for key, value in item.meta.items():
            if key == "image":
                continue
            embed.add_field(name=key, value=value)

        await ctx.send(embed=embed)

    @checks.mod_or_permissions()
    @items.command()
    async def add(self, ctx, *, name: str):
        """Add a custom item.
         Custom keys that can be used for special additions:
            `image` Setting this to a URL will give that item a special thumbnail when info is viewed for it
            `used` A message for when the item is used

        Henry: rp!settings additem Example
        RPGBot: Describe the item (a description for the item)
        Henry: This is an example item
        RPGBot: Additional information? (Attributes formatted in a list i.e color: 400, value: 200 Set an image for this item with the image key i.e. image: http://example.com/image.png Set this item as usable by adding used key i.e. used: You open the jar and the bird flies away
        Henry: used: You used this item!, image: http://www.sourcecertain.com/img/Example.png
        RPGBot:  Item successfully created

        Requires Bot Moderator or Bot Admin
            """
        try:
            item = dict()
            item["name"] = name
            check = lambda x: x.channel == ctx.channel and x.author == ctx.author
            await ctx.send(await _(ctx, "Describe the item (a description for the item)"))
            response = await self.bot.wait_for("message", timeout=120, check=check)
            if response.content.lower() == "cancel":
                await ctx.send(await _(ctx, "Cancelling!"))
                return

            item["description"] = response.content
            item["meta"] = dict()

            await ctx.send(
                await _(ctx, "Additional information? (Attributes formatted in a list i.e `color: 400, value: 200` "
                             "Set an image for this item with the `image` key i.e. `image: http://example.com/image.png` "
                             "Set this item as usable by adding `used` key i.e. `used: You open the jar and the bird flies away`"))
            while True:
                response = await self.bot.wait_for("message", timeout=60, check=check)
                if response.content.lower() == "cancel":
                    await ctx.send(await _(ctx, "Cancelling!"))
                    return
                elif response.content.lower() == "skip":
                    await ctx.send(await _(ctx, "Skipping!"))
                    break
                else:
                    try:
                        if "\n" in response.content:
                            res = response.content.split("\n")
                        else:
                            res = response.content.split(",")
                        for val in res:
                            key, value = val.split(": ")
                            key = key.strip().casefold()
                            value = value.strip()
                            item["meta"][key] = value
                        else:
                            break
                    except asyncio.TimeoutError:
                        await ctx.send("If you are seeing this message, please report this to the bot author immediately.")
                        return
                    except:
                        await ctx.send(await _(ctx, "Invalid syntax, try again."))
            await self.bot.di.new_item(ctx.guild, ServerItem(**item))
            await ctx.send(await _(ctx, "Item successfully created"))

        except asyncio.TimeoutError:
            await ctx.send(await _(ctx, "Timed out! Try again"))


    @checks.mod_or_permissions()
    @items.command(aliases=["delete"])
    async def remove(self, ctx, *, name: str):
        """Remove a custom item
        Requires Bot Moderator or Bot Admin"""
        try:
            await self.bot.di.remove_item(ctx.guild, name)
            await ctx.send((await _(ctx, "Successfully removed {}")).format(name))
        except KeyError:
            await ctx.send(await _(ctx, "That item doesn't exist"))


