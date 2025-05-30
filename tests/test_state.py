# Copyright 2025 Stefan Götz <github.nooneelse@spamgourmet.com>

# This file is part of initbot.

# initbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.

# initbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with initbot. If not, see <https://www.gnu.org/licenses/>.


from pathlib import Path
import unittest

from initbot.state.factory import create_state_from_source


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
        self.assertEqual(len(state.abilities.get_all()), 1)
        self.assertEqual(len(state.abilities.get_mods()), 1)
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
