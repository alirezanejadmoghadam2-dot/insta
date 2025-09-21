import os
import time
import random
import threading
from pathlib import Path
from flask import Flask
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, MediaNotFound, TwoFactorRequired

# ================================ تنظیمات اصلی ================================

ACCOUNTS = [
    {
        'username': 'ir.hamsar',
        'password': 'armin3254',
        'video_path': 'morakab.mp4',
        'caption': """
متن کپشن شما در اینجا قرار می‌گیرد...
"""
    },
    # می‌توانید اکانت‌های بیشتری اضافه کنید
]

MIN_WAIT_MINUTES = 25
MAX_WAIT_MINUTES = 65

# ======================== وب سرور برای زنده نگه داشتن سرویس =======================

app = Flask(__name__)

@app.route('/')
def home():
    """این تابع به درخواست‌های HTTP پاسخ می‌دهد تا Render سرویس را خاموش نکند."""
    return "Bot is alive and running!"

# =============================================================================

# متغیر گلوبال برای کنترل تایمر آپلود
upload_status = {'in_progress': False, 'start_time': 0}

def upload_progress_timer():
    """یک تایمر زمان سپری شده را در حین آپلود نمایش می‌دهد."""
    while upload_status['in_progress']:
        elapsed = time.time() - upload_status['start_time']
        mins, secs = divmod(int(elapsed), 60)
        timer_str = f"[UPLOADING] زمان سپری شده: {mins:02d}:{secs:02d}"
        print(timer_str, end='\r')
        time.sleep(1)
    print(" " * 40 + "\r", end="") # پاک کردن خط تایمر

def countdown_timer(seconds, prefix=""):
    """تایمر شمارش معکوس را برای زمان استراحت نمایش می‌دهد."""
    total_seconds = int(seconds)
    for i in range(total_seconds, 0, -1):
        mins, secs = divmod(i, 60)
        timer_str = f'{prefix}زمان باقی مانده: {mins:02d}:{secs:02d}'
        print(timer_str, end='\r')
        time.sleep(1)
    print(" " * (len(timer_str) + 5) + "\r", end="")

def warmup_account(cl: Client, username: str):
    # ... (این تابع بدون تغییر باقی می‌ماند)
    try:
        print(f"[{username}] در حال گرم کردن اکانت (شبیه‌سازی رفتار انسانی)...")
        print(f"[{username}] - مشاهده فید اصلی...")
        feed_posts = cl.timeline_feed(amount=5)
        time.sleep(random.uniform(3, 7))

        if feed_posts:
            posts_to_like = random.sample(feed_posts, k=min(len(feed_posts), random.randint(1, 2)))
            for post in posts_to_like:
                try:
                    print(f"[{username}] - در حال لایک کردن یک پست تصادفی...")
                    cl.media_like(post.pk)
                    time.sleep(random.uniform(8, 20))
                except Exception:
                    pass
        
        print(f"[{username}] - مشاهده پروفایل شخصی...")
        cl.user_info(cl.user_id)
        time.sleep(random.uniform(4, 9))
        print(f"[{username}] گرم کردن با موفقیت انجام شد.")
        return True
    except Exception as e:
        print(f"[{username}] خطایی در حین گرم کردن اکانت رخ داد: {e}")
        return False

def upload_reel_for_account(account_info):
    username = account_info['username']
    password = account_info['password']
    video_path = account_info['video_path']
    caption_text = account_info['caption']

    if not os.path.exists(video_path):
        print(f"[{username}] خطا: فایل ویدیویی '{video_path}' پیدا نشد.")
        return

    print(f"[{username}] در حال آماده‌سازی ربات...")
    cl = Client(request_timeout=60) # افزایش زمان انتظار به ۳۰ دقیقه

    # ... (بخش لاگین بدون تغییر باقی می‌ماند)
    device_settings_file = Path(f"{username}_device.json")
    session_file = Path(f"{username}_session.json")
    if device_settings_file.exists(): cl.load_settings(device_settings_file)
    login_successful = False
    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.login(username, password)
            print(f"[{username}] با موفقیت از طریق Session قبلی وارد شدید.")
            login_successful = True
        except Exception: pass
    if not login_successful:
        try:
            cl.login(username, password)
            login_successful = True
        except TwoFactorRequired:
            print(f"[{username}] نیاز به تایید دو مرحله‌ای دارد. لطفاً کد را در کنسول Render وارد کنید.")
            verification_code = input(f"کد 6 رقمی برای '{username}': ").strip()
            try:
                cl.login(username, password, verification_code=verification_code)
                login_successful = True
            except Exception as e_2fa: print(f"[{username}] ورود ناموفق بود: {e_2fa}"); return
        except Exception as e: print(f"[{username}] خطا در ورود: {e}"); return
    if login_successful:
        cl.dump_settings(session_file)
        if not device_settings_file.exists(): cl.dump_settings(device_settings_file)
    else: return
    # ... (پایان بخش لاگین)

    while True:
        warmup_account(cl, username)
        time.sleep(random.uniform(15, 40))
        
        progress_thread = None
        try:
            print(f"\n[{username}] در حال آپلود ریلز از فایل '{video_path}'...")
            
            # شروع تایمر زمان سپری شده
            upload_status['start_time'] = time.time()
            upload_status['in_progress'] = True
            progress_thread = threading.Thread(target=upload_progress_timer)
            progress_thread.start()

            cl.clip_upload(path=video_path, caption=caption_text, share_to_feed=False)
            
            # متوقف کردن تایمر
            upload_status['in_progress'] = False
            progress_thread.join() # منتظر می‌مانیم تا ترد تایمر تمام شود
            
            print(f"✅ [{username}] ریلز با موفقیت به صورت آزمایشی آپلود شد!")
        except Exception as e:
            print(f"❌ [{username}] خطایی در هنگام آپلود رخ داد: {e}")
        finally:
            # اطمینان از اینکه تایمر در هر حالتی (موفقیت یا شکست) متوقف می‌شود
            if upload_status['in_progress']:
                upload_status['in_progress'] = False
            if progress_thread and progress_thread.is_alive():
                progress_thread.join()

        wait_minutes = random.randint(MIN_WAIT_MINUTES, MAX_WAIT_MINUTES)
        wait_seconds = wait_minutes * 60
        prefix = f"[{username}] استراحت به مدت {wait_minutes} دقیقه. "
        countdown_timer(wait_seconds, prefix)
        print(f"[{username}] زمان استراحت به پایان رسید.")

def start_bot_threads():
    """تابع اصلی برای راه‌اندازی تردها برای هر اکانت."""
    if not ACCOUNTS or ACCOUNTS[0]['username'] == 'YOUR_USERNAME_1':
        print("خطا: لطفاً اطلاعات اکانت‌ها را به درستی وارد کنید.")
        return

    random.shuffle(ACCOUNTS)
    print(f"🚀 ربات برای {len(ACCOUNTS)} اکانت با ترتیب تصادفی اجرا می‌شود...")
    for account in ACCOUNTS:
        thread = threading.Thread(target=upload_reel_for_account, args=(account,))
        thread.start()
        time.sleep(random.uniform(10, 25))

if __name__ == "__main__":
    # 1. ربات اینستاگرام را در یک ترد جداگانه در پس‌زمینه اجرا کن
    bot_thread = threading.Thread(target=start_bot_threads)
    bot_thread.start()
    
    # 2. وب سرور Flask را در ترد اصلی اجرا کن تا به Render پاسخ دهد
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


