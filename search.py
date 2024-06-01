# Akatsuki's Nekoweb indexer: CLI search
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

with open("new_index.json", "r") as f:
    data = json.load(f)

def print_warranty():
    warranty_text = """
    THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR, OR CORRECTION.
    """
    print(warranty_text)

def print_conditions():
    conditions_text = """
    You are free to redistribute this software under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
    """
    print(conditions_text)

if __name__ == "__main__":
    print("Akatsuki's Nekoweb Search Copyright (C) 2024 Akatsuki2555")
    print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
    print("This is free software, and you are welcome to redistribute it")
    print("under certain conditions; type `show c' for details.")

    print("Loaded " + str(len(data)) + " indexes")
    while True:
        search_this = input("> ")
        if search_this == "show w":
            print_warranty()
        elif search_this == "show c":
            print_conditions()
        elif search_this == "q":
            break

        search_this = search_this.lower()

        results = []
        for i in data:
            if i["body"] is None:
                continue
            count = i["body"].lower().count(search_this)
            if count > 0:
                results.append({"url": i["url"], "count": count})

        # Sort results based on count
        results = sorted(results, key=lambda x: x["count"], reverse=True)

        # Print sorted results
        for result in results:
            print("Found " + str(result["count"]) + " occurrences in " + result["url"])
