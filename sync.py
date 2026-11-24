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


def slot_of(t):
    h, m = map(int, t.split(":"))
    return round(h * 4 + m / 15)


def cells_of(day):
    """하루를 15분 칸 96개로 편다 (기록장 칸과 같은 모양: '종류|이름')."""
    a = [""] * 96
    if isinstance(day.get("spans"), list):
        for s, e, t, k in day["spans"]:
            for i in range(slot_of(s), min(slot_of(e), 96)):
                a[i] = f"{k}|{t}"
    else:
        for s, e, k, t in from_logs(day):
            for i in range(slot_of(s), min(slot_of(e), 96)):
                a[i] = f"{k}|{t}"
    return a


def part_runs(a):
    """같은 운동 부위가 이어진 덩어리들 (한 것·할 일 상관없이 하나로 본다)."""
    out, cur = [], None
    for i, v in enumerate(a):
        k, _, t = v.partition("|")
        if k not in ("other", "plan-other") or t not in SPLIT:
            cur = None
            continue
        if cur and cur["t"] == t:
            cur["e"] = i + 1
            cur["done"] = cur["done"] or k == "other"
        else:
            cur = {"t": t, "s": i, "e": i + 1, "done": k == "other"}
            out.append(cur)
    return out


def main(folder):
    today = datetime.datetime.now(KST).date()
    monday = today - datetime.timedelta(days=today.weekday())
    week = {(monday + datetime.timedelta(days=i)).isoformat() for i in range(7)}

    every = {}
    for path in glob.glob(os.path.join(folder, "days", "*.json")):
        d = load(path)
        if d.get("date"):
            every[d["date"]] = d

    # 지난 주들의 공부 칸 ("여태 이맘때" 계산용)
    past = {d["date"]: [[s, e] for s, e, _, k in d["spans"] if k == "study"]
            for d in every.values() if d["date"] < monday.isoformat() and isinstance(d.get("spans"), list)}
    past = {k: v for k, v in past.items() if v}

    days = {}
    for d in every.values():
        if d["date"] not in week:
            continue
        if isinstance(d.get("spans"), list):
            days[d["date"]] = {
                "sleep": [[s, e] for s, e, _, k in d["spans"] if k == "sleep"],
                "blocks": [[s, e, k, t] for s, e, t, k in d["spans"] if k not in ("sleep", "skip") and not k.startswith("plan-")],
                "skips": [[s, e] for s, e, _, k in d["spans"] if k == "skip"],
            }
        else:
            days[d["date"]] = {"sleep": [], "blocks": from_logs(d)}

    exams = sorted(items(folder, "exams"), key=lambda e: e["date"])
    upcoming = [e for e in exams if e["date"] >= today.isoformat()]
    wall = load(os.path.join(folder, "plan", "wall.json")) if os.path.exists(os.path.join(folder, "plan", "wall.json")) else {}

    table = items(folder, "timetable")
    weekly = [{"dow": t["day"], "s": t["start"], "e": t["end"], "t": SHORT.get(t["title"], t["title"]),
               "k": "study" if t.get("kind") in STUDY else "school" if t.get("kind") == "학교" else "other"}
              for t in table if t.get("kind") != "운동"]
    # 평일에는 운동이 끝난 뒤부터 밤 12시까지는 공부 시간 (기록장 주간 시간표와 같음)
    for w in ["월", "화", "수", "목", "금"]:
        ends = [t["end"] for t in table if t.get("kind") == "운동" and t["day"] == w]
        if ends and max(ends) < "24:00":
            weekly.append({"dow": w, "s": max(ends), "e": "24:00", "t": "공부", "k": "study"})
    plan, notes, todos = [], {}, []

    # 운동 시간에는 3분할 순서대로 다음에 할 부위를 적는다. (기록장과 같은 규칙)
    # 마지막으로 한 부위의 다음부터 이어 세고, 동우님이 직접 칠한 운동 부위(한 것이든 할 일이든)가 있으면 그 칸을 기준으로 다시 이어서 센다.
    now = datetime.datetime.now(KST)
    now_slot = now.hour * 4 + now.minute // 15
    last = None
    for date in sorted(every):
        if date < today.isoformat():
            done = [r["t"] for r in part_runs(cells_of(every[date])) if r["done"]]
            if done:
                last = done[-1]
    nxt = (SPLIT.index(last) + 1) % 3 if last else None
    wd = ["월", "화", "수", "목", "금", "토", "일"]
    for i in range(7):
        d = monday + datetime.timedelta(days=i)
        if d < today:
            continue
        a = cells_of(every.get(d.isoformat(), {}))
        runs = part_runs(a)
        has_done = any(r["done"] for r in runs)
        ev = [(r["s"], 0, r["t"], None) for r in runs if r["done"] or d > today or r["e"] > now_slot]
        for t in sorted((t for t in table if t.get("kind") == "운동" and t["day"] == wd[i]), key=lambda t: t["start"]):
            s_, e_ = slot_of(t["start"]), min(slot_of(t["end"]), 96)
            if d == today and (e_ <= now_slot or has_done):
                continue  # 이미 끝났거나 오늘 운동을 이미 했으면 세지 않고 그리지도 않는다
            if any(r["s"] < e_ and s_ < r["e"] for r in runs):
                continue  # 직접 칠한 운동이 이 시간을 대신한다
            if all(a[s_:e_]):
                continue  # 칸이 다 지워지거나 다른 것으로 바뀌었다
            ev.append((s_, 1, None, t))
        for _, _, part, t in sorted(ev, key=lambda x: (x[0], x[1])):
            if part:
                nxt = (SPLIT.index(part) + 1) % 3
                continue
            plan.append({"d": d.isoformat(), "s": t["start"], "e": t["end"], "k": "other",
                         "t": SPLIT[nxt] if nxt is not None else "운동"})
            if nxt is not None:
                nxt = (nxt + 1) % 3
    for t in items(folder, "tasks"):
        if t.get("start") and t.get("end"):
            plan.append({"d": t["date"], "s": t["start"], "e": t["end"], "k": "other", "t": t.get("short") or t["title"]})
        elif t.get("repeat"):
            # 반복 할 일: 시작 날짜부터, 매일은 다음 날, 매주는 7일 뒤에 다시 나타난다 (기록장과 같은 규칙)
            if t.get("date") and t["date"] > today.isoformat():
                continue
            done = t.get("done")
            if done:
                gap = (today - datetime.date.fromisoformat(done)).days
                if t["repeat"] == "weekly" and t.get("dow") is not None:
                    # 지정 요일(일요일=0): 가장 가까운 그 요일(오늘 포함) 이후에 했으면 숨긴다
                    back = ((today.weekday() + 1) % 7 - t["dow"]) % 7
                    if done >= (today - datetime.timedelta(days=back)).isoformat():
                        continue
                elif gap < (7 if t["repeat"] == "weekly" else 1):
                    continue
            todos.append({"d": "", "t": t.get("short") or t["title"]})
        elif not t.get("date") or t["date"] == today.isoformat():  # 날짜를 정한 할 일은 그날에만
            todos.append({"d": t.get("date") or "", "t": t.get("short") or t["title"]})
    # 기록장에서 "할 일로 칠하기"로 칠한 연한 칸
    for date in week & set(every):
        for s, e, t, k in every[date].get("spans") or []:
            if k.startswith("plan-"):
                plan.append({"d": date, "s": s, "e": e, "t": t, "k": "study" if k == "plan-study" else "other"})
    for e in exams:
        notes.setdefault(e["date"], []).append(SHORT.get(e["subject"], e["subject"]) + " 시험")

    data = {"exam": {"name": wall.get("name", "시험"), "date": upcoming[0]["date"]} if upcoming else None,
            "days": days, "past": past, "weekly": weekly, "plan": plan, "notes": notes,
            "todos": todos}  # 기록장에서 정한 순서(우선순위) 그대로
    sfx = os.environ.get("WALL_SUFFIX", "")  # 시험 기간에는 data_new.json으로 따로 쓴다
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data{sfx}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
