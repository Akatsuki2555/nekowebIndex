import json

with open("new_index.json", "r") as f:
    data = json.load(f)

if __name__ == "__main__":
    print("Loaded " + str(len(data)) + " indexes")
    while True:
        search_this = input("> ")
        if search_this == "q":
            break

        search_this = search_this.lower()

        results = []
        for i in data:
            if i["body"] is None:
                continue
            count = i["body"].lower().count(search_this)
            if count > 0:
                results.append({"url": i["url"], "count": count})

        # Sort results based on count
        results = sorted(results, key=lambda x: x["count"], reverse=True)

        # Print sorted results
        for result in results:
            print("Found " + str(result["count"]) + " occurrences in " + result["url"])
