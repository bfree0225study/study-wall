"""공부 기록장 저장소 내보내기(폴더)를 data.json으로 바꾼다.

사용: python3 sync.py <내보낸 폴더>
폴더 구조: <폴더>/days/<날짜>.json, <폴더>/plan/<이름>.json
"""
import datetime
import glob
import json
import os
import sys

KST = datetime.timezone(datetime.timedelta(hours=9))
SHORT = {"영어": "영", "수학": "수", "기하": "기", "화학": "화", "국어": "국"}


def load(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    # 내보내기 도구가 문서를 data로 감싸는 경우도 받는다.
    return doc["data"] if isinstance(doc.get("data"), dict) else doc


def items(folder, name):
    path = os.path.join(folder, "plan", name + ".json")
    return load(path).get("items", []) if os.path.exists(path) else []


def from_logs(day):
    blocks = []
    for log in day.get("logs", []):
        h, m = map(int, log["start"].split(":"))
        end = min(h * 60 + m + round(log["hours"] * 60), 24 * 60)
        study = log.get("kind") in ("학원", "자습", "인강")
        name = SHORT.get(log.get("subject"), log.get("subject")) if study else log.get("note")
        blocks.append([log["start"], f"{end // 60:02d}:{end % 60:02d}",
                       "study" if study else "other", name or log.get("kind", "")])
    return blocks


def main(folder):
    today = datetime.datetime.now(KST).date()
    monday = today - datetime.timedelta(days=today.weekday())
    week = {(monday + datetime.timedelta(days=i)).isoformat() for i in range(7)}

    days = {}
    for path in glob.glob(os.path.join(folder, "days", "*.json")):
        d = load(path)
        if d.get("date") not in week:
            continue
        if isinstance(d.get("spans"), list):
            days[d["date"]] = {
                "sleep": [[s, e] for s, e, _, k in d["spans"] if k == "sleep"],
                "blocks": [[s, e, k, t] for s, e, t, k in d["spans"] if k != "sleep"],
            }
        else:
            days[d["date"]] = {"sleep": [], "blocks": from_logs(d)}

    exams = sorted(items(folder, "exams"), key=lambda e: e["date"])
    upcoming = [e for e in exams if e["date"] >= today.isoformat()]
    wall = load(os.path.join(folder, "plan", "wall.json")) if os.path.exists(os.path.join(folder, "plan", "wall.json")) else {}

    weekly = [{"dow": t["day"], "s": t["start"], "e": t["end"], "t": SHORT.get(t["title"], t["title"])}
              for t in items(folder, "timetable") if t.get("kind") != "학교"]
    plan, notes = [], {}
    for t in items(folder, "tasks"):
        if t.get("start") and t.get("end"):
            plan.append({"d": t["date"], "s": t["start"], "e": t["end"], "t": t.get("short") or t["title"]})
        else:
            notes.setdefault(t["date"], []).append(t.get("short") or t["title"])
    for e in exams:
        notes.setdefault(e["date"], []).append(SHORT.get(e["subject"], e["subject"]) + " 시험")

    data = {"exam": {"name": wall.get("name", "시험"), "date": upcoming[0]["date"]} if upcoming else None,
            "days": days, "weekly": weekly, "plan": plan, "notes": notes}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
