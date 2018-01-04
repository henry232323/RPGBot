A RPG bot, with a working inventory, market and economy, team setups and characters aswell. Each user has a server unique inventory and balance. Players may list items on a market for other users to buy. Users may create characters with teams from Pokemon in their storage box. Server administrators may add and give items to the server and its users.
Pokemon boxes and server configurations. 

Made by Henry#6174

[**Add to your server**](https://discordapp.com/oauth2/authorize?client_id=305177429612298242&scope=bot&permissions=322625)

[**Support Server**](https://discord.gg/UYJb8fQ)



# Commands

- [Admin Commands](#admin-commands)
- [Characters Commands](#characters-commands)
  - [allchars](#allchars)
  - [character](#character)
  - [character create](#character-create)
  - [character delete](#character-delete)
  - [character edit](#character-edit)
  - [characters](#characters)
- [Economy Commands](#economy-commands)
  - [baltop](#baltop)
  - [bid](#bid)
  - [economy](#economy)
  - [givemoney](#givemoney)
  - [lootbox](#lootbox)
  - [lootbox buy](#lootbox-buy)
  - [lootbox create](#lootbox-create)
  - [lootbox delete](#lootbox-delete)
  - [lotto](#lotto)
  - [lotto enter](#lotto-enter)
  - [lotto new](#lotto-new)
  - [market](#market)
  - [market buy](#market-buy)
  - [market create](#market-create)
  - [market remove](#market-remove)
  - [market search](#market-search)
  - [pay](#pay)
  - [setbalance](#setbalance)
  - [shop](#shop)
  - [shop additem](#shop-additem)
  - [shop buy](#shop-buy)
  - [shop removeitem](#shop-removeitem)
  - [shop sell](#shop-sell)
  - [startbid](#startbid)
  - [takemoney](#takemoney)
- [Groups Commands](#groups-commands)
  - [guild](#guild)
  - [guild create](#guild-create)
  - [guild delete](#guild-delete)
  - [guild deposit](#guild-deposit)
  - [guild deposititems](#guild-deposititems)
  - [guild info](#guild-info)
  - [guild invite](#guild-invite)
  - [guild join](#guild-join)
  - [guild kick](#guild-kick)
  - [guild leave](#guild-leave)
  - [guild setdescription](#guild-setdescription)
  - [guild seticon](#guild-seticon)
  - [guild setimage](#guild-setimage)
  - [guild setmod](#guild-setmod)
  - [guild toggleopen](#guild-toggleopen)
  - [guild transfer](#guild-transfer)
  - [guild withdraw](#guild-withdraw)
  - [guild withdrawitems](#guild-withdrawitems)
  - [guilds](#guilds)
- [Inventory Commands](#inventory-commands)
  - [give](#give)
  - [giveitem](#giveitem)
  - [inventory](#inventory)
  - [takeitem](#takeitem)
- [Mapping Commands](#mapping-commands)
  - [map](#map)
  - [map check](#map-check)
  - [map create](#map-create)
  - [map move](#map-move)
- [Misc Commands](#misc-commands)
  - [donate](#donate)
  - [feedback](#feedback)
  - [info](#info)
  - [ping](#ping)
  - [rtd](#rtd)
  - [source](#source)
  - [totalcmds](#totalcmds)
- [Pokemon Commands](#pokemon-commands)
  - [box](#box)
  - [pokemon](#pokemon)
  - [pokemon create](#pokemon-create)
  - [pokemon info](#pokemon-info)
  - [pokemon release](#pokemon-release)
  - [pokemon trade](#pokemon-trade)
- [Salary Commands](#salary-commands)
  - [salaries](#salaries)
  - [salary](#salary)
  - [salary create](#salary-create)
  - [salary delete](#salary-delete)
- [Settings Commands](#settings-commands)
  - [setstart](#setstart)
  - [settings](#settings)
  - [settings additem](#settings-additem)
  - [settings iteminfo](#settings-iteminfo)
  - [settings items](#settings-items)
  - [settings removeitem](#settings-removeitem)
- [Team Commands](#team-commands)
  - [team](#team)
  - [team add](#team-add)
  - [team remove](#team-remove)
- [User Commands](#user-commands)
  - [experience](#experience)
  - [experience add](#experience-add)
  - [experience setlevel](#experience-setlevel)
  - [userinfo](#userinfo)
  

## Characters Commands

#### allchars
>**Description:** List all guild characters

>**Usage:** `rp!allchars`

#### character
>**Description:** Get info on a character

>**Usage:** `rp![character|c|char|personnage] <name>`

#### character create
>**Description:** Create a new character

>**Usage:** `rp!character [create|new|nouveau|creer] <name> [user]`

#### character delete
>**Description:** Delete a character of the given name (you must be the owner)

>**Usage:** `rp!character [delete|remove|supprimer] <name>`

#### character edit
>**Description:** Edit a character
Usage: rp!character edit John description John likes bananas!
Valid values for the [item] (second argument):
    name: the character's name
    description: the description of the character
    level: an integer representing the character's level
    meta: same usage as the character create command a: b value pairs

>**Usage:** `rp!character edit <character> <attribute> <value>`

#### characters
>**Description:** List all your characters

>**Usage:** `rp![characters|chars|personnages] [user]`

## Economy Commands

#### ***Economy related commands: balance, market, etc***

#### baltop
>**Description:** Get the top 10 server balances

>**Usage:** `rp!baltop`

#### bid
>**Description:** Place a bid on the current bidding item in the channel

>**Usage:** `rp!bid`

#### economy
>**Description:** Check your or another users balance

>**Usage:** `rp![economy|bal|balance|eco|e] [member]`

#### givemoney
>**Description:** Give the members money (Moderators)

>**Usage:** `rp!givemoney <amount> [members...]`

#### lootbox
>**Description:** List the current lootboxes

>**Usage:** `rp![lootbox|lb]`

#### lootbox buy
>**Description:** Buy a lootbox of the given name

>**Usage:** `rp!lootbox buy <name>`

#### lootbox create
>**Description:** Create a new lootbox, under the given `name` for the given cost
Use {item}x{#} notation to add items with {#} weight
Weight being an integer. For example:
bananax2 orangex3. The outcome of the box will be
Random Choice[banana, banana, orange, orange, orange]

>**Usage:** `rp!lootbox [create|new] <name> <cost> [items...]`

#### lootbox delete
>**Description:** Delete a lootbox with the given name

>**Usage:** `rp!lootbox [delete|remove] <name>`

#### lotto
>**Description:** List the currently running lottos.

>**Usage:** `rp![lotto|lottery]`

#### lotto enter
>**Description:** Enter the lottery with the given name.

>**Usage:** `rp!lotto [enter|join] <name>`

#### lotto new
>**Description:** Create a new lotto, with jackpot payout lasting time in seconds

>**Usage:** `rp!lotto [new|create] <name> <jackpot> <time>`

#### market
>**Description:** View the current market listings

>**Usage:** `rp![market|m|pm]`

#### market buy
>**Description:** Buy a given amount of an item from the player market at the cheapest given price

>**Usage:** `rp!market [buy|purchase] <id>`

#### market create
>**Description:** Create a new market listing

>**Usage:** `rp!market [create|createlisting|new|listitem|list] <cost> <amount> <item>`

#### market remove
>**Description:** Remove an item from the market

>**Usage:** `rp!market [remove|rm] <id>`

#### market search
>**Description:** Search the market for an item

>**Usage:** `rp!market search <item>`

#### pay
>**Description:** Pay another user money

>**Usage:** `rp!pay <amount> <member>`

#### setbalance
>**Description:** Set the balance of the given members to an amount

>**Usage:** `rp![setbalance|set] <amount> [members...]`

#### shop
>**Description:** Get all items currently listed on the server shop

>**Usage:** `rp!shop`

#### shop additem
>**Description:** Add an item to the server shop, to make an item unsaleable or unbuyable set their respective values to 0
pb!additem Pokeball
-> 0
-> 10
Can be sold for 10 and cannot be bought. Must be an existing item! Requires Bot Moderator or Admin

>**Usage:** `rp!shop [additem|add] <name>`

#### shop buy
>**Description:** Buy an item from the shop

>**Usage:** `rp!shop buy <item> <amount>`

#### shop removeitem
>**Description:** Remove a listed item

>**Usage:** `rp!shop removeitem <name>`

#### shop sell
>**Description:** Sell an item to the shop

>**Usage:** `rp!shop sell <item> <amount>`

#### startbid
>**Description:** Start a bid for an item

>**Usage:** `rp!startbid <item> <amount> <startbid>`

#### takemoney
>**Description:** Give the members money (Moderators)

>**Usage:** `rp!takemoney <amount> [members...]`

## Groups Commands

#### ***Commands for guild management***

#### guild
>**Description:** Get info on a member's guild. Subcommands for guild management

>**Usage:** `rp![guild|g] [member]`

#### guild create
>**Description:** Create a new guild

>**Usage:** `rp!guild create <name>`

#### guild delete
>**Description:** Delete your guild

>**Usage:** `rp!guild delete`

#### guild deposit
>**Description:** Deposit an amount of money into the guild bank

>**Usage:** `rp!guild deposit <amount> [guild_name]`

#### guild deposititems
>**Description:** Deposit items into the guild's storage, uses {item}x{#} notation

>**Usage:** `rp!guild deposititems [items...]`

#### guild info
>**Description:** Get info on a guild

>**Usage:** `rp!guild info <name>`

#### guild invite
>**Description:** Invite a user your closed guild

>**Usage:** `rp!guild invite <user>`

#### guild join
>**Description:** Join a guild (if you have an invite for closed guilds)

>**Usage:** `rp!guild join <name>`

#### guild kick
>**Description:** Kick a member from a guild

>**Usage:** `rp!guild kick <user>`

#### guild leave
>**Description:** Leave your guild

>**Usage:** `rp!guild leave`

#### guild setdescription
>**Description:** Set the guild's description

>**Usage:** `rp!guild [setdescription|setdesc] <description>`

#### guild seticon
>**Description:** Set the guild's icon

>**Usage:** `rp!guild seticon <url>`

#### guild setimage
>**Description:** Set the guild's image

>**Usage:** `rp!guild setimage <url>`

#### guild setmod
>**Description:** Give the listed users mod for your guild (guild owner only)

>**Usage:** `rp!guild setmod [members...]`

#### guild toggleopen
>**Description:** Toggle the Guilds open state

>**Usage:** `rp!guild toggleopen`

#### guild transfer
>**Description:** Transfer ownership of a guild to someone else

>**Usage:** `rp!guild transfer <user>`

#### guild withdraw
>**Description:** Take money from the guild bank

>**Usage:** `rp!guild withdraw <amount>`

#### guild withdrawitems
>**Description:** Withdraw items from the guild (guild mods only)

>**Usage:** `rp!guild withdrawitems [items...]`

#### guilds
>**Description:** List guilds

>**Usage:** `rp!guilds`

## Inventory Commands

#### give
>**Description:** Give items ({item}x{#}) to a member; ie: ;give @Henry#6174 pokeballx3

>**Usage:** `rp!give <other> [items...]`

#### giveitem
>**Description:** Give an item to a person (Not out of your inventory)

>**Usage:** `rp!giveitem <item> <num> [members...]`

#### inventory
>**Description:** Check your or another users inventory.

>**Usage:** `rp![inventory|i|inv] [member]`

#### takeitem
>**Description:** Remove an item from a person's inventory

>**Usage:** `rp![takeitem|take] <item> <num> [members...]`

## Mapping Commands

#### map
>**Description:** See the server map

>**Usage:** `rp![map|carte]`

#### map check
>**Description:** See what is on the current character's tile

>**Usage:** `rp!map [check|look|regarder|inspect|voir] <character>`

#### map create
>**Description:** Create a custom map for the guild (if one exists it will be overwritten)

>**Usage:** `rp!map [create|creer|new|nouvelle] <xsize> <ysize>`

#### map move
>**Description:** Move a character in a direction (valid directions include N/S/E/W for the cardinal directions respectively)
(Not yet added)

>**Usage:** `rp!map [move|bouger|aller|go] <direction>`

## Misc Commands

#### donate
>**Description:** Donation information

>**Usage:** `rp!donate`

#### feedback
>**Description:** Give me some feedback on the bot

>**Usage:** `rp!feedback <feedback>`

#### info
>**Description:** Bot Info

>**Usage:** `rp!info`

#### ping
>**Description:** Test the bot's connection ping

>**Usage:** `rp!ping`

#### rtd
>**Description:** Roll a number of dice with given sides (ndx notation)
Example: rp!rtd 3d7 2d4
Optional Additions:
    Test for success by adding a >/<#
    Grab the top n rolls by adding ^n
    Add to the final roll by just adding a number (pos or neg)
    
    Examples of all:
        rp!rtd 8d8 -12 15 ^4 >32
        
        -> Roll failed (30 > 32) ([8 + 7 + 6 + 6] + -12 + 15) (Grabbed top 4 out of 8)

>**Usage:** `rp![rtd|rollthedice|dice] [dice...]`

#### source
>**Description:** Displays my full source code or for a specific command.
To display the source code of a subcommand you have to separate it by
periods, e.g. tag.create for the create subcommand of the tag command.

>**Usage:** `rp!source [command]`

#### totalcmds
>**Description:** Get totals of commands and their number of uses

>**Usage:** `rp!totalcmds`

## Pokemon Commands

#### box
>**Description:** Check the pokemon in your box

>**Usage:** `rp!box [member]`

#### pokemon
>**Description:** Subcommands for Pokemon management, see rp!help pokemon
Same use as rp!box

>**Usage:** `rp![pokemon|p] [member]`

#### pokemon create
>**Description:** Create a new Pokemon to add to your box

>**Usage:** `rp!pokemon [create|new]`

#### pokemon info
>**Description:** Get info on a Pokemon

>**Usage:** `rp!pokemon info <id>`

#### pokemon release
>**Description:** Release a Pokemon from your box

>**Usage:** `rp!pokemon [release|delete|rm|remove] <id>`

#### pokemon trade
>**Description:** Offer a trade to a user.
`your_id` is the ID of the Pokemon you want to give, `their_id` is the Pokemon you want from them.
`other` being the user you want to trade with

>**Usage:** `rp!pokemon trade <your_id> <their_id> <other>`

## Salary Commands

#### ***Salary commands***

#### salaries
>**Description:** See guild salaries

>**Usage:** `rp!salaries`

#### salary
>**Description:** Get a role's salary. Also includes salary subcommands

>**Usage:** `rp![salary|sal] <role>`

#### salary create
>**Description:** Create a daily salary for a user with the given role.
Roles are paid every day at 24:00, every user with the role will receive the amount specified.
If a role with a salary is deleted, the salary will also be deleted.

>**Usage:** `rp!salary create <amount> <role>`

#### salary delete
>**Description:** Remove a created salary

>**Usage:** `rp!salary delete <role>`

## Settings Commands

#### setstart
>**Description:** Set the money start amount for a guild

>**Usage:** `rp!setstart <amount>`

#### settings
>**Description:** Get the current server settings

>**Usage:** `rp![settings|s|configuration|conf]`

#### settings additem
>**Description:** Add a custom item

>**Usage:** `rp!settings additem <name>`

#### settings iteminfo
>**Description:** Get info on a server item

>**Usage:** `rp!settings iteminfo <item>`

#### settings items
>**Description:** See all items for a guild

>**Usage:** `rp!settings items`

#### settings removeitem
>**Description:** Remove a custom item

>**Usage:** `rp!settings [removeitem|deleteitem] <name>`

## Team Commands

#### team
>**Description:** Check a character's team

>**Usage:** `rp!team <character>`

#### team add
>**Description:** Add a Pokemon to a character's team

>**Usage:** `rp!team [add|addmember] <character> <id>`

#### team remove
>**Description:** Remove a Pokemon from a character's team

>**Usage:** `rp!team [remove|removemember] <character> <id>`

## User Commands

#### ***Commands for guild management***

#### experience
>**Description:** Get your or another user's level information. Help on this command for experience subcommands
EXP is calculated using a 0.1x^2+5x+4 where x is equal to the user's current level
Spamming commands or messages will not earn more exp!

>**Usage:** `rp![experience|exp] [member]`

#### experience add
>**Description:** Give the given members an amount of experience

>**Usage:** `rp!experience add <amount> [members...]`

#### experience setlevel
>**Description:** Set the given members level

>**Usage:** `rp!experience [setlevel|set] <level> [members...]`

#### userinfo
>**Description:** Get info on a user

>**Usage:** `rp![userinfo|ui] [user]`