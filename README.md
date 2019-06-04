A RPG bot, with a working inventory, market and economy, team setups and characters aswell. Each user has a server unique inventory and balance. Players may list items on a market for other users to buy. Users may create characters with teams from Pet in their storage box. Server administrators may add and give items to the server and its users.
Pet boxes and server configurations. 

Made by Henry#6174

[![Discord Bots](https://discordbots.org/api/widget/305177429612298242.svg)](https://discordbots.org/bot/305177429612298242)

[**Add to your server**](https://discordapp.com/oauth2/authorize?client_id=305177429612298242&scope=bot&permissions=805694529)

[**Support Server**](https://discord.gg/mXZg2mk)

### Translators
#### French
- [@wRadion#5043](https://discordapp.com/channels/@me/98073537113247744) https://github.com/wRadion
- [@Henry#6174](https://discordapp.com/channels/@me/122739797646245899) (Me) https://github.com/henry232323
- https://github.com/youqad
- https://github.com/Philip-Nicolas
#### Russian
- https://github.com/Mozyl
- https://github.com/Atmyre
#### German
- https://github.com/LW001
- [@Potzerus#3950](https://discordapp.com/channels/@me/125660719323676672) https://github.com/Potzerus
#### Spanish
- https://github.com/Luistorch
- https://github.com/Looker845

### Contributors
- [@terabix#1770](https://discordapp.com/channels/@me/141211057485119488)

### Art Credits
- All bot icons used were made by [@MOSE-FR#5388](https://discordapp.com/channels/@me/249894348567740416)
- Also thanks to [@Volgrim Evrazasvae#5252](https://discordapp.com/channels/@me/335604493192396801)




# Commands

- [Characters Commands](#characters-commands)
  - [allchars](#allchars)
  - [character](#character)
  - [character assume](#character-assume)
  - [character create](#character-create)
  - [character delete](#character-delete)
  - [character edit](#character-edit)
  - [character remattr](#character-remattr)
  - [character unassume](#character-unassume)
  - [characters](#characters)
  - [chareco](#chareco)
  - [chareco givemoney](#chareco-givemoney)
  - [chareco pay](#chareco-pay)
  - [chareco setbalance](#chareco-setbalance)
  - [chareco takemoney](#chareco-takemoney)
  - [charinv](#charinv)
  - [charinv craft](#charinv-craft)
  - [charinv give](#charinv-give)
  - [charinv giveitem](#charinv-giveitem)
  - [charinv takeitem](#charinv-takeitem)
  - [charinv use](#charinv-use)
- [Economy Commands](#economy-commands)
  - [baltop](#baltop)
  - [bank deposit](#bank-deposit)
  - [bank withdraw](#bank-withdraw)
  - [bid](#bid)
  - [economy](#economy)
  - [givemoney](#givemoney)
  - [lotto](#lotto)
  - [lotto cancel](#lotto-cancel)
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
  - [craft](#craft)
  - [give](#give)
  - [giveitem](#giveitem)
  - [inventory](#inventory)
  - [lootbox](#lootbox)
  - [lootbox buy](#lootbox-buy)
  - [lootbox create](#lootbox-create)
  - [lootbox delete](#lootbox-delete)
  - [offer](#offer)
  - [recipe](#recipe)
  - [recipe create](#recipe-create)
  - [recipe delete](#recipe-delete)
  - [recipes](#recipes)
  - [respond](#respond)
  - [takeitem](#takeitem)
  - [use](#use)
  - [wipeinv](#wipeinv)
- [Mapping Commands](#mapping-commands)
  - [map](#map)
  - [map buy](#map-buy)
  - [map check](#map-check)
  - [map create](#map-create)
  - [map delete](#map-delete)
  - [map down](#map-down)
  - [map generate](#map-generate)
  - [map left](#map-left)
  - [map right](#map-right)
  - [map up](#map-up)
- [Misc Commands](#misc-commands)
  - [donate](#donate)
  - [feedback](#feedback)
  - [info](#info)
  - [ping](#ping)
  - [rtd](#rtd)
  - [source](#source)
  - [totalcmds](#totalcmds)
- [Pets Commands](#pets-commands)
  - [box](#box)
  - [pet](#pet)
  - [pet create](#pet-create)
  - [pet edit](#pet-edit)
  - [pet info](#pet-info)
  - [pet release](#pet-release)
  - [pet trade](#pet-trade)
- [Salary Commands](#salary-commands)
  - [salaries](#salaries)
  - [salary](#salary)
  - [salary create](#salary-create)
  - [salary delete](#salary-delete)
  - [salary payout](#salary-payout)
- [Settings Commands](#settings-commands)
  - [currency](#currency)
  - [deleteafter](#deleteafter)
  - [hideinv](#hideinv)
  - [language](#language)
  - [loaddnd](#loaddnd)
  - [loaddndmagic](#loaddndmagic)
  - [loaddndshop](#loaddndshop)
  - [loadmagicshop](#loadmagicshop)
  - [loadpokemon](#loadpokemon)
  - [loadstarwars](#loadstarwars)
  - [loadstarwarsshop](#loadstarwarsshop)
  - [setstart](#setstart)
  - [settings](#settings)
  - [settings additem](#settings-additem)
  - [settings iteminfo](#settings-iteminfo)
  - [settings items](#settings-items)
  - [settings removeitem](#settings-removeitem)
  - [unload](#unload)
- [Team Commands](#team-commands)
  - [team](#team)
  - [team add](#team-add)
  - [team remove](#team-remove)
- [User Commands](#user-commands)
  - [experience](#experience)
  - [experience add](#experience-add)
  - [experience disable](#experience-disable)
  - [experience enable](#experience-enable)
  - [experience setlevel](#experience-setlevel)
  - [userinfo](#userinfo)
  

## Characters Commands

#### allchars
>**Description:** List all guild characters

>**Usage:** `rp!allchars`

#### character
>**Description:** Get info on a character

>**Usage:** `rp![character|c|char|personnage] <name>`

#### character assume
>**Description:** Assume a character. You will send messages with this character's icon and name. Necessary for some character inventory and economy commands

>**Usage:** `rp!character assume <name>`

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
    meta: used like the additional info section when creating; can be used to edit/remove all attributes
Anything else will edit single attributes in the additional info section

>**Usage:** `rp!character edit <character> <attribute> <value>`

#### character remattr
>**Description:** Delete a character attribute
Usage: rp!character remattr John hair color

>**Usage:** `rp!character remattr <character> <attribute>`

#### character unassume
>**Description:** Unassume a character

>**Usage:** `rp!character unassume <character>`

#### characters
>**Description:** List all your characters

>**Usage:** `rp![characters|chars|personnages] [user]`

#### chareco
>**Description:** Check your or another character's balance

>**Usage:** `rp![chareco|ceco|ce|cbal] [name]`

#### chareco givemoney
>**Description:** Give the member's money (Moderators)

>**Usage:** `rp!chareco givemoney <amount> [names...]`

#### chareco pay
>**Description:** Pay another user money

>**Usage:** `rp!chareco pay <amount> <other>`

#### chareco setbalance
>**Description:** Set the balance of the given members to an amount

>**Usage:** `rp!chareco [setbalance|set] <amount> [names...]`

#### chareco takemoney
>**Description:** Take the member's money (Moderators)

>**Usage:** `rp!chareco takemoney <amount> [names...]`

#### charinv
>**Description:** Check your or another character's inventory. Example: rp!cinv Name or just rp!ci

>**Usage:** `rp![charinv|ci|cinv] [name]`

#### charinv craft
>**Description:** Craft a recipe with a given name from the available server recipes; e.g. rp!craft 5 Apple Pie

>**Usage:** `rp!charinv craft <number> <name>`

#### charinv give
>**Description:** Give items ({item}x{#}) to a character; ie: rp!ci give Name Pokeballx3

>**Usage:** `rp!charinv give <other> [items...]`

#### charinv giveitem
>**Description:** Give an item to a character (Not out of your inventory)
Example: rp!ci giveitem Banana 32 Char1 Char2 Char3

>**Usage:** `rp!charinv giveitem <item> <num> [names...]`

#### charinv takeitem
>**Description:** Remove an item from a character's inventory

>**Usage:** `rp!charinv [takeitem|take] <item> <num> [names...]`

#### charinv use
>**Description:** Use an item. Example `rp!use Banana` or `rp!use Banana 5`
To make an item usable, you must put the key `used: <message>` when you are adding additional information for an item

>**Usage:** `rp!charinv use <item> [number=1]`

## Economy Commands

#### ***Economy related commands: balance, market, etc***

#### baltop
>**Description:** Get the top 10 server balances

>**Usage:** `rp!baltop`

#### bank deposit
>**Description:** Deposit `amount` into the bank

>**Usage:** `rp!bank deposit <amount>`

#### bank withdraw
>**Description:** Withdraw `amount` from the bank

>**Usage:** `rp!bank withdraw <amount>`

#### bid
>**Description:** Place a bid on the current bidding item in the channel

>**Usage:** `rp!bid`

#### economy
>**Description:** Check your or another users balance

>**Usage:** `rp![economy|bal|balance|eco|e] [member]`

#### givemoney
>**Description:** Give the member's money (Moderators)

>**Usage:** `rp!givemoney <amount> [members...]`

#### lotto
>**Description:** List the currently running lottos.

>**Usage:** `rp![lotto|lottery]`

#### lotto cancel
>**Description:** Cancel a lottery

>**Usage:** `rp!lotto [cancel|delete] <name>`

#### lotto enter
>**Description:** Enter the lottery with the given name.

>**Usage:** `rp!lotto [enter|join] <name>`

#### lotto new
>**Description:** Create a new lotto, with jacpot payout lasting time in seconds

>**Usage:** `rp!lotto [new|create] <name> <jackpot> <time>`

#### market
>**Description:** View the current market listings

>**Usage:** `rp![market|m|pm]`

#### market buy
>**Description:** Buy a given amount of an item from the player market at the cheapest given price

>**Usage:** `rp!market [buy|purchase|acheter] <id>`

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
>**Description:** Take the member's money (Moderators)

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

>**Usage:** `rp!guild delete [name]`

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

#### craft
>**Description:** Craft a recipe with a given name from the available server recipes; e.g. rp!craft 5 Apple Pie

>**Usage:** `rp!craft <number> <name>`

#### give
>**Description:** Give items ({item}x{#}) to a member; ie: rp!give @Henry#6174 Pokeballx3

>**Usage:** `rp!give <other> [items...]`

#### giveitem
>**Description:** Give an item to a person (Not out of your inventory)
Example: rp!giveitem Banana 32 @Henry#6174 @RPGBot#8700 @JoeShmoe#3012

>**Usage:** `rp!giveitem <item> <num> [members...]`

#### inventory
>**Description:** Check your or another users inventory. Example: rp!inventory @Henry#6174 or just rp!inventory

>**Usage:** `rp![inventory|i|inv] [member]`

#### lootbox
>**Description:** List the current lootboxes

>**Usage:** `rp![lootbox|lb] [name]`

#### lootbox buy
>**Description:** Buy a lootbox of the given name

>**Usage:** `rp!lootbox buy <name>`

#### lootbox create
>**Description:** Create a new lootbox, under the given `name` for the given cost
Use {item}x{#} notation to add items with {#} weight
Weight being an integer. For example:
rp!lootbox create MyBox 500 bananax2 orangex3. The outcome of the box will be
Random Choice[banana, banana, orange, orange, orange]
The price can also be an item (or several items), for example
rp!lootbox create MyBox Key bananax2 orangex3
or
rp!lootbox create MyBox Keyx2 bananax3 orangex3

>**Usage:** `rp!lootbox [create|new] <name> <cost> [items...]`

#### lootbox delete
>**Description:** Delete a lootbox with the given name

>**Usage:** `rp!lootbox [delete|remove] <name>`

#### offer
>**Description:** Send a trade offer to another user. Usage: rp!inventory offer @Henry bananax3 applex1 --Format items as {item}x{#}

>**Usage:** `rp!offer <other> [items...]`

#### recipe
>**Description:** Subcommands for recipes. See data on a specific recipe; e.g. rp!recipe Banana

>**Usage:** `rp!recipe <name>`

#### recipe create
>**Description:** Create a new recipe; e.g.
> rp!recipe create Apple Pie
>> What items must be consumed to follow this recipe? e.g. Applex5 Breadx2
> Applex5 Breadx15 "Pie Tinx1"
>> What items will be given upon the completion of this recipe? e.g. "Apple Piex1"
> "Apple Piex1" "Pie Tinx1"
>> Successfully created new recipe!

>**Usage:** `rp!recipe create <name>`

#### recipe delete
>**Description:** Delete the recipe with the given name; e.g. rp!recipe delete Apple Pie

>**Usage:** `rp!recipe delete <name>`

#### recipes
>**Description:** List all the available server recipes

>**Usage:** `rp!recipes`

#### respond
>**Description:** Respond to a trade offer by another user. Usage: rp!inventory respond @Henry grapex8 applex1 --Format items as {item}x{#}

>**Usage:** `rp!respond <other> [items...]`

#### takeitem
>**Description:** Remove an item from a person's inventory

>**Usage:** `rp![takeitem|take] <item> <num> [members...]`

#### use
>**Description:** Use an item. Example `rp!use Banana` or `rp!use Banana 5`
To make an item usable, you must put the key `used: <message>` when you are adding additional information for an item

>**Usage:** `rp!use <item> [number=1]`

#### wipeinv
>**Description:** Wipe all listed inventories. Must be administrator. To wipe ALL inventories do `rp!wipeinv everyone`

>**Usage:** `rp!wipeinv [members...]`

## Mapping Commands

#### map
>**Description:** See the server map

>**Usage:** `rp![map|carte] <name>`

#### map buy
>**Description:** Buy an item from the shop on the current tile

>**Usage:** `rp!map buy <mapname> <character> <amount> <itemname>`

#### map check
>**Description:** Inspect the current tile a character is on

>**Usage:** `rp!map [check|look|regarder|inspect|voir] <mapname> <character>`

#### map create
>**Description:** Create a map that will generate as it is explored. Set xmax and ymax to -1 for an infinite map
($5 Patrons only)

>**Usage:** `rp!map create <mapname> <xmax> <ymax>`

#### map delete
>**Description:** Delete a map

>**Usage:** `rp!map [delete|supprimer] <name>`

#### map down
>**Description:** Move south on a map

>**Usage:** `rp!map [down|south|sud] <mapname> <character>`

#### map generate
>**Description:** Create a custom map for the guild.
Usage: `rp!map create Earth 64 64`
    This will create a 64x64 map that will generate as the players explore it

>**Usage:** `rp!map [generate|creer|new|nouvelle] <name> <xsize> <ysize>`

#### map left
>**Description:** Move West on a map

>**Usage:** `rp!map [left|west|ouest|gauche] <mapname> <character>`

#### map right
>**Description:** Move East on a map

>**Usage:** `rp!map [right|east|est|droit] <mapname> <character>`

#### map up
>**Description:** Move North on a map

>**Usage:** `rp!map [up|north|nord] <mapname> <character>`

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

>**Usage:** `rp![rtd|rollthedice|dice|roll] [dice...]`

#### source
>**Description:** Displays my full source code or for a specific command.
To display the source code of a subcommand you have to separate it by
periods, e.g. tag.create for the create subcommand of the tag command.

>**Usage:** `rp!source [command]`

#### totalcmds
>**Description:** Get totals of commands and their number of uses

>**Usage:** `rp!totalcmds`

## Pets Commands

#### box
>**Description:** Check the pet in your box

>**Usage:** `rp!box [member]`

#### pet
>**Description:** Subcommands for Pet management, see rp!help pet
Same use as rp!box

>**Usage:** `rp![pet|p] [member]`

#### pet create
>**Description:** Create a new Pet to add to your box

>**Usage:** `rp!pet [create|new]`

#### pet edit
>**Description:** Edit a pet
Usage: rp!pet edit 5 description John likes bananas!
Valid values for the [item] (second argument):
    name: the character's name
    description: the description of the character
    level: an integer representing the character's level
    meta: used like the additional info section when creating; can be used to edit/remove all attributes
Anything else will edit single attributes in the additional info section

>**Usage:** `rp!pet edit <pet_id> <attribute> <value>`

#### pet info
>**Description:** Get info on a Pet

>**Usage:** `rp!pet info <id>`

#### pet release
>**Description:** Release a Pet from your box

>**Usage:** `rp!pet [release|delete|rm|remove] <id>`

#### pet trade
>**Description:** Offer a trade to a user.
`your_id` is the ID of the Pet you want to give, `their_id` is the Pet you want from them.
`other` being the user you want to trade with

>**Usage:** `rp!pet trade <your_id> <their_id> <other>`

## Salary Commands

#### ***Salary commands***

#### salaries
>**Description:** See server salaries

>**Usage:** `rp!salaries`

#### salary
>**Description:** Get a role's salary. Also includes salary subcommands

>**Usage:** `rp![salary|sal] <role>`

#### salary create
>**Description:** Create a daily salary for a user with the given role.
Roles are paid every day at 24:00, every user with the role will receive the amount specified.
If a role with a salary is deleted, the salary will also be deleted.
For example
`rp!salary create @Bot Creator 500` Will create a salary of $500 for a user daily
`rp!salary create @Bot Creator Bananax3 Orangex4` Will create a salary of 3 Bananas and 4 Oranges for a user daily

>**Usage:** `rp!salary create <role> [items_or_number...]`

#### salary delete
>**Description:** Remove a created salary

>**Usage:** `rp!salary delete <role>`

#### salary payout
>**Description:** Manually pay out salaries for a role or all roles

>**Usage:** `rp!salary payout [role]`

## Settings Commands

#### currency
>**Description:** Set the guild currency

>**Usage:** `rp!currency <currency>`

#### deleteafter
>**Description:** Set a time for messages to be automatically deleted after running in seconds. `rp!deleteafter 0` to make messages never be deleted

>**Usage:** `rp!deleteafter <time>`

#### hideinv
>**Description:** Set whether or not user inventories are hidden. If enabled, inventories will be sent via DMs.

>**Usage:** `rp!hideinv <value>`

#### language
>**Description:** Set the guild language or check the language

>**Usage:** `rp!language [language]`

#### loaddnd
>**Description:** This command will pre-load all D&D items and make them available to give

>**Usage:** `rp!loaddnd`

#### loaddndmagic
>**Description:** This command will pre-load all D&D Magic items and make them available to give

>**Usage:** `rp!loaddndmagic`

#### loaddndshop
>**Description:** This command will pre-load all D&D items and make them available in shop

>**Usage:** `rp!loaddndshop`

#### loadmagicshop
>**Description:** This command will pre-load all D&D Magic items and make them available in shop

>**Usage:** `rp!loadmagicshop`

#### loadpokemon
>**Description:** This command will pre-load all Pokemon items and make them available to give

>**Usage:** `rp!loadpokemon`

#### loadstarwars
>**Description:** This command will pre-load all D&D items and make them available to give

>**Usage:** `rp!loadstarwars`

#### loadstarwarsshop
>**Description:** This command will pre-load all Star Wars items and make them available in shop

>**Usage:** `rp!loadstarwarsshop`

#### setstart
>**Description:** Set the money start amount for a guild

>**Usage:** `rp!setstart <amount>`

#### settings
>**Description:** Get the current server settings

>**Usage:** `rp![settings|s|configuration|conf]`

#### settings additem
>**Description:** Add a custom item.
 Custom keys that can be used for special additions:
    `image` Setting this to a URL will give that item a special thumbnail when info is viewed for it
    `used` A message for when the item is used
>Henry: rp!settings additem Example
RPGBot: Describe the item (a description for the item)
Henry: This is an example item
RPGBot: Additional information? (Attributes formatted in a list i.e color: 400, value: 200 Set an image for this item with the image key i.e. image: http://image.com/image.png Set this item as usable by adding used key i.e. used: You open the jar and the bird flies away
Henry: used: You used this item!, image: http://www.sourcecertain.com/img/Example.png
RPGBot:  Item successfully created
    

>**Usage:** `rp!settings additem <name>`

#### settings iteminfo
>**Description:** Get info on a server item

>**Usage:** `rp!settings iteminfo <item>`

#### settings items
>**Description:** See all items for a guild

>**Usage:** `rp!settings items [letter]`

#### settings removeitem
>**Description:** Remove a custom item

>**Usage:** `rp!settings [removeitem|deleteitem] <name>`

#### unload
>**Description:** Unload Pokemon, D&D, D&D Magic, or Star Wars items. `rp!unload {name}` where name is either dnd, dndmagic, pokemon or starwars

>**Usage:** `rp!unload <name>`

## Team Commands

#### team
>**Description:** Check a character's team

>**Usage:** `rp!team <character>`

#### team add
>**Description:** Add a Pet to a character's team

>**Usage:** `rp!team [add|addmember] <character> <id>`

#### team remove
>**Description:** Remove a Pet from a character's team

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

#### experience disable
>**Description:** Disable EXP settings for a guild

>**Usage:** `rp!experience disable`

#### experience enable
>**Description:** Enable EXP settings for a guild

>**Usage:** `rp!experience enable`

#### experience setlevel
>**Description:** Set the given members level

>**Usage:** `rp!experience [setlevel|set] <level> [members...]`

#### userinfo
>**Description:** Get info on a user

>**Usage:** `rp![userinfo|ui] [user]`