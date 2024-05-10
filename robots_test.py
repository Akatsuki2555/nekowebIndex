import asyncio
from urllib import robotparser, parse

import aiohttp


async def check_if_exists(url):
    async with aiohttp.ClientSession() as session:
        session.headers.add("User-Agent", "AkatsukiNekowebBot")
        async with session.get(url) as res:
            return res.ok


async def check_robots(url):
    url_parsed = parse.urlunparse(("https", url, "robots.txt", "", "", ""))
    if not await check_if_exists(url_parsed):
        return False
    rp = robotparser.RobotFileParser()
    rp.set_url(url_parsed)
    rp.read()

    return rp.can_fetch("AkatsukiNekowebBot", url)


async def main():
    url = input("Link to test: ")
    print(await check_robots(url))


if __name__ == '__main__':
    asyncio.run(main())
