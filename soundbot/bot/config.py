from pydantic import BaseSettings


class Settings(BaseSettings):
    project_name: str = "soundboard"
    project_description: str = "A Discord bot which acts as a soundboard. Type commands in a text channel to enable soundbot to join a voice channel and play audio."
    project_license: str = """soundboard is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

initbot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with initbot. If not, see <https://www.gnu.org/licenses/>."""
    project_version: str = "0.1.0"
    bot_token: str


CONF = Settings(_env_file=".env", _env_file_encoding="utf-8")
