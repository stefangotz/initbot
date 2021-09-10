"use strict";

// Copyright 2021 Stefan Götz <github.nooneelse@spamgourmet.com>

// This file is part of Initbot.

// Initbot is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of
// the License, or (at your option) any later version.

// Initbot is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU Affero General Public
// License along with Initbot. If not, see <https://www.gnu.org/licenses/>.

const Discord = require('discord.js');
const client = new Discord.Client();

const cfg = require('./initbot.json');

let chrs = {};

class Chr {
  constructor(user, name, init_mod = undefined) {
    if (typeof (user) !== "string" || user.length < 2) {
      throw `The user ${user} is unsupported`
    }
    this.user = user;
    if (typeof (name) !== "string" || name.length < 2) {
      throw `The name ${name} is unsupported`
    }
    this.name = name;
    this.init_mod = init_mod;
    this.init = -99;
    chrs[name.toLowerCase()] = this;
  }
  static all() {
    return Object.values(chrs);
  }
  static fromName(name) {
    return chrs[name.toLowerCase()];
  }
  static fromUserAll(user) {
    return Chr.all().filter(chr => {
      return chr.user == user;
    });
  }
  static fromUserOne(user) {
    const userChrs = Chr.fromUserAll(user);
    if (userChrs.length == 1) {
      return userChrs[0];
    }
    return undefined;
  }
  static fromUserOrName(user, name = undefined) {
    let chr;
    if (typeof (name) != "undefined") {
      chr = Chr.fromName(name);
    }
    if (typeof (chr) == "undefined") {
      chr = Chr.fromUserOne(user);
    }
    return chr;
  }
  static log() {
    console.log("Characters: " + JSON.stringify(chrs));
  }
  static nameExists(name) {
    return name.toLowerCase() in chrs;
  }
  static userExists(user) {
    return Chr.fromUserAll(user).length > 0;
  }
  static remove(name) {
    delete chrs[name.toLowerCase()];
  }
  static getNameOrUser(user) {
    const chr = Chr.fromUserOne(user);
    if (typeof (chr) === "undefined") {
      return user;
    } else {
      chr.name;
    }
  }
}

let handlers = {}

handlers["add"] = (msg, args) => {
  let init_mod;
  if (!isNaN(args.slice(-1)[0])) {
    init_mod = parseInt(args.pop());
  }
  if (args.length > 0) {
    const name = args.join(" ");
    if (name.length > 0) {
      const chr = new Chr(msg.author.username, name, init_mod);
      Chr.log();
      sendTmpMsg("Added " + chr.name, msg.channel);
      return;
    }
  }
  sendTmpMsg(`Usage: _${cfg.prefix}add <character name> [init bonus]_`, msg.channel);
}

handlers["init"] = (msg, args) => {
  Chr.log();
  console.log("Args: " + JSON.stringify(args));

  let name;
  if (args.length == 2) {
    name = args[0];
    args.shift();
  }
  let chr = Chr.fromUserOrName(msg.author.username, name);

  if (typeof (chr) != "undefined") {
    if (args.length == 1 && !isNaN(args[0])) {
      chr.init = parseInt(args[0]);
      Chr.log();
      sendTmpMsg(`Updated ${chr.name}'s initiative to ${chr.init}`, msg.channel);
    } else {
      sendTmpMsg(`Usage: _${cfg.prefix}init <initiative value>_`, msg.channel);
    }
  } else {
    sendTmpMsg(`Looks like you haven't added a character, ${msg.author.username}. Use the _${cfg.prefix}add_ command first.`, msg.channel);
  }
}

handlers["order"] = (msg) => {
  if (Chr.all().length < 1) {
    sendTmpMsg("¯\\_(ツ)_/¯", msg.channel);
    return;
  }

  let sortedChrs = Chr.all();
  sortedChrs.sort((a, b) => {
    let init_a = a.init;
    if (init_a === null) {
      init_a = -100;
    }
    let init_b = b.init;
    if (init_b === null) {
      init_b = -100;
    }
    let diff = init_b - init_a;
    if (diff == 0) {
      return Math.random() < 0.5 ? -1 : 1;
    }
    return diff;
  });
  console.log("Sorted: " + JSON.stringify(sortedChrs))

  let text = sortedChrs.map((value) => {
    return value.init + ': **' + value.name + '** (' + value.user + ')';
  }).join('\n');

  let embed = new Discord.RichEmbed();
  embed.addField('Initiative Order', text);
  msg.channel.send(embed);
}

handlers["remove"] = (msg, args) => {
  const chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    Chr.remove(chr.name);
    sendTmpMsg("Removed character " + chr.name, msg.channel);
  }
}

handlers["roll"] = (msg, args) => {
  const chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    if (typeof (chr.init_mod) != "undefined") {
      chr.init = roll(20) + chr.init_mod;
      sendTmpMsg(`${chr.name}'s new initiative is ${chr.init}`, msg.channel);
    } else {
      sendTmpMsg(`What is ${chr.name}'s initiative modifier? (Try the ${cfg.prefix}add command.)`, msg.channel)
    }
  }
}

handlers["show"] = (msg, args) => {
  const chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    msg.channel.send(JSON.stringify(chr, null, 2));
  }
}

handlers["set"] = (msg, args) => {
  const chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    console.log("args: " + args);
    for (const arg of args) {
      if (/^\w+=\w+$/.test(arg)) {
        const parts = arg.split("=");
        const key = parts[0];
        const val = tryParseInt(parts[1]);
        chr[key] = val;
      }
    }
    msg.channel.send(JSON.stringify(chr, null, 2));
  }
}

function getChr(msg, args) {
  for (let i = Math.min(4, args.length); i != 0; i -= 1) {
    const candidate = args.slice(0, i).join(" ");
    const chr = Chr.fromName(candidate);
    if (typeof (chr) != "undefined") {
      for (let j = 0; j < i; j += 1) {
        args.shift();
      }
      return chr;
    }
  }
  const chr = Chr.fromUserOne(msg.author.username);
  if (typeof (chr) != "undefined") {
    return chr;
  } else {
    if (Chr.fromUserAll(msg.author.username).length > 1) {
      sendTmpMsg(`You have multiple characters (${Chr.fromUserAll(msg.author.username).map(chr => chr.name)}) - please specify which one to remove`, msg.channel);
    } else {
      sendTmpMsg("You don't seem to be managing any characters right now", msg.channel);
    }
  }
  return undefined;
}

function tryParseInt(str) {
  if (isNaN(str)) {
    return str;
  } else {
    return parseInt(str);
  }
}

function deleteMsg(msg) {
  try {
    msg.delete();
  } catch (e) {
    console.log(e);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function sendTmpMsg(txt, channel) {
  channel.send(txt)
    .then((msg) => {
      deleteMsgAfter(msg, cfg.msgTimeout);
    });
}

async function deleteMsgAfter(msg, ms) {
  await sleep(ms);
  deleteMsg(msg);
}

client.on("ready", () => {
  console.log(`Client ready ${client.user.tag}`);
});

client.on("message", (msg) => {
  console.log("Msg: " + msg.content);
  if (msg.author.bot) return;

  if (!msg.content.startsWith(cfg.prefix)) {
    handleUnstructeredMsg(msg);
  } else {
    handleStructuredMsg(msg);
  }
});

function handleUnstructeredMsg(msg) {
  if (msg.content.length > 30) return;

  if (msg.content.toLowerCase() === "roll") {
    msg.content = cfg.prefix + "roll";
    handleStructuredMsg(msg);
    return;
  }
  if (msg.content.toLowerCase().startsWith("remove")) {
    msg.content = cfg.prefix + msg.content;
    handleStructuredMsg(msg);
    return;
  }
  if (msg.content.toLowerCase() === "inis") {
    msg.content = cfg.prefix + "order";
    handleStructuredMsg(msg);
    return;
  }

  if (/^d[0-9]{1,3}(\s*[+-]\s*[0-9]{1,2}|)$/i.test(msg.content)) {
    console.log("Looks like a dice roll: " + msg.content);
    const parts = msg.content.slice(1).split(/\s*[+-]\s*/);
    const die = parts[0];
    let mod = parts[1];
    if (msg.content.includes("-") && !isNaN(mod)) {
      mod = mod * -1;
    }
    const result = roll(die, mod);
    msg.channel.send(Chr.getNameOrUser(msg.author.username) + " rolled " + result, msg.channel);
    return;
  }

  let chr;
  if (/^(my|[a-z]+'s) [a-z]+ is ([0-9-]+|[a-z]+)$/i.test(msg.content)) {
    if (msg.content.toLowerCase().startsWith("my ")) {
      chr = Chr.fromUserOne(msg.author.username);
    } else {
      const name = msg.content.match(/^[a-z]+/i);
      chr = Chr.fromName(name);
    }
    if (typeof (chr) != "undefined") {
      const tokens = msg.content.slpit(" ");
      const prop = tokens[1];
      const value = tokens[3];
      msg.content = cfg.prefix + "set " + chr.name + " " + prop + "=" + value;
      handleStructuredMsg(msg);
      return;
    }
  }

  let txt = msg.content.replace(/:/g, "");
  let tokens = txt.split(/ +/);
  console.log("Msg tokens: " + JSON.stringify(tokens));

  let has_init_keyword = false;
  const init_key_words = ["ini", "init", "initiative"];
  tokens = tokens.filter(token => {
    let is_init_keyword = init_key_words.includes(token.toLowerCase());
    has_init_keyword = has_init_keyword || is_init_keyword;
    return !is_init_keyword;
  });
  console.log("Filtered msg tokens: " + JSON.stringify(tokens));
  console.log("Has init keyword: " + has_init_keyword);

  if (tokens.length == 0) return;
  if (isNaN(tokens[tokens.length - 1])) return;
  if (tokens.length > 4) return;
  if (!has_init_keyword) return;

  const init = parseInt(tokens.pop());
  const name = tokens.join(" ");
  console.log(`Name: ${name}, init: ${init}`);
  if (isNaN(init)) return;

  if (typeof (name) !== "undefined" && name.length > 1 && !Chr.nameExists(name) && has_init_keyword) {
    chr = new Chr(msg.author.username, name)
  }
  if (typeof (chr) === "undefined") {
    chr = Chr.fromUserOrName(msg.author.username, name)
  }
  if (typeof (chr) !== "undefined") {
    chr.init = init;
    sendTmpMsg(`Updated ${chr.name}'s initiative to ${chr.init}`, msg.channel);
  }
}

function handleStructuredMsg(msg) {
  let tokens = msg.content.split(/ +/);
  console.log("Msg tokens: " + JSON.stringify(tokens));
  if (tokens.length == 0) return;
  let cmd = tokens[0].substring(1, tokens[0].length).toLowerCase();
  console.log("Msg cmd: " + cmd);
  let args = tokens.slice(1)
  if (cmd in handlers) {
    try {
      handlers[cmd](msg, args);
    } catch (e) {
      console.log(e);
      msg.author.send(e);
    }
  }
}

function roll(die, mod) {
  console.log(`rolling d${die} mod ${mod}`);
  if (typeof (mod) == "undefined") {
    mod = 0;
  }
  return 1 + Math.floor(Math.random() * `${die}.0`) + mod;
}

client.login(cfg.token);
