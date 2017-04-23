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


from collections import namedtuple, Counter
import discord
from discord.ext import commands

Pokemon = namedtuple("Pokemon", ["id", "name", "type", "stats", "meta"])
ServerItem = namedtuple("ServerItem", ["name", "description", "meta"])
Character = namedtuple("Character", ["name", "owner", "level", "team", "meta"])

class Converter(commands.MemberConverter):
    def convert(self):
        if self.argument == 'everyone' or self.argument == '@everyone':
            return 'everyone'
        return super().convert()

default_user = {
    "money": 0,
    "box": [],
    "items": dict(),
}

default_server = {
    "start": 0,
    "items": dict(),
    "characters": dict()
}

example_pokemon = {
    "id": 0,
    "name": "Pichi",
    "type": "Pikachu",
    "stats": {
        "level": 15,
        "health": 22,
        "attack": 34,
        "defense": 15,
        "spatk": 46,
        "spdef": 29
    },
    "meta": {
        "color": "yellow",
        "nature": "hasty"
    }
}

example_serveritem = {
    "name": "pokeball",
    "description": "Used to catch Pokemon, one of the weakest balls",
    "meta": {
        "color": "red and white",
        "rate": 20
    }
}

example_character = {
    "name": "Ash Ketchum",
    "owner": 166349353999532035,
    "level": 25,
    "team": [0],
    "meta": {
        "hair": "black",
        "favorite_pokemon": "Pichi",
        "image": "http://pa1.narvii.com/6320/3cf4ee1c3106552c4d8116218d556b97da0da020_128.gif"
    }
}

example_user = {
    "money": 25,
    "box": [
        Pokemon(**example_pokemon)
        ],
    "items": {
        "pokeball": 12
    }
}

example_server = {
    "start": 500,
    "items": {
        "pokeball": ServerItem(**example_serveritem)
    }
}


class DataInteraction(object):
    def __init__(self, bot):
        self.bot = bot

    async def get_team(self, guild, character):
        gd = await self.bot.db.get_guild_data(guild)
        character = Character(gd["characters"][character])
        owner = discord.utils.get(guild.members, id=character.owner)
        ud = await self.bot.db.get_user_data(owner)

        pokemon = [Pokemon(x) for x in ud["box"] if x[0] in character.team]

        return pokemon

    async def get_box(self, member):
        ud = await self.bot.db.get_user_data(member)
        return list(Pokemon(*x) for x in ud["box"])

    async def get_balance(self, member):
        return (await self.bot.db.get_user_data(member))["money"]

    async def get_inventory(self, member):
        ud = await self.bot.db.get_user_data(member)
        return ud["items"]

    async def get_pokemon(self, member, id):
        box = await self.get_box(member)
        for x in box:
            if x[0] == id:
                return x
        else:
            raise KeyError("Pokemon doesn't exist!")

    async def get_guild_start(self, guild):
        return (await self.bot.db.get_guild_data(guild))["start"]

    async def get_guild_items(self, guild):
        ud = await self.bot.db.get_guild_data(guild)
        return {y: ServerItem(*x) for y,x in ud["items"].items()}

    async def get_guild_characters(self, guild):
        ud = await self.bot.db.get_guild_data(guild)
        return {y: Character(*x) for y,x in ud["items"].items()}

    async def add_pokemon(self, owner, pokemon):
        ud = await self.bot.db.get_user_data(owner)
        id = ud["box"][-1].id + 1 if ud["box"] else 0
        ud["box"].append(Pokemon(**pokemon, id=id))
        await self.bot.db.update_user_data(owner, ud)
        return id

    async def new_item(self, guild, serveritem):
        gd = await self.bot.db.get_guild_data(guild)
        gd["items"][serveritem.name] = serveritem
        await self.bot.db.update_user_data(guild, gd)

    async def remove_item(self, guild, item):
        gd = await self.bot.db.get_guild_data(guild)
        del gd["items"]
        await self.bot.db.update_user_data(guild, gd)

    async def give_items(self, member, *items):
        ud = await self.bot.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].update(dict(items))
        await self.bot.db.update_user_data(member, ud)
        return ud["items"]

    async def take_items(self, member, *items):
        ud = await self.bot.db.get_user_data(member)
        ud["items"] = Counter(ud["items"])
        ud["items"].subtract(dict(items))
        if [1 for x in ud["items"].values() if x < 0]:
            raise ValueError("Cannot take more items than the user has!")
        await self.bot.db.update_user_data(member, ud)
        return ud["items"]

    async def add_eco(self, member, amount):
        ud = await self.bot.db.get_user_data(member)
        ud["money"] += amount
        await self.bot.db.update_user_data(member, ud)
        return ud["money"]

    async def set_eco(self, member, amount):
        ud = await self.bot.db.get_user_data(member)
        ud["money"] = amount
        await self.bot.db.update_user_data(member, ud)
        return ud["money"]

    async def add_to_team(self, guild, character, id):
        gd = await self.bot.db.get_guild_data(guild)
        character = gd["characters"][character]
        character["team"].append(id)
        if len(character["team"]) > 6:
            raise ValueError("Team is limited to 6!")
        await self.bot.db.update_guild_data(guild, gd)

    async def remove_from_team(self, guild, character, id):
        gd = await self.bot.db.get_guild_data(guild)
        character = gd["characters"][character]
        character["team"].remove(id)
        await self.bot.db.update_guild_data(guild, gd)
