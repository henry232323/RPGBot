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
from collections import Counter
from random import choice, randint
import json
from recordclass import recordclass

import discord
from async_timeout import timeout
from discord.ext import commands

from .utils import checks
from .utils.data import MemberConverter, NumberConverter, get, chain, create_pages, IntConverter
from .utils.translation import _


class Economy(commands.Cog):
    """Economy related commands: balance, market, etc"""

    def __init__(self, bot):
        self.bot = bot
        self.bids = list()
        self.bot.shutdowns.append(self.shutdown)

    async def shutdown(self):
        with open("resources/lotteries.json", 'w') as lf:
            lf.write(json.dumps(self.bot.lotteries))

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.group(aliases=["bal", "balance", "eco", "e"], invoke_without_command=True)
    async def economy(self, ctx, *, member: discord.Member = None):
        """Check your or another users balance.
        Example: rp!e @Henry#6174
        Will not display others' balances if inventory hiding is enabled."""
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

        bal = await ctx.bot.di.get_all_balances(member)

        data = """
On you:\t\t {:.2f} dollars
In the bank:\t {:.2f} dollars in the bank
Total:\t\t {:.2f} dollars
        """

        embed = discord.Embed(
            description=(await _(ctx, data)).format(
                int(bal[0]) if int(bal[0]) == bal[0] else bal[0],
                int(bal[1]) if int(bal[1]) == bal[1] else bal[1],
                sum(bal)
            ),
            color=randint(0, 0xFFFFFF),
        )

        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_thumbnail(url="https://opengameart.org/sites/default/files/styles/medium/public/gold_pile_0.png")
        await dest.send(embed=embed)

    @checks.mod_or_permissions()
    @commands.command(aliases=["set"])
    async def setbalance(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Set the balance of the given members to an amount
        Example: rp!setbalance 500 everyone
        Example: rp!setbalance 500 @Henry#6174 @JohnDoe#0001
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        for member in members:
            async with self.bot.di.rm.lock(member.id):
                await self.bot.di.set_eco(member, amount)

        await ctx.send(await _(ctx, "Balances changed"))

    @checks.mod_or_permissions()
    @commands.command()
    async def givemoney(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Give the member's money
        Example: rp!givemoney 5000 @Henry#6174 @JohnDoe#0001
        Example: rp!givemoney 50 everyone (or @\u200beveryone)
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        for member in members:
            async with self.bot.di.rm.lock(member.id):
                await self.bot.di.add_eco(member, amount)

        await ctx.send(await _(ctx, "Money given"))

    @checks.mod_or_permissions()
    @commands.command()
    async def takemoney(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Take the member's money
        Example: rp!takemoney 5000 @Henry#6174
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)
        succ = False

        for member in members:
            async with self.bot.di.rm.lock(member.id):
                try:
                    await self.bot.di.take_from_bank(member, amount)
                    succ = True
                except ValueError:
                    await ctx.send((await _(ctx, "Could not take money from {}, user does not have enough")))

        if succ:
            await ctx.send(await _(ctx, "Money taken"))

    @commands.command()
    async def pay(self, ctx, amount: NumberConverter, member: discord.Member):
        """Pay another user money
        Example: rp!pay 500 @Henry#6174"""
        if ctx.author.bot:
            await ctx.send(
                await _(ctx, "Bots don't have money to pay other people! Use rp!givemoney instead of rp!pay"))
            return
        amount = abs(amount)
        async with self.bot.di.rm.lock(ctx.author.id):
            await self.bot.di.add_eco(ctx.author, -amount)
        async with self.bot.di.rm.lock(member.id):
            await self.bot.di.add_eco(member, amount)
        await ctx.send((await _(ctx, "Successfully paid {} dollars to {}")).format(amount, member))

    @commands.group(aliases=["m", "pm"], invoke_without_command=True)
    async def market(self, ctx):
        """View the current market listings"""
        um = await self.bot.di.get_guild_market(ctx.guild)
        market = list(um.values())
        desc = await _(ctx,
                       "\u27A1 to see the next page"
                       "\n\u2B05 to go back"
                       "\n\u274C to exit"
                       )
        if not market:
            await ctx.send(await _(ctx, "No items on the market to display."))
            return

        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title=await _(ctx, "Player Market"), color=randint(0, 0xFFFFFF), )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        clen = 10
        for i in range(0, len(market), clen):
            chunks.append(market[i:i + clen])

        i = 0
        try:
            users = [await ctx.guild.fetch_member(x['user']) for x in chunks[i]]
        except Exception:
            br = []
            fr = dict()
            for listing, data in um.items():
                for datum in data:
                    if 'item' not in listing:
                        id = self.bot.randsample()
                        fr[id] = dict(id=id, item=listing, user=ctx.author.id, cost=datum['cost'],
                                      amount=datum['amount'])
                br.append(listing)

            for i in br:
                del um[i]
            um.update(fr)

            await self.bot.di.update_guild_market(ctx.guild, um)
            market = list(um.items())
            chunks = []
            for i in range(0, len(market), clen):
                chunks.append(market[i:i + clen])

            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])

        currency = await ctx.bot.di.get_currency(ctx.guild)

        fin = [[x['id'], f"{x['cost']} {currency}", f"x{x['amount']}", x['item'], str(y)] for x, y in
               zip(chunks[i], users)]
        fin.insert(0, [await _(ctx, "ID"),
                       await _(ctx, "COST"),
                       await _(ctx, "NUMBER"),
                       await _(ctx, "ITEM"),
                       await _(ctx, "SELLER")])
        embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

        max = len(chunks) - 1

        msg = await ctx.send(embed=embed)
        for emote in emotes:
            await msg.add_reaction(emote)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
            except asyncio.TimeoutError:
                await ctx.send(await _(ctx, "Timed out! Try again"))
                await msg.delete()
                return

            if u == ctx.guild.me:
                continue

            if u != ctx.author or r.emoji not in emotes:
                try:
                    await msg.remove_reaction(r.emoji, u)
                except:
                    pass
                continue

            if r.emoji == emotes[0]:
                if i == 0:
                    pass
                else:
                    i -= 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"{x['cost']} dollars", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, [await _(ctx, "ID"),
                                   await _(ctx, "COST"),
                                   await _(ctx, "NUMBER"),
                                   await _(ctx, "ITEM"),
                                   await _(ctx, "SELLER")])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"{x['cost']} dollars", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, [await _(ctx, "ID"),
                                   await _(ctx, "COST"),
                                   await _(ctx, "NUMBER"),
                                   await _(ctx, "ITEM"),
                                   await _(ctx, "SELLER")])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send("Closing")
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @market.command(aliases=["createlisting", "new", "listitem", "list"])
    async def create(self, ctx, cost: NumberConverter, amount: IntConverter, *, item: str):
        """Create a new market listing. The listing will return a unique identifier for the item.
         This is used to buy the item later.

        Example: rp!market list 500 12 Apple
        This will list 12 Apples from your inventory for $500"""
        amount = abs(amount)
        cost = abs(cost)
        market = await self.bot.di.get_guild_market(ctx.guild)

        async with self.bot.di.rm.lock(ctx.author.id):
            try:
                await self.bot.di.take_items(ctx.author, (item, amount))
            except ValueError:
                await ctx.send(await _(ctx, "You don't have enough of these to sell!"))
                return

        id = self.bot.randsample()
        market[id] = dict(id=id, item=item, user=ctx.author.id, cost=cost, amount=amount)

        async with self.bot.di.rm.lock(ctx.guild.id):
            await self.bot.di.update_guild_market(ctx.guild, market)

        await ctx.send((await _(ctx, "Item listed with ID {}")).format(id))

    @market.command(aliases=["purchase", "acheter"])
    async def buy(self, ctx, id: str):
        """Buy a listing from the player market.

        Example: rp!market buy CRP1I7
        IDs for items can be found in rp!market"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            market = await self.bot.di.get_guild_market(ctx.guild)
            item = market.pop(id)

            if not item:
                await ctx.send(await _(ctx, "That is not a valid ID!"))
                return

            try:
                await self.bot.di.add_eco(ctx.author, -item['cost'])
            except ValueError:
                await ctx.send(await _(ctx, "You cant afford this item!"))
                return

            owner = discord.utils.get(ctx.guild.members, id=item["user"])
            if owner is None:
                owner = discord.Object(item["user"])
                owner.guild = ctx.guild

            async with self.bot.di.rm.lock(owner.id):
                await self.bot.di.add_eco(owner, item['cost'])

            async with self.bot.di.rm.lock(ctx.author.id):
                await self.bot.di.give_items(ctx.author, (item["item"], item["amount"]))

            await self.bot.di.update_guild_market(ctx.guild, market)
        await ctx.send(await _(ctx, "Items successfully bought"))
        if not isinstance(owner, discord.Object):
            await owner.send((await _(ctx,
                                      "{} bought {} {} from you for {} dollars with ID {} on server {}")).format(
                ctx.author, item["item"], item["amount"], item['cost'], id, ctx.guild.name))

    @market.command()
    async def search(self, ctx, *, item: str):
        """Search the market for an item.
        Example: rp!market search Banana"""
        um = await self.bot.di.get_guild_market(ctx.guild)
        market = [i for i in um.values() if i['item'] == item]
        desc = await _(ctx, """
        \u27A1 to see the next page
        \u2B05 to go back
        \u274C to exit
        """)
        if not market:
            await ctx.send(await _(ctx, "No items on the market to display."))
            return

        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title=await _(ctx, "Player Market"), color=randint(0, 0xFFFFFF), )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        for i in range(0, len(market), 25):
            chunks.append(market[i:i + 25])

        i = 0
        try:
            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])
        except Exception:
            br = []
            fr = dict()
            for listing, data in um.items():
                for datum in data:
                    if 'item' not in listing:
                        id = self.bot.randsample()
                        fr[id] = dict(id=id, item=listing, user=ctx.author.id, cost=datum['cost'],
                                      amount=datum['amount'])
                br.append(listing)

            for i in br:
                del um[i]
            um.update(fr)

            await self.bot.di.update_guild_market(ctx.guild, um)
            market = list(um.items())
            chunks = []
            for i in range(0, len(market), 25):
                chunks.append(market[i:i + 25])

            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])

        # items = [f"{x['id']}\t| {x['cost']} dollars\t| x{x['amount']}\t| {x['item']}\t| {y.mention}" for x, y in zip(chunks[i], users)]
        # items.insert(0, "ID\t\t| COST\t\t| NUMBER\t\t| ITEM\t\t| SELLER")
        fin = [[x['id'], f"{x['cost']} dollars", f"x{x['amount']}", x['item'], str(y)] for x, y in
               zip(chunks[i], users)]
        fin.insert(0, [await _(ctx, "ID"),
                       await _(ctx, "COST"),
                       await _(ctx, "NUMBER"),
                       await _(ctx, "ITEM"),
                       await _(ctx, "SELLER")])
        embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

        max = len(chunks) - 1

        msg = await ctx.send(embed=embed)
        for emote in emotes:
            await msg.add_reaction(emote)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
            except asyncio.TimeoutError:
                await ctx.send(await _(ctx, "Timed out! Try again"))
                await msg.delete()
                return

            if u == ctx.guild.me:
                continue

            if u != ctx.author or r.emoji not in emotes:
                try:
                    await msg.remove_reaction(r.emoji, u)
                except:
                    pass
                continue

            if r.emoji == emotes[0]:
                if i == 0:
                    pass
                else:
                    i -= 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"{x['cost']} dollars", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, [await _(ctx, "ID"),
                                   await _(ctx, "COST"),
                                   await _(ctx, "NUMBER"),
                                   await _(ctx, "ITEM"),
                                   await _(ctx, "SELLER")])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"{x['cost']} dollars", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, [await _(ctx, "ID"),
                                   await _(ctx, "COST"),
                                   await _(ctx, "NUMBER"),
                                   await _(ctx, "ITEM"),
                                   await _(ctx, "SELLER")])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send(await _(ctx, "Closing"))
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @market.command(aliases=["rm"], name="remove")
    async def _market_remove(self, ctx, id: str):
        """Remove an item from the market"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            market = await self.bot.di.get_guild_market(ctx.guild)
            try:
                item = market.pop(id)
            except KeyError:
                await ctx.send(await _(ctx, "That is not a valid ID!"))
                return

            if item["user"] == ctx.author.id:
                await self.bot.di.give_items(ctx.author, (item["item"], item["amount"]))
                await self.bot.di.update_guild_market(ctx.guild, market)
            else:
                await ctx.send(await _(ctx, "This is not your item to remove!"))

    @commands.group(invoke_without_command=True, aliases=['lottery'])
    async def lotto(self, ctx):
        """List the currently running lottos."""
        if ctx.guild.id in self.bot.lotteries:
            embed = discord.Embed(color=randint(0, 0xFFFFFF))
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
            embed.set_thumbnail(
                url="https://mir-s3-cdn-cf.behance.net/project_modules/disp/196b9d18843737.562d0472d523f.png"
            )

            for lotto, value in self.bot.lotteries[ctx.guild.id].items():
                embed.add_field(name=lotto,
                                value=(await _(ctx, "Jackpot: {} dollars\n{} players entered")).format(value["jackpot"],
                                                                                                       len(value[
                                                                                                               "players"])))
            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send(await _(ctx, "No lotteries currently running!"))

    @checks.mod_or_permissions()
    @lotto.command(aliases=["delete"])
    async def cancel(self, ctx, name: str):
        """Cancel a lottery
        Example: rp!lotto cancel MyLotto
        Requires Bot Moderator or Bot Admin"""
        try:
            del self.bot.lotteries[ctx.guild.id][name]
        except KeyError:
            await ctx.send(await _(ctx, "There is no lottery of that name!"))

    @checks.mod_or_permissions()
    @lotto.command(aliases=["create"])
    async def new(self, ctx, name: str, jackpot: NumberConverter, time: NumberConverter):
        """Create a new lotto, with jackpot payout lasting time in seconds.
        Requires Bot Moderator or Bot Admin
        For example: `rp!lotto create MyLotto 5000 3600` will create a new lotto called MyLotto
        (rp!lotto enter MyLotto to join), which has a jackpot of 5000 and lasts 1 hour (3600 seconds)"""
        if ctx.guild.id not in self.bot.lotteries:
            self.bot.lotteries[ctx.guild.id] = dict()
        if name in self.bot.lotteries[ctx.guild.id]:
            await ctx.send(await _(ctx, "A lottery of that name already exists!"))
            return
        current = dict(jackpot=jackpot, players=list(), channel=ctx.channel.id)
        self.bot.lotteries[ctx.guild.id][name] = current
        await ctx.send(await _(ctx, "Lottery created!"))
        await asyncio.sleep(time)
        if name in self.bot.lotteries[ctx.guild.id]:
            if current["players"]:
                winner = discord.utils.get(ctx.guild.members, id=choice(current["players"]))

                async with self.bot.di.rm.lock(winner.id):
                    await self.bot.di.add_eco(winner, current["jackpot"])
                await ctx.send(
                    (await _(ctx, "Lottery {} is now over!\n{} won {}! Congratulations!")).format(name, winner.mention,
                                                                                                  current["jackpot"]))
            else:
                await ctx.send((await _(ctx, "Nobody entered {}! Its over now.")).format(name))
            del self.bot.lotteries[ctx.guild.id][name]

    @lotto.command(aliases=["join"])
    async def enter(self, ctx, *, name: str):
        """Enter the lottery with the given name.
        For example: `rp!lotto enter MyLotto` to join the lotto with the name MyLotto"""
        if ctx.guild.id in self.bot.lotteries:
            if name in self.bot.lotteries[ctx.guild.id]:
                if ctx.author.id not in self.bot.lotteries[ctx.guild.id][name]["players"]:
                    self.bot.lotteries[ctx.guild.id][name]["players"].append(ctx.author.id)
                    await ctx.send(await _(ctx, "Lotto entered!"))
                else:
                    await ctx.send(await _(ctx, "You're already in this lotto!"))
            else:
                await ctx.send(await _(ctx, "This server has no lotto by that name! See rp!lotto"))
        else:
            await ctx.send(await _(ctx, "This server has no lottos currently running!"))

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Get all items currently listed on the server shop"""
        shop = sorted((await self.bot.di.get_guild_shop(ctx.guild)).items(), key=lambda x: x[0])

        if not shop:
            await ctx.send(await _(ctx, "No items in the shop to display."))
            return

        desc = await _(ctx, "\u27A1 to see the next page"
                            "\n\u2B05 to go back"
                            "\n\u274C to exit")

        title = await _(ctx, "Server Shop")
        author = ctx.guild.name
        author_url = ctx.guild.icon_url

        def lfmt(v):
            d = ""
            if v["buy"]:
                d += f"Buy Value: {v['buy']}"
            if v["sell"]:
                d += f"\nSell Value: {v['sell']}"
            if v["level"]:
                d += f"\nLevel: {v['level']}"

            return d

        await create_pages(ctx, shop, lfmt, description=desc, title=title,
                           author=author, author_url=author_url)

    @shop.command(aliases=["add"])
    @checks.mod_or_permissions()
    async def additem(self, ctx, *, name: str):
        """Add an item to the server shop, to make an item unsaleable or unbuyable set their respective values to 0
        rp!shop additem Pokeball
        -> 0
        -> 10
        Can be sold for 10 and cannot be bought. Must be an existing item (Use rp!settings additem first)!
          Requires Bot Moderator or Admin"""

        gd = await self.bot.db.get_guild_data(ctx.guild)
        if name not in gd["items"]:
            await ctx.send(
                await _(ctx, "This item doesn't exist! Try creating the item first with `rp!settings additem`"))
            return

        shop = gd.get("shop_items", dict())
        item = dict(buy=0, sell=0, level=0)
        shop[name] = item
        check = lambda x: x.author is ctx.author and x.channel is ctx.channel

        await ctx.send(await _(ctx, "Say 'cancel' to cancel or 'skip' to skip a step"))
        try:
            while True:
                await ctx.send(await _(ctx, "How much should this be buyable for? 0 for not buyable"))
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["buy"] = float(resp.content)
                except ValueError:
                    if resp.content.lower() == "cancel":
                        await ctx.send(await _(ctx, "Cancelling!"))
                        return
                    await ctx.send(await _(ctx, "That is not a valid number!"))
                    continue
                break

            while True:
                await ctx.send(await _(ctx, "How much should this be sellable for? 0 for not sellable"))
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["sell"] = float(resp.content)
                except ValueError:
                    if resp.content.lower() == "cancel":
                        await ctx.send(await _(ctx, "Cancelling!"))
                        return
                    await ctx.send(await _(ctx, "That is not a valid number!"))
                    continue
                break

            while True:
                await ctx.send(
                    await _(ctx, "What is the minimum level a user must be for this item? 0 for no minimum"))
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["level"] = int(resp.content)
                except ValueError:
                    if resp.content.lower() == "cancel":
                        await ctx.send(await _(ctx, "Cancelling!"))
                        return
                    await ctx.send(await _(ctx, "That is not a valid number!"))
                    continue
                break

            if not sum(item.values()):
                await ctx.send(
                    await _(ctx, "You can't make an item with 0 for every value! Cancelling, try again."))
                return

        except asyncio.TimeoutError:
            await ctx.send(await _(ctx, "Timed out! Cancelling"))
            return

        await self.bot.di.update_guild_shop(ctx.guild, shop)
        await ctx.send(await _(ctx, "Guild shop updated"))

    @shop.command(aliases=["remove"])
    @checks.mod_or_permissions()
    async def removeitem(self, ctx, *, name: str):
        """Remove a listed item
        Example: `rp!shop remove Pokeball`
        Requires Bot Moderator or Bot Admin"""

        shop = await self.bot.di.get_guild_shop(ctx.guild)
        try:
            del shop[name]
        except KeyError:
            await ctx.send(await _(ctx, "That item isn't listed!"))
            return
        await self.bot.di.update_guild_shop(ctx.guild, shop)
        await ctx.send(await _(ctx, "Successfully removed item"))

    @shop.command(name="buy")
    async def _buy(self, ctx, item: str, amount: IntConverter):
        """Buy an item from the shop"""
        amount = abs(amount)

        shop = await self.bot.di.get_guild_shop(ctx.guild)
        ulvl, uexp = await self.bot.di.get_user_level(ctx.author)
        try:
            iobj = shop.get(item)
            if not iobj or not iobj["buy"]:
                await ctx.send(await _(ctx, "This item cannot be bought!"))
                return
            if iobj["level"] > ulvl:
                await ctx.send(await _(ctx, "You aren't high enough level for this item!"))
                return

            async with self.bot.di.rm.lock(ctx.author.id):
                await self.bot.di.add_eco(ctx.author, -iobj["buy"] * amount)
        except ValueError:
            await ctx.send(await _(ctx, "You can't afford this many!"))
            return

        async with self.bot.di.rm.lock(ctx.author.id):
            await self.bot.di.give_items(ctx.author, (item, amount))
        await ctx.send((await _(ctx, "Successfully bought {} {}s")).format(amount, item))

    @shop.command(name="sell")
    async def _sell(self, ctx, item: str, amount: IntConverter):
        """Sell an item to the shop
        Example: rp!shop sell Apple 5"""
        amount = abs(amount)
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        iobj = shop.get(item)
        if not iobj or not iobj["sell"]:
            await ctx.send(await _(ctx, "This item cannot be sold!"))
            return

        async with self.bot.di.rm.lock(ctx.author.id):
            try:
                await self.bot.di.take_items(ctx.author, (item, amount))
            except ValueError:
                await ctx.send(await _(ctx, "You don't have enough to sell"))
                return

            await self.bot.di.add_eco(ctx.author, iobj["sell"] * amount)
        await ctx.send((await _(ctx, "Successfully sold {} {}s")).format(amount, item))

    @commands.command()
    async def startbid(self, ctx, item: str, amount: NumberConverter, startbid: NumberConverter):
        """Start a bid for an item
        Example: `rp!startbid Banana 5 40` This will start a bid for 5 Bananas, starting at $40"""

        if ctx.channel.id in self.bids:
            await ctx.send(await _(ctx, "This channel already has a bid going!"))
            return

        amount = abs(amount)

        async with self.bot.di.rm.lock(ctx.author.id):
            try:
                await self.bot.di.take_items(ctx.author, (item, amount))
            except ValueError:
                await ctx.send((await _(ctx, "You do not have x{} {}!")).format(amount, item))
                return

        self.bids.append(ctx.channel.id)
        await ctx.send((await _(ctx,
                                "{} Has started a bid for x{} {} starting at {} dollars\nBid runs for 60 seconds `rp!bid` to place a bid!")
                        ).format(
            ctx.author, amount, item, startbid))
        cb = Counter()

        try:
            with timeout(60, loop=self.bot.loop):
                while True:
                    resp = await self.bot.wait_for("message", check=lambda x: x.content.startswith(
                        "rp!bid") and x.channel == ctx.channel)
                    try:
                        bid = abs(int(resp.content[6:]))
                        if bid < startbid:
                            continue
                        cb[resp.author] = bid
                    except ValueError:
                        continue
        except asyncio.TimeoutError:
            pass

        await ctx.send(await _(ctx, "Bid over!"))

        if not cb:
            await ctx.send(await _(ctx, "Nobody bid!"))

            async with self.bot.di.rm.lock(ctx.author.id):
                await self.bot.di.give_items(ctx.author, (item, amount))
            self.bids.remove(ctx.channel.id)
            return

        for x in range(len(cb)):
            winner, wamount = cb.most_common(x + 1)[x]
            wb = await self.bot.di.get_balance(winner)
            if wb >= wamount:
                async with self.bot.di.rm.lock(winner.id):
                    await ctx.send((await _(ctx, "{} won the bid for {} dollars!")).format(winner, amount))
                    await self.bot.di.add_eco(winner, -wamount)
                    await self.bot.di.give_items(winner, (item, amount))

                async with self.bot.di.rm.lock(ctx.author.id):
                    await self.bot.di.add_eco(ctx.author, wamount)
                break
        else:
            await ctx.send(await _(ctx, "Nobody bid and had enough money to pay for it!"))
            async with self.bot.di.rm.lock(ctx.author.id):
                await self.bot.di.give_items(ctx.author, (item, amount))

        self.bids.remove(ctx.channel.id)

    @commands.command()
    async def bid(self, ctx):
        """Place a bid on the current bidding item in the channel. `rp!bid 5`"""

    @commands.command()
    async def baltop(self, ctx):
        """Get the top 10 server balances"""
        req = f"""SELECT (UUID, info->'{ctx.guild.id}'->>'money') FROM userdata;"""
        async with self.bot.db._conn.acquire() as connection:
            resp = await connection.fetch(req)

        users = [(discord.utils.get(ctx.guild.members, id=int(x["row"][0])), x["row"][1]) for x in resp if
                 (len(x["row"]) == 2) and (x["row"][1] is not None)]
        users = [x for x in users if x[0]]
        users.sort(key=lambda x: -float(x[1]))

        currency = await ctx.bot.di.get_currency(ctx.guild)
        msg = "\n".join(f"{x}: {y[0]} {y[1]} {currency}" for x, y in zip(range(1, 11), users))
        await ctx.send(f"```\n{msg}\n```")

    @commands.group(aliases=["banc"], invoke_without_command=True)
    async def bank(self, ctx):
        bal = (await self.bot.di.get_all_balances(ctx.author))[1]

        await ctx.send(
            (await _(ctx, "You have {} dollars in the bank")).format(int(bal) if int(bal) == bal else bal)
        )

    @bank.command()
    async def deposit(self, ctx, amount: float):
        """Deposit `amount` into the bank.
        Example: rp!bank deposit 500.3"""

        async with self.bot.di.rm.lock(ctx.author.id):
            bal = (await self.bot.di.get_all_balances(ctx.author))
            if amount > bal[0]:
                await ctx.send(await _(ctx, "You don't have enough to deposit!"))
                return
            await ctx.bot.di.set_balances(ctx.author, bal[0] - amount, bal[1] + amount)

            await ctx.send(
                (await _(ctx,
                         "Successfully transferred {} dollars to your bank. You have {} dollars total in the bank")).format(
                    amount,
                    bal[1] + amount))

    @bank.command()
    async def withdraw(self, ctx, amount: float):
        """Withdraw `amount` from the bank
        Example: rp!bank withdraw 499"""

        async with self.bot.di.rm.lock(ctx.author.id):
            bal = (await self.bot.di.get_all_balances(ctx.author))
            if amount > bal[1]:
                await ctx.send(await _(ctx, "You don't have enough to withdraw!"))
                return
            await ctx.bot.di.set_balances(ctx.author, bal[0] + amount, bal[1] - amount)

            await ctx.send((await _(ctx,
                                    "Successfully transferred {} dollars from your bank. You have {} dollars total in the bank")).format(
                amount, bal[1] - amount))
