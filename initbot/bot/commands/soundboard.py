from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict
import json
from discord.embeds import Embed  # type: ignore
from discord.ext import commands  # type: ignore
from discord.ext.commands import Bot  # type: ignore
from discord.ext.commands.context import Context  # type: ignore
from discord.player import FFmpegPCMAudio  # type: ignore


@dataclass
class Sound:
    name: str
    description: str
    file: str
    category: str


sounds_file = Path(__file__).parents[2] / "sounds/sounds.json"
if sounds_file.exists():
    with open(sounds_file, encoding="utf8") as fd:
        SOUNDS: List[Sound] = [
            Sound(**a) for a in json.load(fd)["sounds"]
        ]  # type: ignore

SOUNDS_DICT: Dict[str, Sound] = {s.name: s for s in SOUNDS}


async def turn_off_soundboard(ctx: Context):
    for client in ctx.bot.voice_clients:
        if client.is_connected:
            await client.disconnect()


async def turn_on_soundboard(ctx: Context):
    if len(ctx.guild.voice_channels) > 0:
        await ctx.guild.voice_channels[0].connect()


async def play_sound(bot: Bot, sound_file: str):
    if len(bot.voice_clients) > 0:
        client = bot.voice_clients[0]

        if client.is_playing:
            client.stop()

        if (Path("./initbot/sounds") / sound_file).exists():
            audio = FFmpegPCMAudio(source="./initbot/sounds/" + sound_file)
            client.play(audio)
        else:
            raise ValueError(f"File '{sound_file}' not found")


def lookup_sound(sound_name: str):
    if sound_name in SOUNDS_DICT.keys():
        return SOUNDS_DICT[sound_name].file
    return ""


def format_sounds():
    formatted_list: str = "\n".join(f"` {s.name}  ` {s.description}" for s in SOUNDS)
    return formatted_list


@commands.command()
async def sounds(ctx):
    """Lists all the available sounds"""
    sound_md = format_sounds()
    sound_embed = Embed(title="Soundboard", description=sound_md)
    await ctx.send(embed=sound_embed)


@sounds.error
async def sounds_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


@commands.command(usage="[sound name]")
async def sound(ctx, sound_name: str):
    """Plays a sound."""
    selected_sound = lookup_sound(sound_name)
    if len(selected_sound) > 0:
        await ctx.send(f":loudspeaker: Playing {sound_name}", delete_after=10)
        await play_sound(ctx.bot, selected_sound)
    else:
        await ctx.send(f"I don't know {sound_name} :shrug:", delete_after=5)


@sound.error
async def sound_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


@commands.command()
async def shush(ctx):
    """Stops the current sound from playing."""
    for client in ctx.bot.voice_clients:
        if client.is_playing:
            client.stop()


@shush.error
async def shush_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


@commands.command(usage="status [on | off]")
async def soundboard(ctx: Context, status: str = ""):
    """Turn sound effects on or off. The bot will join the first voice channel it finds."""
    soundboard_status: bool = any(vc.is_connected for vc in ctx.bot.voice_clients)
    if status == "on" and not soundboard_status:
        soundboard_status = True
        await turn_on_soundboard(ctx)
    if status == "off" and soundboard_status:
        soundboard_status = False
        await turn_off_soundboard(ctx)

    stat: str = "on" if soundboard_status == 1 else "off"
    await ctx.send(f":play_pause: Soundboard is `{stat}`", delete_after=5)


@soundboard.error
async def soundboard_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
