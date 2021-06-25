from discord.ext import commands
import discord.utils
from discord.ext.commands.errors import CheckFailure


def is_owner_check(message):
    return message.author.id == 122739797646245899


def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))


# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually having
# the permissions required for them.
# Of course, the owner will always be able to execute commands.

def check_permissions(ctx, perms):
    msg = ctx.message
    if is_owner_check(msg):
        return True

    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def role_or_permissions(ctx, check, **perms):
    if check_permissions(ctx, perms):
        return True

    if callable(check):
        fcheck = check
    else:
        fcheck = lambda r: r.name in check

    ch = ctx.message.channel
    author = ctx.message.author
    if isinstance(ch, (discord.DMChannel, discord.GroupChannel)):
        return False  # can't have roles in PMs

    role = discord.utils.find(fcheck, author.roles)
    if role is None:
        if callable(check):
            raise commands.CommandError("You do not have permission to use this command!")
        else:
            for role in ctx.guild.roles:
                if role.name in check:
                    raise commands.CommandError(
                        "You need a special role to do this! ({})".format(", ".join(f"'{n}'" for n in check)))
            else:
                raise commands.CommandError("You need to create a role with one of the following names and give it to "
                                            "yourself: {}".format(", ".join(f"'{n}'" for n in check)))
    return True


def mod_or_inv():
    def predicate(ctx):
        return role_or_permissions(ctx, ('Bot Mod', 'Bot Admin', 'Bot Inventory', 'Bot Moderator'),
                                   manage_server=True)

    return commands.check(predicate)


def modpredicate(ctx):
    return role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                               manage_server=True)


def mod_or_permissions(**perms):
    def predicate(ctx):
        result = role_or_permissions(ctx, ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                     manage_server=True, **perms)
        if not result:
            raise CheckFailure("You need permission to use this command! "
                               "You need a Discord role with the name `Bot Admin` or the manage server permission to use "
                               "this command!")

        return result

    return commands.check(predicate)


def admin_or_permissions(**perms):
    def predicate(ctx):
        return role_or_permissions(ctx, ('Bot Admin',), manage_server=True, **perms)

    return commands.check(predicate)


def is_in_servers(*server_ids):
    def predicate(ctx):
        server = ctx.message.server
        if server is None:
            return False
        return server.id in server_ids

    return commands.check(predicate)


def is_lounge_cpp():
    return is_in_servers('153712751779250176')


def chcreate_or_permissions(**perms):
    def predicate(ctx):
        return role_or_permissions(ctx, lambda r: r.name == 'Temporary Channel', manage_channels=True, **perms)

    return commands.check(predicate)


def owner_or_permissions(**perms):
    def predicate(ctx):
        return role_or_permissions(ctx, lambda ctx: is_owner_check(ctx.message))

    return commands.check(predicate)


def nsfw_channel():
    def predicate(ctx):
        if not (isinstance(ctx.channel,
                           (discord.DMChannel, discord.GroupChannel)) or "nsfw" in ctx.channel.name.casefold()):
            raise ChannelError("This command can only be used in `nsfw` channels!")
        return True

    return commands.check(predicate)


def no_pm():
    def predicate(ctx):
        if ctx.command.name == "help":
            return True
        if ctx.guild is None:
            raise commands.NoPrivateMessage('This command cannot be used in private messages.')
        return True

    return commands.check(predicate)


class ChannelError(commands.CommandError):
    def __init__(self, message):
        self.__message__ = message
        super().__init__(message)
