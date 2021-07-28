"use strict";

// Copyright 2021 Stefan Götz <github.nooneelse@spamgourmet.com>

// This file is part of Initbot.

// Initbot is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Initbot is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with Initbot.  If not, see <https://www.gnu.org/licenses/>.

const Discord = require('discord.js');
const client = new Discord.Client();

const cfg = require('./initbot.json');

var chrs = {};

class Chr {
  constructor(user, name, init_mod = undefined) {
    this.user = user;
    this.name = name;
    this.init_mod = init_mod;
    this.init = null;
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
    let userChrs = Chr.fromUserAll(user);
    if (userChrs.length == 1) {
      return userChrs[0];
    }
    return undefined;
  }
  static fromUserOrName(user, name = undefined) {
    var chr;
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
}

var handlers = {}

handlers["add"] = (msg, args) => {
  var chr
  if (args.length == 2) {
    chr = new Chr(msg.author.username, args[0], parseInt(args[1]));
  } else if (args.length == 1) {
    chr = new Chr(msg.author.username, args[0]);
  } else {
    sendTmpMsg(`Usage: _${cfg.prefix}add <character name> [init bonus]_`, msg.channel);
    return;
  }
  Chr.log();
  sendTmpMsg("Added " + JSON.stringify(chr), msg.channel);
}

handlers["init"] = (msg, args) => {
  Chr.log();
  console.log("Args: " + JSON.stringify(args));

  if (args.length == 2) {
    var name = args[0];
    args.shift();
  }
  var chr = Chr.fromUserOrName(msg.author.username, name);

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

  var sortedChrs = Chr.all();
  sortedChrs.sort((a, b) => {
    var init_a = a.init;
    if (init_a === null) {
      init_a = -100;
    }
    var init_b = b.init;
    if (init_b === null) {
      init_b = -100;
    }
    var diff = init_b - init_a;
    if (diff == 0) {
      return Math.random() < 0.5 ? -1 : 1;
    }
    return diff;
  });
  console.log("Sorted: " + JSON.stringify(sortedChrs))

  var text = sortedChrs.map((value) => {
    return value.init + ': **' + value.name + '** (' + value.user + ')';
  }).join('\n');

  var embed = new Discord.RichEmbed();
  embed.addField('Initiative Order', text);
  msg.channel.send(embed);
}

handlers["remove"] = (msg, args) => {
  let chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    Chr.remove(chr.name);
    sendTmpMsg("Removed character " + chr.name, msg.channel);
  }
}

handlers["roll"] = (msg, args) => {
  let chr = getChr(msg, args);
  if (typeof (chr) != "undefined") {
    if (typeof (chr.init_mod) != "undefined") {
      chr.init = 1 + Math.floor(Math.random() * 20.0) + chr.init_mod;
      sendTmpMsg(`${chr.name}'s new initiative is ${chr.init}`, msg.channel);
    } else {
      sendTmpMsg(`What is ${chr.name}'s initiative modifier? (Try the ${cfg.prefix}add command.)`, msg.channel)
    }
  }
}

function getChr(msg, args) {
  var name
  if (args.length > 0) {
    name = args.join(" ");
  }
  let chr = Chr.fromUserOrName(msg.author.username, name);
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

  if (msg.content === "roll") {
    msg.content = cfg.prefix + "roll";
    handleStructuredMsg(msg);
    return;
  }
  if (msg.content.startsWith("remove")) {
    msg.content = cfg.prefix + msg.content;
    handleStructuredMsg(msg);
    return;
  }
  if (msg.content === "inis") {
    msg.content = cfg.prefix + "inis";
    handleStructuredMsg(msg);
    return;
  }

  var txt = msg.content.replace(/:/g, "");
  var tokens = txt.split(/ +/);
  console.log("Msg tokens: " + JSON.stringify(tokens));

  var has_init_keyword = false;
  let init_key_words = ["ini", "init", "initiative"];
  tokens = tokens.filter(token => {
    var is_init_keyword = init_key_words.includes(token.toLowerCase());
    has_init_keyword = has_init_keyword || is_init_keyword;
    return !is_init_keyword;
  });
  console.log("Filtered msg tokens: " + JSON.stringify(tokens));
  console.log("Has init keyword: " + has_init_keyword);

  if (isNaN(tokens[tokens.length - 1])) return;
  if (tokens.length > 4) return;

  let init = parseInt(tokens.pop());
  let name = tokens.join(" ");
  console.log(`Name: ${name}, init: ${init}`);

  if (typeof (name) !== "undefined" && !Chr.nameExists(name) && has_init_keyword) {
    var chr = new Chr(msg.author.username, name)
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
  var tokens = msg.content.split(/ +/);
  console.log("Msg tokens: " + JSON.stringify(tokens));
  if (tokens.length == 0) return;
  var cmd = tokens[0].substring(1, tokens[0].length);
  console.log("Msg cmd: " + cmd);
  var args = tokens.slice(1)
  if (cmd in handlers) {
    try {
      handlers[cmd](msg, args);
    } catch (e) {
      console.log(e);
      msg.author.send(e);
    }
  }
}

client.login(cfg.token);
