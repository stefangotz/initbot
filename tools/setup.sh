#!/bin/sh

# Copyright 2021 Stefan Götz <github.nooneelse@spamgourmet.com>

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

set -ue

cd "$(dirname "$(realpath "${0}")")"/..

if ! curl -sSL https://install.python-poetry.org | python3 -; then
	curl -sSL https://install.python-poetry.org | py -
fi
poetry install
poetry run pre-commit install
