from discord.ext import commands  # type: ignore
from discord.player import FFmpegPCMAudio  # type: ignore
from discord import VoiceChannel  # type: ignore


async def play_sound(voice_channel: VoiceChannel):
    client = await voice_channel.connect()
    audio = FFmpegPCMAudio(source="./initbot/sounds/battle-160.mp3")
    client.play(audio)


@commands.command(usage="[sound name]")
async def sound(ctx, sound_name: str):
    """Plays a sound."""
    if len(ctx.guild.voice_channels) > 0:
        await ctx.send(f":loudspeaker: Playing {sound_name}", delete_after=10)
        await play_sound(ctx.guild.voice_channels[0])


@sound.error
async def sound_error(ctx, error):
    await ctx.send(str(error), delete_after=5)


@commands.command()
async def shush(ctx):
    """Stops the current sound from playing."""
    for client in ctx.bot.voice_clients:
        if client.is_playing:
            client.stop()
            await client.disconnect()


@shush.error
async def shush_error(ctx, error):
    await ctx.send(str(error), delete_after=5)
