import os
import time
from telethon import TelegramClient, events
from google import genai
from google.genai import types

# ----------------- কনফিগারেশন -----------------
API_ID = 38782586                   # আপনার Telegram API ID (সংখ্যা)
API_HASH = '29cacefdc879e4eac0325c1c67f716cf'  # আপনার Telegram API Hash
GEMINI_API_KEY = 'AQ.Ab8RN6JIbH-HApCyq2UIcnHzUOuo00gfJ8QTiQinykeWFAFPNQ' # গুগল এআই স্টুডিওর ফ্রি API Key

# কুলডাউন (একই ব্যক্তিকে কত সেকেন্ড পর আবার উত্তর দেবে)
COOLDOWN_SECONDS = 180  # ৩ মিনিট

# ----------------- আপনার নিজস্ব নির্দেশাবলি (System Instruction) -----------------
# এখানে আপনি যা লিখে দেবেন, এআই ঠিক সেভাবেই আচরণ করবে:
SYSTEM_INSTRUCTION = """
তুমি আমার পার্সোনাল টেলিগ্রাম অ্যাকাউন্টের পক্ষ থেকে কথা বলছো।
তোমার দায়িত্ব হলো আমার হয়ে নম্র ও সংক্ষেপে উত্তর দেওয়া।

আমার সম্পর্কে প্রয়োজনীয় তথ্য:
- আমার নাম: [আপনার নাম]
- আমি বর্তমানে একটু ব্যস্ত আছি বা বাইরে আছি, তাই সরাসরি মেসেজ দেখতে পারছি না।
- যদি কেউ সালাম দেয় বা কুশল জিজ্ঞেস করে (যেমন: কেমন আছেন, hi): স্বাভাবিকভাবে সালামের উত্তর দেবে এবং বলবে আমি ভালো আছি।
- যদি কেউ কোনো জরুরি কাজ বা সার্ভিসের কথা জানতে চায়: তাকে বলবে মেসেজ দিয়ে রাখতে, আমি অনলাইনে ফিরেই বিস্তারিত জানাবো।
- যদি কেউ এমন কিছু জিজ্ঞেস করে যা এই তথ্যের বাইরে: সরাসরি বানিয়ে কিছু বলবে না; শুধু বলবে "আমি ভাইয়াকে বিষয়টি জানাচ্ছি, উনি এসে উত্তর দেবেন।"
- উত্তর অবশ্যই খুব বড় করবে না, ১-২ বাক্যের মধ্যে সংক্ষিপ্ত ও স্বাভাবিক রাখবে।
"""
# -------------------------------------------------------------------------------

# ক্লায়েন্ট সেটআপ
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
telethon_client = TelegramClient('gemini_userbot_session', API_ID, API_HASH)

user_last_replied = {}

@telethon_client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    # শুধু প্রাইভেট চ্যাটে কাজ করবে
    if not event.is_private:
        return

    sender = await event.get_sender()
    if not sender or sender.is_self or sender.bot:
        return

    user_text = (event.raw_text or "").strip()
    if not user_text:
        return

    user_id = sender.id
    current_time = time.time()

    # কুলডাউন চেক
    if current_time - user_last_replied.get(user_id, 0) < COOLDOWN_SECONDS:
        return

    try:
        # Gemini API কল করা (Gemini 2.5 Flash মডেল ফ্রি এবং অত্যন্ত দ্রুত)
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,  # কম টেম্পারেচার দিলে এআই বানিয়ে কিছু বলবে না, আপনার নিয়মে থাকবে
            )
        )

        reply_text = response.text.strip() if response.text else None

        if reply_text:
            await event.reply(reply_text)
            user_last_replied[user_id] = current_time
            print(f"[{time.strftime('%H:%M:%S')}] Gemini রিপ্লাই দিয়েছে: {sender.first_name} -> {reply_text}")

    except Exception as e:
        print(f"Gemini API বা টেলিগ্রাম এরর: {e}")

print("জেমিনি কানেক্টেড ইউজারবট শুরু হচ্ছে... বন্ধ করতে Ctrl+C চাপুন।")

with telethon_client:
    print("লগইন সফল! আপনার অ্যাকাউন্টে AI অটো-রিপ্লাই সচল আছে।")
    telethon_client.run_until_disconnected()
