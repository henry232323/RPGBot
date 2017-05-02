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

from random import choice
import asyncio

from .utils.data import Converter
from .utils import checks


class Economy(object):
    """Economy related commands: balance, market, etc"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["bal", "balance", "eco", "e"], no_pm=True, invoke_without_command=True)
    async def economy(self, ctx, member: discord.Member=None):
        """Check your or another users balance"""
        if member is None:
            member = ctx.author

        bal = await self.bot.di.get_balance(member)

        await ctx.send(f"{member.display_name} has {bal} Pokédollars")

    @checks.mod_or_permissions()
    @economy.command(aliases=["set"], no_pm=True)
    async def setbalance(self, ctx, amount: int, *members: Converter):
        """Set the balance of the given members to an amount"""
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.set_eco(member, amount)

        await ctx.send("Balances changed")

    @checks.mod_or_permissions()
    @economy.command(aliases=["give"], no_pm=True)
    async def givemoney(self, ctx, amount: int, *members: Converter):
        """Give the members money (Moderators)"""
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.add_eco(member, amount)

        await ctx.send("Money given")

    @commands.command(no_pm=True)
    async def pay(self, ctx, amount: int, member: discord.Member):
        """Pay another user money"""
        amount = abs(amount)
        await self.bot.di.add_eco(ctx.author, -amount)
        await self.bot.di.add_eco(member, amount)
        await ctx.send(f"Successfully paid {amount} Pokédollars to {member}")

    @commands.group(no_pm=True, aliases=["m", "pm"], invoke_without_command=True)
    async def market(self, ctx):
        """View the current market listings"""
        market = list((await self.bot.di.get_guild_market(ctx.guild)).items())
        desc = """
        \u27A1 to see the next page
        \u2B05 to go back
        \u274C to exit
        """
        if not market:
            await ctx.send("No items on the market to display.")
            return
        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title="Player Market")
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        for i in range(0, len(market), 25):
            chunks.append(market[i:i + 25])

        i = 0
        for item, value in chunks[i]:
            fmt = "\n".join(str(discord.utils.get(ctx.guild.members, id=x['user'])) + f": \u20BD{x['cost']} x{x['amount']}" for x in value)
            embed.add_field(name=item, value=fmt)

        max = len(chunks) - 1

        msg = await ctx.send(embed=embed)
        for emote in emotes:
            await msg.add_reaction(emote)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
            except asyncio.TimeoutError:
                await ctx.send("Timed out! Try again")
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
                    embed.clear_fields()
                    i -= 1
                    for item, value in chunks[i]:
                        fmt = "\n".join(str(
                            discord.utils.get(ctx.guild.members, id=x['user'])) + f": \u20BD{x['cost']} x{x['amount']}"
                                        for x in value)
                        embed.add_field(name=item, value=fmt)

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    for item, value in chunks[i]:
                        fmt = "\n".join(str(
                            discord.utils.get(ctx.guild.members, id=x['user'])) + f": \u20BD{x['cost']} x{x['amount']}"
                                        for x in value)
                        embed.add_field(name=item, value=fmt)

                    await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send("Closing")
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @market.command(no_pm=True, aliases=["createlisting", "new", "listitem", "list"])
    async def create(self, ctx, cost: int, amount: int, *, item: str):
        """Create a new market listing"""
        amount = abs(amount)
        cost = abs(cost)
        market = await self.bot.di.get_guild_market(ctx.guild)
        items = await self.bot.di.get_guild_items(ctx.guild)

        if item not in items:
            await ctx.send("That is not a valid item!")
            return

        if item not in market:
            market[item] = list()

        try:
            await self.bot.di.take_items(ctx.author, (item, amount))
        except ValueError:
            await ctx.send("You dont have enough of these to sell!")
            return

        for listing in market[item]:
            if listing["user"] == ctx.author.id and listing["cost"] == cost:
                listing["amount"] += amount
                break
        else:
            market[item].append(dict(user=ctx.author.id, cost=cost, amount=amount))

        await self.bot.di.update_guild_market(ctx.guild, market)

        await ctx.send("Item listed!")

    @market.command(no_pm=True, aliases=["purchase"])
    async def buy(self, ctx, amount: int, *, item: str):
        """Buy a given amount of an item from the player market at the cheapest given price"""
        amount = abs(amount)
        market = await self.bot.di.get_guild_market(ctx.guild)
        items = market.get(item)
        if not items:
            await ctx.send("There are none of those on the market! Sorry")
            return

        fcost = 0
        remaining = amount
        while remaining:
            m = min(items, key=lambda x: x.cost)
            if m.amount < remaining:
                items.remove(m)
                remaining -= m.amount
                fcost += m.amount * m.cost
            else:
                m.amount -= amount
                fcost += m.cost * amount

        try:
            await self.bot.di.add_eco(-fcost)
        except ValueError:
            await ctx.send("You cant afford this many!")
            return

        await self.bot.di.give_items(ctx.author, (item, amount))
        await self.bot.di.update_guild_market(ctx.guild, market)
        await ctx.send("Items successfully bought")

    @commands.group(invoke_without_command=True, aliases=['lb'], no_pm=True)
    async def lootbox(self, ctx):
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
                value = "Cost: {}\n\t".format(data["cost"]) + "\n\t".join(fmt.format(item, (value/total)*100) for item, value in data["items"].items())
                embed.add_field(name=box,
                                value=value)

            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send("No current lootboxes")

    @checks.mod_or_permissions()
    @lootbox.command(name="create", aliases=["new"], no_pm=True)
    async def _create(self, ctx, name: str, cost: int, *items: str):
        """Create a new lootbox, under the given `name` for the given cost
        Use {item}x{#} notation to add items with {#} weight
        Weight being an integer. For example:
        bananax2 orangex3. The outcome of the box will be
        Random Choice[banana, banana, orange, orange, orange]"""

        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            await ctx.send("Lootbox already exists, updating...")

        winitems = {}
        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            winitems.update({split: num})

            boxes[name] = dict(cost=cost, items=winitems)

        await ctx.send("Lootbox successfully created")
        await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)

    @lootbox.command(name="buy", no_pm=True)
    async def _buy(self, ctx, name: str):
        """Buy a lootbox of the given name"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        try:
            box = boxes[name]
        except KeyError:
            await ctx.send("That is not a valid lootbox")
            return

        bal = await self.bot.di.get_balance(ctx.author)
        if bal < box["cost"]:
            await ctx.send("You cant afford this box")
            return

        await self.bot.di.add_eco(ctx.author, box["cost"])
        winitems = []
        for item, amount in box["items"].items():
            winitems += [item] * amount

        result = choice(winitems)
        await self.bot.di.give_items(ctx.author, (result, 1))
        await ctx.send("You won a(n) {}".format(result))

    @lootbox.command(name="delete", aliases=["remove"], no_pm=True)
    async def _delete(self, ctx, name: str):
        """Delete a lootbox with the given name"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            del boxes[name]
            await ctx.send("Loot box removed")
        else:
            await ctx.send("Invalid loot box")

            await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)

    @commands.group(invoke_without_command=True, aliases=['lottery'], no_pm=True)
    async def lotto(self, ctx):
        """List the currently running lottos."""
        if ctx.guild.id in self.bot.lotteries:
            embed = discord.Embed()
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
            embed.set_thumbnail(
                url="https://mir-s3-cdn-cf.behance.net/project_modules/disp/196b9d18843737.562d0472d523f.png"
            )

            for lotto, value in self.bot.lotteries[ctx.guild.id].items():
                embed.add_field(name=lotto,
                                value="Jackpot: {} Pokédollars\n{} players entered".format(value["jackpot"],
                                                                                  len(value["players"])))
            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send("No lotteries currently running!")

    @checks.mod_or_permissions()
    @lotto.command(aliases=["create"], no_pm=True)
    async def new(self, ctx, name: str, jackpot: int, time: int):
        """Create a new lotto, with jacpot payout lasting time in seconds"""
        if ctx.guild.id not in self.bot.lotteries:
            self.bot.lotteries[ctx.guild.id] = dict()
        if name in self.bot.lotteries[ctx.guild.id]:
            await ctx.send("A lottery of that name already exists!")
            return
        current = dict(jackpot=jackpot, players=list(), channel=ctx.channel)
        self.bot.lotteries[ctx.guild.id][name] = current
        await ctx.send("Lottery created!")
        await asyncio.sleep(time)
        if current["players"]:
            winner = choice(current["players"])
            await self.bot.di.add_eco(winner, current["jackpot"])
            await current["channel"].send("Lottery {} is now over!\n{} won {}! Congratulations!".format(name, winner.mention, current["jackpot"]))
        else:
            await ctx.send("Nobody entered {}! Its over now.".format(name))
        del self.bot.lotteries[ctx.guild.id][name]

    @lotto.command(aliases=["join"], no_pm=True)
    async def enter(self, ctx, name: str):
        """Enter the lottery with the given name."""
        if ctx.guild.id in self.bot.lotteries:
            if name in self.bot.lotteries[ctx.guild.id]:
                if ctx.author not in self.bot.lotteries[ctx.guild.id][name]["players"]:
                    self.bot.lotteries[ctx.guild.id][name]["players"].append(ctx.author)
                    await ctx.send("Lotto entered!")
                else:
                    await ctx.send("You're already in this lotto!")
            else:
                await ctx.send("This server has no lotto by that name! See ;lotto")
        else:
            await ctx.send("This server has no lottos currently running!")

    @commands.group(no_pm=True, invoke_without_command=True)
    async def shop(self, ctx):
        shop = list((await self.bot.di.get_guild_shop(ctx.guild)).items())
        desc = """
                \u27A1 to see the next page
                \u2B05 to go back
                \u274C to exit
                """
        if not shop:
            await ctx.send("No items in the shop to display.")
            return
        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title="Server Shop")
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        for i in range(0, len(shop), 25):
            chunks.append(shop[i:i + 25])

        i = 0
        for item, value in chunks[i]:
            fmt = f"Buy Value: {value['buy']}\nSell Value: {value['sell']}"
            embed.add_field(name=item, value=fmt)

        max = len(chunks) - 1

        msg = await ctx.send(embed=embed)
        for emote in emotes:
            await msg.add_reaction(emote)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
            except asyncio.TimeoutError:
                await ctx.send("Timed out! Try again")
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
                    embed.clear_fields()
                    i -= 1
                    for item, value in chunks[i]:
                        fmt = f"Buy Value: {value['buy']}\nSell Value: {value['sell']}"
                        embed.add_field(name=item, value=fmt)

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    for item, value in chunks[i]:
                        fmt = f"Buy Value: {value['buy']}\nSell Value: {value['sell']}"
                        embed.add_field(name=item, value=fmt)

                    await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send("Closing")
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @shop.command(no_pm=True)
    @checks.mod_or_permissions()
    async def additem(self, ctx, name: str, buyvalue: int=0, sellvalue: int=0):
        """Add an item to the server shop, to make an item unsaleable or unbuyable set their respective values to 0
        pb!additem Pokeball 0 10
        Can be sold for 10 and cannot be bought. Must be an existing item!"""
        gd = await self.bot.db.get_guild_data(ctx.guild)
        if name not in gd.items():
            await ctx.send("This item doesn't exist!")
            return

        shop = gd["shop_items"]
        item = dict(buy=buyvalue, sell=sellvalue)
        shop[name] = item

        await self.bot.di.update_guild_shop(shop)
        await ctx.send("Guild shop updated")

    @shop.command(no_pm=True)
    @checks.mod_or_permissions()
    async def removeitem(self, ctx, name: str):
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        try:
            del shop[name]
        except KeyError:
            await ctx.send("That item isn't listed!")
            return
        await self.bot.di.update_guild_shop(shop)
        await ctx.send("Successfully removed item")

    @shop.command(no_pm=True)
    async def buy(self, ctx, item: str, amount: int):
        amount = abs(amount)
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        try:
            item = shop[item]
            await self.bot.add_eco(ctx.author, -item["buy"] * amount)
        except KeyError:
            await ctx.send("This item cannot be bought!")
            return
        except ValueError:
            await ctx.send("You can't afford this many!")
            return

        await self.bot.di.add_items(ctx.author, (item, amount))
        await ctx.send(f"Successfully bought {amount} {item}s")

    @shop.command(no_pm=True)
    async def sell(self, ctx, item: str, amount: int):
        amount = abs(amount)
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        try:
            item = shop[item]
            await self.bot.add_eco(ctx.author, item["sell"] * amount)
        except KeyError:
            await ctx.send("This item cannot be sold!")
            return

        try:
            await self.bot.di.take_items(ctx.author, (item, amount))
        except ValueError:
            await ctx.send("You don't have enough to sell")
            return

        await ctx.send(f"Successfully bought {amount} {item}s")