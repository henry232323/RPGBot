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

from .utils.data import NumberConverter, MemberConverter, ItemOrNumber
from .utils import checks
from .utils.translation import _

from random import choice


class Inventory(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['i', 'inv'])
    @checks.no_pm()
    async def inventory(self, ctx, *, member: discord.Member = None):
        """Check your or another users inventory."""
        if member is None:
            member = ctx.message.author

        inv = await self.bot.di.get_inventory(member)
        if not inv:
            await ctx.send(await _(ctx, "This inventory is empty!"))
            return

        fmap = map(lambda x: f"{x[0]} x{x[1]}", inv.items())
        fmt = "\n".join(fmap)
        embed = discord.Embed(description=fmt)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @checks.mod_or_permissions()
    @commands.command(aliases=["take"])
    @checks.no_pm()
    async def takeitem(self, ctx, item: str, num: NumberConverter, *members: MemberConverter):
        """Remove an item from a person's inventory"""
        if "everyone" in members:
            members = ctx.guild.members

        num = abs(num)
        for member in members:
            await self.bot.di.take_items(member, (item, num))

        await ctx.send(await _(ctx, "Items taken!"))

    @checks.mod_or_permissions()
    @commands.command()
    @checks.no_pm()
    async def giveitem(self, ctx, item: str, num: NumberConverter, *members: MemberConverter):
        """Give an item to a person (Not out of your inventory)"""
        if "everyone" in members:
            members = ctx.guild.members

        items = await self.bot.di.get_guild_items(ctx.guild)
        if item not in items:
            await ctx.send(await _(ctx, "That is not a valid item!"))
            return

        num = abs(num)
        for member in members:
            await self.bot.di.give_items(member, (item, num))

        await ctx.send(await _(ctx, "Items given!"))

    @commands.command()
    @checks.no_pm()
    async def give(self, ctx, other: discord.Member, *items: str):
        """Give items ({item}x{#}) to a member; ie: ;give @Henry#6174 pokeballx3"""
        fitems = []
        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            fitems.append((split, num))

        try:
            await self.bot.di.take_items(ctx.author, *fitems)
            await self.bot.di.give_items(other, *fitems)
            await ctx.send((await _(ctx, "Successfully gave {} {}")).format(other, items))
        except:
            await ctx.send(await _(ctx, "You do not have enough to give away!"))

    @commands.command()
    @checks.no_pm()
    async def wipeinv(self, ctx, *members: MemberConverter):
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            ud = await self.bot.db.get_user_data(member)
            ud["items"] = {}
            await self.bot.db.update_user_data(member, ud)

    @commands.command()
    @checks.no_pm()
    async def use(self, ctx, item, number: int = 1):
        number = abs(number)
        try:
            await self.bot.di.take_items(ctx.author, (item, number))
            items = await self.bot.di.get_guild_items(ctx.guild)
            msg = items.get(item).meta['used']
            if msg is None:
                await ctx.send(await _(ctx, "This item is not usable!"))
            else:
                await ctx.send(msg)
                await ctx.send((await _(ctx, "Used {} {}s")).format(number, item))
        except:
            await ctx.send(await _(ctx, "You do not have that many to use!"))

    @checks.no_pm()
    @commands.group(invoke_without_command=True, aliases=['lb'])
    async def lootbox(self, ctx):
        """List the current lootboxes"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if boxes:
            embed = discord.Embed()
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
            embed.set_thumbnail(
                url="https://mir-s3-cdn-cf.behance.net/project_modules/disp/196b9d18843737.562d0472d523f.png"
            )
            fmt = "{0}: {1:.2f}%"
            for box, data in boxes.items():
                total = sum(data["items"].values())
                value = "{}: {}\n\t".format(await _(ctx, "cost"), data["cost"]) + "\n\t".join(
                    fmt.format(item, (value / total) * 100) for item, value in data["items"].items())
                embed.add_field(name=box,
                                value=value)

            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send(await _(ctx, "No current lootboxes"))

    @checks.no_pm()
    @checks.mod_or_permissions()
    @lootbox.command(name="create", aliases=["new"])
    async def _create(self, ctx, name: str, cost: ItemOrNumber, *items: str):
        """Create a new lootbox, under the given `name` for the given cost
        Use {item}x{#} notation to add items with {#} weight
        Weight being an integer. For example:
        bananax2 orangex3. The outcome of the box will be
        Random Choice[banana, banana, orange, orange, orange]"""

        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            await ctx.send(await _(ctx, "Lootbox already exists, updating..."))

        winitems = {}
        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            winitems.update({split: num})

            boxes[name] = dict(cost=cost, items=winitems)

        if isinstance(cost, str):
            await ctx.send((await _(ctx, "Lootbox {} successfully created and requires one {} to open.")).format(name, cost))
        else:
            await ctx.send((await _(ctx, "Lootbox {} successfully created and requires 1 dollars to open")).format(name, cost))
        await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)

    @checks.no_pm()
    @lootbox.command(name="buy")
    async def _lootbox_buy(self, ctx, *, name: str):
        """Buy a lootbox of the given name"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        try:
            box = boxes[name]
        except KeyError:
            await ctx.send(await _(ctx, "That is not a valid lootbox"))
            return

        cost = box["cost"]
        if isinstance(cost, str):
            try:
                await self.bot.di.take_items(ctx.author, (cost, 1))
            except ValueError:
                await ctx.send((await _(ctx, "You do not have 1 {}")).format(cost))
                return
        else:
            try:
                await self.bot.di.add_eco(ctx.author, -cost)
            except ValueError:
                await ctx.send(await _(ctx, "You cant afford this box"))
                return

        winitems = []
        for item, amount in box["items"].items():
            winitems += [item] * amount

        result = choice(winitems)
        await self.bot.di.give_items(ctx.author, (result, 1))
        await ctx.send((await _(ctx, "You won a(n) {}")).format(result))

    @checks.no_pm()
    @lootbox.command(name="delete", aliases=["remove"])
    async def _lootbox_delete(self, ctx, *, name: str):
        """Delete a lootbox with the given name"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            del boxes[name]
            await ctx.send(await _(ctx, "Lootbox removed"))
            await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)
        else:
            await ctx.send(await _(ctx, "Invalid loot box"))
