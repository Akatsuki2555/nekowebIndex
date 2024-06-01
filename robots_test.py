import asyncio
import logging
from urllib import parse
import robots
import aiohttp

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
    rp = robots.RobotsParser.from_uri(url_parsed_robots)

    logger.debug("Checking AkatsukiNekowebBot for robots.txt %s for path %s", url_parsed_robots, url_parsed.path)
    can = rp.can_fetch("AkatsukiNekowebBot", url_parsed.path)
    logger.debug("%s for %s", str(can), url)
    return can


async def main():
    url = input("Link to test: ")
    print(await check_robots(url))


if __name__ == '__main__':
    asyncio.run(main())
