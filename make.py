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
BLUE_FILL = (58, 92, 172)
RED = (186, 52, 44)
RED_FILL = (196, 70, 58)
SLEEP = (150, 144, 130)
TOP_EMPTY = 0.30      # 위쪽 시계 자리
BOTTOM_EMPTY = 0.075  # 아래쪽 잠금화면 단축 아이콘 자리
SS = 2                # 2배로 그린 뒤 줄여 선을 매끄럽게 한다

SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
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
    if size < 15 * u:
        return
    f = font(BOLD, int(size))
    if text_w(g, s, f) < box[2] - box[0] - 4 * u:
        g.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), s, font=f, fill=color, anchor="mm")


def hatch(g, box, color, step, width):
    """수면 칸의 빗금: 칸 안에 들어오는 45도 선만 그린다."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    for c in range(int(step), int(w + h), int(step)):
        ax, ay = (x0 + c, y0) if c <= w else (x1, y0 + c - w)
        bx, by = (x0, y0 + c) if c <= h else (x0 + c - h, y1)
        g.line((ax, ay, bx, by), fill=color, width=width)


def header(g, data, today, W, L, R, y, u):
    """머리말: 내 노트 표기 그대로 -N주 + 일 단위 분수."""
    exam = data.get("exam")
    if not exam:
        return y + 136 * u
    left = (datetime.date.fromisoformat(exam["date"]) - today).days
    weeks, rest = divmod(max(left, 0), 7)
    fs, fb, ff = font(SANS, int(36 * u)), font(SERIF, int(104 * u)), font(SERIF, int(34 * u))
    g.text((L, y + 42 * u), f"{exam['name']}까지", font=fs, fill=INK_SOFT)
    x = L + text_w(g, f"{exam['name']}까지", fs) + 22 * u
    g.text((x, y - 16 * u), f"-{weeks}", font=fb, fill=INK)
    x += text_w(g, f"-{weeks}", fb) + 14 * u
    g.text((x + 3 * u, y + 8 * u), str(rest), font=ff, fill=INK)
    g.line((x, y + 58 * u, x + 26 * u, y + 58 * u), fill=INK, width=max(2, int(3 * u)))
    g.text((x + 3 * u, y + 62 * u), "7", font=ff, fill=INK)
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
        name = WD[i]
        color = RED if i >= 5 else INK
        g.text((cx - text_w(g, name, f_head) / 2, y - 6 * u), name, font=f_head, fill=color)
        # 날짜는 노트의 분수처럼 월을 위, 일을 아래에 적는다.
        mo, da = str(d.month), str(d.day)
        g.text((cx - text_w(g, mo, f_date) / 2, y + 34 * u), mo, font=f_date, fill=INK_SOFT)
        g.line((cx - 20 * u, y + 69 * u, cx + 20 * u, y + 69 * u), fill=INK_SOFT, width=max(2, int(2 * u)))
        g.text((cx - text_w(g, da, f_date) / 2, y + 70 * u), da, font=f_date, fill=INK_SOFT)
        if d == today:
            r_x, r_y = col * 0.40, 62 * u
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
        if strong and h < 24:
            g.text((L, Y(h) - 2 * u), str(h), font=f_axis, fill=INK_SOFT)
    for i in range(8):
        g.line((X(i), top, X(i), bottom), fill=RULE_STRONG, width=max(1, int(2 * u)))

    # 기록과 일정
    pad = 4 * u
    week_study, sleep_hours, sleep_days = 0, 0, 0
    totals = []
    for i, d in enumerate(dates):
        rec = data["days"].get(d.isoformat(), {})
        spent = 0
        for s, e in rec.get("sleep", []):
            box = (X(i) + pad, Y(hours(s)), X(i + 1) - pad, Y(hours(e)))
            hatch(g, box, SLEEP, 15 * u, max(1, int(2 * u)))
            sleep_hours += hours(e) - hours(s)
        if rec.get("sleep"):
            sleep_days += 1
        for s, e, kind, name in rec.get("blocks", []):
            a, b = hours(s), hours(e)
            fill, ink = (BLUE_FILL, BLUE) if kind == "study" else (RED_FILL, RED)
            box = (X(i) + pad, Y(a), X(i + 1) - pad, Y(b))
            g.rectangle(box, fill=fill, outline=ink, width=max(1, int(2 * u)))
            box_text(g, box, name, PAPER, u)
            if kind == "study":
                spent += b - a
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
                box = (X(i) + pad, Y(a), X(i + 1) - pad, Y(b))
                g.rectangle(box, outline=RULE_STRONG, width=max(1, int(2 * u)))
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
