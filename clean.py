import json
from urllib.parse import urlparse


def main():
    with open("index.json", "r") as data:
        data = json.load(data)

    index = 0
    new_data = []
    for i in data:
        index += 1
        print("Processing link %d/%d        " % (index, len(data)), end="\r")
        parsed_url = urlparse(i.get("url", "https://nekoweb.org"))
        if parsed_url.netloc == "nekoweb.org" or parsed_url.netloc == "www.nekoweb.org":
            continue

        links_to = []
        for j in i.get("links_to", []):
            if j not in links_to:
                j = j.rstrip('/')
                parsed_to = urlparse(j)
                if parsed_to.netloc == "nekoweb.org" or parsed_to.netloc == "www.nekoweb.org":
                    continue
                links_to.append(j)

        links_from = []
        for j in i.get("links_from", []):
            if j not in links_from:
                j = j.rstrip('/')
                parsed_from = urlparse(j)
                if parsed_from.netloc == "nekoweb.org" or parsed_from.netloc == "www.nekoweb.org":
                    continue
                links_from.append(j)

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

    with open("new_index.json", "w") as outfile:
        json.dump(new_data, outfile)


if __name__ == "__main__":
    main()
