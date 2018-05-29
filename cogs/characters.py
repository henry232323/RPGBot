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

import discord
from discord.ext import commands

from .utils import checks
from .utils.data import Character
from .utils.translation import _


class Characters(object):
    def __init__(self, bot):
        self.bot = bot

    @checks.no_pm()
    @commands.command(aliases=["chars", "personnages"])
    async def characters(self, ctx, user: discord.Member = None):
        """List all your characters"""
        if user is None:
            user = ctx.author
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        characters = [x for x, y in characters.items() if y.owner == user.id]
        if not characters:
            await ctx.send((await _(ctx, "{} has no characters to display")).format(user))
            return

        embed = discord.Embed(description="\n".join(characters))
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @checks.no_pm()
    @commands.command()
    async def allchars(self, ctx):
        """List all guild characters"""
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        if not characters:
            await ctx.send(await _(ctx, "No characters to display"))
            return

        embed = discord.Embed()
        words = dict()
        for x in characters.keys():
            if x[0].casefold() in words:
                words[x[0].casefold()].append(x)
            else:
                words[x[0].casefold()] = [x]

        for key, value in words.items():
            if value:
                embed.add_field(name=key.upper(), value="\n".join(value))

        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @checks.no_pm()
    @commands.group(invoke_without_command=True, aliases=["c", "char", "personnage"])
    async def character(self, ctx, *, name: str):
        """Get info on a character"""
        try:
            char = (await self.bot.di.get_guild_characters(ctx.guild))[name]
        except KeyError:
            await ctx.send((await _(ctx, "Character {} does not exist!")).format(name))
            return

        try:
            owner = discord.utils.get(ctx.guild.members, id=char.owner)
            embed = discord.Embed(description=char.description)
            embed.set_author(name=char.name, icon_url=owner.avatar_url)
            if char.meta.get("image"):
                embed.set_thumbnail(url=char.meta.get("image"))
            embed.add_field(name=await _(ctx, "Name"), value=char.name)
            embed.add_field(name=await _(ctx, "Owner"), value=str(owner))
            if char.level is not None:
                embed.add_field(name=await _(ctx, "Level"), value=char.level)
            team = await self.bot.di.get_team(ctx.guild, char.name)
            tfmt = "\n".join(f"{p.name} ({p.type})" for p in team) if team else await _(ctx, "Empty")
            embed.add_field(name=await _(ctx, "Team"), value=tfmt)
            mfmt = "\n".join(f"**{x}:** {y}" for x, y in char.meta.items())
            if mfmt.strip():
                embed.add_field(name=await _(ctx, "Additional Info"), value=mfmt)

            await ctx.send(embed=embed)
        except:
            owner = discord.utils.get(ctx.guild.members, id=char.owner)
            embed = discord.Embed(description=char.description)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.add_field(name=await _(ctx, "Name"), value=char.name)
            embed.add_field(name=await _(ctx, "Owner"), value=str(owner))
            embed.add_field(name=await _(ctx, "Level"), value=char.level)
            mfmt = "\n".join(f"**{x}:** {y}" for x, y in char.meta.items())
            if mfmt.strip():
                embed.add_field(name=await _(ctx, "Additional Info"), value=mfmt)

            await ctx.send(embed=embed)

    @checks.no_pm()
    @character.command(aliases=["new", "nouveau", "creer"])
    async def create(self, ctx, name: str, user: discord.Member = None):
        """Create a new character"""
        if user is None or user == ctx.author:
            user = ctx.author
        else:
            if not checks.role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                              manage_server=True):
                await ctx.send(await _(ctx, "Only Bot Mods/Bot Admins may make characters for other players!"))
                return

        characters = await self.bot.di.get_guild_characters(ctx.guild)
        if name in characters:
            await ctx.send(await _(ctx, "A character with this name already exists!"))
            return

        check = lambda x: x.channel is ctx.channel and x.author is ctx.author
        character = dict(name=name, owner=user.id, meta=dict(), team=list())
        await ctx.send(
            await _(ctx, "Describe the character (Relevant character sheet) (Say `done` when you're done describing)"))
        content = ""
        while True:
            response = await self.bot.wait_for("message", check=check, timeout=300)
            if response.content.lower() == "done":
                break
            else:
                if len(content) + len(response.content) > 3500:
                    await ctx.send(await _("Can't create a description of over 3500 characters"))
                else:
                    content += response.content + "\n"
        character["description"] = content
        await ctx.send(
            await _(ctx,
                    "Any additional info? (Add a character image using the image keyword. Formats use regular syntax e.g. "
                    "`image: http://image.com/image.jpg, hair_color: blond, nickname: Kevin` (Separate keys with commas or newlines)"
                    ))
        while True:
            response = await self.bot.wait_for("message", check=check, timeout=300)
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
                        key = key.strip()
                        value = value.strip()
                        character["meta"][key] = value
                    else:
                        break
                except:
                    await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                    continue

        character["level"] = character["meta"].pop("level", None)

        await self.bot.di.add_character(ctx.guild, Character(**character))
        await ctx.send(
            await _(ctx, "Character created! rp!team addmember to add Pokemon (optional) to your character's team!"))

    @checks.no_pm()
    @character.command(aliases=["remove", "supprimer"])
    async def delete(self, ctx, *, name: str):
        """Delete a character of the given name (you must be the owner)"""
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        character = characters.get(name)
        if character is None:
            await ctx.send(await _(ctx, "That character doesn't exist!"))
            return

        is_mod = checks.role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                            manage_server=True)
        if character.owner != ctx.author.id and not is_mod:
            await ctx.send(await _(ctx, "You do not own this character!"))
            return

        await self.bot.di.remove_character(ctx.guild, name)
        await ctx.send(await _(ctx, "Character deleted"))

    @checks.no_pm()
    @character.command()
    async def edit(self, ctx, character, attribute, *, value):
        """Edit a character
        Usage: rp!character edit John description John likes bananas!
        Valid values for the [item] (second argument):
            name: the character's name
            description: the description of the character
            level: an integer representing the character's level
            meta: used like the additional info section when creating; can be used to edit/remove all attributes
        Anything else will edit single attributes in the additional info section
        """
        attribute = attribute.lower()
        chars = await self.bot.di.get_guild_characters(ctx.guild)
        character = chars.get(character)
        if character is None:
            await ctx.send(await _(ctx, "That character doesn't exist!"))
            return

        try:
            is_mod = checks.role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False
        if character.owner != ctx.author.id and not is_mod:
            await ctx.send(await _(ctx, "You do not own this character!"))
            return

        character = list(character)
        if attribute == "name":
            await self.bot.di.remove_character(ctx.guild, character[0])
            character[0] = value
        elif attribute == "description":
            character[2] = value
        elif attribute == "level":
            character[3] = int(value)
        elif attribute == "meta":
            try:
                character[5] = {}
                if "\n" in value:
                    res = value.split("\n")
                else:
                    res = value.split(",")
                for val in res:
                    key, value = val.split(": ")
                    key = key.strip()
                    value = value.strip()
                    if key != "maps":
                        character[5][key] = value
            except:
                await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                return
        else:
            character[5][attribute] = value

        await self.bot.di.add_character(ctx.guild, Character(*character))
        await ctx.send(await _(ctx, "Character edited!"))
