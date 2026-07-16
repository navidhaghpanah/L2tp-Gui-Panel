# L2TP VPN + GUI Panel (Farsi)

نصب یک‌مرحله‌ای سرور **L2TP/IPsec** به‌همراه **پنل وب فارسی** برای مدیریت کاربران، سهمیه ترافیک، محدودیت زمانی و پایش مصرف.

## 🚀 نصب سریع (One-Click)

روی یک سرور تازه Ubuntu 20.04/22.04/24.04 به‌صورت روت اجرا کنید:

```bash
curl -fsSL https://raw.githubusercontent.com/navidhaghpanah/L2tp-Gui-Panel/main/install.sh -o install.sh && sudo bash install.sh
```

اسکریپت این موارد را می‌پرسد: دامنه، ایمیل SSL، نام‌کاربری/رمز پنل، PSK و اولین کاربر VPN.

### نصب کاملاً خودکار (بدون سؤال)

```bash
curl -fsSL https://raw.githubusercontent.com/navidhaghpanah/L2tp-Gui-Panel/main/install.sh -o install.sh
sudo DOMAIN=l2tp.example.com EMAIL=you@mail.com \
     PANEL_USER=admin PANEL_PASS='StrongPass!' \
     VPN_PSK='MySharedKey' V1USER=user1 V1PASS='pass1' \
     bash install.sh
```

> **پیش‌نیاز:** دامنه باید به IP سرور اشاره کند و پورت‌های **UDP 500/4500** و **TCP 80/443** در فایروال/Security Group باز باشند.

## ✨ امکانات
- افزودن/حذف کاربر از پنل وب
- **سهمیه ترافیک** برای هر کاربر (گیگابایت)
- **محدودیت زمانی / انقضا** برای هر کاربر (روز) + دکمه تمدید
- **تک‌نشست** (هر کاربر فقط یک اتصال هم‌زمان)
- **محدودیت پهنای‌باند**: دانلود ۲۰۰ / آپلود ۲۰ مگابیت
- قطع و بلاک خودکار هنگام اتمام حجم یا انقضا
- صفحه ورود اختصاصی + **SSL خودکار (Let's Encrypt)**
- رابط فارسی RTL، تاریخ شمسی، پایش مصرف زنده

## 🧩 اجزا
| فایل | توضیح |
|------|-------|
| `install.sh` | نصب‌کننده کامل |
| `vpn-panel.py` | پنل وب (پورت داخلی 8088، پشت nginx) |
| `vpn-enforce.py` | سرویس اعمال محدودیت حجم/زمان |

## 🔧 مدیریت دستی
- کاربران: `/etc/ppp/chap-secrets`
- سهمیه/انقضا: `/var/lib/vpnstat/meta.json`
- مصرف: `/var/lib/vpnstat/usage.json`
- سرویس‌ها: `systemctl status vpn-panel vpn-enforce`

## ⚠️ امنیت
حتماً هنگام نصب رمزهای قوی برای پنل و PSK انتخاب کنید. L2TP پروتکل قدیمی است؛ برای امنیت بیشتر IKEv2/WireGuard را در نظر بگیرید.
