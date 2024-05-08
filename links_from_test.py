import json

if __name__ == '__main__':
    with open('index.json', 'r') as f:
        data = json.load(f)

    # there's links_to, links_from, and url
    # links_to needs to be populated with links that are in the body of the page
    for i in data:
        for j in data:
            for k in j["links_to"]:
                links = []
                if k == i["url"]:
                    links.append(j["url"])

        i["links_to"] = links

    with open('index_test.json', 'w') as f:
        json.dump(data, f)
