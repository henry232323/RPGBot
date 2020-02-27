import json

import discord
from discord.ext import commands

import csv
from io import StringIO, BytesIO

from .utils import checks
from .utils.data import ServerItem
from .utils.translation import _


class Backups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.admin_or_permissions()
    async def loaddnd(self, ctx):
        """This command will pre-load all D&D items and make them available to give
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.new_items(ctx.guild, (ServerItem(**item) for item in self.bot.dnditems.values()))
        await ctx.send(await _(ctx, "Successfully added all D&D items!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loadstarwars(self, ctx):
        """This command will pre-load all Star Wars items and make them available to give
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.new_items(ctx.guild, (ServerItem(**item) for item in self.bot.switems.values()))
        await ctx.send(await _(ctx, "Successfully added all Star Wars items!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loadstarwarsshop(self, ctx):
        """This command will pre-load all Star Wars items and make them available in shop
        Requires Bot Moderator or Bot Admin"""
        items = {}
        for item, value in self.bot.switems.items():
            try:
                items[item] = dict(buy=int("".join(filter(str.isdigit, value["meta"]["Cost"].split(" ")[0]))), sell=0,
                                   level=0)
            except:
                continue

        await self.bot.di.add_shop_items(ctx.guild, items)
        await ctx.send(await _(ctx, "Successfully added all Star Wars items to shop!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loaddndshop(self, ctx):
        """This command will pre-load all D&D items and make them available in shop
        Requires Bot Moderator or Bot Admin"""
        items = {}
        for item, value in self.bot.dnditems.items():
            try:
                items[item] = dict(buy=int("".join(filter(str.isdigit, value["meta"]["Cost"]))), sell=0, level=0)
            except:
                continue

        await self.bot.di.add_shop_items(ctx.guild, items)
        await ctx.send(await _(ctx, "Successfully added all D&D items to shop!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loadmagicshop(self, ctx):
        """This command will pre-load all D&D Magic items and make them available in shop
        Requires Bot Moderator or Bot Admin"""
        items = {}
        for item, value in self.bot.dndmagic.items():
            try:
                items[item] = dict(buy=int("".join(filter(str.isdigit, value["meta"]["Cost"]))), sell=0, level=0)
            except:
                continue

        await self.bot.di.add_shop_items(ctx.guild, items)
        await ctx.send(await _(ctx, "Successfully added all D&D magic items to shop!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loaddndmagic(self, ctx):
        """This command will pre-load all D&D Magic items and make them available to give
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.new_items(ctx.guild, (ServerItem(**item) for item in self.bot.dndmagic.values()))
        await ctx.send(await _(ctx, "Successfully added all D&D items!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loadpokemon(self, ctx):
        """This command will pre-load all Pokemon items and make them available to give
        Requires Bot Moderator or Bot Admin"""
        await self.bot.di.new_items(ctx.guild, (ServerItem(**item) for item in self.bot.pokemonitems.values()))
        await ctx.send(await _(ctx, "Successfully added all Pokemon items!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def loaditems(self, ctx, *, arguments: str=""):
        """This command load all the items in the attached file.
        See an example file here: https://github.com/henry232323/RPGBot/blob/master/tutorial.md
        Requires Bot Moderator or Bot Admin."""
        items = []
        if not ctx.message.attachments:
            await ctx.send(await _(ctx, "This command needs to have a file attached!"))
            return

        attachment = ctx.message.attachments.pop()
        size = attachment.size
        if size > 2 ** 20:
            await ctx.send(await _(ctx, "This file is too large!"))
            return

        file = BytesIO()
        await attachment.save(file)
        file.seek(0)

        nfile = StringIO(file.getvalue().decode())
        nfile.seek(0)

        csv_reader = csv.DictReader(nfile)
        shop_items = {}

        for row in csv_reader:
            items.append(dict(
                name=row["name"],
                description=row.get("description", "No description."),
                meta={}
            ))
            if not row["name"]:
                await ctx.send(await _(ctx, "Error: There is an item with a missing name!"))
                return
            for k, v in row.items():
                if k not in ["name", "description", "buyprice", "sellprice"]:
                    if v:
                        items[-1]["meta"][k] = v

            if float(row.get("buyprice", 0)) or float(row.get("sellprice", 0)):
                shop_items[row["name"]] = dict(buy=float(row.get("buyprice", 0)), sell=float(row.get("sellprice", 0)),
                                               level=0)

        if "replace" in arguments:
            await self.bot.di.update_guild_shop(ctx.guild, shop_items)
            await self.bot.di.update_guild_items(ctx.guild, (ServerItem(**item) for item in items))
            await ctx.send(await _(ctx, "Successfully loaded and replaced all items!"))
        else:
            await self.bot.di.add_shop_items(ctx.guild, shop_items)
            await self.bot.di.new_items(ctx.guild, (ServerItem(**item) for item in items))
            await ctx.send(await _(ctx, "Successfully loaded all items!"))

    @commands.command()
    @checks.mod_or_permissions()
    async def unload(self, ctx, name: str):
        """Unload Pokemon, D&D, D&D Magic, or Star Wars items. `rp!unload {name}` where name is either dnd, dndmagic, pokemon or starwars
        Requires Bot Moderator or Bot Admin"""
        if name == "dnd":
            items = self.bot.dnditems
        elif name == "dndmagic":
            items = self.bot.dndmagic
        elif name == "pokemon":
            items = self.bot.pokemonitems
        elif name == "starwars":
            items = self.bot.switems
        else:
            await ctx.send(await _(ctx, "That is not a valid input, look at `rp!help unload`"))
            return

        await self.bot.di.remove_items(ctx.guild, *items)
        await self.bot.di.remove_shop_items(ctx.guild, *items)
        await ctx.send((await _(ctx, "Successfully removed all {} items!")).format(name))

    async def send_as_file(self, destination, data, name):
        await destination.send(file=discord.File(BytesIO(data.encode()), filename=name))

    @commands.command()
    @checks.mod_or_permissions()
    async def export(self, ctx, subsection: str = None):
        """Export a server's data"""
        data = await self.bot.db.get_guild_data(ctx.guild)
        if subsection is not None and subsection not in data:
            await ctx.send((await _(ctx,
                                    "{} is not a valid subsection! Try providing no subsection and see the available keys")).format(
                subsection))
            return
        if subsection != None:
            data = data[subsection]

        await self.send_as_file(ctx.author, json.dumps(data),
                                name="{}.json".format(subsection if subsection else ctx.guild.name))

    @commands.command()
    @checks.mod_or_permissions()
    async def exportitems(self, ctx):
        """Export the items of the server into a loadable CSV"""
        items = await self.bot.di.get_guild_items(ctx.guild)
        fieldnames = {"name", "description"}
        for item in items.values():
            fieldnames.update(item.meta.keys())
        fp = StringIO()
        writer = csv.DictWriter(fp, fieldnames=list(fieldnames))
        writer.writeheader()
        for item in items.values():
            writer.writerow({"name": item.name, "description": item.description, **item.meta})
        fp.seek(0)

        await ctx.author.send(file=discord.File(BytesIO(fp.read().encode()), filename="items.csv"))
