"""Apps Script 내보내기(export.json)를 sync.py가 읽는 폴더 구조로 푼다.

사용: python3 tools/unpack.py export.json export
export.json 모양: {"days": {"2026-11-04": {...}}, "plan": {"tasks": {...}}}
풀린 모양:       export/days/<날짜>.json, export/plan/<이름>.json
"""
import json
import os
import re
import sys

# 파일 이름으로 쓸 수 있는 모양만 받는다(내보내기 내용은 믿지 않는다).
NAMES = {"days": r"\d{4}-\d{2}-\d{2}", "plan": r"[a-z]{1,20}"}


def main(src, out):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not all(isinstance(data.get(k), dict) for k in NAMES):
        sys.exit("내보내기 모양이 올바르지 않습니다. 이미지를 만들지 않고 멈춥니다.")
    if not data["days"] and not data["plan"]:
        sys.exit("내보내기가 비어 있습니다. 빈 이미지를 올리지 않으려고 멈춥니다.")
    for sub, pattern in NAMES.items():
        os.makedirs(os.path.join(out, sub), exist_ok=True)
        for name, doc in data[sub].items():
            if re.fullmatch(pattern, name) and isinstance(doc, dict):
                with open(os.path.join(out, sub, name + ".json"), "w", encoding="utf-8") as f:
                    json.dump(doc, f, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
