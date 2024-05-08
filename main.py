import asyncio
import json
import os.path

from bs4 import BeautifulSoup
import requests
import logging
import aiohttp

from urllib.parse import urlparse, urlunparse

DEV_MODE = False  # Set this to false in production

os.unlink("logs.log")

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
    content = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc is not None:
        content += meta_desc.get("content")

    if soup.find("main") is not None:
        content += soup.find("main").text
    else:
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"]):
            content += tag.text + " "

    if content != "":
        return content
    else:
        logger.error("Page %s has no body text" % soup.title.string)
        return soup.find("body").text


not_nekoweb = []

if os.path.exists("not_nekoweb.json"):
    with open("not_nekoweb.json", "r") as f:
        not_nekoweb = json.load(f)


async def index_page(url: str):
    parsed_url = urlparse(url)
    if DEV_MODE:
        if parsed_url.netloc != "akatsuki.nekoweb.org" and parsed_url.netloc != "bee.nekoweb.org":
            logger.warning("Skipping %s as it's not on the Akatsuki domain" % url)
            return

    else:
        if parsed_url.netloc in not_nekoweb:
            logger.warning("Skipping %s as it's already confirmed to not be nekoweb" % url)
            return

    orig_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1)) as session:
            session.headers.add("User-Agent", "Akatsuki-Spider-Bot/1.0")
            logger.debug("Indexing %s" % url)
            async with session.get(url) as res:
                if not res.ok:
                    logger.warning("Skipping %s as it's a non OK response" % url)
                    return

                if "X-Powered-By" not in res.headers or res.headers["X-Powered-By"] != "Nekoweb":
                    logger.warning("Skipping %s as it's a Nekoweb site" % url)
                    not_nekoweb.append(parsed_url.netloc)
                    with open("not_nekoweb.json", "w") as f:
                        json.dump(not_nekoweb, f)
                    return

                text = await res.text()

            soup = BeautifulSoup(text, 'html.parser')

            logger.debug("Title of %s is %s" % (url, soup.title.string))
            logger.debug("Body of %s is %s" % (url, soup.find("body").text))

            links_to = []
            for link in soup.find_all('a'):

                link_url = link.get("href")
                if not is_link(link_url):
                    continue

                link_parsed = urlparse(get_full_link(url, link_url))
                if link_parsed.netloc == parsed_url.netloc:
                    continue  # Remove links to self

                logger.debug("Adding link from %s to %s" % (url, get_full_link(orig_url, link_url)))
                links_to.append(get_full_link(orig_url, link_url))

            data.extend([{
                "title": soup.title.string,
                "body": get_body_text(soup),
                "url": url,
                "links_to": links_to,
                "links_from": []  # Generate this later
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
                except Exception:
                    logger.error("An error occured while trying to index " + get_full_link(orig_url, link_url))
    except asyncio.TimeoutError:
        logger.error("Timeout while trying to fetch %s" % url)
        logger.warning('Treating %s as a non nekoweb site' % url)
        not_nekoweb.append(parsed_url.netloc)
        with open("not_nekoweb.json", "w") as f:
            json.dump(not_nekoweb, f)


async def main():
    to_search = [
        "https://nekoweb.org/",
    ]
    # await index_page("https://akatsuki.nekoweb.org/")
    for i in to_search:
        await index_page(i)

    logger.debug("Finished indexing, waiting 1 second before starting links_from generation")
    await asyncio.sleep(1)

    global data

    new_data = []
    for i in data:
        links_from = []
        for j in data:
            for k in j["links_to"]:
                link_to_parsed = urlparse(k)
                url_parsed = urlparse(i["url"])

                if link_to_parsed.netloc == url_parsed.netloc and link_to_parsed.path == url_parsed.path:
                    logger.debug("Adding link from: " + j["url"] + " to: " + i["url"])
                    links_from.append(j["url"])

        i["links_from"] = links_from
        new_data.append(i)

    data = new_data

    new_data = []
    for i in data:
        url_list_from = []
        for j in i["links_from"]:
            j = j.rstrip('/')
            if j not in url_list_from:
                url_list_from.append(j)
            else:
                logger.debug("Removing duplicate link: " + j + " from: " + i["url"])

        url_parsed_to = []
        for j in i["links_to"]:
            j = j.rstrip('/')
            if j not in url_parsed_to:
                url_parsed_to.append(j)
            else:
                logger.debug("Removing duplicate link: " + j + " from: " + i["url"])

        i["links_from"] = url_list_from
        i["links_to"] = url_parsed_to
        new_data.append(i)

    data = new_data

    with open("index.json", "w") as f:
        logger.debug("Saving index.json")
        json.dump(data, f, indent=2, sort_keys=True)


if __name__ == '__main__':
    logger.debug("Starting indexer")
    asyncio.run(main())
