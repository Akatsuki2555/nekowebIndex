import asyncio
import json
import logging
from urllib.parse import urlparse
from robots_test import check_robots

logger = logging.getLogger("Akatsuki_Cleaner")
logger.setLevel(logging.DEBUG)
log_console = logging.StreamHandler()
log_file = logging.FileHandler("logs_cleaner.log", encoding='utf-8')
log_console.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
log_file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
log_console.setLevel(logging.INFO)
log_file.setLevel(logging.DEBUG)
logger.addHandler(log_console)
logger.addHandler(log_file)

disallowed_links = []
allowed_links = []

async def main():
    with open("index.json", "r") as data:
        data = json.load(data)

    index = 0
    new_data = []
    for i in data:
        index += 1
        logger.info("Processing link %d/%d" % (index, len(data)))
        parsed_url = urlparse(i.get("url", "https://nekoweb.org"))
        if parsed_url.netloc == "nekoweb.org" or parsed_url.netloc == "www.nekoweb.org":
            logger.info("Is Nekoweb homepage: %s", i.get("url", "https://nekoweb.org"))
            continue

        if i["url"] not in allowed_links and i["url"] not in disallowed_links:
            logger.debug("Checking %s for disallowed/allowed links...", i["url"])
            if await check_robots(i["url"]):
                logger.debug("URL %s is allowed", i["url"])
                allowed_links.append(i["url"])
            else:
                logger.info("URL %s is disallowed", i["url"])
                disallowed_links.append(i["url"])

        if i["url"] in disallowed_links:
            logger.debug("Skipping page %s", i["url"])
            continue

        logger.debug("Fixing links_to for %s", i["url"])
        links_to = []
        for j in i.get("links_to", []):
            if j not in links_to:
                j = j.removesuffix('/')
                parsed_to = urlparse(j)
                if parsed_to.netloc == "nekoweb.org" or parsed_to.netloc == "www.nekoweb.org":
                    continue
                logger.debug("Adding %s to links_to", j)
                links_to.append(j)
            else:
                logger.debug("Duplicate link %s, skipping", j)

        logger.debug("Fixing links_from for %s", i["url"])
        links_from = []
        for j in i.get("links_from", []):
            if j not in links_from:
                j = j.removesuffix('/')
                parsed_from = urlparse(j)
                if parsed_from.netloc == "nekoweb.org" or parsed_from.netloc == "www.nekoweb.org":
                    continue
                logger.debug("Adding %s to links_from", j)
                links_from.append(j)
            else:
                logger.debug("Duplicate link %s, skipping", j)

        logger.debug("Removing spaces in body")
        body = i.get("body", "")
        body = body.replace("\n", "")
        body = body.replace("\r", "")
        body = body.replace("\t", "")
        for j in range(100):
            body = body.replace("  ", " ")

        new_data.append({
            "title": i.get("title", ""),
            "body": body,
            "url": i.get("url", ""),
            "links_from": links_from,
            "links_to": links_to
        })

    print()
    print("Finished.")
    print("%d links were skipped." % len(disallowed_links))

    with open("new_index.json", "w") as outfile:
        json.dump(new_data, outfile)


if __name__ == "__main__":
    asyncio.run(main())
