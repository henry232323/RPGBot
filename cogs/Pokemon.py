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

class Pokemon(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["p"])
    @commands.guild_only()
    async def pokemon(self, ctx):
        """Subcommands for Pokemon management, see pb!help pokemon"""
        pass

    @pokemon.command(aliases=["new"])
    @commands.guild_only()
    async def create(self, ctx):
        """Create a new Pokemon to add to your box"""
        try:
            check = lambda x: x.channel is ctx.channel and x.author is ctx.author
            pokemon = dict()
            await ctx.send("In any step type 'cancel' to cancel")
            await ctx.send("What will its nickname be?")
            response = await self.bot.wait_for("message", check=check, timeout=30)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelled")
                return
            else:
                pokemon["name"] = response.content

            await ctx.send("What species of Pokemon is it?")
            response = await self.bot.wait_for("message", check=check, timeout=30)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelled")
                return
            else:
                pokemon["type"] = response.content

            await ctx.send("In any order, what are its stats? (level, health, attack, defense, spatk, spdef)"
                           "For example `level: 5, health: 22, attack: 56`"
                           " Type 'skip' to skip.")

            pokemon["stats"] = dict()
            valid_stats = ["level", "health", "attack", "defense", "spatk", "spdef"]
            while True:
                response = await self.bot.wait_for("message", check=check, timeout=30)
                if response.content.lower() == "cancel":
                    await ctx.send("Cancelled")
                    return
                elif response.content.lower() == "skip":
                    await ctx.send("Skipping")
                else:
                    try:
                        if "\n" in response.content:
                            res = response.content.split("\n")
                        else:
                            res = response.content.split(",")
                        for val in res:
                            key, value = val.split(": ")
                            key = key.strip().lower()
                            value = value.strip()
                            if key not in valid_stats:
                                await ctx.send(f"{key} is not a valid stat! Try again")
                                break
                            pokemon["stats"][key] = int(value)
                        else:
                            break
                    except:
                        await ctx.send("Invalid formatting! Try again")
                        continue
                    continue

                break

            pokemon["meta"] = dict()
            await ctx.send("Any additional data? (Format like the above, for example "
                           "nature: hasty, color: brown)")

            while True:
                response = await self.bot.wait_for("message", check=check, timeout=30)
                if response.content.lower() == "cancel":
                    await ctx.send("Cancelling!")
                    return
                elif response.content.lower() == "skip":
                    await ctx.send("Skipping!")
                else:
                    try:
                        if "\n" in response.content:
                            res = response.content.split("\n")
                        else:
                            res = response.content.split(",")
                        for val in res:
                            key, value = val.split(": ")
                            key = key.strip().lower()
                            value = value.strip()
                            pokemon["meta"][key] = value
                        else:
                            break
                    except:
                        await ctx.send("Invalid formatting! Try again")
                        continue

            id = await self.bot.di.add_pokemon(ctx.author, pokemon)
            await ctx.send(f"Finished! Pokemon has been added to box with ID {id}")

        except asyncio.TimeoutError:
            await ctx.send("Timed out! Try again")

    @pokemon.command()
    @commands.guild_only()
    async def info(self, ctx, id: int):
        """Get info on a Pokemon"""
        pokemon = await self.bot.di.get_pokemon(ctx.author, id)

        embed = discord.Embed(title=f"{pokemon.name}")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        embed.add_field(name="Nickname", value=pokemon.name)
        embed.add_field(name="Species", value=pokemon.type)
        embed.add_field(name="ID", value=pokemon.id)
        stats = "\n".join(f"{x}: {y}" for x, y in pokemon.stats.items())
        meta = "\n".join(f"{x}: {y}" for x, y in pokemon.meta.items())
        embed.add_field(name="Stats", value=stats)
        embed.add_field(name="Additional Info", value=meta)

        await ctx.send(embed=embed)
