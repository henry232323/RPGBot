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
from collections import Counter
from random import randint

from .utils.data import Guild, NumberConverter, validate_url, Object
from .utils import checks
from .utils.translation import _


class Groups(commands.Cog):
    """Commands for guild management"""

    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.group(aliases=["g"], invoke_without_command=True)
    async def guild(self, ctx, member: discord.Member = None):
        """Get info on a member's guild. Subcommands for guild management
        Example:
            rp!guild @Henry#6174
            rp!guild
        """
        if member is None:
            member = ctx.author

        mg = await self.bot.di.get_user_guild(member)
        if mg is None:
            await ctx.send(await _(ctx, "User does not have a guild!"))
            return

        guild = (await self.bot.di.get_guild_guilds(ctx.guild)).get(mg)
        if guild is None:
            await ctx.send(await _(ctx, "That guild doesn't exist here!"))
            return

        mobj = [await ctx.guild.fetch_member(x) for x in guild.members[:20]]

        members = "\n".join([u.mention for u in mobj if u])
        if len(guild.members) > 20:
            members = members + (await _(ctx, "\nAnd {} more...")).format(len(guild.members) - 20)

        litems = guild.items.items() if len(guild.items) < 20 else list(guild.items.items())[20:]
        items = "\n".join(f"{x} x{y}" for x, y in litems)

        embed = discord.Embed(description=guild.description or await _(ctx, "This guild doesn't have a description"),
                              color=randint(0, 0xFFFFFF))
        embed.set_author(name=guild.name, icon_url=guild.icon or ctx.guild.icon_url)
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon)
        if guild.image is not None:
            embed.set_image(url=guild.image)

        owner = await ctx.guild.fetch_member(guild.owner)
        oment = owner.mention if owner else "Not in server"
        currency = await ctx.bot.di.get_currency(ctx.guild)

        embed.add_field(name=await _(ctx, "Owner"), value=oment)
        embed.add_field(name=await _(ctx, "Open"), value=str(guild.open))
        embed.add_field(name=await _(ctx, "Bank Balance"), value=f"{guild.bank} {currency}")
        embed.add_field(name=await _(ctx, "Members"), value=members or await _(ctx, "None"))
        embed.add_field(name=await _(ctx, "Items"), value=items or await _(ctx, "None"))

        await ctx.send(embed=embed)

    @commands.command()
    async def guilds(self, ctx):
        """List guilds"""
        guilds = list((await self.bot.di.get_guild_guilds(ctx.guild)).items())
        embed = discord.Embed(color=randint(0, 0xFFFFFF))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        if not guilds:
            await ctx.send(await _(ctx, "No guilds to display."))
            return

        desc = await _(ctx, """
        \u27A1 to see the next page
        \u2B05 to go back
        \u274C to exit
        """)

        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title="Server Guilds", color=randint(0, 0xFFFFFF))
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        for i in range(0, len(guilds), 25):
            chunks.append(guilds[i:i + 25])

        i = 0
        for item, value in chunks[i]:
            fmt = (await _(ctx, "Owner: {}\nMembers: {}\nOpen: {}")).format(
                discord.utils.get(ctx.guild.members, id=int(value.owner)), len(value.members), value.open)
            embed.add_field(name=item, value=fmt)

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
                    embed.clear_fields()
                    i -= 1
                    for emote in emotes:
                        await msg.add_reaction(emote)

                    await msg.edit(embed=embed)

            elif r.emoji == emotes[1]:
                if i == max:
                    pass
                else:
                    embed.clear_fields()
                    i += 1
                    for emote in emotes:
                        await msg.add_reaction(emote)

                    await msg.edit(embed=embed)
            else:
                await msg.delete()
                await ctx.send(await _(ctx, "Closing"))
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @guild.command()
    async def info(self, ctx, *, name: str):
        """Get info on a guild
        Example: rp!guild info MyGuild"""
        guild = (await self.bot.di.get_guild_guilds(ctx.guild)).get(name)
        if guild is None:
            await ctx.send(await _(ctx, "That guild doesn't exist here!"))
            return

        members = "\n".join([(await ctx.guild.fetch_member(member)).mention for member in guild.members])
        if guild.member_count > 20:
            members = members + (await _(ctx, "\nAnd {} more...")).format(guild.members - 20)

        items = "\n".join([f"{x} x{y}" for x, y in
                           (guild.items.items() if len(guild.items) >= 20 else list(guild.items.items())[20:])])
        if len(guild.items) > 20:
            items = items + (await _(ctx, "\nAnd {} more...")).format(len(guild.items) - 20)

        embed = discord.Embed(description=guild.description or await _(ctx, "This guild doesn't have a description"),
                              color=randint(0, 0xFFFFFF))
        embed.set_author(name=guild.name, icon_url=guild.icon or ctx.guild.icon_url)
        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon)
        if guild.image is not None:
            embed.set_image(url=guild.image)

        embed.add_field(name=await _(ctx, "Owner"), value=discord.utils.get(ctx.guild.members, id=guild.owner).mention)
        embed.add_field(name=await _(ctx, "Open"), value=str(guild.open))
        embed.add_field(name=await _(ctx, "Bank Balance"), value=f"{guild.bank}")
        embed.add_field(name=await _(ctx, "Members"), value=members or await _(ctx, "None"))
        embed.add_field(name=await _(ctx, "Items"), value=items or await _(ctx, "None"))

        await ctx.send(embed=embed)

    @guild.command()
    async def create(self, ctx, *, name: str):
        """Create a new guild
        Example:
            Henry:  rp!guild create MyGuild
            RPGBot: 'cancel' or 'skip' to cancel creation or skip a step
                    Describe the Guild (guild description)
            Henry:  This guild is super cool
            RPGBot: Is this guild open to everyone? Or is an invite necessary? (yes or no, no is assumed)
            Henry:  yes
            RPGBot: If you'd like give a URL to an image for the guild
            Henry:  https://i.ytimg.com/vi/mPCEODZSotE/maxresdefault.jpg
            RPGBot: Finally, you can also set an icon for the guild
            Henry:  https://vignette.wikia.nocookie.net/kingofthehill/images/c/c7/Bobby.png/revision/latest?cb=20150524012917
            RPGBot: Guild successfully created!

            """

        async with self.bot.di.rm.lock(ctx.author.id):
            async with self.bot.di.rm.lock(ctx.guild.id):
                ug = await self.bot.di.get_user_guild(ctx.author)
                if ug is not None:
                    await ctx.send(await _(ctx, "You're already in a guild! Leave this guild to create a new one"))
                    return
                guilds = await self.bot.di.get_guild_guilds(ctx.guild)
                if name in guilds:
                    await ctx.send(await _(ctx, "A guild with this name already exists!"))
                    return
                owner = discord.utils.get(guilds.values(), owner=ctx.author.id)
                if owner is not None:
                    await ctx.send(await _(ctx, "You already own a guild!"))
                    return
                try:
                    check = lambda x: x.channel is ctx.channel and x.author is ctx.author
                    guild = dict(name=name,
                                 owner=ctx.author.id,
                                 description="",
                                 members=set(),
                                 bank=0,
                                 items=dict(),
                                 open=False,
                                 image=None,
                                 invites=set())
                    await ctx.send(await _(ctx, "'cancel' or 'skip' to cancel creation or skip a step"))
                    await ctx.send(await _(ctx, "Describe the Guild (guild description)"))
                    response = await self.bot.wait_for("message", check=check, timeout=120)
                    if response.content.lower() == "cancel":
                        await ctx.send(await _(ctx, "Cancelling!"))
                        return
                    elif response.content.lower() == "skip":
                        await ctx.send(await _(ctx, "Skipping!"))
                    else:
                        guild["description"] = response.content
                    await ctx.send(
                        await _(ctx,
                                "Is this guild open to everyone? Or is an invite necessary? (yes or no, no is assumed)"))
                    response = await self.bot.wait_for("message", timeout=60, check=check)
                    if response.content.lower() == "cancel":
                        await ctx.send(await _(ctx, "Cancelling!"))
                        return
                    elif response.content.lower() == "skip":
                        await ctx.send(await _(ctx, "Skipping!"))
                        guild["open"] = False
                    else:
                        guild["open"] = response.content.lower() == "yes"

                    await ctx.send(await _(ctx, "If you'd like give a URL to an image for the guild"))
                    while True:
                        response = await self.bot.wait_for("message", timeout=60, check=check)
                        if response.content.lower() == "cancel":
                            await ctx.send(await _(ctx, "Cancelling!"))
                            return
                        elif response.content.lower() == "skip":
                            await ctx.send(await _(ctx, "Skipping!"))
                            break
                        else:
                            if validate_url(response.content):
                                guild["image"] = response.content
                                break
                            else:
                                await ctx.send(await _(ctx, "That isn't a valid URL!"))

                    await ctx.send(await _(ctx, "Finally, you can also set an icon for the guild"))
                    while True:
                        response = await self.bot.wait_for("message", timeout=60, check=check)
                        if response.content.lower() == "cancel":
                            await ctx.send(await _(ctx, "Cancelling!"))
                            return
                        elif response.content.lower() == "skip":
                            await ctx.send(await _(ctx, "Skipping!"))
                            break
                        else:
                            if validate_url(response.content):
                                guild["image"] = response.content
                                break
                            else:
                                await ctx.send(await _(ctx, "That isn't a valid URL!"))

                    guild["members"].add(ctx.author.id)
                    guilds[name] = Guild(**guild)
                    await self.bot.di.update_guild_guilds(ctx.guild, guilds)
                    await self.bot.di.set_guild(ctx.author, guild["name"])

                    await ctx.send(await _(ctx, "Guild successfully created!"))
                except asyncio.TimeoutError:
                    await ctx.send(await _(ctx, "Timed out! Try again"))

    @guild.command()
    async def join(self, ctx, *, name: str):
        """Join a guild. (if you have an invite for closed guilds)"""
        async with self.bot.di.rm.lock(ctx.author.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is not None:
                await ctx.send(await _(ctx, "You're already in a guild! Leave this guild to join a new one"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(name)
            if guild is None:
                await ctx.send(await _(ctx, "That guild doesnt exist!"))
                return

            guild.members = set(guild.members)

            if not guild.open and ctx.author.id not in guild.invites:
                await ctx.send(await _(ctx, "This guild is closed and you don't have an invite!"))
                return

            if ctx.author.id in guild.invites:
                guild.invites.remove(ctx.author.id)

            guild.members.add(ctx.author.id)
            await self.bot.di.set_guild(ctx.author, guild.name)
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Guild joined!"))

    @guild.command()
    async def leave(self, ctx):
        """Leave your guild. Will ask you to delete your guild if you are the owner."""
        async with self.bot.di.rm.lock(ctx.author.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)

            if ug not in guilds:
                await self.bot.di.set_guild(ctx.author, None)
                await ctx.send(await _(ctx, "Guild left."))
                return

            guild = guilds[ug]
            if guild.owner == ctx.author.id:
                try:
                    await ctx.send(await _(ctx, "Guild will be deleted is this alright? {yes / no}"))
                    resp = await self.bot.wait_for("message",
                                                   check=lambda x: x.author is ctx.author and x.channel is ctx.channel)
                except TimeoutError:
                    await ctx.send(await _(ctx, "Didn't respond in time! Cancelling"))
                    return

                if resp.content == "yes":
                    await ctx.send(await _(ctx, "Alright then!"))

                    await ctx.bot.di.add_eco(Object(id=guild.owner, guild=ctx.guild), guild.bank)
                    await ctx.bot.di.give_items(Object(id=guild.owner, guild=ctx.guild), *guild.items.items())
                    await self.bot.di.remove_guild(ctx.guild, guild.name)
                    await ctx.send(await _(ctx, "Guild removed!"))
                    await self.bot.di.set_guild(ctx.author, None)
                    return
                else:
                    await ctx.send(await _(ctx, "Cancelling!"))
                    return

            guild.members.remove(ctx.author.id)
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await self.bot.di.set_guild(ctx.author, None)
            await ctx.send(await _(ctx, "Guild left."))

    @guild.command()
    async def kick(self, ctx, *, user: discord.Member):
        """Kick a member from a guild."""
        if user == ctx.author:
            return
        async with self.bot.di.rm.lock(ctx.author.id):
            async with self.bot.di.rm.lock(user.id):
                ug = await self.bot.di.get_user_guild(ctx.author)
                if ug is None:
                    await ctx.send(await _(ctx, "You aren't in a guild!"))
                    return
                guilds = await self.bot.di.get_guild_guilds(ctx.guild)
                guild = guilds.get(ug)
                if guild.owner != ctx.author.id:
                    await ctx.send(await _(ctx, "You do not own this guild!"))
                    return

                if user.id not in guild.members:
                    await ctx.send(await _(ctx, "User isn't in this guild!"))
                    return

                guild.members.remove(user.id)
                await self.bot.di.set_guild(user, None)
                await self.bot.di.update_guild_guilds(ctx.guild, guilds)
                await ctx.send(await _(ctx, "User kicked"))

    @guild.command()
    async def invite(self, ctx, user: discord.Member):
        """Invite a user your closed guild"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)
            guild.invites = set(guild.invites)
            if guild.owner != ctx.author.id:
                await ctx.send(await _(ctx, "You do not own this guild!"))
                return

            guild.invites.add(user.id)
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send((await _(ctx, "Sent a guild invite to {}")).format(user))

    @guild.command()
    async def delete(self, ctx, *, name: str = None):
        """Delete your guild.
        To delete a guild you do not own, you must have Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            if name is not None:
                assert checks.modpredicate(ctx)
                ug = name
            else:
                ug = await self.bot.di.get_user_guild(ctx.author)
                if ug is None:
                    await ctx.send(await _(ctx, "You aren't in a guild!"))
                    return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds[ug]
            if name is None and guild.owner != ctx.author.id:
                await ctx.send(await _(ctx, "You do not own this guild!"))
                return

            await ctx.send(await _(ctx, "Are you sure you want to delete the guild? {yes/no}"))
            try:
                resp = await self.bot.wait_for("message", timeout=60,
                                               check=lambda x: x.author is ctx.author and x.channel == ctx.channel)
            except asyncio.TimeoutError:
                await ctx.send(await _(ctx, "Timed out! Try again"))
                return

            if resp.content.lower() == "yes":
                await ctx.send(await _(ctx, "Alright then!"))

                async with self.bot.di.rm.lock(guild.owner):
                    await ctx.bot.di.add_eco(Object(id=guild.owner, guild=ctx.guild), guild.bank)
                    await ctx.bot.di.give_items(Object(id=guild.owner, guild=ctx.guild), *guild.items.items())
                await self.bot.di.remove_guild(ctx.guild, guild.name)
                await ctx.send(await _(ctx, "Guild removed!"))
            else:
                await ctx.send(await _(ctx, "Cancelling!"))

    @guild.command()
    async def deposit(self, ctx, amount: NumberConverter, guild_name: str = None):
        """Deposit an amount of money into the guild bank.
        To deposit into a guild are not a member of, you must have Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            amount = abs(amount)
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)

            if not guild_name:
                guild_name = await self.bot.di.get_user_guild(ctx.author)
                guild = guilds.get(guild_name)

                if guild_name is None or guild is None:
                    await self.bot.di.set_guild(ctx.author, None)
                    await ctx.send(await _(ctx, "You aren't in a guild!"))
                    return
            else:
                guild = guilds.get(guild_name)
                if guild is None:
                    await ctx.send(await _(ctx, "That guild is invalid!"))
                    return

            try:

                async with self.bot.di.rm.lock(ctx.author.id):
                    await self.bot.di.add_eco(ctx.author, -amount)
            except ValueError:
                await ctx.send(await _(ctx, "You don't have enough to deposit!"))
                return

            guild.bank += amount
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(
                (await _(ctx, "Successfully deposited {} dollars into {}'s bank")).format(amount, guild_name))

    @guild.command()
    async def withdraw(self, ctx, amount: NumberConverter):
        """Take money from the guild bank (guild mods only)
        To withdraw from a guild you are not a member of, you must have Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            amount = abs(amount)
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)
            if ctx.author.id not in guild.mods and ctx.author.id != guild.owner:
                await ctx.send(await _(ctx, "Only mods can withdraw money!"))
                return

            guild.bank -= amount
            if guild.bank < 0:
                await ctx.send(await _(ctx, "Cannot withdraw more than the guild has!"))
                return

            async with self.bot.di.rm.lock(ctx.author.id):
                await self.bot.di.add_eco(ctx.author, amount)

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send((await _(ctx, "Successfully withdrew {} dollars")).format(amount))

    @guild.command()
    async def setmod(self, ctx, *members: discord.Member):
        """Give the listed users mod for your guild (guild owner only)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)
            if ctx.author.id != guild.owner:
                await ctx.send(await _(ctx, "Only the guild owner can add mods"))
                return
            guild.mods = set(guild.invites)
            for member in members:
                if member.id not in guild.members:
                    await ctx.send((await _(ctx, "{} couldn't be added! Not in guild!")).format(member))
                else:
                    guild.mods.add(member.id)

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Successfully added mods!"))

    @guild.command()
    @checks.mod_or_permissions()
    async def give(self, ctx, name: str, *items: str):
        """Put items into the guild's storage, uses {item}x{#} notation. Does not take from inventory
        Example: rp!guild give MyGuild Bananax5 Orangex10
        Requires Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(name)

            if guild is None:
                await ctx.send(await _(ctx, "That guild is invalid!"))
                return

            fitems = []
            for item in items:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                fitems.append((split, num))

            guild.items = Counter(guild.items)
            guild.items.update(dict(fitems))

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Successfully deposited items!"))

    @guild.command()
    @checks.mod_or_permissions()
    async def take(self, ctx, name: str, *items: str):
        """Take items from the guild. Does not take from inventory
        Example: rp!guild take MyGuild Bananax5 Orangex10
        Requires Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(name)

            if guild is None:
                await ctx.send(await _(ctx, "That guild is invalid!"))
                return

            fitems = []
            for item in items:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                fitems.append((split, num))

            guild.items = Counter(guild.items)
            guild.items.subtract(dict(fitems))

            for item, value in list(guild.items.items()):
                if value < 0:
                    await ctx.send(await _(ctx, "The guild does not have enough items to take!"))
                    return
                if value == 0:
                    del guild.items[item]

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Successfully withdrew items"))

    @guild.command()
    @checks.mod_or_permissions()
    async def givemoney(self, ctx, guild_name: str, amount: NumberConverter):
        """Deposit an amount of money into the bank of a guild. Does not take from user's bank.
        Example: rp!guild givemoney MyGuild 500
        Requires Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            amount = abs(amount)
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)

            guild = guilds.get(guild_name)

            if guild is None:
                await ctx.send(await _(ctx, "That guild is invalid!"))
                return

            guild.bank += amount
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(
                (await _(ctx, "Successfully deposited {} dollars into {}'s bank")).format(amount, guild_name))

    @guild.command()
    @checks.mod_or_permissions()
    async def takemoney(self, ctx, guild_name: str, amount: NumberConverter):
        """Take money from the guild bank.
        Example: rp!guild takemoney MyGuild 500
        Requires Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            amount = abs(amount)
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(guild_name)
            if guild is None:
                await ctx.send(await _(ctx, "That guild is invalid!"))
                return

            guild.bank -= amount
            if guild.bank < 0:
                await ctx.send(await _(ctx, "Cannot withdraw more than the guild has!"))
                return

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send((await _(ctx, "Successfully withdrew {} dollars")).format(amount))

    @guild.command()
    async def deposititems(self, ctx, *items: str):
        """Deposit items into the guild's storage, uses {item}x{#} notation
        Example: rp!guild deposititems Bananax5 Orangex10
        To deposit into a guild you are not a member of, you must have Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            fitems = []
            for item in items:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                fitems.append((split, num))

            try:
                async with self.bot.di.rm.lock(ctx.author.id):
                    await self.bot.di.take_items(ctx.author, *fitems)
            except ValueError:
                await ctx.send(await _(ctx, "You don't have enough to give!"))
                return

            guild.items = Counter(guild.items)
            guild.items.update(dict(fitems))

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Successfully deposited items!"))

    @guild.command()
    async def withdrawitems(self, ctx, *items: str):
        """Withdraw items from the guild (guild mods only)
        Example: rp!guild withdrawitems Bananax5 Orangex10
        To withdraw from a guild you are not a member of, you must have Bot Moderator or Bot Admin"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            if ctx.author.id not in guild.mods and ctx.author.id != guild.owner:
                await ctx.send(await _(ctx, "Only mods can withdraw items!"))
                return

            fitems = []
            for item in items:
                split = item.split('x')
                split, num = "x".join(split[:-1]), abs(int(split[-1]))
                fitems.append((split, num))

            guild.items = Counter(guild.items)
            guild.items.subtract(dict(fitems))

            for item, value in list(guild.items.items()):
                if value < 0:
                    await ctx.send(await _(ctx, "The guild does not have enough items to take!"))
                    return
                if value == 0:
                    del guild.items[item]

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)

        async with self.bot.di.rm.lock(ctx.author.id):
            await self.bot.di.give_items(ctx.author, *fitems)
        await ctx.send(await _(ctx, "Successfully withdrew items"))

    @guild.command()
    async def toggleopen(self, ctx):
        """Toggle the Guilds open state (guild owner only)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            if ctx.author.id != guild.owner:
                await ctx.send(await _(ctx, "Only the owner can toggle this!"))
                return

            guild.open = not guild.open
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(
                (await _(ctx, "Guild is now {}")).format(
                    await _(ctx, 'open') if guild.open else await _(ctx, 'closed')))

    @guild.command()
    async def seticon(self, ctx, url: str):
        """Set the guild's icon (guild mods only)"""
        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            if ctx.author.id != guild.owner and ctx.author.id not in guild.mods:
                await ctx.send(await _(ctx, "Only guild mods may set this!"))
                return

            guild.icon = url
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Updated guild icon url!"))

    @guild.command()
    async def setimage(self, ctx, url: str):
        """Set the guild's image (guild mods only)"""
        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            if ctx.author.id != guild.owner and ctx.author.id not in guild.mods:
                await ctx.send(await _(ctx, "Only guild mods may set this!"))
                return

            guild.image = url
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Updated guild image url!"))

    @guild.command(aliases=["setdesc"])
    async def setdescription(self, ctx, *, description):
        """Set the guild's description (guild mods only)"""
        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)

            if ctx.author.id != guild.owner and ctx.author.id not in guild.mods:
                await ctx.send(await _(ctx, "Only guild mods may set this!"))
                return

            guild.description = description
            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Updated guild's description!"))

    @guild.command()
    async def transfer(self, ctx, user: discord.Member):
        """Transfer ownership of a guild to someone else (guild owner only)"""
        async with self.bot.di.rm.lock(ctx.guild.id):
            ug = await self.bot.di.get_user_guild(ctx.author)
            if ug is None:
                await ctx.send(await _(ctx, "You aren't in a guild!"))
                return
            guilds = await self.bot.di.get_guild_guilds(ctx.guild)
            guild = guilds.get(ug)
            if guild.owner != ctx.author.id:
                await ctx.send(await _(ctx, "You do not own this guild!"))
                return

            if user.id not in guild.members:
                await ctx.send(await _(ctx, "User isn't in this guild!"))
                return

            guild.owner = user.id

            await self.bot.di.update_guild_guilds(ctx.guild, guilds)
            await ctx.send(await _(ctx, "Successfully transferred ownership"))
