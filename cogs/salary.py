import datetime
import asyncio
import json
from collections import defaultdict

import discord
from discord.ext import commands

from .utils import data, checks
from .utils.translation import _


class Salary(object):
    """Salary commands"""

    def __init__(self, bot):
        self.bot = bot
        self.first = True

    async def on_ready(self):
        self.bot.loop.create_task(self.run_salaries())

    async def run_salaries(self):
        if self.first:
            self.first = False
            _today = datetime.datetime(*datetime.datetime.utcnow().timetuple()[:3])
            time_until = (_today + datetime.timedelta(days=1)).timestamp() - datetime.datetime.utcnow().timestamp()
            await asyncio.sleep(time_until)
            while True:
                try:
                    dels = defaultdict(list)

                    req = f"""SELECT UUID, info ->> 'salaries' FROM servdata;"""
                    async with self.bot.db._conn.acquire() as connection:
                        response = await connection.fetch(req)
                    guilds = (y for y in ((x["uuid"], json.loads(x["?column?"])) for x in response if x["?column?"]) if
                              y[1])

                    for guild, roles in guilds:
                        try:
                            gob = self.bot.get_guild(guild)
                            if gob:
                                for role, amount in roles.items():
                                    rob = discord.utils.get(gob.roles, id=int(role))
                                    if rob:
                                        for member in rob.members:
                                            if isinstance(amount, int):
                                                try:
                                                    await self.bot.di.add_eco(member, amount)
                                                except ValueError:
                                                    await self.bot.di.set_eco(member, 0)
                                            else:
                                                payamount, giveamount = sum(
                                                    filter(lambda x: isinstance(x, (int, float)), amount)), tuple(
                                                    filter(
                                                        lambda x: isinstance(x, (list, tuple)), amount))
                                                if payamount:
                                                    try:
                                                        await self.bot.di.add_eco(member, payamount)
                                                    except ValueError:
                                                        await self.bot.di.set_eco(member, 0)
                                                if giveamount:
                                                    await self.bot.di.update_items(member, *giveamount)
                                    else:
                                        dels[gob].append((roles, role))
                        except:
                            pass
                    try:
                        for g, rs in dels.items():
                            for allroles, r in rs:
                                del allroles[r]
                            await self.bot.di.update_salaries(g, allroles)
                    except:
                        pass
                except:
                    pass
                finally:
                    await asyncio.sleep(86400)

    @commands.command()
    @checks.no_pm()
    async def salaries(self, ctx):
        """See guild salaries"""
        embed = discord.Embed()
        sals = await self.bot.di.get_salaries(ctx.guild)
        if not sals:
            await ctx.send(await _(ctx, "There are no current salaries on this server"))
        else:
            dels = []
            for role, amount in sals.items():
                roleobj = discord.utils.get(ctx.guild.roles, id=int(role)).name
                if roleobj is None:
                    dels.append(role)
                embed.add_field(name=roleobj,
                                value="{} {}".format(amount, await ctx.bot.di.get_currency(ctx.guild)))
            for d in dels:
                del sals[d]
            if dels:
                await self.bot.di.update_salaries(ctx.guild, sals)
            embed.set_author(name=await _(ctx, "Guild Salaries"), icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=["sal"])
    @checks.no_pm()
    async def salary(self, ctx, role: discord.Role):
        """Get a role's salary. Also includes salary subcommands"""
        salary = (await self.bot.di.get_salaries(ctx.guild)).get(role.id, None)
        if salary is None:
            await ctx.send(await _(ctx, "That role does not have a salary!"))
        else:
            await ctx.send((await _(ctx, "{} has a daily salary of {}")).format(role, salary))

    @salary.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def create(self, ctx, role: discord.Role, *items_or_number: data.ItemOrNumber):
        """Create a daily salary for a user with the given role.
         Roles are paid every day at 24:00, every user with the role will receive the amount specified.
         If a role with a salary is deleted, the salary will also be deleted.
         For example
         `rp!salary create @Bot Creator 500` Will create a salary of $500 for a user daily
         `rp!salary create @Bot Creator Bananax3 Orangex4` Will create a salary of 3 Bananas and 4 Oranges for a user daily
         """
        sals = await self.bot.di.get_salaries(ctx.guild)
        if len(items_or_number) == 1 and isinstance(items_or_number[0], int):
            items_or_number = items_or_number[0]

        sals[role.id] = items_or_number
        await self.bot.di.update_salaries(ctx.guild, sals)
        await ctx.send((await _(ctx, "Successfully created a daily salary of {} for {}")).format(items_or_number, role))

    @salary.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def delete(self, ctx, *, role: discord.Role):
        """Remove a created salary"""
        sals = await self.bot.di.get_salaries(ctx.guild)
        if str(role.id) in sals:
            del sals[str(role.id)]
            await self.bot.di.update_salaries(ctx.guild, sals)
            await ctx.send((await _(ctx, "Successfully deleted the daily salary for {}")).format(role))
        else:
            await ctx.send(await _(ctx, "That role has no salaries!"))

    @salary.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def payout(self, ctx, role: discord.Role = None):
        """Manually pay out salaries for a role or all roles"""
        dels = []
        roles = await self.bot.di.get_salaries(ctx.guild)
        try:
            if role is not None:
                roles = {role.id: roles[str(role.id)]}
        except KeyError:
            await ctx.send(await _(ctx, "That role doesn't have a salary!"))
        for role, amount in roles.items():
            rob = discord.utils.get(ctx.guild.roles, id=int(role))
            if rob:
                for member in rob.members:
                    if isinstance(amount, int):
                        try:
                            await self.bot.di.add_eco(member, amount)
                        except ValueError:
                            await self.bot.di.set_eco(member, 0)
                    else:
                        payamount, giveamount = sum(
                            filter(lambda x: isinstance(x, (int, float)), amount)), tuple(filter(
                            lambda x: isinstance(x, (list, tuple)), amount))
                        if payamount:
                            try:
                                await self.bot.di.add_eco(member, payamount)
                            except ValueError:
                                await self.bot.di.set_eco(member, 0)
                        if giveamount:
                            await self.bot.di.update_items(member, *giveamount)
            else:
                dels.append(role)

        if dels:
            await ctx.send((await _(ctx, "Roles {} were missing")).format(dels))
            for role in dels:
                del roles[role]

            await self.bot.di.update_salaries(ctx.guild, roles)

        await ctx.send(await _(ctx, "Salaries payed out"))
