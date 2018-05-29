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

from .utils.data import MemberConverter, ItemOrNumber, chain, IntConverter, create_pages, parse_varargs
from .utils import checks
from .utils.translation import _

from random import choice


class Inventory(object):
    def __init__(self, bot):
        self.bot = bot
        self.trades = {}

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

        fmap = map(lambda x: f"{x[0]} x{x[1]}", sorted(inv.items()))
        fmt = "\n".join(fmap)
        embed = discord.Embed(description=fmt)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        await ctx.send(embed=embed)

    @checks.mod_or_permissions()
    @commands.command(aliases=["take"])
    @checks.no_pm()
    async def takeitem(self, ctx, item: str, num: IntConverter, *members: MemberConverter):
        """Remove an item from a person's inventory"""
        members = chain(members)

        num = abs(num)
        for member in members:
            await self.bot.di.take_items(member, (item, num))

        await ctx.send(await _(ctx, "Items taken!"))

    @checks.mod_or_permissions()
    @commands.command()
    @checks.no_pm()
    async def giveitem(self, ctx, item: str, num: IntConverter, *members: MemberConverter):
        """Give an item to a person (Not out of your inventory)"""
        members = chain(members)

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
        """Give items ({item}x{#}) to a member; ie: rp!give @Henry#6174 pokeballx3"""
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
        members = chain(members)

        for member in members:
            ud = await self.bot.db.get_user_data(member)
            ud["items"] = {}
            await self.bot.db.update_user_data(member, ud)

    @commands.command()
    @checks.no_pm()
    async def use(self, ctx, item, number: int = 1):
        number = abs(number)
        items = await self.bot.di.get_guild_items(ctx.guild)
        msg = items.get(item).meta.get('used')
        if msg is None:
            await ctx.send(await _(ctx, "This item is not usable!"))
            return
        try:
            await self.bot.di.take_items(ctx.author, (item, number))
        except ValueError:
            await ctx.send(await _(ctx, "You do not have that many to use!"))
            return

        await ctx.send(msg)
        await ctx.send((await _(ctx, "Used {} {}s")).format(number, item))

    @checks.no_pm()
    @commands.group(invoke_without_command=True, aliases=['lb'])
    async def lootbox(self, ctx, name: str = None):
        """List the current lootboxes"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name is not None:
            boxes = {name: boxes.get(name)}
            if boxes[name] is None:
                await ctx.send(await _(ctx, "That is not a valid lootbox"))
                return
        if boxes:
            boxes = sorted(boxes.items(), key=lambda x: x[0])
            desc = await _(ctx, "\u27A1 to see the next page"
                                "\n\u2B05 to go back"
                                "\n\u274C to exit")

            cstr = await _(ctx, "cost")

            def lfmt(v):
                fmt = "{0}: {1:.2f}%"
                total = sum(v["items"].values())

                if isinstance(v["cost"], (int, float)):
                    cost = v["cost"]
                elif isinstance(v["cost"], str):
                    cost = v["cost"] + "x1"
                else:
                    cost = "{}x{}".format(*v["cost"])

                value = "{}: {}\n\t".format(cstr, cost) + "\n\t".join(
                    fmt.format(item, (value / total) * 100) for item, value in v["items"].items())

                return value

            await create_pages(ctx, boxes, lfmt, description=desc, title=await _(ctx, "Server Lootboxes"),
                               author=ctx.guild.name, author_url=ctx.guild.icon_url,
                               thumbnail="https://mir-s3-cdn-cf.behance.net/project_modules/disp/196b9d18843737.562d0472d523f.png",
                               footer=str(ctx.message.created_at), chunk=4)

        else:
            await ctx.send(await _(ctx, "No current lootboxes"))

    @checks.no_pm()
    @checks.mod_or_permissions()
    @lootbox.command(name="create", aliases=["new"])
    async def _create(self, ctx, name: str, cost: ItemOrNumber, *items: str):
        """Create a new lootbox, under the given `name` for the given cost
        Use {item}x{#} notation to add items with {#} weight
        Weight being an integer. For example:
        rp!lootbox create MyBox 500 bananax2 orangex3. The outcome of the box will be
        Random Choice[banana, banana, orange, orange, orange]
        The price can also be an item (or several items), for example
        rp!lootbox create MyBox Key bananax2 orangex3
        or
        rp!lootbox create MyBox Keyx2 bananax3 orangex3
        """

        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            await ctx.send(await _(ctx, "Lootbox already exists, updating..."))

        winitems = {}
        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            winitems.update({split: num})

            boxes[name] = dict(cost=cost, items=winitems)
        if not winitems:
            await ctx.send(await _(ctx, "You cannot create an empty lootbox!"))

        if isinstance(cost, tuple):
            await ctx.send(
                (await _(ctx, "Lootbox {} successfully created and requires {} {} to open.")).format(name, cost[1],
                                                                                                     cost[0]))
        else:
            await ctx.send(
                (await _(ctx, "Lootbox {} successfully created and requires {} dollars to open")).format(name, cost))
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
        if isinstance(cost, (str, tuple, list)):
            cost, val = cost if isinstance(cost, tuple) else (cost, 1)
            try:
                await self.bot.di.take_items(ctx.author, cost)
            except ValueError:
                await ctx.send((await _(ctx, "You do not have {} {}")).format(cost, val))
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

    @commands.command()
    @checks.no_pm()
    async def offer(self, ctx, other: discord.Member, *items: str):
        """Send a trade offer to another user. Usage: rp!inventory offer @Henry bananax3 applex1 --Format items as {item}x{#}"""
        self.trades[other] = (ctx, items)
        await ctx.send("Say rp!respond @User ")
        await asyncio.sleep(300)
        if self.trades.pop(other) is None:
            await ctx.send((await _(ctx, "{} failed to respond")).format(other))

    @commands.command()
    @checks.no_pm()
    async def respond(self, ctx, other: discord.Member, *items: str):
        """Respond to a trade offer by another user. Usage: rp!inventory respond @Henry grapex8 applex1 --Format items as {item}x{#}"""
        sender = ctx.message.author
        if sender in self.trades and other == self.trades[sender][0].message.author:
            await ctx.send(
                await _(ctx, "Both parties say rp!accept @Other to accept the trade or rp!decline @Other to decline"))
            already = None

            def check(message):
                if not (message.channel == ctx.channel):
                    return False
                if not message.content.startswith(("rp!accept", "rp!decline",)):
                    return False
                if message.author in (other, sender):
                    if message.author == already:
                        return False
                    if message.author == sender:
                        return other in message.mentions
                    else:
                        return sender in message.mentions
                else:
                    return False

            try:
                msg = await self.bot.wait_for("message",
                                              timeout=30,
                                              check=check)
            except TimeoutError:
                msg = None

            await ctx.send(await _(ctx, "Response one received!"))
            if not msg:
                await ctx.send(await _(ctx, "Failed to accept in time!"))
                del self.trades[sender]
                return

            elif msg.content.startswith("rp!decline"):
                await ctx.send(await _(ctx, "Trade declined, cancelling!"))
                del self.trades[sender]
                return

            already = msg.author

            try:
                msg2 = await self.bot.wait_for("message",
                                               timeout=30,
                                               check=check)
            except TimeoutError:
                msg2 = None

            await ctx.send(await _(ctx, "Response two received!"))

            if not msg2:
                await ctx.send(await _(ctx, "Failed to accept in time!"))
                del self.trades[sender]
                return

            elif msg2.content.startswith("rp!decline"):
                await ctx.send(await _(ctx, "Trade declined, cancelling!"))
                del self.trades[sender]
                return

            oinv = (await self.bot.di.get_inventory(other))
            sinv = (await self.bot.di.get_inventory(sender))
            for item in self.trades[sender][1]:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                if num <= 0:
                    await ctx.send((await _(ctx, "Invalid value for number {} of {}")).format(num, split))
                    del self.trades[sender]
                    return
                if split not in oinv or num > oinv[split]:
                    await ctx.send(
                        (await _(ctx, "{} does not have enough {} to trade! Trade cancelled!")).format(other, split))
                    del self.trades[sender]
                    return

            for item in items:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                if num <= 0:
                    await ctx.send((await _(ctx, "Invalid value for number {} of {}")).format(num, split))
                    del self.trades[sender]
                    return
                if split not in sinv or num > sinv[split]:
                    await ctx.send(
                        (await _(ctx, "{} does not have enough {} to trade! Trade cancelled!")).format(sender, split))
                    del self.trades[sender]
                    return

            await ctx.send(await _(ctx, "Swapping items"))
            titems = []
            for item in items:
                split = item.split('x')
                titems.append(("x".join(split[:-1]), abs(int(split[-1]))))
            await self.bot.di.take_items(sender, *titems)
            await self.bot.di.give_items(other, *titems)
            ritems = []
            for item in self.trades[sender][1]:
                split = item.split('x')
                ritems.append(("x".join(split[:-1]), abs(int(split[-1]))))
            await self.bot.di.take_items(other, *ritems)
            await self.bot.di.give_items(sender, *ritems)

            await ctx.send(await _(ctx, "Trade complete!"))
            del self.trades[sender]

    @commands.command()
    @checks.no_pm()
    async def craft(self, ctx, number: int, *name: str):
        """Craft a recipe with a given name from the available server recipes; e.g. rp!craft 5 Apple Pie"""
        recipes = await ctx.bot.di.get_guild_recipes(ctx.guild)
        recipe = recipes.get(name)
        if recipe is None:
            await ctx.send(await _(ctx, "That recipe doesn't exist!"))
            return

        uinv = await self.bot.di.get_inventory(ctx.author)
        for item, n in recipe[0].items():
            if uinv.get(item) < n * number:
                await ctx.send(
                    (await _(ctx, "You need {} {} to craft this! You only have {}")).format(n * number, item,
                                                                                            uinv.get(item)))
                return

        await ctx.bot.di.take_items(ctx.author, *recipe[0].items())
        await ctx.bot.di.give_items(ctx.author, *recipe[1].items())

        await ctx.send((await _(ctx, "Successfully crafted {} {}")).format(number, name))

    @commands.command()
    @checks.no_pm()
    async def recipes(self, ctx):
        """List all the available server recipes"""
        recipes = await ctx.bot.di.get_guild_recipes(ctx.guild)

        if recipes:
            boxes = sorted(recipes.items(), key=lambda x: x[0])
            desc = await _(ctx, "\u27A1 to see the next page"
                                "\n\u2B05 to go back"
                                "\n\u274C to exit")

            def lfmt(v):
                fmt = "Input:\n{}\nOutput:\n{}"

                inputstr = "\n".join(f"\t{i}: n" for i, n in v[0].items())
                outputstr = "\n".join(f"\t{i}: n" for i, n in v[1].items())
                return fmt.format(inputstr, outputstr)

            await create_pages(ctx, boxes, lfmt, description=desc, title=await _(ctx, "Server Recipes"),
                               author=ctx.guild.name, author_url=ctx.guild.icon_url,
                               thumbnail="http://chittagongit.com/images/scroll-icon-vector/scroll-icon-vector-0.jpg",
                               footer=str(ctx.message.created_at), chunk=4)

        else:
            await ctx.send(await _(ctx, "No current recipes"))

    @commands.group(invoke_without_command=True)
    @checks.no_pm()
    async def recipe(self, ctx, name: str):
        """Subcommands for recipes. See data on a specific recipe; e.g. rp!recipe Banana"""
        recipes = await ctx.bot.di.get_guild_recipes(ctx.guild)

        if name is not None:
            recipes = {name: recipes.get(name)}
            if recipes[name] is None:
                await ctx.send(await _(ctx, "That is not a valid recipe"))
                return
        if recipes:
            recipes = sorted(recipes.items(), key=lambda x: x[0])
            desc = await _(ctx, "\u27A1 to see the next page"
                                "\n\u2B05 to go back"
                                "\n\u274C to exit")

            def lfmt(v):
                fmt = "Input:\n{}\nOutput:\n{}"
                inputstr = "\n".join(f"\t{i}: n" for i, n in v[0].items())
                outputstr = "\n".join(f"\t{i}: n" for i, n in v[1].items())
                return fmt.format(inputstr, outputstr)

            await create_pages(ctx, recipes, lfmt, description=desc, title=await _(ctx, "Server Recipes"),
                               author=ctx.guild.name, author_url=ctx.guild.icon_url,
                               thumbnail="http://chittagongit.com/images/scroll-icon-vector/scroll-icon-vector-0.jpg",
                               footer=str(ctx.message.created_at), chunk=4)

        else:
            await ctx.send(await _(ctx, "No current recipes"))

    @recipe.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def create(self, ctx, *name: str):
        """Create a new recipe; e.g.
        > rp!recipe create Apple Pie
        >> What items must be consumed to follow this recipe? e.g. Applex5 Breadx2
        > Applex5 Breadx15 "Pie Tinx1"
        >> What items will be given upon the completion of this recipe? e.g. "Apple Piex1"
        > "Apple Piex1" "Pie Tinx1"
        >> Successfully created new recipe!
        """
        await ctx.send(await _(ctx, "What items must be consumed to follow this recipe? e.g. "
                                    "Applex5 Breadx2"))
        while True:
            try:
                inmsg = await ctx.bot.wait_for("message",
                                               check=lambda x: x.author == ctx.author and (x.channel == ctx.channel),
                                               timeout=120)
                inmsgparts = parse_varargs(inmsg.content)

                initems = []
                for item in inmsgparts:
                    split = item.split('x')
                    initems.append(("x".join(split[:-1]), abs(int(split[-1]))))

                break
            except:
                from traceback import print_exc
                print_exc()
                await ctx.send(await _(ctx, "Invalid formatting! Try again!"))

        await ctx.send(await _(ctx, "What items will be given upon the completion of this recipe? e.g. "
                                    "\"Apple Piex1\""))
        while True:
            try:
                outmsg = await ctx.bot.wait_for("message",
                                                check=lambda x: x.author == ctx.author and (x.channel == ctx.channel),
                                                timeout=120)
                outmsgparts = parse_varargs(outmsg.content)

                outitems = []
                for item in outmsgparts:
                    split = item.split('x')
                    outitems.append(("x".join(split[:-1]), abs(int(split[-1]))))

                break
            except:
                from traceback import print_exc
                print_exc()
                await ctx.send(await _(ctx, "Invalid formatting! Try again!"))

        await ctx.bot.di.add_recipe(ctx.guild, name, dict(initems), dict(outitems))
        await ctx.send(await _(ctx, "Successfully created new recipe!"))

    @recipe.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def delete(self, ctx, *name: str):
        """Delete the recipe with the given name; e.g. rp!recipe delete Apple Pie"""
        await ctx.bot.di.remove_recipe(ctx.guild, name)
        await ctx.send(await _(ctx, "Successfully deleted the recipe"))