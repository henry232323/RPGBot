Welcome to RPGBot! Sit down, relax and get ready to fill your gullet with plenty of how-to and whats-it to get you started here. Whether you're looking to build a server focused on a full-scale role-playing world, or just want to add some more variety to your collection of unique bots, look no more! This Discord bot serves as your tavern master for RPing in the flavour of your choice.

Here in this compendium, I'll be going over some of the house specials RPGBot has to offer. If you would like a look at the full menu, just enter rp!help and a list of all the base commands [cmds] will be sent right to your DM. Now, take any of those and put it after the help cmd rp!help <cmd> and you will get a more detailed list of the sub cmds for that particular one. If you then take one of those cmds and add it to the format rp!help <cmd> <subcmd> you'll get a list of all the ingredients that make up that specific action.

## Some things to note:
  - For a full index of the Bot's commands, use `rp!help` or read through the [command list](https://github.com/henry232323/RPGBot/blob/master/README.md)
  - Some commands require a special rank, you will see an error that mentions the `Bot Mod` or `Bot Admin` roles. If a command does not work with `Bot Mod`, it likely requires `Bot Admin`, these two roles are not the same. To use these commands, create a role with one of the two names (case sensitive) and give it to the user you want to have those permissions.
  - Command examples using [r|p] separate alternative usable cmds; only one is used NOT both/all.
  - Command examples using <rp> mean for the word(s) within to be substituted with the appropitate entry.
  - Command examples using [g] mean that the action is optional.
  - Command actions with a name containing spaces require "My Character One" surrounding the name. Often, if it is the last argument, the quotation marks can be omitted.
  - Some commands that may need you to list multiple items and the number of each of those items may use a special syntax called Item x Number notation. This means you will put the item name, followed by an x (meaning times), then the number of that item you want. For example `rp!give @Henry#6174 Bananax3 Orangex5`. Some items may have multiple words in them, for these format them as follows: `rp!give @Henry#6174 "Old Bookx3"` (with quotation marks)
  
  
  **NOTE: All example brackets are not used in the actual comand.**
  For example, if the signature of the command is `rp![character|char|c|personnage] <name>`, that means to use the command we may do one of the following:
    - `rp!character Henry`
    - `rp!personnage Henry`
    - `rp!c My Character's Name Here` 


## Characters
  - rp![character|char|c|personnage] <name>
  - rp!character [create|new|creer|nouveau] <name> [user]
  - rp![characters|chars]
  - rp!allchars

Entering the `rp!character` command will give you details on that character. Characters can be created by anyone but you must have the Bot Mod role to create characters for other users. You may view all of your owned characters with the `rp!characters` command or all of the characters in the server with `rp!allchars`.

## Settings
  - rp![settings|s|configuration|conf]
  - rp!settings additem <name>
  - rp!settings [removeitem|deleteitem] <name>
  - rp!settings iteminfo <item>
  - rp!currency <currency>
  - rp!setstart <amount>
  - rp!deleteafter <time>
  - rp!hideinv <value>
  - rp!language [language]
  - rp!loaddnd
  - rp!loaddndmagic
  - rp!loaddndshop
  - rp!loadmagicshop
  - rp!loadpokemon
  - rp!loadstarwars
  - rp!loadstarwarsshop
  - rp!unload <name>
  - rp!loaditems
  
For players wishing to use the inventory system, there are a number of ways to get started. The most important command 
for adding items manually is rp!settings additem. This command is used to manually begin creating an item which may be given 
to players. Alternatively, all commands listed above beginning with "load" are commands whose function is to allow players 
to add a number of premade items from popular games such as D&D and Pokemon. If you wish to add your own commands en masse, 
you may also create a spreadsheet of all the items and export it to CSV, which the bot can read and load items from.

The rp!loaditems command requires a file (or several) to be attached, which it will then read and use to create the new
items. 


To retrieve a summary all of the settings, use the following command.
- rp![settings|s|configuration|conf] 
To begin adding items

## Guilds

## Teams

## Economy
  - rp![economy|eco|e|balance|bal] [user]
  - rp![bank|banc] deposit
  - rp![bank|banc] withdraw
  - rp!pay <amount> <user>
  - rp![salary|sal] <role>
  - rp!salary collect [role]
  - rp!salaries
  - rp!baltop

The full economy system of RPGBot is a pretty filling dish, but is easier to digest when split into smaller portions. Here we'll go over the basic eco funtions. Using the eco cmd will show the monetary balance you or anyone else currently has on hand as well as in the bank. The bank cmds will allow for deposits and withdrawls to and from your bank and cash-on-hand balances, respectively. To give another user money from your cash-on-hand, use the pay cmd. Users may collect salaries from those set to any roles they may have. Users may view specific role's salary  or the salaries for all roles. Also, baltop will list the top ten balances in the server.

### Lottery
  - rp![lottery|lotto]
  - rp!lottery [enter|join] <name>

Lotteries are created by a Bot Mod. The lottery cmd will list all of the currently running lottos. Users can enter any current lotto.

### Lootbox
  - rp![lootbox|lb] [name]
  - rp!lootbox buy <name>

Lootboxes are a luck-of-the-draw item that users may buy for a certain amount or item to receive an item from a set list at random. Users may view a lootbox specifically by name or all.
### Shop
  - rp!shop
  - rp!shop buy <item> <amount>
  - rp!shop sell <tiem> <amount>

The shop cmd will list all the items that have been added to the shop (refer to Moderation on page # for how-to on adding items). The shop pages will show the item name, buy price and sell price of each one. Users can buy or sell any of the items listed.

### Market
  - rp![market|m|pm]
  - rp!market search <item>
  - rp!market [buy|purchase|acheter] <ID>
  - rp!market [create|createlisting|listitem|list|new] <cost> <amount> <item>
  - rp!market [remove|rm] <id>
  - rp!startbid <item> <amount> <startingbid>
  - rp!bid

The market allows users to list and buy items from other users. Items are listed on the market from individual inventories. All listings may be viewed with the market cmd. To find an item ID, use search to show any and all listings of that item and the given IDs. Then use buy along with the ID of the listing you would like to buy. You can create your own listing of an item for others to buy off the market or remove any that you've previously listed. To put an item up for bid, use the startbid cmd to start a bid war. Others may bid on the item within the allotted time.

## Inventory

### Crafting

## Dungeon Dice

## Maps
![Map example](https://cdn.discordapp.com/attachments/350340609229193227/577218347415109692/mapexample.JPG "Example")

An example map file can be found [here](https://github.com/henry232323/RPGBot/blob/master/map.yml)


## User/Settings/Info
   - rp![s|settings] additem 
   
    Henry: rp!settings additem Example
    RPGBot: Describe the item (a description for the item)
    Henry: This is an example item
    RPGBot: Additional information? (Attributes formatted in a list i.e color: 400, value: 200 Set an image for this item with the image key i.e. image: http://image.com/image.png Set this item as usable by adding used key i.e. used: You open the jar and the bird flies away
    Henry: used: You used this item!, image: http://www.sourcecertain.com/img/Example.png
    RPGBot:  Item successfully created

## Moderation
