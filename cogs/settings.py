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

    @commands.group(aliases=["s", "configuration", "conf"], invoke_without_command=True)
    async def settings(self, ctx):
        """Get the current server settings"""
        settings = await self.bot.db.get_guild_data(ctx.guild)
        embed = discord.Embed(color=randint(0, 0xFFFFFF),)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name=await _(ctx, "Starting Money"),
                        value=f"{settings['start']} {settings.get('currency', 'dollars')}")
        embed.add_field(name=await _(ctx, "Items"), value="{} {}".format(len(settings['items']), await _(ctx, "items")))
        embed.add_field(name=await _(ctx, "Characters"),
                        value="{} {}".format(len(settings['characters']), await _(ctx, "characters")))
        embed.add_field(name=await _(ctx, "Maps"),
                        value=await _(ctx, "None") if not settings.get("maps") else "\n".join(
                            (x if x != settings.get("default_map") else f"**{x}**") for x in settings["maps"]))
        embed.add_field(name=await _(ctx, "Currency"), value=f"{settings.get('currency', 'dollars')}")
        embed.add_field(name=await _(ctx, "Language"), value=f"{settings.get('language', 'en')}")
        embed.add_field(name=await _(ctx, "Experience Enabled"), value=f"{settings.get('exp', True)}")
        embed.add_field(name=await _(ctx, "Prefix"), value=f"{settings.get('prefix', 'rp!')}")
        embed.add_field(name=await _(ctx, "Hide Inventories"), value=f"{settings.get('hideinv', False)}")
        embed.add_field(name=await _(ctx, "Wipe Userdata on Leave"), value=f"{settings.get('wipeonleave', False)}")
        time = settings.get('msgdel', 0)
        embed.add_field(name=await _(ctx, "Message Auto Delete Time"), value=f"{time if time is not 0 else 'Never'}")
        await ctx.send(embed=embed)

    @settings.command()
    async def iteminfo(self, ctx, *, item: str):
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

    @settings.command()
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

    @checks.mod_or_permissions()
    @settings.command()
    async def additem(self, ctx, *, name: str):
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
    @settings.command(aliases=["deleteitem"])
    async def removeitem(self, ctx, *, name: str):
        """Remove a custom item
        Requires Bot Moderator or Bot Admin"""
        try:
            await self.bot.di.remove_item(ctx.guild, name)
            await ctx.send((await _(ctx, "Successfully removed {}")).format(name))
        except KeyError:
            await ctx.send(await _(ctx, "That item doesn't exist"))

    @checks.mod_or_permissions()
    @commands.command()
    async def setstart(self, ctx, amount: NumberConverter):
        """Set the money start amount for a guild
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_start(ctx.guild, amount)
        await ctx.send((await _(ctx, "Starting amount changed to {} dollars")).format(amount))


    # @checks.mod_or_permissions()
    # @commands.command()
    # async def setmapchars(self, ctx, choice: bool):
    #     """Set the map to give items etc to characters instead
    #     Requires Bot Moderator or Bot Admin"""
    #     await self.bot.di.set_map_chars(ctx.guild, choice)
    #     await ctx.send((await _(ctx, "Use chars for maps set to: {}")).format(choice))

    @commands.command()
    @checks.admin_or_permissions()
    async def language(self, ctx, language: str = None):
        """Set the guild language or check the language
        English = en
        German = de
        Spanish = es
        Portugese = pt
        Russian = ru
        (if something appears in english despite your
        settings theres no translation for it yet, you can help write those if you want)
        Requires Bot Moderator or Bot Admin"""
        if language is None:
            lang = await self.bot.di.get_language(ctx.guild)
            await ctx.send((await _(ctx, "The guild language is set to {}")).format(lang))
        else:
            if language not in self.bot.languages:
                await ctx.send(await _(ctx, "That is not a valid language!"))
                return
            await self.bot.di.set_language(ctx.guild, language)
            await ctx.send(await _(ctx, "Language successfully set!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def currency(self, ctx, currency: str):
        """Set the guild currency
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_currency(ctx.guild, currency)
        await ctx.send(await _(ctx, "Currency successfully set!"))

    @commands.command()
    @checks.mod_or_permissions()
    async def deleteafter(self, ctx, time: int):
        """Set a time for messages to be automatically deleted after running in seconds. `rp!deleteafter 0` to make messages never be deleted
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_delete_time(ctx.guild, time)
        await ctx.send(await _(ctx, "Updated settings"))

    @commands.command()
    @checks.admin_or_permissions()
    async def setdefaultmap(self, ctx, mapname: str):
        """Set the server's default map.
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_default_map(ctx.guild, mapname)
        await ctx.send(await _(ctx, "Updated default map"))

    @commands.command()
    @checks.admin_or_permissions()
    async def setprefix(self, ctx, new_prefix: str):
        """Set the server's custom prefix. The default prefix will continue to work.
        Example:
            rp!setprefix ! --> !setprefix rp!

        Requires Bot Moderator or Bot Admin"""
        self.bot.prefixes[str(ctx.guild.id)] = new_prefix
        await ctx.send(await _(ctx, "Updated server prefix"))

    @commands.command()
    async def prefix(self, ctx):
        """View the current custom prefix for the server

        Requires Bot Moderator or Bot Admin"""
        prefix = self.bot.prefixes.get(str(ctx.guild.id), "rp!")
        await ctx.send(prefix)

    @commands.command(disabled=True, hidden=True)
    @checks.admin_or_permissions()
    async def setcmdprefix(self, ctx, cmdpath: str, *, value: str):
        """Set a custom prefix for a command. The default prefix will continue to work.
        Example:
            Henry: rp!setcmdprefix rtd /
            Henry: /1d20
            RPGBot: Henry rolled Roll 9 ([9])

        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_cmd_prefixes(ctx.guild, cmdpath, value)
        await ctx.send(await _(ctx, "Updated command prefix"))

    @commands.command(disabled=True, hidden=True)
    async def prefixes(self, ctx):
        """View the current custom command prefixes for the server

        Requires Bot Moderator or Bot Admin"""
        prefixes = await self.bot.di.get_cmd_prefixes(ctx.guild)
        await ctx.send("\n".join(f"{k}: {v}" for k, v in prefixes.items()) or "rp!")

    @commands.command()
    @checks.admin_or_permissions()
    async def wipeonleave(self, ctx, value: str):
        """Set the server's setting for what to do when a player leaves. Set to true to wipe player data.
        Values are True and False

        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.set_leave_setting(ctx.guild, value)
        await ctx.send(await _(ctx, "Updated server setting"))

    @commands.command()
    @checks.admin_or_permissions()
    async def hideinv(self, ctx, value: bool):
        """Set whether or not user inventories are hidden. If enabled, inventories will be sent via DMs.
        Values are True/False
        Requires Bot Moderator or Bot Admin"""
        gd = await self.bot.db.get_guild_data(ctx.guild)
        gd["hideinv"] = value
        await self.bot.db.update_guild_data(ctx.guild, gd)
        await ctx.send(await _(ctx, "Updated inventory setting"))

