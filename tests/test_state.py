# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from pathlib import Path
import unittest

from initbot_core.state.factory import create_state_from_source


class Test(unittest.TestCase):
    def test_load_json(self):
        state = create_state_from_source(f"json:{Path(__file__).parent / 'data'}")
        self._test_state(state)

    def test_load_sqlite(self):
        state = create_state_from_source(
            f"sqlite:{Path(__file__).parent / 'data' / 'test.sqlite'}"
        )
        self._test_state(state)

    def _test_state(self, state):
        self.assertIsNotNone(state)
        self.assertIsNotNone(state.abilities)
        self.assertEqual(len(state.abilities.get_all()), 6)
        self.assertEqual(len(state.abilities.get_mods()), 16)
        self.assertIsNotNone(state.augurs)
        self.assertEqual(len(state.augurs.get_all()), 1)
        self.assertIsNotNone(state.characters)
        self.assertEqual(len(state.characters.get_all()), 1)
        self.assertIsNotNone(state.classes)
        self.assertEqual(len(state.classes.get_all()), 1)
        self.assertIsNotNone(state.crits)
        self.assertEqual(len(state.crits.get_all()), 1)
        self.assertIsNotNone(state.occupations)
        self.assertEqual(len(state.occupations.get_all()), 1)
