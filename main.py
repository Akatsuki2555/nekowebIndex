import asyncio
import json
import os.path

from bs4 import BeautifulSoup
import requests
import logging
import aiohttp

from urllib.parse import urlparse, urlunparse

logger = logging.getLogger("Akatsuki")
logger.setLevel(logging.DEBUG)
log_console = logging.StreamHandler()
log_file = logging.FileHandler("logs.log")
log_console.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
log_file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log_console.setLevel(logging.INFO)
log_file.setLevel(logging.DEBUG)
logger.addHandler(log_console)
logger.addHandler(log_file)

if os.path.exists("index.json"):
    with open("index.json", "r") as f:
        logger.debug("Loaded existing index file index.json")
        data = json.load(f)
else:
    logger.warning("Creating new index.json file")
    data = []


def is_link(url: str) -> bool:
    if url is None:
        return False
    if url.startswith('mailto'):
        logger.info("Skipping %s as it's a mail link" % url)
        return False
    if url.startswith("tel"):
        logger.info("Skipping %s as it's a phone link" % url)
        return False

    return True


def get_full_link(base: str, url: str):
    if not is_link(url):
        logger.critical("The link %s is NOT a link but has been fed to the function" % url)
        raise ValueError("Invalid URL")

    base_parsed = urlparse(base)
    parsed = urlparse(url)
    if parsed.netloc == "":
        return urlunparse(("https", base_parsed.netloc, parsed.path, '', parsed.query, ''))

    return urlunparse(("https", parsed.netloc, parsed.path, '', parsed.query, ''))


async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()


def get_body_text(soup: BeautifulSoup):
    # try and find a meta description tag
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc is not None:
        return meta_desc.get("content")

    # fall back to main tag
    if soup.find("main") is not None:
        return soup.find("main").text

    # try and index h1, h2, h3, h4, h5, h6 and p
    body_text = ""
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"]):
        body_text += tag.text + " "

    if body_text != "":
        return body_text

    # fall back to body tag
    return soup.find("body").text


async def index_page(url: str):
    parsed_url = urlparse(url)
    if "nekoweb.org" not in parsed_url.netloc:
        logger.warning("Skipping %s as it's not a nekoweb org" % url)
        return

    orig_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    async with aiohttp.ClientSession() as session:
        logger.debug("Indexing %s" % url)
        async with session.get(url) as res:
            if res.status != 200:
                logger.warning("Skipping %s as it's a non-200 response" % url)
                return

            text = await res.text()

        soup = BeautifulSoup(text, 'html.parser')

        logger.debug("Title of %s is %s" % (url, soup.title.string))
        logger.debug("Body of %s is %s" % (url, soup.find("body").text))
        data.extend([{
            "title": soup.title.string,
            "body": get_body_text(soup),
            "url": url
        }])

        for link in soup.find_all('a'):
            link_url = link.get("href")
            logger.debug("Link with text %s has URL %s" % (link.text, link_url))
            if not is_link(link_url):
                logger.debug("Link %s is not a link" % link_url)
                continue

            if any(url2["url"] == get_full_link(orig_url, link_url) for url2 in data):
                logger.debug("Link %s already indexed" % link_url)
                continue

            try:
                logger.debug("Recursively indexing page %s " % get_full_link(orig_url, link_url))
                await index_page(get_full_link(orig_url, link_url))

                with open("index.json", "w") as f:
                    logger.debug("Saving index.json")
                    json.dump(data, f)
            except Exception:
                logger.error("An error occured while trying to index " + get_full_link(orig_url, link_url))


async def main():
    to_search = [
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=personal",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=art",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=blog",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=games",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=trans",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=cat",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=furry",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=gay",
        "https://nekoweb.org/explore?page=1&sort=lastupd&by=tag&q=cute"
    ]
    # await index_page("https://akatsuki.nekoweb.org/")
    for i in to_search:
        await index_page(i)


if __name__ == '__main__':
    logger.debug("Starting indexer")
    asyncio.run(main())
