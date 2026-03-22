# 🔬 Alpha Checker

> **A local URL security analysis tool built with Python & Streamlit.**  
> Instantly scan any link and get a detailed safety report — no external APIs, no data sent anywhere.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?style=flat-square&logo=streamlit)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

---

## ✨ Features

- 🔒 **7-point security analysis** on every URL you submit
- 💼 **Persistent Wallet** — scanned URLs are saved to disk and survive page reloads
- 📊 **Safety Score (0–100)** with a clear SAFE / SUSPICIOUS / DANGEROUS verdict
- 🗂️ **Filter & manage** your scan history directly from the Wallet tab
- ⬇️ **Export wallet** as a JSON file anytime
- ⚙️ **Factory Reset** option to wipe all stored data with one click
- 🚫 **100% local** — no accounts, no cloud, no external data transmission

---

## 🛡️ Security Checks Performed

| # | Check | Description |
|---|-------|-------------|
| 1 | **HTTPS Protocol** | Is the connection encrypted? |
| 2 | **SSL Certificate** | Is the certificate valid? How many days until expiry? |
| 3 | **DNS Resolution** | Does the domain actually exist? |
| 4 | **Domain Age (WHOIS)** | New domains are flagged as suspicious |
| 5 | **URL Pattern Analysis** | Detects phishing keywords, suspicious TLDs, IP-as-hostname, @ tricks |
| 6 | **Redirect Chain** | Flags unusually long or suspicious redirect chains |
| 7 | **HTTP Security Headers** | Checks for HSTS, CSP, X-Frame-Options, X-Content-Type |

### Scoring System

| Score | Verdict |
|-------|---------|
| 70 – 100 | 🟢 **SAFE** |
| 40 – 69 | 🟡 **SUSPICIOUS** |
| 0 – 39 | 🔴 **DANGEROUS** |

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher — https://www.python.org/downloads/

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/alpha-checker.git
cd alpha-checker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open your browser at **http://localhost:8501**

---

## 🗂️ Project Structure

```
alpha-checker/
├── app.py                  # Main Streamlit application
├── wallet_data.json        # Auto-created on first scan (persistent storage)
├── requirements.txt        # Python dependencies
├── install_windows.bat     # Windows one-click installer
├── install_mac.sh          # macOS / Linux installer
└── README.md
```

---

<img width="1129" height="548" alt="Screenshot 2026-03-22 at 11 24 10 PM" src="https://github.com/user-attachments/assets/e8250fbb-923a-40e9-9daf-4d723a576bd7" />


## 🧰 Tech Stack

| Library | Purpose |
|---------|---------|
| Streamlit | Web UI framework |
| Requests | HTTP requests and header fetching |
| dnspython | DNS resolution checks |
| python-whois | Domain age lookup |
| tldextract | TLD parsing |
| ssl / socket | SSL certificate verification (stdlib) |
| json / os | Local disk persistence (stdlib) |

---

## 💾 Data Storage

Alpha Checker stores your scan history in a local file `wallet_data.json` placed next to `app.py`. No data ever leaves your machine.

- **On scan** — entry is written to disk immediately
- **On reload** — wallet is loaded from disk automatically
- **Factory Reset** (Settings tab) — deletes `wallet_data.json` permanently

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

Built with Python and Streamlit · Alpha Checker v1.0
