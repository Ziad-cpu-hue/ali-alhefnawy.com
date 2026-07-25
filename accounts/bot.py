import os
import django
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔧 إضافة مسار المشروع إلى sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

# 🎯 إعداد إعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Code.settings')  # ← غيره لاسم مشروعك لو مختلف
django.setup()

# 📦 استيراد النماذج
from accounts.models import Student
from django.contrib.auth.models import User

# 🤖 توكن البوت
BOT_TOKEN = '7602255958:AAFAQiMsWphke4GwGb9vWXBxiolJgNi6L-g'

# 🎬 أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    print(f"📩 /start received from: {username} - chat_id: {chat_id}")

    # نحاول نربط الطالب من خلال اليوزرنيم
    student = Student.objects.filter(user__username=username).first()

    if student:
        student.telegram_chat_id = chat_id
        student.save()
        await context.bot.send_message(chat_id=chat_id, text="✅ تم ربط حسابك بنجاح بالمنصة.")
        print(f"✅ Chat ID {chat_id} saved for student: {student.full_name}")
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ لم يتم العثور على حسابك في النظام. تأكد من تسجيلك أو تواصل مع الدعم.")
        print(f"⚠️ No matching student found for username: {username}")

# 🚀 تشغيل البوت
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    print("✅ Bot is now running... Waiting for /start messages.")
    application.run_polling()

if __name__ == '__main__':
    main()
