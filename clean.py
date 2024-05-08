import json


def main():
    with open("index.json", "r") as data:
        data = json.load(data)

    new_data = []
    for i in data:
        if i['url'].startswith("https://nekoweb.org"):
            continue
        links_to = []
        for j in i["links_to"]:
            if j not in links_to:
                links_to.append(j)

        new_data.append({
            "title": i["title"],
            "body": i["body"].replace("\n", ""),
            "url": i["url"],
            "links_from": i["links_from"],
            "links_to": links_to
        })

    with open("new_index.json", "w") as outfile:
        json.dump(new_data, outfile)


if __name__ == "__main__":
    main()
