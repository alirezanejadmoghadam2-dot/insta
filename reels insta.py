import os
import time
import random
import threading
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, MediaNotFound, TwoFactorRequired

# ================================ تنظیمات اصلی ================================

ACCOUNTS = [
    {
        'username': 'ir.hamsar',
        'password': 'armin3254',
        'video_path': 'morakab.mp4',
        'caption': """
می‌خوام بهتون نشون بدم که استراتژی‌ای که بهتون معرفی شده، تا امروز تقریباً صد درصد موفق بوده، ولی با احتیاط ما همون نود درصد رو در نظر می‌گیریم. حالا چطور می‌تونید بدون لورج گرفتن از این استراتژی استفاده کنید؟ چطور می‌تونید بدون لورج گرفتن و فقط با هر پنج روز یک بار باز شدن معامله، طی دو تا سه سال به یک درآمد غیرقابل تصور برسید؟
.
می‌ریم سراغ محاسبه‌ی سپرده‌ی مرکب.
مبلغ سپرده رو فقط ۱۰۰ دلار می‌زنید. شما سرمایه‌ی زیادی نیاز ندارید، فقط همین صد دلار، نه بیشتر. نرخ هر دوره‌ی ما بین پنج تا پانزده درصد متغیره، اما ما میانگین هشت درصد رو در نظر می‌گیریم. سود سالانه هم دقیقا بر اساس همین پایه محاسبه می‌شه. مدت سپرده این‌طوری تعریف می‌شه: هر پنج روز یک بار باز بشه. یعنی تقریباً ۷۳ بار در سال. پس ما ۷۳ پوزیشن در سال خواهیم داشت.
.
نتیجه‌ی سه سال تلاش تیم ما، رسیدن به یک استراتژی صد درصدی بود که به صورت رایگان در اختیارتون گذاشتیم
.
هزینه ای که شما برای ۳ سال کار ما میدین لایک و کامنت و شیر هست. ارادتمند.
"""
    },
]

MIN_WAIT_MINUTES = 25
MAX_WAIT_MINUTES = 65


# =============================================================================

def countdown_timer(seconds, prefix=""):
    total_seconds = int(seconds)
    for i in range(total_seconds, 0, -1):
        mins, secs = divmod(i, 60)
        timer_str = f'{prefix}زمان باقی مانده: {mins:02d}:{secs:02d}'
        print(timer_str, end='\r')
        time.sleep(1)
    print(" " * (len(timer_str) + 5) + "\r", end="")


def warmup_account(cl: Client, username: str):
    try:
        print(f"[{username}] در حال گرم کردن اکانت (شبیه‌سازی رفتار انسانی)...")
        print(f"[{username}] - مشاهده فید اصلی...")
        # <<< تغییر ۳: استفاده از فید اصلی کاربر که قابل اطمینان‌تر است
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
    # <<< تغییر ۱: افزایش زمان انتظار برای درخواست‌ها به ۶۰۰ ثانیه (۱۰ دقیقه)
    cl = Client(request_timeout=5000)

    device_settings_file = Path(f"{username}_device.json")
    session_file = Path(f"{username}_session.json")

    if device_settings_file.exists():
        cl.load_settings(device_settings_file)
        print(f"[{username}] تنظیمات دستگاه بارگذاری شد.")

    login_successful = False
    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.login(username, password)
            print(f"[{username}] با موفقیت از طریق Session قبلی وارد شدید.")
            login_successful = True
        except Exception:
            print(f"[{username}] سشن قبلی نامعتبر بود. تلاش برای ورود مجدد...")
            # اگر سشن خراب بود، اجازه می‌دهیم کد به بخش لاگین اصلی برود
            pass

    if not login_successful:
        try:
            cl.login(username, password)
            login_successful = True
            print(f"[{username}] با موفقیت وارد اکانت شد.")
        except TwoFactorRequired:
            print(f"[{username}] نیاز به تایید دو مرحله‌ای (2FA) دارد.")
            verification_code = input(f"لطفاً کد 6 رقمی را برای اکانت '{username}' وارد کنید: ").strip()
            try:
                cl.login(username, password, verification_code=verification_code)
                login_successful = True
                print(f"[{username}] با موفقیت با کد تایید وارد شدید.")
            except Exception as e_2fa:
                print(f"[{username}] ورود با کد تایید ناموفق بود. خطا: {e_2fa}")
                return
        except Exception as e:
            print(f"[{username}] خطایی جدی در هنگام ورود رخ داد: {e}")
            return

    if login_successful:
        cl.dump_settings(session_file)
        if not device_settings_file.exists():
            cl.dump_settings(device_settings_file)
            print(f"[{username}] تنظیمات دستگاه برای اولین بار ایجاد شد.")
    else:
        return

    while True:
        warmup_account(cl, username)
        time.sleep(random.uniform(15, 40))
        try:
            # <<< تغییر ۲: اضافه کردن پیام قبل از آپلود
            print(f"\n[{username}] در حال آپلود ریلز از فایل '{video_path}'...")
            print(f"[{username}] این فرآیند ممکن است بسته به سرعت اینترنت شما طولانی باشد. لطفاً صبور باشید.")

            cl.clip_upload(path=video_path, caption=caption_text, share_to_feed=False)
            print(f"✅ [{username}] ریلز با موفقیت به صورت آزمایشی آپلود شد!")
        except Exception as e:
            print(f"❌ [{username}] خطایی در هنگام آپلود رخ داد: {e}")

        wait_minutes = random.randint(MIN_WAIT_MINUTES, MAX_WAIT_MINUTES)
        wait_seconds = wait_minutes * 60
        prefix = f"[{username}] استراحت به مدت {wait_minutes} دقیقه. "
        countdown_timer(wait_seconds, prefix)
        print(f"[{username}] زمان استراحت به پایان رسید. آماده برای چرخه بعدی.")


if __name__ == "__main__":
    if not ACCOUNTS or ACCOUNTS[0]['username'] == 'YOUR_USERNAME_1':
        print("خطا: لطفاً اطلاعات اکانت‌ها را به درستی وارد کنید.")
    else:
        random.shuffle(ACCOUNTS)
        threads = []
        print(f"🚀 ربات برای {len(ACCOUNTS)} اکانت با ترتیب تصادفی اجرا می‌شود...")
        for account in ACCOUNTS:
            thread = threading.Thread(target=upload_reel_for_account, args=(account,))
            threads.append(thread)
            thread.start()
            time.sleep(random.uniform(10, 25))
        for thread in threads:
            thread.join()