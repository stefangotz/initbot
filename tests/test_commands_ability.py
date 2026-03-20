# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from discord import Embed

from initbot_chat.commands.ability import abl, abls, mod, mods


async def test_abls_sends_embed(mock_ctx):
    await abls.callback(mock_ctx)
    mock_ctx.send.assert_called_once()
    # abls sends with embed= keyword argument
    embed = mock_ctx.send.call_args.kwargs["embed"]
    assert isinstance(embed, Embed)
    assert embed.title == "Abilities"


async def test_abl_by_full_name(mock_ctx):
    await abl.callback(mock_ctx, "Luck")
    mock_ctx.send.assert_called_once()


async def test_abl_by_prefix(mock_ctx):
    await abl.callback(mock_ctx, "Str")
    mock_ctx.send.assert_called_once()


async def test_mods_sends_table(mock_ctx):
    await mods.callback(mock_ctx)
    mock_ctx.send.assert_called_once()


async def test_mod_by_score(mock_ctx):
    await mod.callback(mock_ctx, 10)
    mock_ctx.send.assert_called_once()
