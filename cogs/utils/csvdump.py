import json
import csv
items = {}

with open('../../resources/starwars.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
        else:
            items[row["Item"]] = dict(
                name=row["Item"],
                description=row["Description, Special"],
                meta=dict(
                    Book=row["Book"],
                    Rarity=row["Rarity"],
                    Enc=row["Enc"],
                    Cost=row["Price"]
                )
            )
            for k, v in list(items[row["Item"]]["meta"].items()):
                if not v:
                    del items[row["Item"]]["meta"][k]
        line_count += 1

with open('../../resources/starwars.json', 'w') as jf:
    json.dump(items, jf, indent=4)
