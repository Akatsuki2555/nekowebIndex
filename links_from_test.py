import json

if __name__ == '__main__':
    with open('index.json', 'r') as f:
        data = json.load(f)

    for i in data:
        for j in data:
            for k in j["links_to"]:
                if k == i["url"]:
                    i["links_from"].append(j["url"])

    with open('index_test.json', 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
