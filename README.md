# Initbot

Discord bot that manages RPG character initiatives

## Discord

The bot understands a few structured commands as well as a few unstructured messages.
These can be sent in any channel the bot user is a member of or as DMs.

### Structured Commands

- `$add name [initiativeModifier]`:
  Make a character with the given name known to the bot.
  Optionally, provide the character's initiative modifier.
  The bot keeps track of who sent this message and associates the sender with the character.
  Anyone can update that character, but when the sender has only this one character, they can omit the characetr name from most other commands.
  When this message is sent multiple times for the same character name, that character's sender and initiative modifier are updated.
- `$init [name] initiativeValue`:
  Set the current initiative value of a character.
  The optional name identifies the character to set the initiavite value for.
  If no name is given and the sender of the message has added only a single character so far, that character is updated.
- `$roll [name]`:
  Roll initiative for a character (D20 + initiative modifier).
  This only works if the initiative modifier has been set for this character via `$add`.
  The optional name identifies the character to roll for.
  If no name is given and the sender of the message has added only a single character so far, that character is updated.
- `$inis`:
  Make the bot send a message with all characters sorted by their initiative values.
  Ties are broken randomly.
- `$remove [name]`:
  Remove a character from the bot.
  The optional name identifies the character to remove.
  If no name is given and the sender of the message has added only a single character so far, that character is removed.

### Unstructured Messages

This basically means that the bot tries to interpret all messages it sees, so you don't need to use the strict `$` commands above.
The bot does however ignore any message longer than 30 characters because it's unlikely someone wants to have that elaborate a discussion with the bot.

- `ini Leeroy 28` sets _Leeroy_'s initiative to 28.
  If the bot didn't know the character _Leeroy_ before, well, it does now and associates it with the sender of the message.
- `ini Leeroy 5` sets _Leeroy_'s initiative (any user can do this, even users who haven't created _Leeroy_).
- `ini 5` or even just `5`: if the sender has added only one character so far, then that character's initiative is updated to the given value.
  `init`, `initiative`, `init:`, `ini:`, etc. work just as well.
- `inis`, `roll`, and `remove` work as above, just without the `$` prefix.
