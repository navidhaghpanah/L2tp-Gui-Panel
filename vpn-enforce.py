#!/usr/bin/env python3
# Enforce per-user data quota AND time expiry: disconnect & block violators.
import json, os, glob, time, signal, datetime

META="/var/lib/vpnstat/meta.json"; USAGE="/var/lib/vpnstat/usage.json"
ONLINE="/run/vpn-online"; BLOCK="/run/vpn-blocked"

def jload(p):
    try: return json.load(open(p))
    except Exception: return {}
def live(ifc):
    def rd(x):
        try: return int(open("/sys/class/net/%s/statistics/%s"%(ifc,x)).read())
        except Exception: return 0
    return rd("rx_bytes")+rd("tx_bytes")
def online_map():
    m={}
    for f in glob.glob(ONLINE+"/*"):
        ifc=os.path.basename(f)
        try:
            ls=open(f).read().splitlines(); u=ls[0].strip(); pid=int(ls[1].split()[1])
        except Exception: continue
        m[u]=(ifc,pid)
    return m

os.makedirs(BLOCK,exist_ok=True)
while True:
    meta=jload(META); usage=jload(USAGE); om=online_map()
    today=datetime.date.today()
    users=set(list(meta.keys())+list(usage.keys())+list(om.keys()))
    for u in users:
        info=meta.get(u,{}); quota=info.get("quota",0); expire=info.get("expire","")
        base=usage.get(u,{"rx":0,"tx":0}); total=base.get("rx",0)+base.get("tx",0)
        if u in om: total+=live(om[u][0])
        over_quota = bool(quota) and total>=quota
        expired=False
        if expire:
            try: expired=datetime.date.fromisoformat(expire)<today
            except Exception: expired=False
        violate=over_quota or expired
        blocked=os.path.exists(BLOCK+"/"+u)
        if violate:
            if u in om:
                try: os.kill(om[u][1],signal.SIGTERM)
                except Exception: pass
            if not blocked: open(BLOCK+"/"+u,"w").write(str(int(time.time())))
        else:
            if blocked:
                try: os.remove(BLOCK+"/"+u)
                except Exception: pass
    time.sleep(20)
