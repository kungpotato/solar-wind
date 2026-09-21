#!/usr/bin/env python3
"""Solar Wind — financial projection model.

Edit the ASSUMPTIONS below (or the scenario overrides at the bottom of the model section),
then run:  python3 docs/financial-model.py   → regenerates docs/03-financial-projection.html
All figures are assumptions for cash planning, not forecasts.
"""
# ===================== ASSUMPTIONS =====================
import json
WEEKS=4.33; DCA=50.0; APY=0.05
BASE_USERS=[0,30,100,200,300,450,650,900,1300,1800,2400,3300,4500,6000,7800,10000,12500,15000,18000,21000,24000,27000,30000,33000]
def stage(m,users):
    if m<=1: return 'Stage 0 · Build'
    if m<=5: return 'Stage 0 · Beta'
    if m<=12: return 'Lean Phase-1'
    return 'GA'
def run(name, users_mult=1.0, fee_bps=25, perf=0.0, aum_fee_bps_yr=0, pro_conv=0.0, pro_price=0.0, churn=0.03, grant=0.0, grant_month=5, gas_single=0.03, gas_batch=0.012, audit1=12000, audit2=30000, legal=2000):
    rows=[]; aum=0; cum=0; minc=0; be=None; a1=co=a2=False
    for i in range(24):
        m=i+1; u=round(BASE_USERS[i]*users_mult); st=stage(m,u)
        contrib=u*DCA*WEEKS
        aum=aum*(1-churn)+contrib
        vol_fee=contrib*fee_bps/10000
        perf_fee=(aum*APY/12*perf if m>=6 else 0) + (aum*aum_fee_bps_yr/10000/12 if m>=13 else 0)
        pro=u*pro_conv*pro_price if m>=4 else 0
        g=grant if m==grant_month else 0
        rev=vol_fee+perf_fee+pro
        gas_pc=gas_single if st.startswith('Stage 0') else gas_batch
        gas=u*WEEKS*gas_pc
        if st.startswith('Stage 0'): infra=5 if m>=3 else 0
        elif st=='Lean Phase-1': infra=600+(400 if u>5000 else 0)
        else: infra=1000+(400 if u>5000 else 0)+(500 if u>20000 else 0)
        rpc=0 if u<10000 else (200 if u<30000 else 500)
        llm=0  # BYO-LLM: platform pays no tokens
        tools=2 if m>=1 else 0
        email=0 if u<5000 else 20
        bounty=300 if st=='GA' else 0
        marketing=0 if st!='GA' else 200
        oneoff=0; notes=[]
        if m==2: oneoff+=legal; notes.append(f'legal consult ${legal/1000:g}k')
        if not a1 and aum>=100000: oneoff+=audit1; a1=True; notes.append(f'audit contest ${audit1/1000:g}k (TVL ≥ $100k)')
        if not co and rev>=1000: oneoff+=1000; co=True; notes.append('จดบริษัท $1k (รายได้ ≥ $1k/mo)')
        if not a2 and m>=12 and aum>=1000000: oneoff+=audit2; a2=True; notes.append(f'audit round 2 ${audit2/1000:g}k (TVL ≥ $1M)')
        if g: notes.append(f'grant +${g/1000:g}k')
        opex=gas+infra+rpc+llm+tools+email+bounty+marketing
        net=rev+g-opex-oneoff
        cum+=net; minc=min(minc,cum)
        if be is None and rev-opex>0 and m>=3: be=m
        rows.append(dict(m=m,stage=st,users=u,aum=aum,vol=vol_fee,perf=perf_fee,pro=pro,grant=g,rev=rev,gas=gas,infra=infra,rpc=rpc,llm=llm,other=tools+email+bounty+marketing,opex=opex,oneoff=oneoff,net=net,cum=cum,notes='; '.join(notes)))
    return dict(name=name,rows=rows,min_cash=minc,breakeven=be,cum24=cum,rev24=sum(r['rev'] for r in rows),opex24=sum(r['opex']+r['oneoff'] for r in rows))
scen={
 'base':run('Base'),
 'cons':run('Conservative',users_mult=0.5,fee_bps=15,churn=0.05,audit1=15000),
 'up':run('Upside',users_mult=1.5,fee_bps=30,churn=0.02,grant=20000),
}

# ===================== HTML TEMPLATE =====================
TPL = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Solar Wind — Financial Projection</title>
<meta name="description" content="24-month financial projection for Solar Wind by stage (Stage 0 build/beta, Lean Phase-1, GA): revenue, costs, one-off spend, cash need and break-even under three scenarios.">
<style>
:root{ color-scheme:light;
  --bg:#f7f8fa; --surface:#ffffff; --ink:#111827; --muted:#5b6472; --line:#d9dee7;
  --accent:#6d28d9; --accent-2:#1d4ed8; --ok:#0b6e4f; --warn:#b45309; --danger:#b91c1c;
  --chip:#eef2f7; --code:#f1f5f9;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans Thai","Sarabun",sans-serif}
body{padding:0 16px}
.wrap{max-width:1180px;margin:0 auto;padding:32px 0 96px}
header.hero{border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:32px}
.kicker{color:var(--accent);font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-size:12px}
h1{font-size:clamp(28px,4vw,40px);line-height:1.15;margin:8px 0 12px}
h2{font-size:24px;margin:48px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:18px;margin:28px 0 8px}
p{margin:8px 0}
.lead{font-size:18px;color:var(--muted)}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:2px 12px;font-size:13px}
a{color:var(--accent-2);text-decoration:none}
nav.toc{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:24px 0}
nav.toc ol{margin:0;padding-left:20px;columns:2;column-gap:32px}
@media (max-width:640px){nav.toc ol{columns:1}}
figure{margin:20px 0;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;overflow-x:auto}
figure svg{width:100%;height:auto;display:block;font-family:inherit}
figcaption{color:var(--muted);font-size:13px;margin-top:10px}
.tablewrap{overflow-x:auto;margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:14px;background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--chip);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;background:var(--code);border:1px solid var(--line);border-radius:4px;padding:1px 5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:14px 0}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px}
.card h4{margin:0 0 6px;font-size:14px;color:var(--muted)}
.card .big{font-size:30px;font-weight:700;line-height:1.1;margin:4px 0}
.card p{margin:4px 0 0;color:var(--muted);font-size:13px}
.callout{border-left:4px solid var(--accent);background:var(--surface);border-radius:8px;padding:12px 16px;margin:16px 0}
.callout.ok{border-left-color:var(--ok)}
.callout.warn{border-left-color:var(--warn)}
.callout.danger{border-left-color:var(--danger)}
.sub{fill:var(--muted);font-size:11px}
.small{font-size:13px;color:var(--muted)}
ul,ol{padding-left:22px}
li{margin:4px 0}
footer{margin-top:64px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
</style>
</head>
<body>
<div class="wrap">

<header class="hero">
  <div class="kicker">Solar Wind · Financial Projection · v3.0 (Phase A crypto DCA · revenue-first)</div>
  <h1>Financial Projection<br><span style="font-weight:500;color:var(--muted)">รายรับ–รายจ่าย 24 เดือน แยกตาม Stage</span></h1>
  <p class="lead">ประมาณการทางการเงินของ Solar Wind ตามสถาปัตยกรรม v3.0 — Phase A crypto DCA (USDC → ETH/cbBTC บน Base) ที่ต้องทำเงินจริงตั้งแต่เดือนที่ 2 ด้วยต้นทุน ≈ $0; Phase B (tokenized stocks) ไม่อยู่ในตัวเลขนี้ และ unit economics ใน <a href="01-system-architecture.html#economics">01 หัวข้อ 9.1</a>: ตัวเลขทั้งหมดเป็น <strong>สมมติฐาน</strong> สำหรับวางแผนเงินสด ไม่ใช่การพยากรณ์ — ต้องแทนที่ด้วยข้อมูลจริงหลัง beta (metric <code>gas_cost_per_settle_usd</code>, <code>fee_per_cycle_usd</code>, churn จริง)</p>
  <div class="meta">
    <span class="chip">Horizon: 24 เดือน</span>
    <span class="chip">Currency: USD</span>
    <span class="chip">Date: 2026-09-21</span>
    <span class="chip">Model: <code>docs/financial-model.py</code> (แก้สมมติฐานแล้วรันใหม่ได้)</span>
  </div>
</header>

<nav class="toc">
<ol>
  <li><a href="#summary">สรุป (Base case)</a></li>
  <li><a href="#assumptions">สมมติฐาน</a></li>
  <li><a href="#stages">รายรับ–รายจ่ายแยกตาม Stage</a></li>
  <li><a href="#monthly">ตารางรายเดือน (Base case)</a></li>
  <li><a href="#scenarios">3 Scenarios: Conservative / Base / Upside</a></li>
  <li><a href="#funding">เงินที่ต้องมีและแผนหาเงิน</a></li>
  <li><a href="#risks">อะไรทำให้โมเดลพัง</a></li>
</ol>
</nav>

<h2 id="summary">1. สรุป (Base case)</h2>
<div class="grid">
  <div class="card"><h4>เงินสดที่ต้องมี (cash need สูงสุด)</h4><div class="big" style="color:var(--danger)">{{FUND}}</div><p>จุดต่ำสุดของเงินสดสะสม — เกือบทั้งหมดคือ audit ($42k ใน 2 รอบ) ไม่ใช่ค่ารัน; audit รอบ 2 เลื่อนได้</p></div>
  <div class="card"><h4>Operating break-even</h4><div class="big">{{OPBE}}</div><p>รายรับรายเดือน &gt; ค่ารันรายเดือน ตั้งแต่ ~{{OPBE_USERS}} users เพราะ Stage 0 ≈ $0</p></div>
  <div class="card"><h4>Cash break-even (คืนทุนสะสม)</h4><div class="big">{{CASHBE}}</div><p>~{{CASHBE_USERS}} users; หลัง audit รอบ 2 ที่ M12</p></div>
  <div class="card"><h4>จ่ายเงินเดือนตัวเองได้ ($3k/เดือน)</h4><div class="big">{{PAY}}</div><p>net ≥ $3k/เดือน ที่ ~{{PAY_USERS}} users (fee-only: ต้อง users หลักหมื่น)</p></div>
  <div class="card"><h4>รายรับสะสม 24 เดือน</h4><div class="big" style="color:var(--ok)">{{REV24}}</div><p>รายจ่ายสะสม {{OPEX24}} (รวม one-off) → เงินสดสะสม {{CUM24}}</p></div>
</div>
<figure>{{CHART}}<figcaption>Base case: รายรับ (เขียว) แซงค่ารัน (แดง) ตั้งแต่ {{OPBE}}; ยอดแดงที่ M5 และ M12 คือ audit. เงินสดสะสม (ม่วง, แกนขวา) ต่ำสุดที่ M12 แล้วกลับเป็นบวกที่ {{CASHBE}}</figcaption></figure>
<div class="callout ok"><strong>อ่านแบบ solo dev:</strong> ค่ารัน ≈ $0 จน operating break-even ตั้งแต่เดือนแรกที่มี fee; "ค่าเข้า" (legal $2k + audit contest $12k) คือเงินก้อนเดียวที่ต้องหาใน 4 เดือนแรก และ audit รอบ 2 ($30k) เลื่อนได้จนกว่า TVL จะถึง $1M — ถ้าได้ grant $20k (Upside) cash need ลดเหลือ {{UP_FUND}}; ถ้าโตช้าครึ่งหนึ่ง (Conservative) ต้องมี {{CONS_FUND}} และไม่คืนทุนใน 24 เดือน — จุดอ่อนของโมเดล fee-only คือรายได้ต่อ user เล็ก ($0.54/เดือน) ต้องการ users หลักหมื่น</div>

<h2 id="assumptions">2. สมมติฐาน</h2>
<h3>2.1 รายรับต่อผู้ใช้</h3>
<div class="tablewrap"><table>
<tr><th>ตัวแปร</th><th>Base</th><th>ที่มา / หมายเหตุ</th></tr>
<tr><td>งบ DCA เฉลี่ย</td><td>50 USDC/สัปดาห์ = $216.7/เดือน (ซื้อ ETH/cbBTC)</td><td>พารามิเตอร์จาก workshop; ผู้ใช้จริงอาจต่ำกว่า (ทำ sensitivity ที่ 25 USDC ก่อน launch)</td></tr>
<tr><td>Protocol fee</td><td>25 bps ของ amountIn ($0.125/cycle, $0.54/user/เดือน)</td><td>ช่วง 15–30 bps; หักบนเชนผ่าน FeeModule (แบบ interface fee) — เปิดตั้งแต่ M2</td></tr>
<tr><td>Performance / AUM fee</td><td><strong>ไม่มี (v3.0)</strong></td><td>ไม่เก็บค่าจัดการทรัพย์สินตาม legal posture (01 หัวข้อ 1.1)</td></tr>
<tr><td>Subscription</td><td><strong>ไม่มี (v3.0)</strong></td><td>ผู้ใช้ plug LLM เองและเลือกไม่ใช้ AI ได้ — ไม่มี feature ที่คุ้มจ่ายรายเดือน; รายได้ = protocol fee อย่างเดียว</td></tr>
<tr><td>AUM</td><td>สะสมจากเงินที่ซื้อผ่านระบบ × retention; churn 3%/เดือน — ใช้เป็นตัวชี้วัด ไม่ใช่ฐานรายได้ใน Base</td><td>Non-custodial: หุ้นอยู่ในกระเป๋าผู้ใช้</td></tr>
<tr><td>Solver surplus share (20%)</td><td>$0</td><td>ไม่นับในแผน — เป็น upside เมื่อ route ดีกว่า minOut</td></tr>
</table></div>
<h3>2.2 การเติบโตของผู้ใช้ (active users ปลายเดือน)</h3>
<div class="tablewrap"><table>
<tr><th>Stage</th><th>เดือน</th><th>Users</th><th>เหตุผล</th></tr>
<tr><td>Stage 0 · Build</td><td>M1</td><td>0</td><td>contract/agent/solver มีจาก workshop — เปลี่ยน pair + infra ฟรี; Base Sepolia</td></tr>
<tr><td>Stage 0 · Beta (Base mainnet, fee on)</td><td>M2–M5</td><td>30 → 300</td><td>cap 100 USDC/สัปดาห์/คน และ TVL cap จนกว่า audit contest จะเสร็จ (M4)</td></tr>
<tr><td>Lean Phase-1</td><td>M6–M12</td><td>450 → 3,300</td><td>T0 ผ่าน (รายได้ &gt; $1k/เดือน) → ตั้งบริษัท M6; โต ~35%/เดือน</td></tr>
<tr><td>GA</td><td>M13–M24</td><td>4,500 → 33,000</td><td>โตชะลอเหลือ ~10–30%/เดือน; audit รอบ 2 ก่อนเปิด</td></tr>
</table></div>
<h3>2.3 รายจ่าย</h3>
<div class="tablewrap"><table>
<tr><th>รายการ</th><th>Stage 0</th><th>Lean Phase-1</th><th>GA</th><th>หมายเหตุ</th></tr>
<tr><td>Gas (solver จ่าย)</td><td>$0.03/settle (ไม่มี batch)</td><td>$0.012/settle (settleBatch)</td><td>$0.012/settle</td><td>Base L2; = users × 4.33 × gas — ผันแปรตามผู้ใช้โดยตรง</td></tr>
<tr><td>Infra (OCI)</td><td>$0–5</td><td>$600 (+$400 เมื่อ &gt; 5k users = PG HA, T2)</td><td>$1,000 (+$400 T2, +$500 เมื่อ &gt; 20k)</td><td>จาก 02 หัวข้อ 13; ไม่มี Redis/Kafka/Firewall</td></tr>
<tr><td>RPC</td><td>$0 (free tier)</td><td>$0 จนถึง 10k users</td><td>$200 (10k+) → $500 (30k+)</td><td>trigger T4 own node ไม่ถึงใน 24 เดือน</td></tr>
<tr><td>LLM</td><td>$0</td><td>$0</td><td>$0</td><td>BYO-LLM (01 ADR-005): ผู้ใช้ใส่ key เองฝั่งเบราว์เซอร์; macro signal เป็น deterministic indicators</td></tr>
<tr><td>อื่น ๆ (domain, email, bug bounty reserve, marketing)</td><td>$2</td><td>$2–22</td><td>~$520 (bounty $300 + marketing $200)</td><td>Telegram/Cloudflare/GitHub = free tier</td></tr>
<tr><td>เงินเดือนผู้ก่อตั้ง</td><td colspan="3">ไม่รวมในโมเดล — ดูบรรทัด "จ่ายเงินเดือนตัวเองได้" ในสรุป</td><td></td></tr>
</table></div>
<h3>2.4 One-off</h3>
<div class="tablewrap"><table>
<tr><th>รายการ</th><th class="num">จำนวน</th><th>เดือน</th><th>หมายเหตุ</th></tr>
<tr><td>Legal consult เบา ๆ (posture "software + protocol", ก.ล.ต. ไทย digital-asset advisor)</td><td class="num">$2,000</td><td>M2</td><td>ก่อน beta — ตัดออกไม่ได้</td></tr>
<tr><td>Audit รอบ 1 (contest ขนาดเล็ก/community)</td><td class="num">$12,000</td><td>เมื่อ TVL ≥ $100k (Base: M4)</td><td>เมื่อ TVL ~$100k; ก่อนหน้านั้นใช้ cap ต่อ user + TVL cap + bounty</td></tr>
<tr><td>จดทะเบียนบริษัท</td><td class="num">$1,000</td><td>เมื่อรายได้ ≥ $1k/เดือน (Base: M6)</td><td>เมื่อรายได้ &gt; $1k/เดือน (T0)</td></tr>
<tr><td>Audit รอบ 2 (บริษัท) + contest</td><td class="num">$30,000</td><td>เมื่อ TVL ≥ $1M และ m ≥ 12 (Base: M12)</td><td>เมื่อ TVL &gt; $1M — เลื่อนได้ถ้าไม่ถึง</td></tr>
</table></div>

<h2 id="stages">3. รายรับ–รายจ่ายแยกตาม Stage (Base case, รวมทั้ง stage)</h2>
<div class="tablewrap"><table>
<tr><th>Stage</th><th class="num">Users</th><th class="num">AUM ปลาย stage</th><th class="num">Protocol fee</th><th class="num">รายรับรวม</th><th class="num">Gas</th><th class="num">Infra</th><th class="num">RPC+อื่น</th><th class="num">One-off</th><th class="num">Net</th><th>หมายเหตุ</th></tr>
{{STAGE_ROWS}}
</table></div>
<div class="callout"><strong>สิ่งที่ตารางบอก:</strong> ค่ารันเกือบศูนย์ทำให้ operating break-even เร็ว แต่ fee-only ($0.54/user/เดือน) แปลว่า "เงินจริง" ต้องมาจากจำนวนผู้ใช้หลักหมื่น — Stage 0/Lean คือช่วงพิสูจน์ว่าหาผู้ใช้ได้ ไม่ใช่ช่วงทำกำไร; GA คือช่วงที่ fee เริ่มเลี้ยงคนได้</div>

<h2 id="monthly">4. ตารางรายเดือน (Base case)</h2>
<div class="tablewrap"><table>
<tr><th>เดือน</th><th>Stage</th><th class="num">Users</th><th class="num">AUM</th><th class="num">Protocol fee</th><th class="num">รายรับ</th><th class="num">Gas</th><th class="num">Infra</th><th class="num">RPC+อื่น</th><th class="num">One-off</th><th class="num">Net</th><th class="num">เงินสดสะสม</th><th>หมายเหตุ</th></tr>
{{MONTH_ROWS}}
</table></div>

<h2 id="scenarios">5. 3 Scenarios</h2>
<div class="tablewrap"><table>
<tr><th>Scenario</th><th class="num">Users M24</th><th class="num">AUM M24</th><th class="num">รายรับ 24 เดือน (fee only)</th><th class="num">รายจ่าย 24 เดือน</th><th class="num">เงินสดสะสม M24</th><th class="num">Cash need</th><th class="num">Operating BE</th><th class="num">Cash BE</th><th class="num">จ่ายเงินเดือน $3k ได้</th></tr>
{{SCEN_ROWS}}
</table></div>
<div class="tablewrap"><table>
<tr><th>ตัวแปร</th><th>Conservative</th><th>Base</th><th>Upside</th></tr>
<tr><td>Users</td><td>0.5× ของ base</td><td>ตามหัวข้อ 2.2</td><td>1.5× ของ base</td></tr>
<tr><td>Protocol fee</td><td>15 bps</td><td>25 bps</td><td>30 bps</td></tr>
<tr><td>Churn/เดือน</td><td>5%</td><td>3%</td><td>2%</td></tr>
<tr><td>Grant</td><td>—</td><td>—</td><td>$20k ที่ M5 (Base Builder / RetroPGF)</td></tr>
<tr><td>Audit รอบ 1</td><td>$15k</td><td>$12k</td><td>$12k</td></tr>
</table></div>
<div class="callout warn"><strong>Conservative ไม่คืนทุนใน 24 เดือน</strong> — ไม่ใช่เพราะค่ารัน แต่เพราะ audit $55k เทียบกับรายรับที่โตช้า; บทเรียนคือ <em>อย่าจ่าย audit รอบ 2 จนกว่า metrics จริงจะยืนยันการเติบโต</em> (ผูกกับ trigger T0 และจำนวน paying users ไม่ใช่ปฏิทิน)</div>

<h2 id="funding">6. เงินที่ต้องมีและแผนหาเงิน</h2>
<div class="grid">
  <div class="card"><h4>Cash need (Base)</h4><div class="big" style="color:var(--danger)">{{FUND}}</div><p>= audit 2 รอบ + legal + บริษัท − กำไรสะสมช่วง Lean</p></div>
  <div class="card"><h4>ถ้าไม่มีเงินก้อน</h4><div class="big">~$2k</div><p>เริ่มด้วย legal consult อย่างเดียว; audit contest จ่ายจากรายได้/grant เมื่อ TVL ถึง; audit รอบ 2 เลื่อนจนกว่า TVL &gt; $1M — cap ต่อ user คือ risk control ระหว่างนั้น</p></div>
  <div class="card"><h4>Grant target</h4><div class="big">$10–20k</div><p>Base Builder Grants, Optimism RetroPGF, hackathon — ครอบ audit รอบ 1 ทั้งก้อน</p></div>
</div>
<ol>
  <li><strong>M1:</strong> เปลี่ยน pair ของ workshop เป็น USDC→ETH/cbBTC, infra Stage 0 (OCI ≈ $0), Base Sepolia; สมัคร grant/hackathon ด้วย demo</li>
  <li><strong>M2:</strong> legal consult $2k → beta บน Base mainnet กับคนรู้จัก 30 คน, <strong>fee เปิดตั้งแต่ swap แรก</strong>, cap 100 USDC/สัปดาห์/คน + TVL cap $50k, bounty</li>
  <li><strong>M4:</strong> audit contest $12k เมื่อ TVL ~$100k (จาก grant ถ้าได้)</li>
  <li><strong>M6:</strong> รายได้ &gt; $1k/เดือน → จดบริษัท $1k; ย้ายขึ้น Lean เมื่อ T0</li>
  <li><strong>M12:</strong> audit รอบ 2 $30k เฉพาะเมื่อ TVL &gt; $1M — ไม่งั้นเลื่อน</li>
  <li><strong>M13+ (GA):</strong> net เป็นบวกทุกเดือน; เริ่มเจรจา partner สำหรับ Phase B (tokenized stocks) เมื่อมีบริษัท + รายได้</li>
</ol>

<h2 id="risks">7. อะไรทำให้โมเดลพัง (เรียงตาม impact)</h2>
<div class="tablewrap"><table>
<tr><th>ความเสี่ยง</th><th>ผลต่อโมเดล</th><th>สัญญาณเตือน / ทางแก้</th></tr>
<tr><td>งบ DCA จริงต่ำกว่า 50 USDC (เช่น 20 USDC)</td><td>รายรับ ×0.4 ทุกบรรทัด แต่ gas เท่าเดิม → margin ต่อ cycle เหลือ 2–4×</td><td>ตั้งขั้นต่ำต่อ cycle (เช่น 20 USDC) ให้ fee ≥ 3× gas; settleBatch ลด gas</td></tr>
<tr><td>หาผู้ใช้ไม่ได้ (คู่แข่ง crypto DCA เยอะ)</td><td>= Conservative หรือแย่กว่า; รายได้ Phase A เล็กแต่ต้นทุน ≈ 0 จึงไม่เจ๊ง แค่ไม่โต</td><td>จุดขาย non-custodial + gasless + rules ของผู้ใช้; ช่องทาง: Base ecosystem, Telegram communities, open-source</td></tr>
<tr><td>ก.ล.ต. ไทยมองว่า hosted agent = digital-asset advisor/manager</td><td>ต้องปิด hosted สำหรับผู้ใช้ไทย เหลือ self-host</td><td>legal consult M2; self-host guide พร้อมตั้งแต่แรก; geo-policy ใน config</td></tr>
<tr><td>Exploit สัญญาก่อน audit</td><td>เสียได้สูงสุด 1 period budget/user × users (cap ควบคุม)</td><td>cap 100 USDC/สัปดาห์ + TVL cap ก่อน audit; bounty; canary</td></tr>
<tr><td>Gas spike ยาว (Base base fee ×5)</td><td>gas ≈ fee → margin ~1×</td><td>gas rules ชะลอ (มีแล้ว); alarm 7-day avg gas &gt; 30% ของ fee; ปรับ fee bps ผ่าน Timelock</td></tr>
<tr><td>Churn 5%+ / โตช้า</td><td>= Conservative: ไม่คืนทุน 24 เดือน</td><td>เลื่อน audit รอบ 2; ลด cap; ไม่ขยาย infra ก่อน trigger</td></tr>
<tr><td>Phase B (หลักทรัพย์) ไม่มี partner/ใบอนุญาต</td><td>ไม่กระทบ Phase A — แค่ไม่ได้ขยายไปหุ้น</td><td>Phase A ต้องเลี้ยงตัวเองได้โดยไม่พึ่ง Phase B</td></tr>
<tr><td>Exploit สัญญา</td><td>เงินผู้ใช้ ≤ 1 period budget/คน แต่ชื่อเสียงจบ</td><td>audit + bug bounty + canary; blast radius ตามสถาปัตยกรรม</td></tr>
</table></div>

<footer>Solar Wind · Financial Projection v3.0 · 2026-09-21 · สร้างจาก <code>docs/financial-model.py</code> — แก้สมมติฐานในไฟล์นั้นแล้วรัน <code>python3 docs/financial-model.py</code> เพื่อสร้างหน้านี้ใหม่ · ตัวเลขทั้งหมดเป็นสมมติฐาน ไม่ใช่คำแนะนำทางการเงิน · v3.0: Phase A crypto DCA, protocol fee อย่างเดียว</footer>
</div>
</body>
</html>
"""
# ===================== RENDER =====================
S=scen
def money(x, dec=0):
    if abs(x)<0.5 and dec==0: return '0'
    s=f'{abs(x):,.{dec}f}'
    return ('−' if x<0 else '')+'$'+s
def k(x): return ('−' if x<0 else '')+f'${abs(x)/1000:,.1f}k'
def cls(x): return ' style="color:var(--danger)"' if x<0 else ''
base=S['base']; rows=base['rows']
# per-stage aggregates for base
stages=['Stage 0 · Build','Stage 0 · Beta','Lean Phase-1','GA']
agg={}
for st in stages:
    rs=[r for r in rows if r['stage']==st]
    agg[st]=dict(months=f"M{rs[0]['m']}–M{rs[-1]['m']}", n=len(rs), users=f"{rs[0]['users']:,}→{rs[-1]['users']:,}",
        rev=sum(r['rev'] for r in rs), vol=sum(r['vol'] for r in rs), perf=sum(r['perf'] for r in rs), pro=sum(r['pro'] for r in rs),
        gas=sum(r['gas'] for r in rs), infra=sum(r['infra'] for r in rs), rpc=sum(r['rpc'] for r in rs), llm=sum(r['llm'] for r in rs), other=sum(r['other'] for r in rs),
        opex=sum(r['opex'] for r in rs), oneoff=sum(r['oneoff'] for r in rs), net=sum(r['net'] for r in rs), aum=rs[-1]['aum'], notes='; '.join(x for x in (r['notes'] for r in rs) if x))
# chart (base): monthly rev vs opex+oneoff, cumulative cash
W,H=1000,360; L,R,T,B=70,70,20,50
maxm=max(max(r['rev'],r['opex']+r['oneoff']) for r in rows); maxm=70000
cmin=min(r['cum'] for r in rows); cmax=max(r['cum'] for r in rows)
def x(i): return L+(W-L-R)*i/23
def y1(v): return T+(H-T-B)*(1-v/maxm)
def y2(v): return T+(H-T-B)*(1-(v-cmin)/(cmax-cmin))
p_rev=' '.join(f'{x(i):.1f},{y1(r["rev"]):.1f}' for i,r in enumerate(rows))
p_opex=' '.join(f'{x(i):.1f},{y1(min(r["opex"]+r["oneoff"],maxm)):.1f}' for i,r in enumerate(rows))
p_cum=' '.join(f'{x(i):.1f},{y2(r["cum"]):.1f}' for i,r in enumerate(rows))
grid=''.join(f'<line x1="{L}" y1="{y1(v):.1f}" x2="{W-R}" y2="{y1(v):.1f}" stroke="var(--line)"/><text x="{L-6}" y="{y1(v)+4:.1f}" text-anchor="end" class="sub">{k(v)}</text>' for v in [0,20000,40000,60000])
grid2=''.join(f'<text x="{W-R+6}" y="{y2(v)+4:.1f}" class="sub">{k(v)}</text>' for v in [cmin,0,100000,200000,cmax])
xl=''.join(f'<text x="{x(i):.1f}" y="{H-B+18}" text-anchor="middle" class="sub">M{i+1}</text>' for i in range(0,24,2))
# stage bands
bands=''; 
for st,col in zip(stages,['#eef2f7','#fef3c7','#dcfce7','#ede9fe']):
    idx=[i for i,r in enumerate(rows) if r['stage']==st]
    x0=x(idx[0])-(x(1)-x(0))/2; x1=x(idx[-1])+(x(1)-x(0))/2
    bands+=f'<rect x="{x0:.1f}" y="{T}" width="{x1-x0:.1f}" height="{H-T-B}" fill="{col}" opacity=".6"/><text x="{(x0+x1)/2:.1f}" y="{T+14}" text-anchor="middle" class="sub">{st}</text>'
zero_y=y2(0)
chart=f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Base case: revenue, cost, cumulative cash">
{bands}{grid}<line x1="{L}" y1="{zero_y:.1f}" x2="{W-R}" y2="{zero_y:.1f}" stroke="var(--muted)" stroke-dasharray="4 4"/>
<polyline points="{p_opex}" fill="none" stroke="var(--danger)" stroke-width="2"/>
<polyline points="{p_rev}" fill="none" stroke="var(--ok)" stroke-width="2.5"/>
<polyline points="{p_cum}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-dasharray="7 4"/>
{grid2}{xl}
<text x="{L}" y="{H-8}" class="sub"><tspan fill="var(--ok)" font-weight="600">— รายรับ/เดือน</tspan>  <tspan fill="var(--danger)" font-weight="600">— รายจ่าย/เดือน (รวม one-off)</tspan>  <tspan fill="var(--accent)" font-weight="600">- - เงินสดสะสม (แกนขวา)</tspan></text>
</svg>'''
def month_rows(rs):
    out=''
    for r in rs:
        out+=f'<tr><td>M{r["m"]}</td><td class="small">{r["stage"]}</td><td class="num">{r["users"]:,}</td><td class="num">{k(r["aum"])}</td><td class="num">{money(r["vol"])}</td><td class="num"><strong>{money(r["rev"])}</strong></td><td class="num">{money(r["gas"])}</td><td class="num">{money(r["infra"])}</td><td class="num">{money(r["rpc"]+r["llm"]+r["other"])}</td><td class="num">{money(r["oneoff"])}</td><td class="num"{cls(r["net"])}><strong>{money(r["net"])}</strong></td><td class="num"{cls(r["cum"])}>{money(r["cum"])}</td><td class="small">{r["notes"]}</td></tr>\n'
    return out
def stage_rows():
    out=''
    for st in stages:
        a=agg[st]
        out+=f'<tr><td><strong>{st}</strong><br><span class="small">{a["months"]} ({a["n"]} เดือน)</span></td><td class="num">{a["users"]}</td><td class="num">{k(a["aum"])}</td><td class="num">{money(a["vol"])}</td><td class="num"><strong>{money(a["rev"])}</strong></td><td class="num">{money(a["gas"])}</td><td class="num">{money(a["infra"])}</td><td class="num">{money(a["rpc"]+a["llm"]+a["other"])}</td><td class="num">{money(a["oneoff"])}</td><td class="num"{cls(a["net"])}><strong>{money(a["net"])}</strong></td><td class="small">{a["notes"]}</td></tr>\n'
    return out
def scen_rows():
    out=''
    for key,label in [('cons','Conservative'),('base','Base'),('up','Upside')]:
        v=S[key]; r=v['rows']; cashbe=next((x['m'] for x in r if x['cum']>0 and x['m']>5),None)
        pay=next((x['m'] for x in r if x['net']>=3000 and x['oneoff']==0),None)
        out+=f'<tr><td><strong>{label}</strong></td><td class="num">{r[-1]["users"]:,}</td><td class="num">{k(r[-1]["aum"])}</td><td class="num">{k(v["rev24"])}</td><td class="num">{k(v["opex24"])}</td><td class="num"{cls(v["cum24"])}><strong>{k(v["cum24"])}</strong></td><td class="num" style="color:var(--danger)"><strong>{k(v["min_cash"])}</strong></td><td class="num">M{v["breakeven"]}</td><td class="num">{"M"+str(cashbe) if cashbe else "ไม่ถึงใน 24 เดือน"}</td><td class="num">{"M"+str(pay) if pay else "ไม่ถึงใน 24 เดือน"}</td></tr>\n'
    return out
html=TPL
html=html.replace('{{CHART}}',chart).replace('{{STAGE_ROWS}}',stage_rows()).replace('{{MONTH_ROWS}}',month_rows(rows)).replace('{{SCEN_ROWS}}',scen_rows())
def _be(rs,cond): return next((x['m'] for x in rs if cond(x)),None)
opbe=base['breakeven']; cashbe=_be(rows,lambda x: x['cum']>0 and x['m']>5); pay=_be(rows,lambda x: x['net']>=3000 and x['oneoff']==0)
fmtm=lambda m: f'M{m}' if m else 'ไม่ถึงใน 24 เดือน'
html=html.replace('{{OPBE}}',fmtm(opbe)).replace('{{CASHBE}}',fmtm(cashbe)).replace('{{PAY}}',fmtm(pay))
html=html.replace('{{CASHBE_USERS}}',f"{rows[cashbe-1]['users']:,}" if cashbe else '—').replace('{{PAY_USERS}}',f"{rows[pay-1]['users']:,}" if pay else '—').replace('{{OPBE_USERS}}',f"{rows[opbe-1]['users']:,}" if opbe else '—')
html=html.replace('{{FUND}}',k(-base['min_cash'])).replace('{{CUM24}}',k(base['cum24'])).replace('{{REV24}}',k(base['rev24'])).replace('{{OPEX24}}',k(base['opex24']))
html=html.replace('{{CONS_FUND}}',k(-S['cons']['min_cash'])).replace('{{UP_FUND}}',k(-S['up']['min_cash']))
import os
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'03-financial-projection.html')
open(out,'w').write(html); print('written',out)
