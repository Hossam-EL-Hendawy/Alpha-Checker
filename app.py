import streamlit as st
import requests
import ssl
import socket
import whois
import re
import time
import ipaddress
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
import dns.resolver
import tldextract
import urllib3

urllib3.disable_warnings()

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alpha Checker – URL Safety",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Persistent Storage: JSON file on disk ────────────────────────────────────
# Saved next to app.py → survives every page reload, browser restart, etc.
WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallet_data.json")

def file_load() -> list:
    try:
        if os.path.exists(WALLET_FILE):
            with open(WALLET_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def file_save(wallet: list):
    try:
        tmp = WALLET_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(wallet, f, ensure_ascii=False, indent=2)
        os.replace(tmp, WALLET_FILE)
    except Exception as e:
        st.toast(f"Could not save wallet: {e}", icon="⚠️")

def file_clear():
    try:
        if os.path.exists(WALLET_FILE):
            os.remove(WALLET_FILE)
    except Exception:
        pass

# ─── Bootstrap session state ──────────────────────────────────────────────────
if "wallet" not in st.session_state:
    st.session_state.wallet = file_load()

if "factory_reset_confirmed" not in st.session_state:
    st.session_state.factory_reset_confirmed = False

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: #080b14; color: #e2e8f0; }
.stApp { background: #080b14; }

.stTabs [data-baseweb="tab-list"] { gap:.5rem; background:#0f172a; border-radius:12px; padding:.35rem; border:1px solid #1e293b; }
.stTabs [data-baseweb="tab"] { background:transparent!important; border-radius:8px!important; color:#64748b!important; font-family:'Syne',sans-serif!important; font-weight:700!important; font-size:.9rem!important; padding:.5rem 1.2rem!important; border:none!important; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#0ea5e9,#6366f1)!important; color:white!important; }
.stTabs [data-baseweb="tab-panel"] { padding-top:1.5rem!important; }

.hero { text-align:center; padding:2rem 0 1.2rem; }
.hero h1 { font-size:3rem; font-weight:800; letter-spacing:-1px; color:#f8fafc; margin-bottom:.3rem; }
.hero h1 .alpha { color:#38bdf8; }
.hero h1 .checker { color:#a78bfa; }
.hero p { color:#64748b; font-size:1rem; font-family:'Space Mono',monospace; }

.stTextInput > div > div > input { background:#0f172a!important; border:1.5px solid #1e293b!important; border-radius:10px!important; color:#e2e8f0!important; font-family:'Space Mono',monospace!important; font-size:.95rem!important; padding:.75rem 1rem!important; }
.stTextInput > div > div > input:focus { border-color:#38bdf8!important; box-shadow:0 0 0 2px rgba(56,189,248,.15)!important; }

.stButton > button { background:linear-gradient(135deg,#0ea5e9,#6366f1)!important; color:white!important; border:none!important; border-radius:10px!important; font-family:'Syne',sans-serif!important; font-weight:700!important; font-size:1rem!important; padding:.65rem 2.5rem!important; letter-spacing:.5px!important; transition:opacity .2s!important; width:100%!important; }
.stButton > button:hover { opacity:.88!important; }

.score-safe    { background:linear-gradient(135deg,#052e16,#14532d); border:1px solid #16a34a; border-radius:16px; padding:1.8rem; text-align:center; margin:1.5rem 0; }
.score-warning { background:linear-gradient(135deg,#1c1400,#2d1f00); border:1px solid #ca8a04; border-radius:16px; padding:1.8rem; text-align:center; margin:1.5rem 0; }
.score-danger  { background:linear-gradient(135deg,#1f0505,#3b0a0a); border:1px solid #dc2626; border-radius:16px; padding:1.8rem; text-align:center; margin:1.5rem 0; }
.score-number  { font-size:4rem; font-weight:800; font-family:'Space Mono',monospace; line-height:1; margin-bottom:.4rem; }
.score-label   { font-size:1.3rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; }

.check-card   { background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:1rem 1.25rem; margin-bottom:.75rem; display:flex; align-items:flex-start; gap:1rem; }
.check-icon   { font-size:1.4rem; min-width:1.8rem; }
.check-title  { font-weight:700; font-size:.95rem; margin-bottom:.2rem; }
.check-detail { font-family:'Space Mono',monospace; font-size:.78rem; color:#64748b; word-break:break-all; }
.badge-safe   { color:#4ade80; } .badge-warn { color:#fbbf24; } .badge-danger { color:#f87171; } .badge-info { color:#38bdf8; }

.section-title { font-size:.78rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#475569; margin:1.5rem 0 .75rem; font-family:'Space Mono',monospace; }
.url-display   { background:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:.75rem 1rem; font-family:'Space Mono',monospace; font-size:.82rem; color:#94a3b8; word-break:break-all; margin-bottom:.5rem; }

.wallet-card  { background:#0f172a; border:1px solid #1e293b; border-radius:14px; padding:1rem 1.25rem; margin-bottom:.9rem; }
.wallet-card:hover { border-color:#334155; }
.wallet-url   { font-family:'Space Mono',monospace; font-size:.82rem; color:#94a3b8; word-break:break-all; margin-bottom:.5rem; }
.wallet-meta  { display:flex; gap:.75rem; align-items:center; flex-wrap:wrap; }
.wallet-badge { font-size:.72rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; padding:.2rem .65rem; border-radius:20px; font-family:'Space Mono',monospace; }
.wb-safe      { background:#052e16; color:#4ade80; border:1px solid #16a34a; }
.wb-warn      { background:#1c1400; color:#fbbf24; border:1px solid #ca8a04; }
.wb-danger    { background:#1f0505; color:#f87171; border:1px solid #dc2626; }
.wallet-score { font-family:'Space Mono',monospace; font-size:.82rem; color:#475569; }
.wallet-time  { font-family:'Space Mono',monospace; font-size:.75rem; color:#334155; margin-left:auto; }

.wstat       { background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:1rem; text-align:center; }
.wstat-num   { font-size:2rem; font-weight:800; font-family:'Space Mono',monospace; }
.wstat-label { font-size:.72rem; color:#475569; letter-spacing:2px; text-transform:uppercase; font-family:'Space Mono',monospace; }

.storage-info { background:#060f1a; border:1px solid #0ea5e9; border-radius:12px; padding:1rem 1.25rem; margin-bottom:1rem; }
.storage-row  { display:flex; justify-content:space-between; align-items:center; padding:.35rem 0; border-bottom:1px solid #0f172a; font-family:'Space Mono',monospace; font-size:.8rem; }
.storage-row:last-child { border-bottom:none; }
.storage-key  { color:#475569; }
.storage-val  { color:#38bdf8; font-weight:700; }

.reset-box       { background:#1a0505; border:1px solid #7f1d1d; border-radius:14px; padding:1.25rem 1.5rem; margin-top:.5rem; }
.reset-box-title { font-size:.78rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#f87171; font-family:'Space Mono',monospace; margin-bottom:.5rem; }
.reset-box-desc  { font-size:.82rem; color:#64748b; font-family:'Space Mono',monospace; line-height:1.7; }

.empty-wallet       { text-align:center; padding:3rem 1rem; color:#334155; font-family:'Space Mono',monospace; font-size:.9rem; }
.empty-wallet .icon { font-size:3rem; margin-bottom:1rem; }

hr { border-color:#1e293b!important; margin:1.5rem 0!important; }
.stSpinner > div { border-top-color:#38bdf8!important; }
</style>
""", unsafe_allow_html=True)


# ─── Security Check Functions ──────────────────────────────────────────────────

PHISHING_KEYWORDS = [
    "login","signin","account","verify","secure","update","confirm","banking",
    "paypal","apple","google","microsoft","amazon","netflix","password",
    "credential","wallet","crypto","bitcoin","free","prize","winner","lucky",
    "urgent","suspended","unusual","activity",
]
SUSPICIOUS_TLDS = [
    ".tk",".ml",".ga",".cf",".gq",".xyz",".pw",".top",".click",
    ".download",".loan",".win",".racing",".party",".stream",".review",
]

def normalize_url(url):
    url = url.strip()
    if not url.startswith(("http://","https://")): url = "https://" + url
    return url

def check_ssl(hostname):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((hostname,443),timeout=5), server_hostname=hostname) as s:
            cert = s.getpeercert()
            expire_dt = datetime.strptime(cert.get("notAfter",""), "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (expire_dt - datetime.now(timezone.utc)).days
            return {"status":"safe","message":f"Valid SSL - expires in {days_left} days","score":20}
    except ssl.SSLCertVerificationError:
        return {"status":"danger","message":"SSL certificate verification FAILED","score":-30}
    except Exception as e:
        return {"status":"warning","message":f"Could not verify SSL: {str(e)[:60]}","score":-10}

def check_https(url):
    if url.startswith("https://"):
        return {"status":"safe","message":"Connection uses HTTPS (encrypted)","score":10}
    return {"status":"danger","message":"Plain HTTP - traffic is unencrypted!","score":-20}

def check_redirects(url):
    try:
        resp = requests.Session().get(url, timeout=8, allow_redirects=True, verify=False,
                                      headers={"User-Agent":"Mozilla/5.0 (Alpha Checker)"})
        chain = [r.url for r in resp.history] + [resp.url]
        if len(chain) > 4:
            return {"status":"warning","message":f"Long redirect chain ({len(chain)} hops)","score":-10}
        if len(chain) > 1:
            return {"status":"info","message":f"Redirected {len(chain)-1}x to: {chain[-1][:60]}","score":0}
        return {"status":"safe","message":"No redirects detected","score":5}
    except requests.exceptions.SSLError:
        return {"status":"danger","message":"SSL error during connection","score":-20}
    except Exception as e:
        return {"status":"warning","message":f"Could not follow redirects: {str(e)[:60]}","score":-5}

def check_domain_age(hostname):
    try:
        w = whois.whois(hostname)
        creation = w.creation_date
        if isinstance(creation, list): creation = creation[0]
        if creation:
            if creation.tzinfo is None: creation = creation.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - creation).days
            if age_days < 30:    return {"status":"danger",  "message":f"Domain only {age_days} days old - very suspicious!","score":-25}
            elif age_days < 180: return {"status":"warning", "message":f"Young domain: {age_days} days old","score":-10}
            else:                return {"status":"safe",    "message":f"Established domain: ~{age_days//365} year(s) old","score":15}
    except Exception:
        pass
    return {"status":"warning","message":"Could not retrieve WHOIS data","score":-5}

def check_url_patterns(url, hostname):
    issues, score = [], 0
    try:
        ipaddress.ip_address(hostname)
        issues.append("IP address used instead of domain"); score -= 20
    except ValueError:
        pass
    if len(url) > 100:
        issues.append(f"Very long URL ({len(url)} chars)"); score -= 10
    if len(hostname.split(".")) > 4:
        issues.append(f"{len(hostname.split('.'))-2} subdomains detected"); score -= 15
    found_kw = [kw for kw in PHISHING_KEYWORDS if kw in url.lower()]
    if found_kw:
        issues.append(f"Phishing keywords: {', '.join(found_kw[:4])}"); score -= 15
    ext = tldextract.extract(hostname)
    tld = f".{ext.suffix}" if ext.suffix else ""
    if tld in SUSPICIOUS_TLDS:
        issues.append(f"High-risk TLD: {tld}"); score -= 20
    if "@" in url:
        issues.append("@ symbol in URL (phishing trick)"); score -= 25
    if re.search(r"//[^/]", url.split("://",1)[-1]):
        issues.append("Suspicious double slash in path"); score -= 10
    if issues:
        return {"status":"danger" if score<=-20 else "warning","message":" | ".join(issues),"score":score}
    return {"status":"safe","message":"URL structure looks clean","score":10}

def check_security_headers(url):
    try:
        hdrs = {k.lower():v for k,v in requests.get(url, timeout=8, verify=False,
                headers={"User-Agent":"Mozilla/5.0 (Alpha Checker)"}).headers.items()}
        good, missing = [], []
        for h, label in {"strict-transport-security":"HSTS","x-content-type-options":"X-Content-Type",
                          "x-frame-options":"X-Frame-Options","content-security-policy":"CSP"}.items():
            (good if h in hdrs else missing).append(label)
        if len(missing) >= 3:
            return {"status":"warning","message":f"Missing security headers: {', '.join(missing)}","score":-10}
        return {"status":"safe","message":f"Security headers present: {', '.join(good) or 'basic'}","score":5}
    except Exception as e:
        return {"status":"warning","message":f"Could not fetch headers: {str(e)[:60]}","score":0}

def check_dns(hostname):
    try:
        ips = [str(r) for r in dns.resolver.resolve(hostname, "A")]
        return {"status":"safe","message":f"DNS resolves to: {', '.join(ips[:3])}","score":5}
    except dns.resolver.NXDOMAIN:
        return {"status":"danger","message":"Domain does NOT exist (NXDOMAIN)","score":-40}
    except Exception as e:
        return {"status":"warning","message":f"DNS lookup issue: {str(e)[:60]}","score":-5}

STATUS_ICON = {
    "safe":    ("✅","badge-safe"),
    "warning": ("⚠️","badge-warn"),
    "danger":  ("🚨","badge-danger"),
    "info":    ("ℹ️","badge-info"),
}
CHECK_NAMES = {
    "https":"HTTPS Protocol","ssl":"SSL Certificate","dns":"DNS Resolution",
    "domain":"Domain Age (WHOIS)","url":"URL Pattern Analysis",
    "redirect":"Redirect Chain","headers":"HTTP Security Headers",
}

def run_all_checks(url):
    parsed   = urlparse(url)
    hostname = parsed.hostname or ""
    nh = lambda s,m,sc: {"status":s,"message":m,"score":sc}
    return {
        "https":    check_https(url),
        "ssl":      check_ssl(hostname)        if hostname else nh("danger","No hostname",-30),
        "dns":      check_dns(hostname)        if hostname else nh("danger","No hostname",-30),
        "domain":   check_domain_age(hostname) if hostname else nh("warning","Skipped",0),
        "url":      check_url_patterns(url, hostname),
        "redirect": check_redirects(url),
        "headers":  check_security_headers(url),
    }

def compute_score(results):
    return max(0, min(100, 50 + sum(r["score"] for r in results.values())))

def verdict_from_score(score):
    if score >= 70: return "SAFE",       "🟢","#4ade80","score-safe",   "wb-safe"
    if score >= 40: return "SUSPICIOUS", "🟡","#fbbf24","score-warning","wb-warn"
    return               "DANGEROUS",   "🔴","#f87171","score-danger", "wb-danger"

def add_to_wallet(url, score, verdict, wb_cls):
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {"url":url,"score":score,"verdict":verdict,"wb_cls":wb_cls,"time":now}
    for i, item in enumerate(st.session_state.wallet):
        if item["url"] == url:
            st.session_state.wallet[i] = entry
            file_save(st.session_state.wallet)
            return
    st.session_state.wallet.insert(0, entry)
    file_save(st.session_state.wallet)


# ─── UI ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1><span class="alpha">Alpha</span> <span class="checker">Checker</span></h1>
    <p>// Deep URL security analysis engine</p>
</div>
""", unsafe_allow_html=True)

wallet_count = len(st.session_state.wallet)
tab_scanner, tab_wallet, tab_settings = st.tabs([
    "🔬  Scanner",
    f"💼  Wallet  ({wallet_count})",
    "⚙️  Settings",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – SCANNER
# ══════════════════════════════════════════════════════════════════════════════
with tab_scanner:
    col1, col2 = st.columns([4,1])
    with col1:
        url_input = st.text_input("URL", placeholder="https://example.com", label_visibility="collapsed")
    with col2:
        scan_btn = st.button("SCAN", use_container_width=True)
    st.markdown("---")

    if scan_btn and url_input:
        url = normalize_url(url_input)
        st.markdown(f'<div class="url-display">🔗 {url}</div>', unsafe_allow_html=True)

        with st.spinner("Running security checks..."):
            t0 = time.time()
            results = run_all_checks(url)
            elapsed = time.time() - t0

        score = compute_score(results)
        verdict, emoji, color, score_cls, wb_cls = verdict_from_score(score)
        add_to_wallet(url, score, verdict, wb_cls)

        st.markdown(f"""
        <div class="{score_cls}">
            <div class="score-number" style="color:{color}">{score}</div>
            <div class="score-label" style="color:{color}">{emoji} {verdict}</div>
            <div style="color:#64748b;font-size:.78rem;font-family:'Space Mono',monospace;margin-top:.5rem">
                Safety Score / 100 &nbsp;·&nbsp; Scanned in {elapsed:.1f}s
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">▸ Detailed Checks</div>', unsafe_allow_html=True)
        for key, result in results.items():
            icon, badge_cls = STATUS_ICON.get(result["status"], ("❓","badge-info"))
            st.markdown(f"""
            <div class="check-card">
                <div class="check-icon {badge_cls}">{icon}</div>
                <div>
                    <div class="check-title {badge_cls}">{CHECK_NAMES.get(key, key.upper())}</div>
                    <div class="check-detail">{result['message']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        dangers  = sum(1 for r in results.values() if r["status"]=="danger")
        warnings = sum(1 for r in results.values() if r["status"]=="warning")
        safes    = sum(1 for r in results.values() if r["status"]=="safe")
        st.markdown("---")
        c1,c2,c3 = st.columns(3)
        c1.metric("🚨 Critical", dangers)
        c2.metric("⚠️ Warnings", warnings)
        c3.metric("✅ Passed",   safes)

        st.markdown('<div class="section-title">▸ Recommendation</div>', unsafe_allow_html=True)
        if score >= 70:   st.success("✅ This URL appears to be **safe**. Standard precautions still apply.")
        elif score >= 40: st.warning("⚠️ **Proceed with caution.** Some suspicious signals detected.")
        else:             st.error("🚨 **Do NOT visit this site.** Multiple high-risk indicators detected.")
        st.info("💾 Saved to Wallet – persists across page reloads.", icon="📌")

    elif scan_btn and not url_input:
        st.warning("Please enter a URL to scan.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – WALLET
# ══════════════════════════════════════════════════════════════════════════════
with tab_wallet:
    wallet = st.session_state.wallet
    if not wallet:
        st.markdown("""
        <div class="empty-wallet">
            <div class="icon">💼</div>
            <div>No scans yet.</div>
            <div style="margin-top:.4rem;color:#1e293b">
                Scan a URL – it will appear here and persist across reloads.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        total  = len(wallet)
        n_safe = sum(1 for w in wallet if w["verdict"]=="SAFE")
        n_warn = sum(1 for w in wallet if w["verdict"]=="SUSPICIOUS")
        n_dang = sum(1 for w in wallet if w["verdict"]=="DANGEROUS")
        avg_sc = round(sum(w["score"] for w in wallet) / total)

        s1,s2,s3,s4,s5 = st.columns(5)
        for col, num, label, color in [
            (s1,total,"TOTAL","#94a3b8"),(s2,n_safe,"SAFE","#4ade80"),
            (s3,n_warn,"SUSPICIOUS","#fbbf24"),(s4,n_dang,"DANGEROUS","#f87171"),
            (s5,avg_sc,"AVG SCORE","#38bdf8"),
        ]:
            col.markdown(f'<div class="wstat"><div class="wstat-num" style="color:{color}">{num}</div><div class="wstat-label">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        col_f1, col_f2 = st.columns([3,1])
        with col_f1:
            filter_opt = st.selectbox("Filter", ["All","SAFE","SUSPICIOUS","DANGEROUS"], label_visibility="collapsed")
        with col_f2:
            if st.button("🗑 Clear All", use_container_width=True):
                st.session_state.wallet = []
                file_save([])
                st.rerun()

        st.markdown('<div class="section-title">▸ Scanned URLs</div>', unsafe_allow_html=True)
        filtered = wallet if filter_opt=="All" else [w for w in wallet if w["verdict"]==filter_opt]

        if not filtered:
            st.markdown(f'<p style="color:#475569;font-family:Space Mono,monospace;font-size:.85rem;padding:1rem 0">No results for: {filter_opt}</p>', unsafe_allow_html=True)
        else:
            for idx, entry in enumerate(filtered):
                st.markdown(f"""
                <div class="wallet-card">
                    <div class="wallet-url">🔗 {entry['url']}</div>
                    <div class="wallet-meta">
                        <span class="wallet-badge {entry['wb_cls']}">{entry['verdict']}</span>
                        <span class="wallet-score">Score: <b>{entry['score']}</b>/100</span>
                        <span class="wallet-time">🕐 {entry['time']}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                _, del_col = st.columns([6,1])
                with del_col:
                    if st.button("✕", key=f"del_{idx}_{entry['url']}", help="Remove"):
                        st.session_state.wallet = [w for w in st.session_state.wallet if w["url"] != entry["url"]]
                        file_save(st.session_state.wallet)
                        st.rerun()

        st.markdown("---")
        st.markdown('<div class="section-title">▸ Export Wallet</div>', unsafe_allow_html=True)
        st.download_button(
            label="⬇️  Download as JSON",
            data=json.dumps(wallet, ensure_ascii=False, indent=2),
            file_name=f"alpha_checker_wallet_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab_settings:
    st.markdown('<div class="section-title">▸ Storage Info</div>', unsafe_allow_html=True)

    file_exists = os.path.exists(WALLET_FILE)
    file_size   = os.path.getsize(WALLET_FILE) if file_exists else 0
    file_mtime  = datetime.fromtimestamp(os.path.getmtime(WALLET_FILE)).strftime("%Y-%m-%d %H:%M:%S") if file_exists else "Not created yet"

    st.markdown(f"""
    <div class="storage-info">
        <div class="storage-row">
            <span class="storage-key">📁 Storage method</span>
            <span class="storage-val">Local JSON file (disk)</span>
        </div>
        <div class="storage-row">
            <span class="storage-key">📄 File name</span>
            <span class="storage-val">wallet_data.json</span>
        </div>
        <div class="storage-row">
            <span class="storage-key">🔢 Total entries</span>
            <span class="storage-val">{len(st.session_state.wallet)}</span>
        </div>
        <div class="storage-row">
            <span class="storage-key">💾 File size</span>
            <span class="storage-val">{file_size:,} bytes</span>
        </div>
        <div class="storage-row">
            <span class="storage-key">🕐 Last saved</span>
            <span class="storage-val">{file_mtime}</span>
        </div>
        <div class="storage-row">
            <span class="storage-key">✅ Persists on reload</span>
            <span class="storage-val">Yes – always</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">▸ Factory Reset</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="reset-box">
        <div class="reset-box-title">⚠️ Danger Zone</div>
        <div class="reset-box-desc">
            Factory Reset will permanently delete:<br>
            &nbsp;• All scanned URLs stored in the Wallet<br>
            &nbsp;• The wallet_data.json file from disk<br>
            &nbsp;• All session data in memory<br><br>
            This action <b>cannot be undone</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.factory_reset_confirmed:
        if st.button("🔴  Factory Reset – Clear All Data", use_container_width=True):
            st.session_state.factory_reset_confirmed = True
            st.rerun()
    else:
        st.error("⚠️ **Are you sure?** This will permanently delete all wallet data from disk.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Yes, reset everything", use_container_width=True):
                file_clear()
                st.session_state.wallet = []
                st.session_state.factory_reset_confirmed = False
                st.success("✅ Factory reset complete. wallet_data.json deleted.")
                st.rerun()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.factory_reset_confirmed = False
                st.rerun()

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#ffffff;font-size:.75rem;font-family:'Space Mono',monospace;padding:2rem 0 1rem">
    Alpha Checker v1.0 · Data saved to wallet_data.json · No external transmission
</div>
""", unsafe_allow_html=True)