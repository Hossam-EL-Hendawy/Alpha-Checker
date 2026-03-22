# 🛡️ LinkGuard – URL Safety Checker

أداة Python لفحص أمان أي رابط عبر واجهة Streamlit.

## التثبيت

```bash
cd url_checker
pip install -r requirements.txt
```

## التشغيل

```bash
streamlit run app.py
```

ثم افتح: http://localhost:8501

## الفحوصات المُنجَزة

| الفحص | الوصف |
|-------|--------|
| ✅ HTTPS | هل الاتصال مشفر؟ |
| ✅ SSL Certificate | هل الشهادة صالحة وغير منتهية؟ |
| ✅ DNS Resolution | هل الدومين موجود فعلاً؟ |
| ✅ Domain Age (WHOIS) | هل الدومين جديد (مريب) أم قديم (موثوق)؟ |
| ✅ URL Pattern Analysis | فحص كلمات التصيد، TLD خطير، IP كـ hostname |
| ✅ Redirect Chain | هل يوجد redirect مريب أو طويل؟ |
| ✅ HTTP Security Headers | HSTS, CSP, X-Frame-Options… |

## نظام النقاط

- **70–100**: آمن 🟢
- **40–69**: مشبوه ⚠️
- **0–39**: خطر 🔴
