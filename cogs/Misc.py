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

class Misc(object):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["rollthedice", "dice"])
    async def rtd(self, ctx, *dice: str):
        """Roll a number of dice with given sides (ndx notation)
        Example: pb!rtd 3d7 2d4 5d8 +20 <30 Test for success by adding >/<# to the end (optional)"""
        try:
            dice = list(dice)
            rolls = dict()
            add = []
            rel = None
            if dice[-1].startswith((">", "<")):
                rel = dice.pop(-1)
                val = int(rel.strip("<>"))
                type = rel[0]

            for die in dice:
                try:
                    number, sides = die.split("d")
                    number, sides = int(number), int(sides)
                    rolls[sides] = [randint(1, sides) for x in range(number)]
                except ValueError:
                    add.append(int(die))

            total = sum(sum(x) for x in rolls.values()) + sum(add)

            if rel is not None:
                if type == "<":
                    if total <  val:
                        succ = "suceeded"
                    else:
                        succ = "failed"
                else:
                    if total > val:
                        succ = "suceeded"
                    else:
                        succ = "failed"

                fmt = "Roll **{0}** ({1} {2} {3}) ([{4}] + {5})" if add else "Roll **{0}** ({1} {2} {3}) ([{4}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(succ, total, type, val, all, " + ".join(map(lambda x: str(x), add)))
            else:
                fmt = "Rolled **{0}** ([{1}] + {2})" if add else "Rolled **{0}** ([{1}])"
                all = "] + [".join(" + ".join(map(lambda x: str(x), roll)) for roll in rolls.values())
                msg = fmt.format(total, all, " + ".join(map(lambda x: str(x), add)))
            await ctx.send(msg)
        except Exception as e:
            print(e)
            await ctx.send("Invalid syntax!")