import json
from urllib.parse import urlparse, urlunparse

if __name__ == '__main__':
    with open('index.json', 'r') as f:
        data = json.load(f)

    new_data = []
    for i in data:
        links_from = []
        for j in data:
            for k in j["links_to"]:
                link_to_parsed = urlparse(k)
                url_parsed = urlparse(i["url"])

                if link_to_parsed.netloc == url_parsed.netloc and link_to_parsed.path == url_parsed.path:
                    print("Adding link from: " + j["url"] + " to: " + i["url"])
                    links_from.append(j["url"])

        print("links_from", links_from, "for", i["url"])
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
                print("Removing duplicate link: " + j + " from: " + i["url"])

        url_parsed_to = []
        for j in i["links_to"]:
            j = j.rstrip('/')
            if j not in url_parsed_to:
                url_parsed_to.append(j)
            else:
                print("Removing duplicate link: " + j + " from: " + i["url"])

        i["links_from"] = url_list_from
        i["links_to"] = url_parsed_to
        new_data.append(i)

    data = new_data

    with open('index_test.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
