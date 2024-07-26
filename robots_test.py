# Akatsuki's Nekoweb indexer: Robots file tester
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

import asyncio
import logging
from urllib import parse
import aiohttp
import requests

logger = logging.getLogger("Akatsuki_Robots")
logger.setLevel(logging.DEBUG)
log_console = logging.StreamHandler()
log_file = logging.FileHandler("logs_robots.log", encoding='utf-8')
log_console.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
log_file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log_console.setLevel(logging.INFO)
log_file.setLevel(logging.DEBUG)
logger.addHandler(log_console)
logger.addHandler(log_file)


class RobotsParser:
    def __init__(self, robots_url: str):
        self.rules = {}
        self.parse_file_or_url(robots_url)

    def parse_file_or_url(self, robots_url):
        """Parses the robots.txt file or fetches it from a URL and stores the rules."""
        try:
            response = requests.get(robots_url)
            if response.status_code == 200:
                content = response.text
            else:
                content = ""  # Treat as empty file

            current_useragent = None
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("User-agent:"):
                    current_useragent = line.split(":")[1].strip()
                    self.rules[current_useragent] = []
                elif current_useragent and line.startswith("Disallow:"):
                    disallow_path = line.split(":")[1].strip()
                    self.rules[current_useragent].append(disallow_path)
        except Exception as e:
            print(f"Error parsing robots.txt: {e}")

    def is_allowed(self, user_agent: str, check_url: str):
        """Checks if a given URL is allowed for the specified user agent."""
        if "*" in self.rules:
            for path in self.rules["*"]:
                if check_url.startswith(path):
                    return False
        if user_agent in self.rules:
            for path in self.rules[user_agent]:
                if check_url.startswith(path):
                    return False
        return True


async def check_if_exists(url):
    async with aiohttp.ClientSession() as session:
        session.headers.add("User-Agent", "AkatsukiNekowebBot")
        async with session.get(url) as res:
            return res.ok


async def check_if_robots_txt_exists(url):
    parsed_url = parse.urlparse(url)
    parsed_url = parse.urlunparse(("https", parsed_url.netloc, "robots.txt", "", "", ""))
    async with aiohttp.ClientSession() as session:
        session.headers.add("User-Agent", "AkatsukiNekowebBot")
        async with session.get(parsed_url) as res:
            return res.ok


async def check_robots(url):
    logger.debug("Checking %s", url)
    url_parsed = parse.urlparse(url)
    url_parsed_robots = parse.urlunparse(("https", url_parsed.netloc, "robots.txt", "", "", ""))
    if not await check_if_exists(url_parsed_robots):
        logger.debug("Page %s doesn't exist", url)
        return True
    if not await check_if_robots_txt_exists(url):
        logger.debug("Page %s doesn't have a robots.txt file", url)
        return True
    rp = RobotsParser(url_parsed_robots)
    logger.debug("Checking AkatsukiNekowebBot for robots.txt %s for path %s", url_parsed_robots, url_parsed.path)
    can = rp.is_allowed("AkatsukiNekowebBot", url_parsed.path)
    logger.debug("%s for %s", str(can), url)
    return can


async def main():
    url = input("Link to test: ")
    print(await check_robots(url))


if __name__ == '__main__':
    asyncio.run(main())
