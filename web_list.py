import json
import urllib.parse

with open('new_index.json', 'r') as f:
    index = json.load(f)

if __name__ == "__main__":
    different_websites = []

    for i in index:
        parsed_url = urllib.parse.urlparse(i['url'])
        if parsed_url.netloc not in different_websites:
            different_websites.append(parsed_url.netloc)

    with open("web_list.json", "w") as f:
        json.dump(different_websites, f, indent=4, sort_keys=True)

