"""잠금화면 이미지 생성: 종이 노트(1주일=1페이지, 세로줄=하루, 0~24시)의 축소판.

data.json 구조
  exam    {"name", "date"}                       머리말의 -N주 계산용
  days    {"YYYY-MM-DD": {"sleep": [[시작, 끝]], "blocks": [[시작, 끝, 종류, 글자]]}}
          종류: study(파랑) / other(빨강). 자정을 넘는 수면은 날짜별로 나눠 적는다.
  weekly  [{"dow": "월", "s", "e", "t"}]         매주 반복 일정 (지나지 않은 날에 흐리게)
  plan    [{"d": "YYYY-MM-DD", "s", "e", "t"}]   특정 날짜 일정 (지나지 않은 날에 흐리게)
  notes   {"YYYY-MM-DD": ["글자"]}               시각 없는 일정 (날짜 아래 빨간 글자)
  exam가 null이면 머리말을 비운다(시험이 끝난 기간).
"""
import datetime
import json
import os

from PIL import Image, ImageDraw, ImageFont

# 디자인은 이 블록만 바꾸면 전체에 반영된다.
PAPER = (244, 239, 227)
RULE = (214, 207, 191)
RULE_STRONG = (176, 168, 150)
INK = (46, 43, 38)
INK_SOFT = (116, 110, 98)
BLUE = (38, 74, 158)
RED = (186, 52, 44)
# 칠하기는 선 없이 연한 색으로 칸 전체를 채운다.
BLUE_FILL = (198, 211, 238)    # 한 공부
RED_FILL = (241, 202, 194)     # 한 공부 외
SLEEP_FILL = (222, 215, 200)   # 수면
BLUE_PLAN = (228, 233, 244)    # 해야 할 공부 (더 흐리게)
RED_PLAN = (247, 227, 221)     # 해야 할 운동·일정
TOP_EMPTY = 0.30      # 위쪽 시계 자리
BOTTOM_EMPTY = 0.075  # 아래쪽 잠금화면 단축 아이콘 자리
BACKDROP = None       # 바탕 무늬를 그리는 함수(선택)
SS = 2                # 2배로 그린 뒤 줄여 선을 매끄럽게 한다

# 글꼴: 고운돋움 (저장소 fonts 폴더에 함께 둔다, SIL OFL)
GOWUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "GowunDodum-Regular.ttf")
SANS = BOLD = SERIF = GOWUN
WD = ["월", "화", "수", "목", "금", "토", "일"]
KST = datetime.timezone(datetime.timedelta(hours=9))


def font(path, size):
    for i in range(10):
        try:
            f = ImageFont.truetype(path, size, index=i)
        except OSError:
            break
        if "KR" in "".join(f.getname()):
            return f
    return ImageFont.truetype(path, size)


def hours(t):
    h, m = t.split(":")
    return int(h) + int(m) / 60


def label(n):
    return f"{n:.1f}".removesuffix(".0")


def text_w(g, s, f):
    return g.textlength(s, font=f)


def box_text(g, box, s, color, u):
    """칸 높이에 맞춰 글자 크기를 줄이고, 너무 작아지면 생략한다."""
    h = box[3] - box[1]
    size = min(26 * u, h * 0.8)
    # 칸 너비에 맞을 때까지 글자를 줄인다 (이름은 줄여 쓰지 않는다).
    while size >= 12 * u and text_w(g, s, font(BOLD, int(size))) >= box[2] - box[0] - 4 * u:
        size -= u
    if size < 12 * u:
        return
    f = font(BOLD, int(size))
    if True:
        g.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), s, font=f, fill=color, anchor="mm")


def header(g, data, today, W, L, R, y, u):
    """머리말: 남은 기간을 주 단위 대분수로 (-5 5/7 = 5주 5일)."""
    exam = data.get("exam")
    if not exam:
        return y + 136 * u
    left = (datetime.date.fromisoformat(exam["date"]) - today).days
    weeks, rest = divmod(max(left, 0), 7)
    fs, fb, ff = font(SANS, int(36 * u)), font(SERIF, int(104 * u)), font(SERIF, int(44 * u))
    base = y + 98 * u
    name = f"{exam['name']}까지"
    g.text((L, base), name, font=fs, fill=INK_SOFT, anchor="ls")
    x = L + text_w(g, name, fs) + 22 * u
    whole = f"-{weeks}" if weeks or not rest else "-"
    g.text((x, base), whole, font=fb, fill=INK, anchor="ls")
    top, bot = g.textbbox((x, base), whole, font=fb, anchor="ls")[1::2]
    mid = (top + bot) / 2
    if rest:
        # 분수는 정수 부분 글자의 가운데 높이에 맞춰 세운다.
        x += text_w(g, whole, fb) + 12 * u
        digit_h = g.textbbox((0, 0), "7", font=ff, anchor="ls")
        digit_h = digit_h[3] - digit_h[1]
        fw = max(text_w(g, str(rest), ff), text_w(g, "7", ff)) + 10 * u
        cx = x + fw / 2
        g.text((cx, mid - 9 * u), str(rest), font=ff, fill=INK, anchor="ms")
        g.line((x, mid, x + fw, mid), fill=INK, width=max(2, int(3 * u)))
        g.text((cx, mid + 9 * u + digit_h), "7", font=ff, fill=INK, anchor="ms")
    return y + 136 * u


def footer(g, week_study, sleep_avg, stamp, L, R, y, u):
    fs, fb, ft = font(SANS, int(32 * u)), font(BOLD, int(46 * u)), font(SANS, int(24 * u))
    g.line((L, y, R, y), fill=RULE_STRONG, width=max(2, int(2 * u)))
    y += 16 * u
    g.text((L, y + 10 * u), "주간", font=fs, fill=INK_SOFT)
    x = L + text_w(g, "주간", fs) + 14 * u
    g.text((x, y - 2 * u), f"{label(week_study)}시간", font=fb, fill=BLUE)
    x += text_w(g, f"{label(week_study)}시간", fb) + 44 * u
    g.text((x, y + 10 * u), "평균 수면", font=fs, fill=INK_SOFT)
    x += text_w(g, "평균 수면", fs) + 14 * u
    g.text((x, y - 2 * u), f"{label(sleep_avg)}시간" if sleep_avg else "–", font=fb, fill=INK)
    g.text((R - text_w(g, stamp, ft), y + 18 * u), stamp, font=ft, fill=INK_SOFT)


def draw(data, today, W, H, out):
    u = W / 1080
    im = Image.new("RGB", (W * SS, H * SS), PAPER)
    g = ImageDraw.Draw(im)
    u *= SS
    if BACKDROP:
        BACKDROP(g, W * SS, H * SS, u)
    W, H = W * SS, H * SS

    margin, axis = 46 * u, 50 * u
    L, R = margin, W - margin
    grid_l = L + axis
    col = (R - grid_l) / 7
    y = header(g, data, today, W, L, R, H * TOP_EMPTY, u)

    monday = today - datetime.timedelta(days=today.weekday())
    dates = [monday + datetime.timedelta(days=i) for i in range(7)]
    f_head, f_date = font(BOLD, int(32 * u)), font(SANS, int(23 * u))
    for i, d in enumerate(dates):
        cx = grid_l + col * (i + 0.5)
        name, md_ = WD[i], f" {d.month}/{d.day}"
        color = RED if i >= 5 else INK
        f_md = font(SANS, int(24 * u))
        tw = text_w(g, name, f_head) + text_w(g, md_, f_md)
        g.text((cx - tw / 2, y - 6 * u), name, font=f_head, fill=color)
        g.text((cx - tw / 2 + text_w(g, name, f_head), y + 2 * u), md_, font=f_md, fill=INK_SOFT)
        # 날짜 대신 그날 기준 시험까지 남은 기간을 대분수(-5 5/7)로 적는다.
        exam = data.get("exam")
        left = (datetime.date.fromisoformat(exam["date"]) - d).days if exam else -1
        if left >= 0:
            w, r = divmod(left, 7)
            whole = f"-{w}" if w or not r else "-"
            fw_ = font(SERIF, int(40 * u))
            ww = text_w(g, whole, fw_)
            frac_w = max(text_w(g, str(r), f_date), text_w(g, "7", f_date)) + 6 * u if r else 0
            x0 = cx - (ww + (6 * u + frac_w if r else 0)) / 2
            mid = y + 70 * u
            g.text((x0, mid), whole, font=fw_, fill=INK_SOFT, anchor="lm")
            if r:
                fx = x0 + ww + 6 * u
                g.text((fx + frac_w / 2, mid - 4 * u), str(r), font=f_date, fill=INK_SOFT, anchor="md")
                g.line((fx, mid, fx + frac_w, mid), fill=INK_SOFT, width=max(2, int(2 * u)))
                g.text((fx + frac_w / 2, mid + 2 * u), "7", font=f_date, fill=INK_SOFT, anchor="ma")
        else:
            md = f"{d.month}/{d.day}"
            g.text((cx - text_w(g, md, f_date) / 2, y + 56 * u), md, font=f_date, fill=INK_SOFT)
        if d == today:
            r_x, r_y = col * 0.49, 62 * u
            g.ellipse((cx - r_x, y + 50 * u - r_y, cx + r_x, y + 50 * u + r_y),
                      outline=RED, width=max(2, int(3 * u)))
    top = y + 118 * u

    foot_h = 96 * u
    total_h = 50 * u
    bottom = H * (1 - BOTTOM_EMPTY) - foot_h - total_h
    hour = (bottom - top) / 24
    Y = lambda h: top + hour * h
    X = lambda i: grid_l + col * i

    # 눈금: 1시간 얇게, 6시간 진하게
    f_axis = font(SANS, int(22 * u))
    for h in range(25):
        strong = h % 6 == 0
        g.line((grid_l, Y(h), R, Y(h)), fill=RULE_STRONG if strong else RULE,
               width=max(1, int((2 if strong else 1) * u)))
        if h % 3 == 0:
            # 시각 글자는 해당 줄 높이의 가운데에 맞춘다.
            g.text((grid_l - 10 * u, Y(h)), str(h), font=f_axis, fill=INK_SOFT, anchor="rm")
    for i in range(8):
        g.line((X(i), top, X(i), bottom), fill=RULE_STRONG, width=max(1, int(2 * u)))

    # 기록과 일정
    pad = 4 * u
    gap = 1.5 * u  # 이어진 칸 사이를 살짝 띄워 구분한다
    week_study, sleep_hours, sleep_days = 0, 0, 0
    totals = []
    for i, d in enumerate(dates):
        rec = data["days"].get(d.isoformat(), {})
        spent = 0
        for s, e in rec.get("sleep", []):
            box = (X(i) + pad, Y(hours(s)) + gap, X(i + 1) - pad, Y(hours(e)) - gap)
            g.rectangle(box, fill=SLEEP_FILL)
            sleep_hours += hours(e) - hours(s)
        if rec.get("sleep"):
            sleep_days += 1
        for s, e, kind, name in rec.get("blocks", []):
            a, b = hours(s), hours(e)
            fill, ink = (BLUE_FILL, BLUE) if kind == "study" else (RED_FILL, RED)
            box = (X(i) + pad, Y(a) + gap, X(i + 1) - pad, Y(b) - gap)
            g.rectangle(box, fill=fill)
            box_text(g, box, name, ink, u)
            if kind == "study":
                spent += b - a
        # 이어 붙은 칸 사이에 구분선을 긋는다.
        ends = {e for _, e in rec.get("sleep", [])} | {e for _, e, _, _ in rec.get("blocks", [])}
        for s, _, _, _ in rec.get("blocks", []):
            if s in ends:
                g.line((X(i) + pad, Y(hours(s)), X(i + 1) - pad, Y(hours(s))), fill=INK_SOFT, width=max(2, int(2 * u)))
        totals.append(spent if d <= today else None)
        week_study += spent if d <= today else 0

        # 지나지 않은 날(오늘 포함)의 남은 일정만 흐리게
        if d >= today:
            items = [p for p in data.get("weekly", []) if p["dow"] == WD[i]]
            items += [p for p in data.get("plan", []) if p["d"] == d.isoformat()]
            done = rec.get("blocks", [])
            for p in items:
                a, b = hours(p["s"]), hours(p["e"])
                # 이미 칠한 시간과 겹치면 기록을 우선한다.
                if any(a < hours(e) and hours(s) < b for s, e, _, _ in done):
                    continue
                box = (X(i) + pad, Y(a) + gap, X(i + 1) - pad, Y(b) - gap)
                g.rectangle(box, fill=BLUE_PLAN if p.get("k") == "study" else RED_PLAN)
                box_text(g, box, p["t"], INK_SOFT, u)

    # 각 날짜 아래 하루 공부 합계
    f_total = font(BOLD, int(32 * u))
    for i, t in enumerate(totals):
        d = dates[i]
        note = data.get("notes", {}).get(d.isoformat(), []) if d >= today else []
        if note:
            s = note[0] + (f"+{len(note) - 1}" if len(note) > 1 else "")
            size = 28
            while text_w(g, s, font(BOLD, int(size * u))) > col - 8 * u and size > 16:
                size -= 2
            f_note = font(BOLD, int(size * u))
            g.text((X(i) + (col - text_w(g, s, f_note)) / 2, bottom + 8 * u), s, font=f_note, fill=RED)
        elif t is not None:
            s = label(t)
            g.text((X(i) + (col - text_w(g, s, f_total)) / 2, bottom + 4 * u), s, font=f_total, fill=BLUE)

    stamp = f"{today.month}/{today.day} 갱신" + (" · 예시" if data.get("example") else "")
    footer(g, week_study, sleep_hours / sleep_days if sleep_days else None, stamp,
           L, R, bottom + total_h, u)
    im.resize((W // SS, H // SS), Image.LANCZOS).save(out, optimize=True)


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    today = datetime.datetime.now(KST).date()
    draw(data, today, 1080, 2340, os.path.join(base, "phone.png"))
    draw(data, today, 1200, 1920, os.path.join(base, "tablet.png"))
