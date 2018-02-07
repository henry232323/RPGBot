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
import asyncio
from .utils.data import ServerItem, NumberConverter
from .utils import checks


class Settings(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["s", "configuration", "conf"], invoke_without_command=True)
    @checks.no_pm()
    async def settings(self, ctx):
        """Get the current server settings"""
        settings = await self.bot.db.get_guild_data(ctx.guild)
        embed = discord.Embed()
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name="Starting Money", value=f"${settings['start']}")
        embed.add_field(name="Items", value=f"{len(settings['items'])} items")
        embed.add_field(name="Characters", value=f"{len(settings['characters'])} characters")
        embed.add_field(name="Maps",
                        value="None" if not settings.get("maps") else "\n\t" + "\n\t".join(settings["maps"]))
        await ctx.send(embed=embed)

    @settings.command()
    @checks.no_pm()
    async def iteminfo(self, ctx, *, item: str):
        """Get info on a server item"""
        items = await self.bot.di.get_guild_items(ctx.guild)
        item = items.get(item)
        if not item:
            await ctx.send("Item doesnt exist!")
            return
        if hasattr(item, "description"):
            embed = discord.Embed(title=item.name, description=item.description)
        else:
            embed = discord.Embed()

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name="Name", value=item.name)
        img = item.meta.get("image")
        embed.set_thumbnail(url=str(img)) if img else None
        for key, value in item.meta.items():
            if key == "image":
                continue
            embed.add_field(name=key, value=value)

        await ctx.send(embed=embed)

    @settings.command()
    @checks.no_pm()
    async def items(self, ctx):
        """See all items for a guild"""
        items = await self.bot.di.get_guild_items(ctx.guild)

        if not items:
            await ctx.send("No items to display")
            return

        embed = discord.Embed()

        words = dict()
        for x in sorted(items.keys()):
            if x[0].casefold() in words:
                words[x[0].casefold()].append(x)
            else:
                words[x[0].casefold()] = [x]

        for key, value in words.items():
            if value:
                embed.add_field(name=key.upper(), value="\n".join(value))

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_footer(text=str(ctx.message.created_at))
        await ctx.send(embed=embed)

    @checks.mod_or_permissions()
    @settings.command()
    @checks.no_pm()
    async def additem(self, ctx, *, name: str):
        """Add a custom item"""
        try:
            item = dict()
            item["name"] = name
            check = lambda x: x.channel is ctx.channel and x.author is ctx.author
            await ctx.send("Describe the item (a description for the item)")
            response = await self.bot.wait_for("message", timeout=120, check=check)
            item["description"] = response.content
            item["meta"] = dict()

            await ctx.send("Additional information? (Attributes formatted in a list i.e `color: 400, value: 200` "
                           "Set an image for this item with the `image` key i.e. `image: http://image.com/image.png`"
                           "Set this item as usable by adding `used` key i.e. `used: You open the jar and the bird flies away`")
            while True:
                response = await self.bot.wait_for("message", timeout=60, check=check)
                if response.content.lower() == "cancel":
                    await ctx.send("Cancelling!")
                    return
                elif response.content.lower() == "skip":
                    await ctx.send("Skipping!")
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
                    except:
                        await ctx.send("Invalid syntax, try again.")
            await self.bot.di.new_item(ctx.guild, ServerItem(**item))
            await ctx.send("Item successfully created")

        except asyncio.TimeoutError:
            await ctx.send("Timed out! Try again")

    @checks.mod_or_permissions()
    @settings.command(aliases=["deleteitem"])
    @checks.no_pm()
    async def removeitem(self, ctx, *, name: str):
        """Remove a custom item"""
        try:
            await self.bot.di.remove_item(ctx.guild, name)
            await ctx.send(f"Successfully removed {name}")
        except KeyError:
            await ctx.send("That item doesn't exist")

    @checks.mod_or_permissions()
    @checks.no_pm()
    @commands.command()
    async def setstart(self, ctx, amount: NumberConverter):
        """Set the money start amount for a guild"""
        await self.bot.di.set_start(ctx.guild, amount)
        await ctx.send(f"Starting amount changed to ${amount}")
