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
SHORT = {}  # 과목 이름은 줄이지 않고 그대로 쓴다
SPLIT = ["등", "가슴", "하체"]  # 3분할 순서. 마지막으로 한 부위의 다음부터 채운다.
STUDY = ("학원", "자습", "인강")


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

    every = {}
    for path in glob.glob(os.path.join(folder, "days", "*.json")):
        d = load(path)
        if d.get("date"):
            every[d["date"]] = d

    def workouts(d):
        spans = [t for _, _, t, k in d.get("spans") or [] if t in SPLIT and not k.startswith("plan-")]
        return spans or [l.get("note") for l in d.get("logs", []) if l.get("note") in SPLIT]

    days = {}
    for d in every.values():
        if d["date"] not in week:
            continue
        if isinstance(d.get("spans"), list):
            days[d["date"]] = {
                "sleep": [[s, e] for s, e, _, k in d["spans"] if k == "sleep"],
                "blocks": [[s, e, k, t] for s, e, t, k in d["spans"] if k != "sleep" and not k.startswith("plan-")],
            }
        else:
            days[d["date"]] = {"sleep": [], "blocks": from_logs(d)}

    exams = sorted(items(folder, "exams"), key=lambda e: e["date"])
    upcoming = [e for e in exams if e["date"] >= today.isoformat()]
    wall = load(os.path.join(folder, "plan", "wall.json")) if os.path.exists(os.path.join(folder, "plan", "wall.json")) else {}

    table = items(folder, "timetable")
    weekly = [{"dow": t["day"], "s": t["start"], "e": t["end"], "t": SHORT.get(t["title"], t["title"]),
               "k": "study" if t.get("kind") in STUDY else "other"}
              for t in table if t.get("kind") not in ("학교", "운동")]
    # 평일에는 운동이 끝난 뒤부터 밤 12시까지는 공부 시간 (기록장 주간 시간표와 같음)
    for w in ["월", "화", "수", "목", "금"]:
        ends = [t["end"] for t in table if t.get("kind") == "운동" and t["day"] == w]
        if ends and max(ends) < "24:00":
            weekly.append({"dow": w, "s": max(ends), "e": "24:00", "t": "공부", "k": "study"})
    plan, notes, todos = [], {}, []

    # 운동 시간에는 3분할 순서대로 다음에 할 부위를 적는다.
    last = None
    for date in sorted(every):
        if date <= today.isoformat() and workouts(every[date]):
            last = workouts(every[date])[-1]
    nxt = (SPLIT.index(last) + 1) % 3 if last else None
    wd = ["월", "화", "수", "목", "금", "토", "일"]
    for i in range(7):
        d = monday + datetime.timedelta(days=i)
        if d < today or (d == today and workouts(every.get(d.isoformat(), {}))):
            continue
        for t in sorted((t for t in table if t.get("kind") == "운동" and t["day"] == wd[i]), key=lambda t: t["start"]):
            plan.append({"d": d.isoformat(), "s": t["start"], "e": t["end"], "k": "other",
                         "t": SPLIT[nxt] if nxt is not None else "운동"})
            if nxt is not None:
                nxt = (nxt + 1) % 3
    for t in items(folder, "tasks"):
        if t.get("start") and t.get("end"):
            plan.append({"d": t["date"], "s": t["start"], "e": t["end"], "k": "other", "t": t.get("short") or t["title"]})
        else:
            todos.append({"d": t.get("date") or "", "t": t.get("short") or t["title"]})
    # 기록장에서 "할 일로 칠하기"로 칠한 연한 칸
    for date in week & set(every):
        for s, e, t, k in every[date].get("spans") or []:
            if k.startswith("plan-"):
                plan.append({"d": date, "s": s, "e": e, "t": t, "k": "study" if k == "plan-study" else "other"})
    for e in exams:
        notes.setdefault(e["date"], []).append(SHORT.get(e["subject"], e["subject"]) + " 시험")

    data = {"exam": {"name": wall.get("name", "시험"), "date": upcoming[0]["date"]} if upcoming else None,
            "days": days, "weekly": weekly, "plan": plan, "notes": notes,
            "todos": sorted(todos, key=lambda x: x["d"] or "9999")}
    sfx = os.environ.get("WALL_SUFFIX", "")  # 시험 기간에는 data_new.json으로 따로 쓴다
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data{sfx}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
