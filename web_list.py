# Akatsuki's Nekoweb indexer: Web list generator
# Copyright (C) 2024  Akatsuki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import urllib.parse

with open('new_index.json', 'r') as f:
    index = json.load(f)

if __name__ == "__main__":
    different_websites = []

    for i in index:
        parsed_url = urllib.parse.urlparse(i['url'])
        if parsed_url.netloc not in different_websites:
            different_websites.append(parsed_url.netloc)

    with open("web_list.json", "w") as f:
        json.dump(different_websites, f, indent=4, sort_keys=True)

