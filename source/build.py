from argparse import ArgumentParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def load_records():
    db = json.loads((ROOT / "data/records.json").read_text(encoding="utf-8-sig"))
    records = db["records"]
    by_id = {record["id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate record ID")
    by_category = {category: [] for category in db["categories"]}
    by_tag = {}
    for record in records:
        by_category[record["category"]].append(record["id"])
        for tag in record["tags"]:
            by_tag.setdefault(tag, []).append(record["id"])
    return {**db, "index": {"byId": by_id, "byCategory": by_category, "byTag": by_tag}}

def main():
    parser = ArgumentParser()
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--id", action="append", default=[])
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--export", action="store_true", help="Export selected rows; no filters exports all")
    args = parser.parse_args()
    db = load_records()
    if args.export or args.category or args.tag or args.id:
        index = db["index"]
        ids = set(index["byId"])
        for keys, lookup in ((args.category, "byCategory"), (args.tag, "byTag"), (args.id, "byId")):
            if keys:
                unknown = set(keys) - set(index[lookup])
                if unknown:
                    parser.error("Unknown " + lookup + ": " + ", ".join(sorted(unknown)))
                matches = set(keys) if lookup == "byId" else {
                    row_id for key in keys for row_id in index[lookup][key]
                }
                ids &= matches
        rows = [row for row in db["records"] if row["id"] in ids]
        if args.format == "md":
            for row in rows:
                print("## " + row["title"] + "\n")
                for point in row["bullets"]:
                    print("- " + point)
                print()
        else:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    index_json = json.dumps(db["index"], ensure_ascii=False, indent=2)
    (ROOT / "data/index.json").write_text(index_json + "\n", encoding="utf-8")
    config = {key: db[key] for key in ("profile", "categories", "photos")}
    config["records"] = list(db["index"]["byId"].values())
    payload = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "src/template.html").read_text(encoding="utf-8")
    (ROOT / "index.html").write_text(template.replace("__PORTFOLIO_DATA__", payload), encoding="utf-8")

if __name__ == "__main__":
    main()
