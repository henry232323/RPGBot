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

import asyncio
from random import choice, randint

import discord
from discord.ext import commands

from .utils import checks
from .utils.data import MemberConverter, ItemOrNumber, chain, IntConverter, create_pages, parse_varargs, chunkn
from .utils.translation import _


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trades = {}

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.command(aliases=['i', 'inv'])
    async def inventory(self, ctx, *, member: discord.Member = None):
        """Check your or another users inventory.
        Example: rp!inventory @Henry#6174 or just rp!inventory"""
        dest = ctx.channel
        if member is None:
            member = ctx.author
        gd = await self.bot.db.get_guild_data(ctx.guild)
        try:
            is_mod = checks.role_or_permissions(ctx,
                                                lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False

        hide = gd.get("hideinv", False)

        if not is_mod and hide:
            member = ctx.author

        if hide:
            dest = ctx.author

        inv = await self.bot.di.get_inventory(member)
        if not inv:
            await dest.send(await _(ctx, "This inventory is empty!"))
            return

        fmap = map(lambda x: f"{x[0]} x{x[1]}", sorted(inv.items()))
        fmt = "\n".join(fmap)
        chunks = chunkn(fmt, 2000)  # [("Items: ", v) for v in chunkn(fmt, 400)]
        for chunk in chunks:
            embed = discord.Embed(description="\n".join(chunk), color=randint(0, 0xFFFFFF))
            embed.set_author(name=member.display_name, icon_url=member.avatar_url)
            try:
                await dest.send(embed=embed)
            except discord.Forbidden:
                await dest.send(chunk)

    @checks.mod_or_permissions()
    @commands.command(aliases=["take"])
    async def takeitem(self, ctx, item: str, num: IntConverter, *members: MemberConverter):
        """Remove an item from a person's inventory
        Example: rp!takeitem Banana 5 @Henry#6174 @JohnDoe#0001
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        num = abs(num)
        for member in members:
            try:
                await self.bot.di.take_items_override(member, (item, num))
            except ValueError:
                await ctx.send((await _(ctx, "Failed to take items from {}")).format(member.display_name))

        await ctx.send(await _(ctx, "Items taken!"))

    @checks.mod_or_permissions()
    @commands.command()
    async def giveitem(self, ctx, item: str, num: IntConverter, *members: MemberConverter):
        """Give an item to a person (Not out of your inventory)
        Example: rp!giveitem Banana 32 @Henry#6174 @RPGBot#8700 @JoeShmoe#3012
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        items = await self.bot.di.get_guild_items(ctx.guild)
        if item not in items:
            await ctx.send(await _(ctx, "That is not a valid item!"))
            return

        num = abs(num)
        for member in members:
            await self.bot.di.give_items(member, (item, num))

        await ctx.send(await _(ctx, "Items given!"))

    @checks.mod_or_permissions()
    @commands.command()
    async def giveitems(self, ctx, other: discord.Member, *items: str):
        """Give items ({item}x{#}) to a member
        Example: rp!giveitems @Henry#6174 Pokeballx3 Orangex5"""
        fitems = []
        item_list = await self.bot.di.get_guild_items(ctx.guild)
        for item in items:
            if item[:item.rfind('x')] not in item_list:
                await ctx.send(await _(ctx, "That is not a valid item!"))
                return
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            fitems.append((split, num))

        await self.bot.di.give_items(other, *fitems)
        await ctx.send(await _(ctx, "Items given!"))

    @checks.mod_or_inv()
    @commands.command()
    async def addinv(self, ctx, num: IntConverter, *, item: str):
        """Give an item to yourself
        Example: rp!addinv 32 Apple Pie
        Requires Bot Moderator or Bot Inventory roles"""

        items = await self.bot.di.get_guild_items(ctx.guild)
        if item not in items:
            await ctx.send(await _(ctx, "That is not a valid item!"))
            return

        num = abs(num)
        await self.bot.di.give_items(ctx.author, (item, num))

        await ctx.send(await _(ctx, "Items given!"))

    @commands.command()
    async def give(self, ctx, other: discord.Member, *items: str):
        """Give items ({item}x{#}) to a member
        Example: rp!give @Henry#6174 Pokeballx3 Orangex5"""
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
    async def givechar(self, ctx, other: str, *items: str):
        """Give items ({item}x{#}) to a character from your inventory
        Example: rp!give @Henry#6174 Pokeballx3 Orangex5"""
        fitems = []
        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            fitems.append((split, num))

        ochar = await self.bot.di.get_character(ctx.guild, other)
        if ochar is None:
            await ctx.send("That character does not exist!")
            return

        try:
            await self.bot.di.take_items(ctx.author, *fitems)
            await self.bot.get_cog("Characters").c_giveitem(ctx.guild, other, *fitems)
            await ctx.send((await _(ctx, "Successfully gave {} {}")).format(other, items))
        except Exception as e:
            await ctx.send(await _(ctx, "You do not have enough to give away!"))

    @commands.command()
    @checks.admin_or_permissions()
    async def wipeinv(self, ctx, *members: MemberConverter):
        """Wipe all listed inventories. Must be administrator. To wipe ALL inventories do `rp!wipeinv everyone`"""

        members = chain(members)

        for member in members:
            ud = await self.bot.db.get_user_data(member)
            ud["items"] = {}
            await self.bot.db.update_user_data(member, ud)

        await ctx.send((await _(ctx, "Wiped {} users' inventories")).format(len(list(members))))

    @commands.command()
    async def use(self, ctx, item, number: int = 1):
        """Use an item. Example: `rp!use Banana` or `rp!use Banana 5`
        To make an item usable, you must put the key `used: <message>` when you are adding additional information for an item.
        Example:
            Henry: rp!s additem Potion
            RPGBot: Describe the item (a description for the item)
            Henry: A potion
            RPGBot: Additional information? (...)
            Henry: used: The potion restored 500 health
            RPGBot: Item successfully created

            ...

            Henry: rp!use Potion 3
            RPGBot: The potion restored 500 health
                    Used 5 Potions
        """
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

        await ctx.send(msg.format(mention=ctx.author.mention,
                                  name=ctx.author.display_name,
                                  channel=ctx.channel))
        await ctx.send((await _(ctx, "Used {} {}s")).format(number, item))

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

    @checks.mod_or_permissions()
    @lootbox.command(name="create", aliases=["new"])
    async def _create(self, ctx, name: str, cost: ItemOrNumber, *items: str):
        """Create a new lootbox, under the given `name` for the given cost
        Use {item}x{#} notation to add items with {#} weight
        Weight being an integer.
        Example:
            rp!lootbox create MyBox 500 bananax2 orangex3. The outcome of the box will be
            Random Choice[banana, banana, orange, orange, orange]
            The price can also be an item (or several items), for example
            rp!lootbox create MyBox Key bananax2 orangex3
            or
            rp!lootbox create MyBox Keyx2 bananax3 orangex3

        If you use 10 total items:
            Keyx3
            Bananax4
            Orangex3

            There will be:
                - A 3/10 chance of getting a Key
                - A 3/10 chance of getting an Orange
                - A 4/10 chance of getting a Banana
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
            return

        if isinstance(cost, (list, tuple)):
            await ctx.send(
                (await _(ctx, "Lootbox {} successfully created and requires {} {} to open.")).format(name, cost[1],
                                                                                                     cost[0]))
        else:
            await ctx.send(
                (await _(ctx, "Lootbox {} successfully created and requires {} dollars to open")).format(name, cost))
        await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)

    @lootbox.command(name="buy")
    async def _lootbox_buy(self, ctx, *, name: str):
        """Buy a lootbox of the given name
        Example: rp!lootbox buy MyLootBox"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        try:
            box = boxes[name]
        except KeyError:
            await ctx.send(await _(ctx, "That is not a valid lootbox"))
            return

        cost = box["cost"]
        if isinstance(cost, (str, tuple, list)):
            cost, val = cost if isinstance(cost, (tuple, list)) else (cost, 1)
            try:
                await self.bot.di.take_items(ctx.author, (cost, val))
            except ValueError:
                await ctx.send((await _(ctx, "You do not have {} {}")).format(val, cost))
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

    @lootbox.command(name="delete", aliases=["remove"])
    @checks.mod_or_permissions()
    async def _lootbox_delete(self, ctx, *, name: str):
        """Delete a lootbox with the given name
        Example: rp!lootbox delete MyLootBox
        Requires Bot Moderator or Bot Admin"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            del boxes[name]
            await ctx.send(await _(ctx, "Lootbox removed"))
            await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)
        else:
            await ctx.send(await _(ctx, "Invalid loot box"))

    @commands.group(invoke_without_command=True)
    async def trade(self, ctx, other: discord.Member, *items: str):
        """Send a trade offer to another user.
        Example: rp!trade @Henry Bananax3 Applex1 --Format items as {item}x{#}"""
        self.trades[other] = (ctx, items)
        await ctx.send((await _(ctx,
                                "{} has 5 minutes to respond to this request using rp!trade respond. See rp!help trade respond for details")).format(
            other))
        await asyncio.sleep(300)
        if self.trades.pop(other) is None:
            await ctx.send((await _(ctx, "{} failed to respond")).format(other))

    @trade.command()
    async def respond(self, ctx, other: discord.Member, *items: str):
        """Respond to a trade offer by another user.
        Example: rp!inventory respond @Henry Grapex8 Applex1
            --Format items as {item}x{#}"""
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
    async def craft(self, ctx, number: int, *, name: str):
        """Craft a recipe with a given name from the available server recipes;
         Example: rp!craft 5 Apple Pie"""
        recipes = await ctx.bot.di.get_guild_recipes(ctx.guild)
        recipe = recipes.get(name)
        if recipe is None:
            await ctx.send(await _(ctx, "That recipe doesn't exist!"))
            return

        uinv = await self.bot.di.get_inventory(ctx.author)
        for item, n in recipe[0].items():
            if uinv.get(item, 0) < n * number:
                await ctx.send(
                    (await _(ctx, "You need {} {} to craft this! You only have {}")).format(n * number, item,
                                                                                            uinv.get(item)))
                return

        await ctx.bot.di.take_items(ctx.author, *((a, b * number) for a, b in recipe[0].items()))
        await ctx.bot.di.give_items(ctx.author, *((a, b * number) for a, b in recipe[1].items()))

        await ctx.send((await _(ctx, "Successfully crafted {} {}")).format(number, name))

    @commands.command()
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

                inputstr = "\n".join(f"\t{i}: {n}" for i, n in v[0].items())
                outputstr = "\n".join(f"\t{i}: {n}" for i, n in v[1].items())
                return fmt.format(inputstr, outputstr)

            await create_pages(ctx, boxes, lfmt, description=desc, title=await _(ctx, "Server Recipes"),
                               author=ctx.guild.name, author_url=ctx.guild.icon_url,
                               thumbnail="http://chittagongit.com/images/scroll-icon-vector/scroll-icon-vector-0.jpg",
                               footer=str(ctx.message.created_at), chunk=4)

        else:
            await ctx.send(await _(ctx, "No current recipes"))

    @commands.group(invoke_without_command=True)
    async def recipe(self, ctx, *, name: str):
        """See data on a specific recipe; Example: rp!recipe Banana"""
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
                inputstr = "\n".join(f"\t{i}: {n}" for i, n in v[0].items())
                outputstr = "\n".join(f"\t{i}: {n}" for i, n in v[1].items())
                return fmt.format(inputstr, outputstr)

            await create_pages(ctx, recipes, lfmt, description=desc, title=await _(ctx, "Server Recipes"),
                               author=ctx.guild.name, author_url=ctx.guild.icon_url,
                               thumbnail="http://chittagongit.com/images/scroll-icon-vector/scroll-icon-vector-0.jpg",
                               footer=str(ctx.message.created_at), chunk=4)

        else:
            await ctx.send(await _(ctx, "No current recipes"))

    @recipe.command()
    @checks.mod_or_permissions()
    async def create(self, ctx, *, name: str):
        """Create a new recipe;
        Example
            > rp!recipe create Apple Pie
            >> What items must be consumed to follow this recipe? e.g. Applex5 Breadx2
            > Applex5 Breadx15 "Pie Tinx1"
            >> What items will be given upon the completion of this recipe? e.g. "Apple Piex1"
            > "Apple Piex1" "Pie Tinx1"
            >> Successfully created new recipe!
        """
        await ctx.send(await _(ctx, "What items must be consumed to follow this recipe? e.g. "
                                    "Applex5 Breadx2"))

        count = 0
        while True:
            try:
                inmsg = await ctx.bot.wait_for("message",
                                               check=lambda x: x.author == ctx.author and (x.channel == ctx.channel),
                                               timeout=120)
                if inmsg.content.lower() == "cancel":
                    await ctx.send(await _(ctx, "Cancelling!"))
                    return
                inmsgparts = parse_varargs(inmsg.content)

                initems = []
                for item in inmsgparts:
                    split = item.split('x')
                    initems.append(("x".join(split[:-1]), abs(int(split[-1]))))

                break
            except Exception as e:
                if isinstance(e, TimeoutError):
                    raise
                await ctx.send(await _(ctx, "Invalid formatting! Try again!"))
                count += 1
                if count >= 3:
                    await ctx.send(await _(ctx, "Too many failed attempts, cancelling!"))
                    return

        await ctx.send(await _(ctx, "What items will be given upon the completion of this recipe? e.g. "
                                    "\"Apple Piex1\""))
        count = 0
        while True:
            try:
                outmsg = await ctx.bot.wait_for("message",
                                                check=lambda x: x.author == ctx.author and (x.channel == ctx.channel),
                                                timeout=120)
                if outmsg.content.lower() == "cancel":
                    await ctx.send(await _(ctx, "Cancelling!"))
                    return

                outmsgparts = parse_varargs(outmsg.content)

                outitems = []
                for item in outmsgparts:
                    split = item.split('x')
                    outitems.append(("x".join(split[:-1]), abs(int(split[-1]))))

                break
            except Exception as e:
                if isinstance(e, TimeoutError):
                    raise
                await ctx.send(await _(ctx, "Invalid formatting! Try again!"))
                count += 1
                if count >= 3:
                    await ctx.send(await _(ctx, "Too many failed attempts, cancelling!"))
                    return

        await ctx.bot.di.add_recipe(ctx.guild, name, dict(initems), dict(outitems))
        await ctx.send(await _(ctx, "Successfully created new recipe!"))

    @recipe.command()
    @checks.mod_or_permissions()
    async def delete(self, ctx, *, name: str):
        """Delete the recipe with the given name; Example: rp!recipe delete Apple Pie
        Requires Bot Moderator or Bot Admin"""
        await ctx.bot.di.remove_recipe(ctx.guild, name)
        await ctx.send(await _(ctx, "Successfully deleted the recipe"))
