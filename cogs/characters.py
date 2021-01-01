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
from collections import Counter

import discord
from discord.ext import commands

from random import randint
import asyncio

from .utils import checks
from .utils.data import Character, NumberConverter, IntConverter, chunkn
from .utils.translation import _


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            return True

        return commands.check(predicate(ctx))

    @commands.command(aliases=["chars", "personnages"])
    async def characters(self, ctx, user: discord.Member = None):
        """List all characters of the user. If no user is given lists your own characters."""
        if user is None:
            user = ctx.author
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        characters = [x for x, y in characters.items() if y.owner == user.id]
        if not characters:
            await ctx.send((await _(ctx, "{} has no characters to display")).format(user))
            return

        embed = discord.Embed(description="\n".join(characters), color=randint(0, 0xFFFFFF), )
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def allchars(self, ctx):
        """List all guild characters"""
        characters = await self.bot.di.get_guild_characters(ctx.guild)
        if not characters:
            await ctx.send(await _(ctx, "No characters to display"))
            return

        embed = discord.Embed(color=randint(0, 0xFFFFFF), )
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

    @commands.group(invoke_without_command=True, aliases=["c", "char", "personnage"])
    async def character(self, ctx, *, name: str):
        """Get info on a character. Example: rp!c Hank"""
        char = await self.bot.di.get_character(ctx.guild, name)
        if char is None:
            await ctx.send((await _(ctx, "Character {} does not exist!")).format(name))
            return

        try:
            owner = await ctx.bot.fetch_user(char.owner)
            embed = discord.Embed(description=char.description)
            embed.set_author(name=char.name, icon_url=owner.avatar_url)
            if char.meta.get("image"):
                embed.set_image(url=char.meta["image"])
            if char.meta.get("icon"):
                embed.set_thumbnail(url=char.meta["icon"])
            embed.add_field(name=await _(ctx, "Name"), value=char.name)
            embed.add_field(name=await _(ctx, "Owner"), value=str(owner))
            if char.level is not None:
                embed.add_field(name=await _(ctx, "Level"), value=char.level)
            # team = await self.bot.di.get_team(ctx.guild, char.name)
            # if team:
            #    tfmt = "\n".join(f"{p.name} ({p.type})" for p in team)
            #    embed.add_field(name=await _(ctx, "Team"), value=tfmt)
            mfmt = "\n".join(f"**{x}:** {y}" for x, y in char.meta.items() if x not in ("icon", "image"))
            if mfmt.strip():
                embed.add_field(name=await _(ctx, "Additional Info"), value=mfmt)

            await ctx.send(embed=embed)
        except:
            owner = await ctx.bot.fetch_user(char.owner)
            embed = discord.Embed(description=char.description)
            embed.set_author(name=char.name, icon_url=owner.avatar_url)
            embed.add_field(name=await _(ctx, "Name"), value=char.name)
            embed.add_field(name=await _(ctx, "Owner"), value=str(owner))
            if char.level is not None:
                embed.add_field(name=await _(ctx, "Level"), value=char.level)
            # team = await self.bot.di.get_team(ctx.guild, char.name)
            # if team:
            #    tfmt = "\n".join(f"{p.name} ({p.type})" for p in team)
            #    embed.add_field(name=await _(ctx, "Team"), value=tfmt)
            mfmt = "\n".join(f"**{x}:** {y}" for x, y in char.meta.items())
            if mfmt.strip():
                embed.add_field(name=await _(ctx, "Additional Info"), value=mfmt)

            await ctx.send(embed=embed)

    @character.command(aliases=["new", "nouveau", "creer"])
    async def create(self, ctx, name: str, user: discord.Member = None):
        """Create a new character
        Example:
            Henry:      rp!character create Bobby Hill
            RPGBot:     Member "Hill" not found. If this is unexpected, please report this to the bot creator
            Henry:      rp!character create "Bobby Hill"
            RPGBot:     Describe the character (Relevant character sheet) (Say done when you're done describing)
            Henry:      He's a little round, but he's a good boy
            Henry:      done
            RPGBot:     Any additional info? (Add a character image using the image keyword or use the icon keyword to give the character an icon. Formats use regular syntax e.g. image: http://example.com/image.jpg, hair_color: blond, nickname: Kevin (Separate keys with commas or newlines)
            Henry:
                    Hair Color: Blonde
                    Body Type: Round
                    Father: Hank Hill
                    image: https://i.ytimg.com/vi/mPCEODZSotE/maxresdefault.jpg
                    icon: https://vignette.wikia.nocookie.net/kingofthehill/images/c/c7/Bobby.png/revision/latest?cb=20150524012917

            RPGBot      Character created!"""
        ouser = user
        if user is None or user == ctx.author:
            user = ctx.author
        else:
            try:
                has_role = checks.role_or_permissions(ctx,
                                                      lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                      manage_server=True)
            except:
                has_role = False
            if not has_role:
                await ctx.send(await _(ctx, "Only Bot Mods/Bot Admins may make characters for other players!"))
                return

        data = await self.bot.db.get_guild_data(ctx.guild)
        characters = await ctx.bot.di.get_guild_characters(ctx.guild)
        if "caliases" not in data:
            data["caliases"] = {}
        aliases = data["caliases"]
        if name in characters or name in aliases:
            await ctx.send(await _(ctx, "A character with this name already exists!"))
            return

        check = lambda x: x.channel == ctx.channel and x.author == ctx.author
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
                    await ctx.send(await _(ctx, "Can't create a description of over 3500 characters"))
                else:
                    content += response.content + "\n"
        character["description"] = content
        await ctx.send(
            await _(ctx,
                    "Any additional info? (Add a character image using the image keyword or"
                    " use the icon keyword to give the character an icon. Formats use regular syntax e.g. "
                    "`image: http://example.com/image.jpg, hair_color: blond, nickname: Kevin` (Separate keys with commas or newlines)"
                    ))
        count = 0
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
                        if len(key) + len(value) > 1024:
                            await ctx.send(await _(ctx, "Can't have an attribute longer than 1024 characters!"))
                            return
                        character["meta"][key] = value
                    else:
                        break
                except:
                    await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                    count += 1
                    if count >= 3:
                        await ctx.send(await _(ctx, "Too many failed attempts, cancelling!"))
                        return
                    continue

        character["level"] = character["meta"].pop("level", None)
        if (len(ctx.message.mentions) > 0 and ouser is None) or (len(ctx.message.mentions) > 1 and ouser is not None):
            newname = character["name"].replace("!", "")
            data = await self.bot.db.get_guild_data(ctx.guild)
            if "caliases" not in data:
                data["caliases"] = {}

            if newname not in data["characters"]:
                data["caliases"][newname] = character["name"]

            await self.bot.db.update_guild_data(ctx.guild, data)

        await self.bot.di.add_character(ctx.guild, Character(**character))
        await ctx.send(
            await _(ctx, "Character created!"))

    @character.command(aliases=["remove", "supprimer"])
    async def delete(self, ctx, *, name: str):
        """Delete a character of the given name (you must be the owner or be a Bot Mod / Bot Admin)"""
        character = await self.bot.di.get_character(ctx.guild, name)
        if character is None:
            await ctx.send(await _(ctx, "That character doesn't exist!"))
            return

        if character.owner != ctx.author.id:
            try:
                is_mod = checks.role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                    manage_server=True)
            except:
                is_mod = False

            if not is_mod:
                await ctx.send(await _(ctx, "You do not own this character!"))
                return

            else:

                async with self.bot.di.rm.lock(ctx.author.id):
                    await self.bot.di.remove_character(ctx.guild, name)
                await ctx.send(await _(ctx, "Character deleted"))
        else:

            async with self.bot.di.rm.lock(ctx.guild.id):
                await self.bot.di.remove_character(ctx.guild, name)
            await ctx.send(await _(ctx, "Character deleted"))

    @character.command()
    async def edit(self, ctx, name: str, attribute: str, *, value: str):
        """Edit a character
        Usage: rp!character edit John description John likes bananas!
        Valid values for the [item] (second argument):
            name: the character's name
            description: the description of the character
            level: an integer representing the character's level
            meta: used like the additional info section when creating; can be used to edit/remove all attributes
        Anything else will edit single attributes in the additional info section

        Bot Moderator or Bot Admin are required to edit other people's characters
        """
        character = await self.bot.di.get_character(ctx.guild, name)
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

        if attribute == "description" and len(value) > 3500:
            await ctx.send(await _(ctx, "Can't have a description longer than 3500 characters!"))
            return
        elif len(attribute) + len(value) > 1024:
            await ctx.send(await _(ctx, "Can't have an attribute longer than 1024 characters!"))
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
                    if key not in ("maps", "map"):
                        character[5][key] = value
            except:
                await ctx.send(await _(ctx, "Invalid formatting! Try again"))
                return
        else:
            character[5][attribute] = value

        async with self.bot.di.rm.lock(ctx.guild.id):
            await self.bot.di.add_character(ctx.guild, Character(*character))
        await ctx.send(await _(ctx, "Character edited!"))

    @character.command()
    async def remattr(self, ctx, name: str, *, attribute: str):
        """Delete a character attribute
        Usage: rp!character remattr John hair color
        """
        attribute = attribute
        character = await self.bot.di.get_character(ctx.guild, name)
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

        if attribute not in character[5]:
            await ctx.send(await _(ctx, "That attribute doesn't exist! Try again"))
            return

        del character[5][attribute]

        async with self.bot.di.rm.lock(ctx.guild.id):
            await self.bot.di.add_character(ctx.guild, Character(*character))
        await ctx.send(await _(ctx, "Removed attribute!"))

    async def unassume(self, ctx, character, wait=60 * 60 * 24):
        author = ctx.author
        data = await self.bot.db.get_guild_data(ctx.guild)
        if "caliases" not in data:
            data["caliases"] = {}

        character = data["caliases"].get(character, character)
        await asyncio.sleep(wait)
        if self.bot.in_character[author.guild.id][author.id] != character:
            return
        del self.bot.in_character[author.guild.id][author.id]
        hooks = await author.guild.webhooks()
        await discord.utils.get(hooks, name=character).delete()

    async def shutdown(self):
        pass

    @character.command(aliases=["a"])
    async def assume(self, ctx, name: str):
        """Assume a character. You will send messages with this character's icon and name. Necessary for some character inventory and economy commands. Lasts one day"""
        data = await self.bot.db.get_guild_data(ctx.guild)
        if "caliases" not in data:
            data["caliases"] = {}

        name = data["caliases"].get(name, name)

        character = await self.bot.di.get_character(ctx.guild, name)
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

        self.bot.in_character[ctx.guild.id][ctx.author.id] = name
        hooks = await ctx.guild.webhooks()
        hook = discord.utils.get(hooks, name=name)

        if hook is None:
            await ctx.channel.create_webhook(name=name)

        await ctx.send((await _(ctx, "You are now {} for the next 24 hours")).format(name))
        self.bot.loop.create_task(self.unassume(ctx, name))

    @character.command(name="unassume", aliases=["ua"])
    async def c_unassume(self, ctx, character: str):
        """Unassume a character"""
        await self.unassume(ctx, character, 0)
        await ctx.send(await _(ctx, "Character unassumed!"))

    async def c_inventory(self, guild, name):
        char = await self.bot.di.get_character(guild, name)
        if 'items' not in char.ustats:
            char.ustats['items'] = {}
        return char.ustats['items']

    @commands.group(invoke_without_command=True, aliases=['ci', 'cinv'])
    async def charinv(self, ctx, *, name: str = None):
        """Check your or another character's inventory."""
        dest = ctx.channel
        if name is None:
            name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
        gd = await self.bot.db.get_guild_data(ctx.guild)
        try:
            is_mod = checks.role_or_permissions(ctx,
                                                lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False

        hide = gd.get("hideinv", False)

        if not is_mod and hide:
            name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)

        if name is None:
            await ctx.send(await _(ctx,
                                   "You are not currently a character! "
                                   "Use the command again with the name of the character to check "
                                   "or use `rp!char assume` to assume a character"))
            return

        if hide:
            dest = ctx.author

        char = await self.bot.di.get_character(ctx.guild, name)
        if 'items' not in char.ustats:
            char.ustats['items'] = {}
        inv = char.ustats['items']

        if not inv:
            await dest.send(await _(ctx, "This inventory is empty!"))
            return

        fmap = map(lambda x: f"{x[0]} x{x[1]}", sorted(inv.items()))
        fmt = "\n".join(fmap)
        chunks = chunkn(fmt, 2000)  # [("Items: ", v) for v in chunkn(fmt, 400)]
        for chunk in chunks:
            embed = discord.Embed(description="\n".join(chunk), color=randint(0, 0xFFFFFF))
            if char.meta.get("icon"):
                embed.set_author(name=name, icon_url=char.meta["icon"])
            else:
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            try:
                await dest.send(embed=embed)
            except discord.Forbidden:
                await dest.send(chunk)

    async def c_takeitem(self, guild, name, *items):
        if isinstance(name, str):
            char = await self.bot.di.get_character(guild, name)
        else:
            char = name
        if 'items' not in char.ustats:
            char.ustats['items'] = {}

        char.ustats["items"] = Counter(char.ustats["items"])
        char.ustats["items"].subtract(dict(items))

        # print(char.ustats["items"])
        for item, value in list(char.ustats["items"].items()):
            if value < 0:
                raise ValueError(f"Cannot take more items than {name} has!")
            if value == 0:
                del char.ustats["items"][item]

        await self.bot.di.add_character(guild, char)

    @checks.mod_or_permissions()
    @charinv.command(aliases=["take"])
    async def takeitem(self, ctx, item: str, num: IntConverter, *names: str):
        """Remove an item from a character's inventory (Moderators)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            num = abs(num)
            for name in names:
                await self.c_takeitem(ctx.guild, name, (item, num))

        await ctx.send(await _(ctx, "Items taken!"))

    async def c_giveitem(self, guild, name, *items):
        if isinstance(name, str):
            char = await self.bot.di.get_character(guild, name)
        else:
            char = name
        if 'items' not in char.ustats:
            char.ustats['items'] = {}

        ud = char.ustats
        ud["items"] = Counter(ud["items"])
        ud["items"].update(dict(items))
        await self.bot.di.add_character(guild, char)

    @checks.mod_or_permissions()
    @charinv.command()
    async def giveitem(self, ctx, item: str, num: IntConverter, *names: str):
        """Give an item to a character (Not out of your inventory) (Moderators)
        Example: rp!ci giveitem Banana 32 Char1 Char2 Char3"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            items = await self.bot.di.get_guild_items(ctx.guild)
            if item not in items:
                await ctx.send(await _(ctx, "That is not a valid item!"))
                return

            num = abs(num)
            for name in names:
                await self.c_giveitem(ctx.guild, name, (item, num))

        await ctx.send(await _(ctx, "Items given!"))

    @charinv.command()
    async def give(self, ctx, other: str, *items: str):
        """Give items ({item}x{#}) to a character; ie: rp!ci give Name Pokeballx3"""
        fitems = []
        name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
        if name is None:
            await ctx.send(await _(ctx,
                                   "You are not currently a character! Use `rp!char assume` to assume a character"))
            return

        ochar = await self.bot.di.get_character(ctx.guild, other)
        if ochar is None:
            await ctx.send("That character does not exist!")
            return

        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            fitems.append((split, num))

        async with self.bot.di.rm.lock(ctx.guild.id):
            try:
                await self.c_takeitem(ctx.guild, name, *fitems)
                await self.c_giveitem(ctx.guild, other, *fitems)
                await ctx.send((await _(ctx, "Successfully gave {} {}")).format(other, items))
            except:
                await ctx.send(await _(ctx, "You do not have enough to give away!"))

    @charinv.command()
    async def givemember(self, ctx, other: discord.Member, *items: str):
        """Give items ({item}x{#}) to a user from your characters inventory; ie: rp!ci givemember Name Pokeballx3"""
        fitems = []
        name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
        if name is None:
            await ctx.send(await _(ctx,
                                   "You are not currently a character! Use `rp!char assume` to assume a character"))
            return

        for item in items:
            split = item.split('x')
            split, num = "x".join(split[:-1]), abs(int(split[-1]))
            fitems.append((split, num))

        async with self.bot.di.rm.lock(ctx.guild.id):
            try:
                await self.c_takeitem(ctx.guild, name, *fitems)
                await self.bot.di.give_items(other, *fitems)
                await ctx.send((await _(ctx, "Successfully gave {} {}")).format(other, items))
            except Exception as e:
                await ctx.send(await _(ctx, "You do not have enough to give away!"))

    @charinv.command()
    async def use(self, ctx, item, number: int = 1):
        """Use an item. Example `rp!use Banana` or `rp!use Banana 5`
        To make an item usable, you must put the key `used: <message>` when you are adding additional information for an item
        If you dont input a number of items you will use one by default.
        """

        async with self.bot.di.rm.lock(ctx.guild.id):
            number = abs(number)
            items = await self.bot.di.get_guild_items(ctx.guild)
            msg = items.get(item).meta.get('used')

            char = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
            if char is None:
                await ctx.send(await _(ctx,
                                       "You are not currently a character! Use `rp!char assume` to assume a character"))
                return

            if msg is None:
                await ctx.send(await _(ctx, "This item is not usable!"))
                return
            try:
                await self.c_takeitem(ctx.guild, char, (item, number))
            except ValueError:
                await ctx.send(await _(ctx, "You do not have that many to use!"))
                return

            await ctx.send(msg.format(mention=ctx.author.mention,
                                      name=ctx.author.display_name,
                                      channel=ctx.channel))
            await ctx.send((await _(ctx, "Used {} {}s")).format(number, item))

    @charinv.command()
    async def craft(self, ctx, number: int, *, name: str):
        """Craft a recipe with a given name from the available server recipes; e.g. rp!craft 5 Apple Pie"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            recipes = await ctx.bot.di.get_guild_recipes(ctx.guild)
            recipe = recipes.get(name)
            if recipe is None:
                await ctx.send(await _(ctx, "That recipe doesn't exist!"))
                return

            uname = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
            if uname is None:
                await ctx.send(await _(ctx,
                                       "You are not currently a character! Use `rp!char assume` to assume a character"))
                return

            uinv = await self.c_inventory(ctx.guild, uname)
            for item, n in recipe[0].items():
                if uinv.get(item, 0) < n * number:
                    await ctx.send(
                        (await _(ctx, "You need {} {} to craft this! You only have {}")).format(n * number, item,
                                                                                                uinv.get(item)))
                    return

            await self.c_takeitem(ctx.guild, uname, *((a, b * number) for a, b in recipe[0].items()))
            await self.c_giveitem(ctx.guild, uname, *((a, b * number) for a, b in recipe[1].items()))

            await ctx.send((await _(ctx, "Successfully crafted {} {}")).format(number, name))

    async def c_balances(self, guild, name):
        char = await self.bot.di.get_character(guild, name)
        if 'money' not in char.ustats:
            char.ustats['money'] = 0
        if 'bank' not in char.ustats:
            char.ustats['bank'] = 0

        return char.ustats['money'], char.ustats['bank']

    @commands.group(aliases=["ceco", "ce", "cbal"], invoke_without_command=True)
    async def chareco(self, ctx, *, name: str = None):
        """Check your or another character's balance"""
        dest = ctx.channel
        if name is None:
            name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)

        gd = await self.bot.db.get_guild_data(ctx.guild)
        try:
            is_mod = checks.role_or_permissions(ctx,
                                                lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False

        hide = gd.get("hideinv", False)

        if not is_mod and hide:
            name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)

        if name is None:
            await ctx.send(await _(ctx,
                                   "You are not currently a character! "
                                   "Use the command again with the name of the character to check "
                                   "or use `rp!char assume` to assume a character"))
            return

        if hide:
            dest = ctx.author

        char = await self.bot.di.get_character(ctx.guild, name)
        if char is None:
            await ctx.send((await _(ctx, "Character {} does not exist!")).format(name))

        bal = await self.c_balances(ctx.guild, name)

        data = """
On you:\t\t {:.2f} dollars
In the bank:\t {:.2f} dollars in the bank
Total:\t\t {:.2f} dollars
        """

        embed = discord.Embed(
            description=(await _(ctx, data)).format(int(bal[0]) if int(bal[0]) == bal[0] else bal[0],
                                                    int(bal[1]) if int(bal[1]) == bal[1] else bal[1],
                                                    sum(bal)
                                                    ),
            color=randint(0, 0xFFFFFF),
        )

        embed.set_author(name=name, icon_url=(char.meta.get("icon", discord.Embed.Empty)))
        embed.set_thumbnail(url="https://opengameart.org/sites/default/files/styles/medium/public/gold_pile_0.png")
        await dest.send(embed=embed)

    async def c_setbalance(self, guild, name, amount):
        char = await self.bot.di.get_character(guild, name)
        if 'money' not in char.ustats:
            char.ustats['money'] = 0
        if 'bank' not in char.ustats:
            char.ustats['bank'] = 0
        char.ustats['money'] = amount
        char.ustats['bank'] = 0

        await self.bot.di.add_character(guild, char)

    @checks.mod_or_permissions()
    @chareco.command(aliases=["set"])
    async def setbalance(self, ctx, amount: NumberConverter, *names: str):
        """Set the balance of the given members to an amount  (Moderators)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            for name in names:
                await self.c_setbalance(ctx.guild, name, amount)

        await ctx.send(await _(ctx, "Balances changed"))

    async def c_addeco(self, guild, name, amount):
        if isinstance(name, str):
            char = await self.bot.di.get_character(guild, name)
        else:
            char = name
        if 'money' not in char.ustats:
            char.ustats['money'] = 0
        if 'bank' not in char.ustats:
            char.ustats['bank'] = 0
        char.ustats['money'] += amount

        if char.ustats['money'] < 0:
            raise ValueError("Cannot take more than user has!")

        await self.bot.di.add_character(guild, char)

    async def c_takeeco(self, guild, name, amount):
        if isinstance(name, str):
            char = await self.bot.di.get_character(guild, name)
        else:
            char = name
        if 'money' not in char.ustats:
            char.ustats['money'] = 0
        if 'bank' not in char.ustats:
            char.ustats['bank'] = 0
        char.ustats['money'] += amount
        if char.ustats['money'] < 0:
            char.ustats['bank'] += char.ustats['money']
            char.ustats['money'] = 0

        if char.ustats['bank'] < 0:
            raise ValueError("Cannot take more than user has!")

        await self.bot.di.add_character(guild, char)

    @checks.mod_or_permissions()
    @chareco.command()
    async def givemoney(self, ctx, amount: NumberConverter, *names: str):
        """Give the character's money (Moderators)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            for name in names:
                await self.c_addeco(ctx.guild, name, amount)

            await ctx.send(await _(ctx, "Money given"))

    @checks.mod_or_permissions()
    @chareco.command()
    async def takemoney(self, ctx, amount: NumberConverter, *names: str):
        """Take the character's money (Moderators)"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            succ = False

            for name in names:
                try:
                    await self.c_takeeco(ctx.guild, name, amount)
                    succ = True
                except ValueError:
                    await ctx.send((await _(ctx, "Could not take money from {}, user does not have enough")))

        if succ:
            await ctx.send(await _(ctx, "Money taken"))

    @chareco.command()
    async def pay(self, ctx, amount: NumberConverter, other: str):
        """Pay another character money"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            amount = abs(amount)

            name = self.bot.in_character[ctx.guild.id].get(ctx.author.id)
            if name is None:
                await ctx.send(await _(ctx,
                                       "You are not currently a character! "
                                       "Use the command again with the name of the character to check "
                                       "or use `rp!char assume` to assume a character"))
                return

            try:
                await self.c_addeco(ctx.guild, name, -amount)
            except ValueError:
                await ctx.send(await _(ctx, "You cannot afford to pay that!"))
            await self.c_addeco(ctx.guild, other, amount)
            await ctx.send((await _(ctx, "Successfully paid {} dollars to {}")).format(amount, other))

    @character.command()
    async def alias(self, ctx, alias_name: str, *, character_name: str):
        """Create an alias for a character.
        Example: rp!c alias Tom Tom Hanks
        This will make the name Tom point to the name Tom Hanks"""

        async with self.bot.di.rm.lock(ctx.guild.id):
            data = await self.bot.db.get_guild_data(ctx.guild)
            if "caliases" not in data:
                data["caliases"] = {}

            if alias_name in data["characters"]:
                await ctx.send(await _(ctx, "A character with this name already exists!"))
                return

            if alias_name in data["caliases"]:
                await ctx.send(await _(ctx, "An alias with this name already exists!"))
                return

            if character_name not in data["characters"]:
                await ctx.send((await _(ctx, "Character {0} does not exist!")).format(character_name))
                return
            data["caliases"][alias_name] = character_name

            await ctx.bot.db.update_guild_data(ctx.guild, data)
        await ctx.send((await _(ctx, "Created a new alias {0} for character {1}")).format(alias_name, character_name))

    @character.command()
    async def removealias(self, ctx, alias_name: str):
        """Remove an alias
        Example: rp!c removealias Tom
        Only character owners may remove the aliases of their characters."""

        async with self.bot.di.rm.lock(ctx.guild.id):
            data = await self.bot.db.get_guild_data(ctx.guild)
            if "caliases" not in data:
                data["caliases"] = {}

            if alias_name not in data["caliases"]:
                await ctx.send(await _(ctx, "This alias doesn't exist!"))
                return

            if data["caliases"][alias_name] in data["characters"]:

                if data["characters"][data["caliases"][alias_name]][
                    1] != ctx.author.id and not checks.role_or_permissions(ctx,
                                                                          lambda r: r.name in (
                                                                                  'Bot Mod', 'Bot Admin',
                                                                                  'Bot Moderator'),
                                                                          manage_server=True):
                    await ctx.send(await _(ctx, "You cannot delete other people's aliases!"))
                    return

            del data["caliases"][alias_name]

            await ctx.bot.db.update_guild_data(ctx.guild, data)
        await ctx.send((await _(ctx, "Removed alias {0}")).format(alias_name))
