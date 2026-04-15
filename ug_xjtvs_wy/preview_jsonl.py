from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="output/ug_xjtvs_wy_corpus.jsonl")
    p.add_argument("--output", default="output/ug_xjtvs_wy_corpus.preview.txt")
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for i, line in enumerate(in_path.open("r", encoding="utf-8")):
        if i >= args.limit:
            break
        obj = json.loads(line)
        lines.append(f"[{i+1}] {obj.get('title','')}\nURL: {obj.get('normalized_url','')}\n{obj.get('cleaned_text','')[:280]}\n")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"preview written: {out_path}")


if __name__ == "__main__":
    main()
