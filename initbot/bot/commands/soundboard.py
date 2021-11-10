from discord.ext import commands  # type: ignore
from discord.player import FFmpegPCMAudio  # type: ignore


@commands.command()
async def sound(ctx):
    """Plays a sound."""
    if len(ctx.guild.voice_channels) > 0:
        voice_channel = ctx.guild.voice_channels[0]
        client = await voice_channel.connect()
        await ctx.send("Playing battle...", delete_after=10)
        audio = FFmpegPCMAudio(source="./initbot/sounds/battle-160.mp3")
        client.play(audio)


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
