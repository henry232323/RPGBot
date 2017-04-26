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

from .utils.data import Guild


class Guilds(object):
    """Commands for guild management"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(no_pm=True)
    async def guild(self, ctx):
        """Subcommands for guild management"""
        pass

    @commands.command(no_pm=True)
    async def guilds(self, ctx):
        """List guilds"""
        guilds = list((await self.bot.di.get_guild_guilds(ctx.guild)).items())
        embed = discord.Embed()
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        if not guilds:
            await ctx.send("No guilds to display.")
            return

        desc = """
        \u27A1 to see the next page
        \u2B05 to go back
        \u274C to exit
        """

        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title="Player Market")
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        for i in range(0, len(guilds), 25):
            chunks.append(guilds[i:i + 25])

        i = 0
        for item, value in chunks[i]:
            fmt = f"""Owner: {value.owner}\nMembers: {len(value.members)}\nOpen: {value.open}"""
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
                await ctx.send("Closing")
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @guild.command(no_pm=True)
    async def info(self, ctx, *, name: str):
        """Get info on a guild"""
        guild = (await self.bot.di.get_guild_guilds(ctx.guild)).get(name)
        if guild is None:
            await ctx.send("That guild doesn't exist here!")
            return

        members = "\n".join([discord.utils.get(ctx.guild.members, id=x).mention for x in (guild.members if len(guild.members) <= 20 else ctx.members[20:])])
        if len(guild.members) > 20:
            members = members + f"\nAnd {guild.members - 20} more..."

        litems = guild.items.items() if len(guild.items) < 20 else list(guild.items.items())[20:]
        items = "\n".join(f"{x} x{y}" for x, y in litems)

        embed = discord.Embed(description=guild.description or "This guild doesn't have a description")
        embed.set_author(name=guild.name, icon_url=guild.icon or ctx.guild.icon_url)
        if guild.image is not None:
            embed.set_thumbnail(url=guild.image)
        if guild.icon is not None:
            embed.set_image(url=guild.icon)

        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Open", value=str(guild.open))
        embed.add_field(name="Bank Balance", value=f"{guild.bank} Pokédollars")
        embed.add_field(name="Members", value=members)
        embed.add_field(name="Items", value=items)

    @guild.command(no_pm=True)
    async def create(self, ctx, *, name: str):
        """Create a new guild"""
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is None:
            await ctx.send("You're already in a guild! Leave this guild to create a new one")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        if name in guilds:
            await ctx.send("A guild with this name already exists!")
            return
        owner = discord.utils.get(guilds, owner=ctx.author.id)
        if owner is not None:
            await ctx.send("You already own a guild!")
            return
        try:
            check = lambda x: x.channel is ctx.channel and x.author is ctx.author
            guild = dict(name=name, owner=ctx.author.id, description="", members=set(), bank=0, items=dict(), open=False, image=None, invites=set())
            await ctx.send("'cancel' or 'skip' to cancel creation or skip a step")
            await ctx.send("Describe the Guild (guild description)")
            response = await self.bot.wait_for("message", check=check, timeout=60)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelling!")
                return
            elif response.content.lower() == "skip":
                await ctx.send("Skipping!")
            else:
                guild["description"] = response.content
            await ctx.send("Is this guild open to everyone? Or is an invite necessary? (yes or no, no is assumed)")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelling!")
                return
            elif response.content.lower() == "skip":
                await ctx.send("Skipping!")
            else:
                guild["open"] = True if response.content.lower() == "yes" else False

            await ctx.send("If you'd like give a URL to an image for the guild")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelling!")
                return
            elif response.content.lower() == "skip":
                await ctx.send("Skipping!")
            else:
                guild["image"] = response.content

            await ctx.send("Finally, you can also set an icon for the guild")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "cancel":
                await ctx.send("Cancelling!")
                return
            elif response.content.lower() == "skip":
                await ctx.send("Skipping!")
            else:
                guild["icon"] = response.content

            guilds[guild["name"]] = Guild(**guild)
            await self.bot.di.update_guild_guilds(guilds)
        except asyncio.TimeoutError:
            await ctx.send("Timed out! Try again")

    @guild.command(no_pm=True)
    async def join(self, ctx, *, name: str):
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is not None:
            await ctx.send("You're already in a guild! Leave this guild to create a new one")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        guild = guilds.get(name)
        if guild is None:
            await ctx.send("That guild doesnt exist!")
            return

        if not guild.open and ctx.author.id not in guild.invites:
            await ctx.send("This guild is closed and you don't have an invite!")
            return

        if ctx.author.id in guild.invites:
            guild.invites.remove(ctx.author.id)

        guild.members.add(ctx.author.id)
        await self.bot.di.set_guild(ctx.author, guild.name)
        await self.bot.di.update_guild_guilds(guilds)
        await ctx.send("Guild joined!")

    @guild.command(no_pm=True)
    async def leave(self, ctx):
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is None:
            await ctx.send("You aren't in a guild!")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        guild = guilds.get(ug)
        guild.members.remove(ctx.user.id)
        await self.bot.di.set_guild(ctx.author, None)
        await self.bot.di.update_guild_guilds(guilds)
        await ctx.send("Guild left.")

    @guild.command(no_pm=True)
    async def kick(self, ctx, user: discord.Member):
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is None:
            await ctx.send("You aren't in a guild!")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        guild = guilds.get(ug)
        if guild.owner != ctx.author.id:
            await ctx.send("You do not own this guild!")
            return

        if user.id not in guild.members:
            await ctx.send("User isn't in this guild!")
            return

        guild.members.remove(user.id)
        await self.bot.di.set_guild(user, None)
        await self.bot.di.update_guild_guilds(guilds)
        await ctx.send("User kicked")

    @guild.command(no_pm=True)
    async def invite(self, ctx, user: discord.Member):
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is None:
            await ctx.send("You aren't in a guild!")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        guild = guilds.get(ug)
        if guild.owner != ctx.author.id:
            await ctx.send("You do not own this guild!")
            return

        guild.invites.add(user.id)
        await self.bot.di.update_guild_guilds(guilds)
        await ctx.send(f"Sent a guild invite to {user}")

    @guild.command(no_pm=True)
    async def delete(self, ctx):
        ug = await self.bot.di.get_user_guild(ctx.author)
        if ug is None:
            await ctx.send("You aren't in a guild!")
            return
        guilds = await self.bot.di.get_guild_guilds(ctx.guild)
        guild = guilds.get(ug)
        if guild.owner != ctx.author.id:
            await ctx.send("You do not own this guild!")
            return

        await ctx.send("Are you sure you want to delete the guild? {yes/no}")
        try:
            resp = await self.bot.wait_for("message", timeout=30, check=lambda x: x.author is ctx.author and x.channel is ctx.channel)
        except asyncio.TimeoutError:
            await ctx.send("Timed out try again!")
            return

        if resp.content.lower() == "yes":
            await ctx.send("Alright then!")

        for mid in guild.members:
            await self.bot.di.set_guild(discord.utils.get(ctx.guild.members, id=mid), None)

        await self.bot.di.remove_guild(ctx.guild, guild.name)
        await ctx.send("Guild removed!")



