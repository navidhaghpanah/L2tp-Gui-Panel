#!/usr/bin/env python3
# L2TP VPN Panel - Farsi UI, login, per-user traffic quota + time limit
import json, os, glob, re, subprocess, urllib.parse, secrets, time, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==== CONFIG (install.sh replaces these) ====
ADMIN_USER = "__PANEL_USER__"
ADMIN_PASS = "__PANEL_PASS__"
# ============================================
STORE  = "/var/lib/vpnstat/usage.json"
META   = "/var/lib/vpnstat/meta.json"
ONLINE = "/run/vpn-online"
BLOCK  = "/run/vpn-blocked"
CHAP   = "/etc/ppp/chap-secrets"
GB = 1024**3
SESSIONS = {}

def jload(p):
    try: return json.load(open(p))
    except Exception: return {}
def jsave(p, d): json.dump(d, open(p, "w"))

def list_users():
    us = []
    try:
        for ln in open(CHAP):
            m = re.match(r'^"([^"]+)"\s+l2tpd\s+"([^"]*)"', ln.strip())
            if m: us.append((m.group(1), m.group(2)))
    except Exception: pass
    return us

def add_user(name, pw, quota_gb, days):
    name = re.sub(r'[^A-Za-z0-9_.-]', '', name or "")
    if not name or not pw: return
    lines = [l for l in open(CHAP).read().splitlines()
             if not re.match(r'^"%s"\s+l2tpd' % re.escape(name), l.strip())]
    lines.append('"%s" l2tpd "%s" *' % (name, pw))
    open(CHAP, "w").write("\n".join(lines) + "\n")
    meta = jload(META)
    try: q = int(float(quota_gb) * GB)
    except Exception: q = 20 * GB
    try: d = int(float(days))
    except Exception: d = 0
    expire = "" if d <= 0 else (datetime.date.today() + datetime.timedelta(days=d)).isoformat()
    meta[name] = {"quota": q, "created": time.strftime("%Y-%m-%d"), "expire": expire}
    jsave(META, meta)
    subprocess.call(["ipsec", "auto", "--rereadsecrets"])

def del_user(name):
    lines = [l for l in open(CHAP).read().splitlines()
             if not re.match(r'^"%s"\s+l2tpd' % re.escape(name), l.strip())]
    open(CHAP, "w").write("\n".join(lines) + "\n")
    for store in (STORE, META):
        d = jload(store)
        if name in d: del d[name]; jsave(store, d)
    try: os.remove(BLOCK + "/" + name)
    except Exception: pass
    subprocess.call(["ipsec", "auto", "--rereadsecrets"])

def reset_usage(name):
    d = jload(STORE)
    if name in d: del d[name]; jsave(STORE, d)
    try: os.remove(BLOCK + "/" + name)
    except Exception: pass

def renew(name, days):
    meta = jload(META)
    if name in meta:
        try: dd = int(float(days))
        except Exception: dd = 30
        base = datetime.date.today()
        cur = meta[name].get("expire", "")
        if cur:
            try:
                c = datetime.date.fromisoformat(cur)
                if c > base: base = c
            except Exception: pass
        meta[name]["expire"] = (base + datetime.timedelta(days=dd)).isoformat()
        jsave(META, meta)
    try: os.remove(BLOCK + "/" + name)
    except Exception: pass

def online_map():
    m = {}
    for f in glob.glob(ONLINE + "/*"):
        ifc = os.path.basename(f)
        try: u = open(f).read().splitlines()[0].strip()
        except Exception: u = ""
        if u: m[u] = ifc
    return m

def live(ifc):
    def rd(x):
        try: return int(open("/sys/class/net/%s/statistics/%s" % (ifc, x)).read())
        except Exception: return 0
    return rd("rx_bytes"), rd("tx_bytes")

def fmt(b):
    b = float(b)
    for u in ["B","KB","MB","GB","TB"]:
        if b < 1024: return "%.2f %s" % (b, u)
        b /= 1024
    return "%.2f PB" % b

def g2j(gy, gm, gd):
    gdm=[0,31,59,90,120,151,181,212,243,273,304,334]
    if gy>1600: jy=979; gy-=1600
    else: jy=0; gy-=621
    gy2=gy+1 if gm>2 else gy
    days=365*gy+(gy2+3)//4-(gy2+99)//100+(gy2+399)//400-80+gd+gdm[gm-1]
    jy+=33*(days//12053); days%=12053
    jy+=4*(days//1461); days%=1461
    if days>365: jy+=(days-1)//365; days=(days-1)%365
    if days<186: jm=1+days//31; jd=1+days%31
    else: jm=7+(days-186)//30; jd=1+(days-186)%30
    return jy,jm,jd
FA=["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسفند"]
def jstr(iso):
    try:
        y,m,d=[int(x) for x in iso.split("-")]; jy,jm,jd=g2j(y,m,d)
        return "%d %s %d"%(jd,FA[jm-1],jy)
    except Exception: return "-"
def tehran_now():
    t=time.gmtime(time.time()+int(3.5*3600)); jy,jm,jd=g2j(t.tm_year,t.tm_mon,t.tm_mday)
    return "%d %s %d - %02d:%02d"%(jd,FA[jm-1],jy,t.tm_hour,t.tm_min)

CSS = """
*{box-sizing:border-box}body{font-family:Vazirmatn,Tahoma,system-ui;margin:0;background:#0b1220;color:#e6edf7;direction:rtl}
.wrap{max-width:1180px;margin:0 auto;padding:24px}
.top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.brand{font-size:22px;font-weight:800}.brand span{color:#6366f1}
.clock{background:#111a2e;border:1px solid #223052;padding:8px 14px;border-radius:10px;font-size:13px;color:#9fb0cc}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.card{flex:1;min-width:150px;background:linear-gradient(135deg,#151f38,#111a2e);border:1px solid #223052;border-radius:14px;padding:14px 16px}
.card .k{color:#8ea1c0;font-size:12px}.card .v{font-size:20px;font-weight:700;margin-top:4px}
.panel{background:#111a2e;border:1px solid #223052;border-radius:14px;padding:16px;margin-bottom:18px}
.panel h3{margin:0 0 12px;font-size:15px;color:#c7d3e8}
form.add{display:flex;gap:10px;flex-wrap:wrap;align-items:end}
label{display:block;font-size:12px;color:#8ea1c0;margin-bottom:5px}
input{padding:9px 11px;border-radius:9px;border:1px solid #2a3a5e;background:#0b1220;color:#e6edf7;font-family:inherit;min-width:120px}
.btn{border:0;border-radius:9px;padding:10px 18px;cursor:pointer;font-family:inherit;font-weight:700;color:#fff}
.btn.g{background:#16a34a}.btn.r{background:#dc2626}.btn.b{background:#6366f1}.btn.y{background:#d97706}.btn.s{padding:5px 9px;font-size:12px;font-weight:600}
table{width:100%;border-collapse:collapse;background:#111a2e;border:1px solid #223052;border-radius:14px;overflow:hidden}
th,td{padding:10px 12px;text-align:right;border-bottom:1px solid #1c2a48;font-size:13px;white-space:nowrap}
th{background:#16223d;color:#9fb0cc;font-weight:700}
tr:hover td{background:#141f38}
.on{color:#22c55e;font-weight:700}.off{color:#64748b}
.bar{height:7px;background:#22304f;border-radius:6px;overflow:hidden;margin-top:5px;min-width:100px}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#eab308,#ef4444)}
.mono{font-family:ui-monospace,Menlo,monospace;direction:ltr;display:inline-block}
.acts{display:flex;gap:6px}.over{color:#ef4444;font-weight:700}
"""

LOGIN = """<!doctype html><html lang=fa dir=rtl><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>ورود به پنل</title>
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel=stylesheet>
<style>%s
.lg{min-height:100vh;display:flex;align-items:center;justify-content:center;background:radial-gradient(1200px 600px at 50%% -10%%,#1e2a4a,#0b1220)}
.box{width:340px;background:#111a2e;border:1px solid #223052;border-radius:18px;padding:28px;box-shadow:0 20px 60px rgba(0,0,0,.45)}
.box h1{font-size:20px;margin:0 0 4px;text-align:center}.box p{color:#8ea1c0;font-size:13px;text-align:center;margin:0 0 20px}
.box input{width:100%%;margin-bottom:14px}.box .btn{width:100%%}
.err{background:#3b1220;border:1px solid #7f1d1d;color:#fca5a5;padding:8px;border-radius:9px;font-size:13px;text-align:center;margin-bottom:14px}
.logo{width:54px;height:54px;margin:0 auto 12px;border-radius:14px;background:linear-gradient(135deg,#6366f1,#22c55e);display:flex;align-items:center;justify-content:center;font-size:26px}</style>
<div class=lg><form class=box method=post action=/login>
<div class=logo>🔒</div><h1>پنل مدیریت VPN</h1><p>L2TP / IPsec</p>
%s
<label>نام کاربری</label><input name=u autofocus required>
<label>رمز عبور</label><input name=p type=password required>
<button class="btn b">ورود</button></form></div></html>"""

def page(body):
    return ("<!doctype html><html lang=fa dir=rtl><meta charset=utf-8>"
        "<meta name=viewport content=\"width=device-width,initial-scale=1\"><title>پنل VPN</title>"
        "<link href=\"https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css\" rel=stylesheet>"
        "<style>"+CSS+"</style><div class=wrap>"+body+"</div>"
        "<script>setTimeout(function(){location.reload()},15000)</script></html>")

class H(BaseHTTPRequestHandler):
    def tok(self):
        m = re.search(r'sid=([A-Za-z0-9_-]+)', self.headers.get("Cookie",""))
        return m.group(1) if m else None
    def authed(self):
        t=self.tok(); return t and SESSIONS.get(t,0)>time.time()
    def rdir(self, loc, cookie=None):
        self.send_response(303); self.send_header("Location",loc)
        if cookie: self.send_header("Set-Cookie",cookie)
        self.end_headers()
    def out(self, s, code=200):
        b=s.encode("utf-8"); self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        ln=int(self.headers.get("Content-Length",0))
        q=urllib.parse.parse_qs(self.rfile.read(ln).decode()); g=lambda k:q.get(k,[""])[0]
        if self.path=="/login":
            if g("u")==ADMIN_USER and g("p")==ADMIN_PASS:
                tk=secrets.token_urlsafe(24); SESSIONS[tk]=time.time()+8*3600
                return self.rdir("/","sid=%s; HttpOnly; Path=/; Max-Age=28800; Secure; SameSite=Lax"%tk)
            return self.out(LOGIN%(CSS,"<div class=err>نام کاربری یا رمز اشتباه است</div>"),401)
        if not self.authed(): return self.rdir("/login")
        if self.path=="/add": add_user(g("u"),g("p"),g("q") or "20",g("d") or "0")
        elif self.path=="/del": del_user(g("u"))
        elif self.path=="/reset": reset_usage(g("u"))
        elif self.path=="/renew": renew(g("u"),g("d") or "30")
        return self.rdir("/")
    def do_GET(self):
        if self.path=="/login":
            if self.authed(): return self.rdir("/")
            return self.out(LOGIN%(CSS,""))
        if self.path=="/logout":
            t=self.tok()
            if t: SESSIONS.pop(t,None)
            return self.rdir("/login","sid=; Path=/; Max-Age=0")
        if not self.authed(): return self.rdir("/login")
        usage=jload(STORE); meta=jload(META); om=online_map()
        users=list_users(); pwmap=dict(users)
        names=sorted(set([u for u,_ in users]+list(meta.keys())),key=lambda x:(len(x),x))
        today=datetime.date.today()
        rows=""; tot_u=tot_d=0; n_on=0
        for i,u in enumerate(names,1):
            base=usage.get(u,{"rx":0,"tx":0}); up=base.get("rx",0); dn=base.get("tx",0)
            on=u in om
            if on:
                lu,ld=live(om[u]); up+=lu; dn+=ld; n_on+=1
            tot_u+=up; tot_d+=dn; total=up+dn
            info=meta.get(u,{}); quota=info.get("quota",0); expire=info.get("expire","")
            created=jstr(info.get("created",""))
            qgb=quota/GB if quota else 0
            pct=min(100,int(total*100/quota)) if quota else 0
            over_q=quota and total>=quota
            expired=False; exp_txt="نامحدود"
            if expire:
                try:
                    ed=datetime.date.fromisoformat(expire); rem_d=(ed-today).days
                    expired=rem_d<0
                    exp_txt=("<span class=over>منقضی</span>" if expired else "%s (%d روز)"%(jstr(expire),rem_d))
                except Exception: pass
            status="<span class=on>● آنلاین</span>" if on else "<span class=off>آفلاین</span>"
            usedcell=("<span class=over>%s</span>"%fmt(total)) if over_q else fmt(total)
            bar="<div class=bar><i style=width:%d%%></i></div>"%pct
            rem=max(quota-total,0)
            acts=("<div class=acts>"
                "<form method=post action=/renew><input type=hidden name=u value=\"%s\"><input type=hidden name=d value=30><button class=\"btn s y\">+۳۰ روز</button></form>"
                "<form method=post action=/reset onsubmit=\"return confirm('صفر کردن مصرف %s؟')\"><input type=hidden name=u value=\"%s\"><button class=\"btn s b\">صفر</button></form>"
                "<form method=post action=/del onsubmit=\"return confirm('حذف کاربر %s؟')\"><input type=hidden name=u value=\"%s\"><button class=\"btn s r\">حذف</button></form>"
                "</div>")%(u,u,u,u,u)
            rows+=("<tr><td>%d</td><td class=mono>%s</td><td class=mono>%s</td><td>%s</td><td>%s</td>"
                   "<td>%s</td><td>%s گیگ</td><td>%s%s</td><td>%s</td><td>%s</td></tr>")%(
                i,u,pwmap.get(u,""),status,created,exp_txt,
                (("%.0f"%qgb) if qgb==int(qgb) else ("%.1f"%qgb)),
                usedcell,bar,fmt(rem),acts)
        cards=("<div class=cards>"
            "<div class=card><div class=k>کل کاربران</div><div class=v>%d</div></div>"
            "<div class=card><div class=k>آنلاین</div><div class=v style=color:#22c55e>%d</div></div>"
            "<div class=card><div class=k>مجموع دانلود</div><div class=v>%s</div></div>"
            "<div class=card><div class=k>مجموع آپلود</div><div class=v>%s</div></div></div>")%(
            len(names),n_on,fmt(tot_d),fmt(tot_u))
        addf=("<div class=panel><h3>➕ افزودن کاربر جدید</h3><form class=add method=post action=/add>"
            "<div><label>نام کاربری</label><input name=u required></div>"
            "<div><label>رمز عبور</label><input name=p required></div>"
            "<div><label>سهمیه (گیگابایت)</label><input name=q type=number step=0.5 value=20 required></div>"
            "<div><label>مدت (روز) — ۰ = نامحدود</label><input name=d type=number value=30 required></div>"
            "<button class=\"btn g\">افزودن</button></form></div>")
        head=("<div class=top><div class=brand>پنل مدیریت <span>VPN</span></div>"
            "<div style=display:flex;gap:10px;align-items:center>"
            "<div class=clock>🗓 %s</div><a href=/logout class=\"btn r s\" style=text-decoration:none>خروج</a></div></div>")%tehran_now()
        table=("<table><tr><th>#</th><th>کاربر</th><th>رمز</th><th>وضعیت</th><th>تاریخ ساخت</th><th>انقضا</th>"
            "<th>سهمیه</th><th>مصرف‌شده</th><th>نمودار</th><th>باقی‌مانده</th><th>عملیات</th></tr>"+rows+"</table>")
        self.out(page(head+cards+addf+table))
    def log_message(self,*a): pass

if __name__=="__main__":
    HTTPServer(("127.0.0.1",8088),H).serve_forever()
