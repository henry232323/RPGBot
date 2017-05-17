#### Characters:
  - *allchars*   List all guild characters
  - *character*  Get info on a character - `rp![character|c|char] <name>`
    - *create*      Create a new character `rp!character [create|new] <name>`
  - *characters* List all your characters `rp![characters|chars]`
#### Economy:
  - *bid*        Place a bid on the current bidding item in the channel
  - *economy*    Check your or another users balance `rp![economy|bal|balance|eco|e] [member]
`
    - *givemoney*   Give the members money (Moderators) `rp!economy [givemoney|give] <amount> [members...]`
    - *setbalance*  Set the balance of the given members to an amount `rp!economy [setbalance|set] <amount> [members...]`
  - *lootbox*    List the current lootboxes `rp![lootbox|lb]`
    - *buy*         Buy a lootbox of the given name `rp!lootbox buy <name>`
    - *create*      Create a new lootbox, under the given `name` for the given cost. 
Use `{item}x{#}` notation to add items with {#} weight.
Weight being an integer. For example with
`bananax2 orangex3`: The outcome of the box will be
a random choice from [banana, banana, orange, orange, orange]
`rp!lootbox [create|new] <name> <cost> [items...]`
    - *delete*      Delete a lootbox with the given name `rp!lootbox [delete|remove] <name>`
  - *lotto*      List the currently running lottos. `rp![lotto|lottery]`
    - *enter*         Enter the lottery with the given name. `rp!lotto [enter|join] <name>`
    - *new*           Create a new lotto, with jacpot payout lasting time in seconds `rp!lotto [new|create] <name> <jackpot> <time>`
  - *market*     View the current market listings `rp![market|m|pm]`
    - *buy*           Buy a given amount of an item from the player market at the cheapest given price `rp!market [buy|purchase] <id>`
    - *create*        Create a new market listing `rp!market [create|createlisting|new|listitem|list] <cost> <amount> <item>`
  - *pay*        Pay another user money `rp!pay <amount> <member>`
  - *shop*       Get all items currently listed on the server shop
    - *additem*       Add an item to the server shop, to make an item unsaleable or unbuyable set their respective values to 0. Requires Bot Moderator or Admin `rp!shop additem <name>`
pb!additem Pokeball 0 10
Can be sold for 10 and cannot be bought. Must be an existing item! `rp!shop additem <name>`
    - *buy*           Buy an item from the shop `rp!shop buy <item> <amount>`
    - *removeitem*    Remove a listed item. Requires Bot Mod or Bot Admin `rp!shop removeitem <name>`
    - *sell*          Sell an item to the shop `rp!shop sell <item> <amount>`
  - *startbid*   Start a bid for an item `rp!startbid <item> <amount> <startbid>`
#### Groups:
  - *guild*      Get info on a member's guild. Subcommands for guild management
    - *create*         Create a new guild `rp!guild create <name>`
    - *delete*         Delete your guild
    - *deposit*        Deposit an amount of money into the guild bank `rp!guild deposit <amount>`
    - *deposititems*   Deposit items into the guild's storage, uses {item}x{#} notation (i.e. bananax3) `rp!guild deposititems [items...]`
    - *info*           Get info on a guild `rp!guild info <name>`
    - *invite*         Invite a user your closed guild `rp!guild invite <user>`
    - *join*           Join a guild (if you have an invite for closed guilds) `rp!guild join <name>`
    - *kick*           Kick a member from a guild `rp!guild kick <user>`
    - *leave*          Leave your guild
    - *setdescription* Set the guild's description `rp!guild [setdescription|setdesc] <description>`
    - *seticon*        Set the guild's icon `rp!guild seticon <url>`
    - *setimage*       Set the guild's image `rp!guild setimage <url>`
    - *setmod*         Give the listed users mod for your guild (guild owner only) `rp!guild setmod [members...]`
    - *toggleopen*     Toggle the Guilds open state
    - *withdraw*       Take money from the guild bank `rp!guild withdraw <amount>`
    - *withdrawitems*  Withdraw items from the guild (guild mods only, same syntax as deposit items) `rp!guild withdrawitems [items...]`
  - *guilds*     List guilds
#### Inventory:
  - *inventory*  Check your or another users inventory. `rp![inventory|i|inv] [member]`
    - *give*           Give items ({item}x{#}) to a member; ie: ;give @Henry#6174 pokeballx3 `rp!inventory give <other> [items...]`
    - *giveitem*       Give an item to a person (Not out of your inventory, must be Bot Moderator) `rp!inventory giveitem <item> <num> [members...]`
    - *takeitem*       Remove an item from a person's inventory (Must be Bot Moderator) `rp!inventory [takeitem|take] <item> <num> [members...]`
#### Misc:
  - *donate*     Donation information
  - *feedback*   Give me some feedback on the bot `rp!feedback <feedback>`
  - *info*       Bot Info
  - *ping*       Test the bot's connection ping
  - *rtd*        Roll a number of dice with given sides (ndx notation)
Example: rp!rtd 3d7 2d4
Optional Additions:
    Test for success by adding a >/<#

    Grab the top n rolls by adding ^n

    Add to the final roll by just adding a number (pos or neg)

    Examples of all:
    
        rp!rtd 8d8 -12 15 ^4 >32
        -> Roll failed (30 > 32) ([8 + 7 + 6 + 6] + -12 + 15) (Grabbed top 4 out of 8)
    `rp![rtd|rollthedice|dice] [dice...]`
  - *source*     Displays my full source code or for a specific command.
                   To display the source code of a subcommand you have to separate it by
                   periods, e.g. tag.create for the create subcommand of the tag command.
`rp!source [command]`
  - *totalcmds*  Get totals of commands and their number of uses
#### Pokemon:
  - *box*        Check the pokemon in your box `rp!box [member]`
  - *pokemon*    Subcommands for Pokemon management, see rp!help pokemon. Same use as rp!box `rp![pokemon|p] [member]`
    - *create*         Create a new Pokemon to add to your box `rp!pokemon [create|new]`
    - *info*           Get info on a Pokemon `rp!pokemon info <id>`
    - *trade*          Offer a trade to a user.
`your_id` is the ID of the Pokemon you want to give, `their_id` is the Pokemon you want from them.
`other` being the user you want to trade with `rp!pokemon trade <your_id> <their_id> <other>`
    - *release*        Release a Pokemon from your box `rp!pokemon [release|delete|rm|remove] <id>`
#### Settings:
  - *settings*   Get the current server settings `rp![settings|s|configuration|conf]`
    - *additem*        Add a custom item `rp!settings additem <name>`
    - *iteminfo*       Get info on a server item `rp!settings iteminfo <item>`
    - *items*          See all items for a guild
#### Team:
  - *team*       Check a character's team `rp!team <character>`
    - *add*            Add a Pokemon to a character's team `rp!team [add|addmember] <character> <id>`
    - *remove*         Remove a Pokemon from a character's team `rp!team [remove|removemember] <character> <id>`
#### User:
  - *userinfo*   Get info on a user `rp![userinfo|ui] [user]`
  - *experience* Get your or another user's level information. Help on this command for experience subcommands
EXP is calculated using a 0.1x^2+5x+4 where x is equal to the user's current level
Spamming commands or messages will not earn more exp! `rp![experience|exp] [member]`
    - *add*         Give the given members an amount of experience `rp!experience add <amount> [members...]`
    - *setlevel*    Set the given members level `rp!experience setlevel <level> [members...]`