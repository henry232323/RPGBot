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

from async_timeout import timeout
from collections import Counter
from random import choice
import asyncio

from .utils.data import Converter, get
from .utils import checks


class Economy(object):
    """Economy related commands: balance, market, etc"""
    def __init__(self, bot):
        self.bot = bot
        self.bids = list()

    @checks.no_pm()
    @commands.group(aliases=["bal", "balance", "eco", "e"], invoke_without_command=True)
    async def economy(self, ctx, member: discord.Member=None):
        """Check your or another users balance"""
        if member is None:
            member = ctx.author

        bal = await self.bot.di.get_balance(member)

        await ctx.send(f"{member.display_name} has ${bal}")

    @checks.no_pm()
    @checks.mod_or_permissions()
    @economy.command(aliases=["set"])
    async def setbalance(self, ctx, amount: int, *members: Converter):
        """Set the balance of the given members to an amount"""
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.set_eco(member, amount)

        await ctx.send("Balances changed")

    @checks.no_pm()
    @checks.mod_or_permissions()
    @economy.command(aliases=["give"])
    async def givemoney(self, ctx, amount: int, *members: Converter):
        """Give the members money (Moderators)"""
        if "everyone" in members:
            members = ctx.guild.members

        for member in members:
            await self.bot.di.add_eco(member, amount)

        await ctx.send("Money given")

    @checks.no_pm()
    @commands.command()
    async def pay(self, ctx, amount: int, member: discord.Member):
        """Pay another user money"""
        amount = abs(amount)
        await self.bot.di.add_eco(ctx.author, -amount)
        await self.bot.di.add_eco(member, amount)
        await ctx.send(f"Successfully paid ${amount} to {member}")

    @checks.no_pm()
    @commands.group(aliases=["m", "pm"], invoke_without_command=True)
    async def market(self, ctx):
        """View the current market listings"""
        um = await self.bot.di.get_guild_market(ctx.guild)
        market = list(um.values())
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
        try:
            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])
        except Exception:
            br = []
            fr = dict()
            for listing, data in um.items():
                for datum in data:
                    if 'item' not in listing:
                        id = self.bot.randsample()
                        fr[id] = dict(id=id, item=listing, user=ctx.author.id, cost=datum['cost'], amount=datum['amount'])
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

        #embed.description = "\n".join(f"{x['id']}: ${x['cost']} for x{x['amount']} {x['item']} from {y.mention}" for x, y in zip(chunks[i], users))

        fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in zip(chunks[i], users)]
        fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
        embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

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
                    i -= 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
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

    @checks.no_pm()
    @market.command(aliases=["createlisting", "new", "listitem", "list"])
    async def create(self, ctx, cost: int, amount: int, *, item: str):
        """Create a new market listing"""
        amount = abs(amount)
        cost = abs(cost)
        market = await self.bot.di.get_guild_market(ctx.guild)

        try:
            await self.bot.di.take_items(ctx.author, (item, amount))
        except ValueError:
            await ctx.send("You dont have enough of these to sell!")
            return

        id = self.bot.randsample()
        market[id] = dict(id=id, item=item, user=ctx.author.id, cost=cost, amount=amount)

        await self.bot.di.update_guild_market(ctx.guild, market)

        await ctx.send("Item listed!")

    @checks.no_pm()
    @market.command(aliases=["purchase"])
    async def buy(self, ctx, id: str):
        """Buy a given amount of an item from the player market at the cheapest given price"""
        market = await self.bot.di.get_guild_market(ctx.guild)
        item = market.get(id)

        if not item:
            await ctx.send("That is not a valid ID!")
            return

        try:
            await self.bot.di.add_eco(-item['cost'])
        except ValueError:
            await ctx.send("You cant afford this item!")
            return

        await self.bot.di.give_items(ctx.author, (item["item"], item["amount"]))
        await self.bot.di.update_guild_market(ctx.guild, market)
        await ctx.send("Items successfully bought")

        await discord.utils.get(ctx.guild.members, id=item["owner"]).send(f"{ctx.author} bought {item['item']} {item['amount']} from you for ${item['cost']} with ID {id} on server {ctx.guild}")

    @checks.no_pm()
    @market.command()
    async def search(self, ctx, item: str):
        """Search the market for an item"""
        um = await self.bot.di.get_guild_market(ctx.guild)
        market = [i for i in um.values() if i['item'] == item]
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
        try:
            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])
        except Exception as e:
            br = []
            fr = dict()
            for listing, data in um.items():
                for datum in data:
                    if 'item' not in listing:
                        id = self.bot.randsample()
                        fr[id] = dict(id=id, item=listing, user=ctx.author.id, cost=datum['cost'], amount=datum['amount'])
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

        # items = [f"{x['id']}\t| ${x['cost']}\t| x{x['amount']}\t| {x['item']}\t| {y.mention}" for x, y in zip(chunks[i], users)]
        # items.insert(0, "ID\t\t| COST\t\t| NUMBER\t\t| ITEM\t\t| SELLER")
        fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in zip(chunks[i], users)]
        fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
        embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

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
                    i -= 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
                    embed.description = "```\n{}\n```".format(self.bot.format_table(fin))

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                    fin = [[x['id'], f"${x['cost']}", f"x{x['amount']}", x['item'], str(y)] for x, y in
                           zip(chunks[i], users)]
                    fin.insert(0, ["ID", "COST", "NUMBER", "ITEM", "SELLER"])
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
                value = "Cost: {}\n\t".format(data["cost"]) + "\n\t".join(fmt.format(item, (value/total)*100) for item, value in data["items"].items())
                embed.add_field(name=box,
                                value=value)

            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send("No current lootboxes")

    @checks.no_pm()
    @checks.mod_or_permissions()
    @lootbox.command(name="create", aliases=["new"])
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

    @checks.no_pm()
    @lootbox.command(name="buy")
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

    @checks.no_pm()
    @lootbox.command(name="delete", aliases=["remove"])
    async def _delete(self, ctx, name: str):
        """Delete a lootbox with the given name"""
        boxes = await self.bot.di.get_guild_lootboxes(ctx.guild)
        if name in boxes:
            del boxes[name]
            await ctx.send("Loot box removed")
        else:
            await ctx.send("Invalid loot box")

            await self.bot.di.update_guild_lootboxes(ctx.guild, boxes)

    @checks.no_pm()
    @commands.group(invoke_without_command=True, aliases=['lottery'])
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
                                value="Jackpot: ${}\n{} players entered".format(value["jackpot"],
                                                                                  len(value["players"])))
            embed.set_footer(text=str(ctx.message.created_at))

            await ctx.send(embed=embed)
        else:
            await ctx.send("No lotteries currently running!")

    @checks.no_pm()
    @checks.mod_or_permissions()
    @lotto.command(aliases=["create"])
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

    @checks.no_pm()
    @lotto.command(aliases=["join"])
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

    @checks.no_pm()
    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Get all items currently listed on the server shop"""
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

        def lfmt(v):
            d = ""
            if value["buy"]:
                d += f"Buy Value: {value['buy']}"
            if value["sell"]:
                d += f"\nSell Value: {value['sell']}"
            if value["level"]:
                d += f"\nLevel: {value['level']}"

            return d

        for item, value in chunks[i]:
            fmt = lfmt(value)
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
                        fmt = lfmt(value)
                        embed.add_field(name=item, value=fmt)

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    for item, value in chunks[i]:
                        fmt = lfmt(value)
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

    @checks.no_pm()
    @shop.command(aliases=["add"])
    @checks.mod_or_permissions()
    async def additem(self, ctx, name: str):
        """Add an item to the server shop, to make an item unsaleable or unbuyable set their respective values to 0
        pb!additem Pokeball
        -> 0
        -> 10
        Can be sold for 10 and cannot be bought. Must be an existing item! Requires Bot Moderator or Admin"""
        gd = await self.bot.db.get_guild_data(ctx.guild)
        if name not in gd["items"]:
            await ctx.send("This item doesn't exist!")
            return

        shop = gd.get("shop_items", dict())
        item = dict(buy=0, sell=0, level=0)
        shop[name] = item
        check = lambda x: x.author is ctx.author and x.channel is ctx.channel

        await ctx.send("Say 'cancel' to cancel or 'skip' to skip a step")
        try:
            while True:
                await ctx.send("How much should this be buyable for? 0 for not buyable")
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["buy"] = int(resp.content)
                except ValueError:
                    await ctx.send("That is not a valid number!")
                    continue
                break

            while True:
                await ctx.send("How much should this be sellable for? 0 for not sellable")
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["sell"] = int(resp.content)
                except ValueError:
                    await ctx.send("That is not a valid number!")
                    continue
                break

            while True:
                await ctx.send("What is the minimum level a user must be for this item? 0 for no minimum")
                resp = await self.bot.wait_for("message", check=check)
                try:
                    item["level"] = int(resp.content)
                except ValueError:
                    await ctx.send("That is not a valid number!")
                    continue
                break

            if not sum(item.values()):
                await ctx.send("You can't make an item with 0 for every value! Cancelling, try again.")
                return

        except asyncio.TimeoutError:
            await ctx.send("Timed out! Cancelling")
            return

        await self.bot.di.update_guild_shop(ctx.guild, shop)
        await ctx.send("Guild shop updated")

    @checks.no_pm()
    @shop.command()
    @checks.mod_or_permissions()
    async def removeitem(self, ctx, name: str):
        """Remove a listed item"""
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        try:
            del shop[name]
        except KeyError:
            await ctx.send("That item isn't listed!")
            return
        await self.bot.di.update_guild_shop(shop)
        await ctx.send("Successfully removed item")

    @checks.no_pm()
    @shop.command()
    async def buy(self, ctx, item: str, amount: int):
        """Buy an item from the shop"""
        amount = abs(amount)
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        ulvl, uexp = await self.bot.di.get_user_level(ctx.author)
        try:
            item = shop[item]
            if not item["buy"]:
                await ctx.send("This item cannot be bought!")
                return
            if item["level"] > ulvl:
                await ctx.send("You aren't high enough level for this item!")
                return
            await self.bot.add_eco(ctx.author, -item["buy"] * amount)
        except ValueError:
            await ctx.send("You can't afford this many!")
            return

        await self.bot.di.add_items(ctx.author, (item, amount))
        await ctx.send(f"Successfully bought {amount} {item}s")

    @checks.no_pm()
    @shop.command()
    async def sell(self, ctx, item: str, amount: int):
        """Sell an item to the shop"""
        amount = abs(amount)
        shop = await self.bot.di.get_guild_shop(ctx.guild)
        item = shop[item]
        if not item["sell"]:
            await ctx.send("This item cannot be sold!")
            return
        await self.bot.add_eco(ctx.author, item["sell"] * amount)

        try:
            await self.bot.di.take_items(ctx.author, (item, amount))
        except ValueError:
            await ctx.send("You don't have enough to sell")
            return

        await ctx.send(f"Successfully sell {amount} {item}s")

    @checks.no_pm()
    @commands.command()
    async def startbid(self, ctx, item: str, amount: int, startbid: int):
        """Start a bid for an item"""
        if ctx.channel.id in self.bids:
            await ctx.send("This channel already has a bid going!")
            return

        amount = abs(amount)
        try:
            await self.bot.di.take_items(ctx.author, (item, amount))
        except ValueError:
            await ctx.send(f"You do not have x{amount} {item}!")
            return

        self.bids.append(ctx.channel.id)
        await ctx.send(f"{ctx.author} Has started a bid for x{amount} {item} starting at ${startbid}\nBid runs for 60 seconds `rp!bid` to place a bid!")
        cb = Counter()

        try:
            with timeout(60, loop=self.bot.loop):
                while True:
                    resp = await self.bot.wait_for("message", check=lambda x: x.content.startswith("rp!bid") and x.channel == ctx.channel)
                    try:
                        bid = abs(int(resp.content[6:]))
                        if bid < startbid:
                            continue
                        cb[resp.author] = bid
                    except ValueError:
                        continue
        except asyncio.TimeoutError:
            pass

        await ctx.send("Bid over!")

        if not cb:
            await ctx.send("Nobody bid!")
            await self.bot.di.give_items(ctx.author, (item, amount))
            self.bids.remove(ctx.channel.id)
            return

        for x in range(len(cb)):
            winner, wamount = cb.most_common(x+1)[x]
            wb = await self.bot.di.get_balance(winner)
            if wb >= wamount:
                await ctx.send(f"{winner} won the bid for ${amount}!")
                await self.bot.di.add_eco(winner, -wamount)
                await self.bot.di.add_eco(ctx.author, wamount)
                await self.bot.di.give_items(winner, (item, amount))
                break
        else:
            await ctx.send("Nobody bid and had enough money to pay for it!")
            await self.bot.di.give_items(ctx.author, (item, amount))

        self.bids.remove(ctx.channel.id)

    @checks.no_pm()
    @commands.command()
    async def bid(self, ctx):
        """Place a bid on the current bidding item in the channel"""