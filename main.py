import asyncio
import json
import logging
import os.path
import sqlite3
from urllib.parse import urlparse, urlunparse

import aiohttp
from bs4 import BeautifulSoup

DEV_MODE = False  # Set this to false in production

os.unlink("logs.log")

logger = logging.getLogger("Akatsuki")
logger.setLevel(logging.DEBUG)
log_console = logging.StreamHandler()
log_file = logging.FileHandler("logs.log", encoding='utf-8')
log_console.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
log_file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log_console.setLevel(logging.INFO)
log_file.setLevel(logging.DEBUG)
logger.addHandler(log_console)
logger.addHandler(log_file)

db = sqlite3.connect("index.db")
cur = db.cursor()


def is_link(url: str) -> bool:
    if url is None:
        return False
    if url.startswith('mailto'):
        logger.debug("Skipping %s as it's a mail link" % url)
        return False
    if url.startswith("tel"):
        logger.debug("Skipping %s as it's a phone link" % url)
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


def db_init():
    cur.execute("CREATE TABLE IF NOT EXISTS `index`("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "url TEXT,"
                "title TEXT,"
                "body TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS `links_to`("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "indexId INTEGER,"
                "url TEXT,"
                "link TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS `links_from`("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "indexId INTEGER,"
                "url TEXT,"
                "link TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS `notNekoweb`("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "url TEXT);")

    logger.warning("Removing all data from the database")
    cur.execute("DELETE FROM `index`")
    cur.execute("DELETE FROM `links_from`")
    cur.execute("DELETE FROM `links_to`")
    db.commit()


def db_add_data(url: str, title: str, body: str, links_from: list[str], links_to: list[str]):
    cur.execute("insert into `index`(url, title, body) values(?, ?, ?)", (url, title, body))
    indexId = cur.lastrowid
    for i in links_from:
        cur.execute("insert into `links_from`(indexId, url, link) values(?, ?, ?)", (indexId, url, i))
    for i in links_to:
        cur.execute("insert into `links_to`(indexId, url, link) values(?, ?, ?)", (indexId, url, i))
    db.commit()


def db_add_to_not_nekoweb(url: str):
    cur.execute("insert into `notNekoweb`(url) values(?)", (url,))
    db.commit()


def db_is_nekoweb(url: str):
    if url == "nekoweb.org":
        return True
    
    cur.execute("select * from `notNekoweb` where url=?", (url,))
    return cur.fetchone() is None


async def index_page(url: str):
    parsed_url = urlparse(url)
    if DEV_MODE:
        if parsed_url.netloc != "akatsuki.nekoweb.org" and parsed_url.netloc != "bee.nekoweb.org":
            logger.warning("Skipping %s as it's not on the Akatsuki domain" % url)
            return

    else:
        print("db_is_nekoweb", parsed_url.netloc, db_is_nekoweb(parsed_url.netloc))
        if not db_is_nekoweb(parsed_url.netloc):
            logger.warning("Skipping %s as it's already confirmed to not be nekoweb" % url)
            return

    orig_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            session.headers.add("User-Agent", "AkatsukiNekowebBot/1.0")
            logger.debug("Indexing %s" % url)
            async with session.get(url) as res:
                if not res.ok:
                    logger.warning("Skipping %s as it's a non OK response" % url)
                    return

                if "X-Powered-By" not in res.headers or res.headers["X-Powered-By"] != "Nekoweb":
                    logger.warning("Skipping %s as it's a Nekoweb site" % url)
                    db_add_to_not_nekoweb(parsed_url.netloc)
                    return

                text = await res.text()

            soup = BeautifulSoup(text, 'html.parser')

            logger.info("Indexing page %s" % urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")))

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

            db_add_data(url, soup.title.string, get_body_text(soup), [], links_to)

            for link in soup.find_all('a'):
                link_url = link.get("href")
                logger.debug("Link with text %s has URL %s" % (link.text, link_url))
                if not is_link(link_url):
                    logger.debug("Link %s is not a link" % link_url)
                    continue

                cur.execute("select * from `index` where url=?", (get_full_link(orig_url, link_url),))
                if cur.fetchone() is not None:
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
        db_add_to_not_nekoweb(parsed_url.netloc)


async def main():
    db_init()

    to_search = [
        "https://nekoweb.org/",
    ]
    # await index_page("https://akatsuki.nekoweb.org/")
    for i in to_search:
        await index_page(i)

    logger.debug("Finished indexing, waiting 1 second before starting links_from generation")
    await asyncio.sleep(1)

    cur.execute("select * from `index`")
    for i in cur.fetchall():
        cur.execute("select * from links_to where link=?", (i[1],))
        for j in cur.fetchall():
            cur.execute("insert into links_from(indexId, url, link) values(?, ?, ?)", (i[0], i[1], j[2]))

    db.commit()

    with open("index.json", "w") as f:
        logger.debug("Saving index.json")
        temp_data = []
        cur.execute("select * from `index`")
        for i in cur.fetchall():
            links_from = []
            cur.execute("select * from links_from where url=?", (i[1],))
            for j in cur.fetchall():
                links_from.append(j[3])

            links_to = []
            cur.execute("select * from links_to where url=?", (i[1],))
            for j in cur.fetchall():
                links_to.append(j[3])

            temp_data.append({
                "title": i[2],
                "body": i[3],
                "url": i[1],
                "links_from": links_from,
                "links_to": links_to
            })

        json.dump(temp_data, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    logger.debug("Starting indexer")
    asyncio.run(main())
