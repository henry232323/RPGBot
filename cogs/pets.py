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
from random import randint

from .utils import checks, data
from .utils.translation import _


class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.command()
    async def box(self, ctx, member: discord.Member = None):
        """Check the pet in your box"""
        if member is None:
            member = ctx.author
        box = await self.bot.di.get_box(member)

        pet = [f"{x.id}: **{x.name}**" for x in box]
        description = "\n".join(pet)
        embed = discord.Embed(description=description, title=f"{member.display_name} Pet", color=randint(0, 0xFFFFFF))
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.group(aliases=["p"], invoke_without_command=True)
    async def pet(self, ctx, member: discord.Member = None):
        """Subcommands for Pet management, see rp!help pet
        Same use as rp!box"""
        if member is None:
            member = ctx.author
        box = await self.bot.di.get_box(member)

        pet = [f"{x.id}: **{x.name}**" for x in box]
        description = "\n".join(pet)
        embed = discord.Embed(description=description, title=f"{member.display_name} Pet", color=randint(0, 0xFFFFFF))
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @pet.command()
    async def edit(self, ctx, pet_id: int, attribute: str, *, value: str):
        """Edit a pet
                Usage: rp!pet edit 5 description John likes bananas!
                Valid values for the [item] (second argument):
                    name: the character's name
                    description: the description of the character
                    level: an integer representing the character's level
                    meta: used like the additional info section when creating; can be used to edit/remove all attributes
                Anything else will edit single attributes in the additional info section
                """
        pet = await self.bot.di.get_pet(ctx.author, pet_id)

        if len(attribute) + len(value) > 1024:
            await ctx.send(await _(ctx, "Can't have an attribute longer than 1024 characters!"))
            return

        pet = list(pet)
        if attribute == "name":
            await self.bot.di.remove_pet(ctx.guild, pet[1])
            pet.name = value
        elif attribute in pet[3]:
            pet[3][attribute] = value
        elif attribute == "meta":
            try:
                pet[4] = {}
                if "\n" in value:
                    res = value.split("\n")
                else:
                    res = value.split(",")
                for val in res:
                    key, value = val.split(": ")
                    key = key.strip()
                    value = value.strip()
                    if key != "maps":
                        pet[4][key] = value
            except:
                await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                return
        else:
            pet[4][attribute] = value

        await self.bot.di.add_pet(ctx.author, data.Pet(*pet))
        await ctx.send(await _(ctx, "Pet edited!"))

    @pet.command(aliases=["new"])
    async def create(self, ctx):
        """Create a new Pet to add to your box"""
        try:
            check = lambda x: x.channel is ctx.channel and x.author is ctx.author
            pet = dict()
            await ctx.send(await _(ctx, "In any step type 'cancel' to cancel"))
            await ctx.send(await _(ctx, "What will its nickname be?"))
            response = await self.bot.wait_for("message", check=check, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send(await _(ctx, "Cancelled"))
                return
            else:
                pet["name"] = response.content

            await ctx.send(await _(ctx, "What species of Pet is it?"))
            response = await self.bot.wait_for("message", check=check, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send(await _(ctx, "Cancelled"))
                return
            else:
                pet["type"] = response.content

            await ctx.send(
                await _(ctx, "In any order, what are its stats? (e.g. level, health, attack, defense, spatk, spdef, speed, etc.)"
                             " For example `level: 5, health: 22, attack: 56`"
                             " Type 'skip' to skip."))

            pet["stats"] = dict()
            count = 0
            while True:
                response = await self.bot.wait_for("message", check=check, timeout=120)
                if response.content.lower() == "cancel":
                    await ctx.send(await _(ctx, "Cancelled"))
                    return
                elif response.content.lower() == "skip":
                    await ctx.send(await _(ctx, "Skipping"))
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
                            pet["stats"][key] = int(value)
                        else:
                            break
                    except:
                        await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                        count += 1
                        if count >= 3:
                            await ctx.send(await _(ctx, "Too many failed attempts, cancelling!"))
                            return
                        continue
                    continue

            pet["meta"] = dict()
            await ctx.send(await _(ctx, "Any additional data? (Format like the above, for example "
                                        "nature: hasty, color: brown)"))
            count = 0
            while True:
                response = await self.bot.wait_for("message", check=check, timeout=120)
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
                            pet["meta"][key] = value
                        else:
                            break
                    except:
                        await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                        count += 1
                        if count >= 3:
                            await ctx.send(await _(ctx, "Too many failed attempts, cancelling!"))
                            return
                        continue

            id = await self.bot.di.add_pet(ctx.author, pet)
            await ctx.send((await _(ctx, "Finished! Pet has been added to box with ID {}")).format(id))

        except asyncio.TimeoutError:
            await ctx.send(await _(ctx, "Timed out! Try again"))
        except Exception:
            import traceback
            traceback.print_exc()

    @pet.command()
    async def info(self, ctx, id: data.IntConverter):
        """Get info on a Pet"""
        pet = await self.bot.di.get_pet(ctx.author, id)

        embed = discord.Embed(title=f"{pet.name}", color=randint(0, 0xFFFFFF))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        embed.add_field(name=await _(ctx, "Nickname"), value=pet.name)
        embed.add_field(name=await _(ctx, "Species"), value=pet.type)
        embed.add_field(name=await _(ctx, "ID"), value=pet.id)
        stats = "\n".join(f"{x}: {y}" for x, y in pet.stats.items())
        meta = "\n".join(f"{x}: {y}" for x, y in pet.meta.items())
        embed.add_field(name=await _(ctx, "Stats"), value=stats or "None")
        embed.add_field(name=await _(ctx, "Additional Info"), value=meta or "None")

        await ctx.send(embed=embed)

    @pet.command(aliases=["delete", "rm", "remove"])
    async def release(self, ctx, id: data.IntConverter):
        """Release a Pet from your box"""
        pk = await self.bot.di.remove_pet(ctx.author, id)
        await ctx.send((await _(ctx, "This Pet has been released! Goodbye {}!")).format(pk.name))

    @pet.command()
    async def trade(self, ctx, your_id: data.IntConverter, their_id: data.IntConverter, other: discord.Member):
        """Offer a trade to a user.
        `your_id` is the ID of the Pet you want to give, `their_id` is the Pet you want from them.
        `other` being the user you want to trade with"""

        await ctx.send(await _(ctx, "Say rp!accept or rp!decline to respond to the trade!"))
        try:
            resp = await self.bot.wait_for("message", timeout=120, check=lambda
                x: x.author == other and x.channel == ctx.channel and ctx.message.content in ["rp!accept",
                                                                                              "rp!decline"])
        except asyncio.TimeoutError:
            await ctx.send(await _(ctx, "Failed to respond in time! Cancelling."))
            return

        if resp.content == "rp!accept":
            yud = await self.bot.db.get_user_data(ctx.author)
            tud = await self.bot.db.get_user_data(other)

            for your_pet in yud["box"]:
                if your_pet[0] == your_id:
                    break
            else:
                raise KeyError((await _(ctx, "{} is not a valid ID!")).format(your_id))
            yud["box"].remove(your_pet)
            tud["box"].append(your_pet)

            for their_pet in tud["box"]:
                if their_pet[0] == your_id:
                    break
            else:
                raise KeyError((await _(ctx, "{} is not a valid ID!")).format(their_id))
            tud["box"].remove(their_pet)
            yud["box"].append(their_pet)

            your_pet["id"], their_pet["id"] = their_pet["id"], your_pet["id"]

            await self.bot.db.update_user_data(ctx.author, yud)
            await self.bot.db.update_user_data(other, tud)
            await ctx.send((await _(ctx, "Trade completed! Traded {} for {}!")).format(your_pet['name'], their_pet['name']))

        else:
            await ctx.send(await _(ctx, "Trade declined! Cancelling."))

    @commands.command(hidden=True)
    async def accept(self, ctx):
        pass

    @commands.command(hidden=True)
    async def decline(self, ctx):
        pass
