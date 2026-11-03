import json, datetime, sys
from PIL import Image, ImageDraw, ImageFont
F="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
B="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def font(p,s):
    for i in range(0,8):
        try:
            f=ImageFont.truetype(p,s,index=i)
            if "KR" in "".join(f.getname()): return f
        except Exception: pass
    return ImageFont.truetype(p,s)
d=json.load(open("data.json",encoding="utf-8"))
today=datetime.date.fromisoformat(d["updated"])
def dd(s): return (datetime.date.fromisoformat(s)-today).days
def make(W,H,out):
    im=Image.new("RGB",(W,H),(18,18,20)); g=ImageDraw.Draw(im)
    u=W/1080; X=int(80*u); R=W-X
    y=int(H*0.32)
    g.text((X,y),f"{d['exam']['name']}까지",font=font(F,int(40*u)),fill=(170,170,170)); y+=int(60*u)
    g.text((X,y),f"D-{dd(d['exam']['date'])}",font=font(B,int(190*u)),fill=(255,255,255)); y+=int(260*u)
    g.line((X,y,R,y),fill=(70,70,70),width=2); y+=int(40*u)
    for it in d["upcoming"][:4]:
        n=dd(it["d"]); g.text((X,y),f"D-{n}",font=font(B,int(40*u)),fill=(255,255,255))
        g.text((X+int(170*u),y),it["t"],font=font(F,int(40*u)),fill=(210,210,210)); y+=int(72*u)
    y+=int(20*u); g.line((X,y,R,y),fill=(70,70,70),width=2); y+=int(40*u)
    for p in d["progress"]:
        g.text((X,y),p["n"],font=font(F,int(36*u)),fill=(210,210,210))
        bx=X+int(150*u); bw=R-bx-int(110*u)
        g.rectangle((bx,y+int(16*u),bx+bw,y+int(34*u)),fill=(55,55,58))
        g.rectangle((bx,y+int(16*u),bx+int(bw*p["p"]/100),y+int(34*u)),fill=(240,240,240))
        g.text((R-int(90*u),y),f"{p['p']}%",font=font(F,int(36*u)),fill=(210,210,210)); y+=int(68*u)
    y+=int(20*u); g.line((X,y,R,y),fill=(70,70,70),width=2); y+=int(40*u)
    g.text((X,y),f"수면 {d['sleep']}   컨디션 {d['condition']}",font=font(F,int(36*u)),fill=(170,170,170))
    g.text((X,H-int(90*u)),f"업데이트 {d['updated']}"+("  (예시 데이터)" if d.get("example") else ""),font=font(F,int(28*u)),fill=(110,110,110))
    im.save(out)
make(1080,2340,"phone.png"); make(1200,1920,"tablet.png")
