from sys import argv
from typing import List, Dict
import json
import re
import requests


def download_mp3(mp3_url: str, path: str):
    print(f"Downloading {mp3_url}")
    filename = mp3_url.split("/")[-1]
    with requests.get(mp3_url, stream=True) as resp:
        with open(f"{path}/{filename}", "wb") as mp3:
            for chunk in resp.iter_content(chunk_size=8192):
                mp3.write(chunk)
    return filename


def process_match(this_match: re.Match, path: str):
    mp3 = this_match.group(2)
    mp3_file_name = download_mp3(mp3, path)
    sound_name = this_match.group(1)

    sound_obj = {
        "name": sound_name,
        "file": mp3_file_name,
        "description": "",
        "category": "",
    }

    return sound_obj


script_args = argv[1:]
ARG_COUNT = len(script_args)
ACCEPTED_ARGS = ["-url", "-datafolder"]
key_vals = {}

for i in range(ARG_COUNT):
    cur_arg = script_args[i]
    if cur_arg in ACCEPTED_ARGS:
        key = cur_arg.lstrip("-")
        value = script_args[i + 1]
        key_vals[key] = value

print(f"Checking url {key_vals['url']}")

response = requests.get(key_vals["url"])

media_pattern = re.compile(r'setMedia", \{\s*title\:\s*"([^"]+)",\s*mp3\:\s*"([^"]+)')
matches = media_pattern.finditer(response.text)

data = {"sounds": []}  # type: Dict[str, List]
for match in matches:
    data["sounds"].append(process_match(match, key_vals["datafolder"]))

with open(key_vals["datafolder"] + "sounds.json", "w", encoding="utf8") as fd:
    json.dump(data, fd, indent="    ")
