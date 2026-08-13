import telebot
from telebot import types
from github import Github
from flask import Flask
import os, threading, random, string, time

# --- WEB SERVER (Render Keep-Alive) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Nexa Mod Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- SECURE CONFIG (From Render Environment Variables) ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = 'Skj1111/online-login'
FILE_KEYS = 'keys.txt'
FILE_ADMINS = 'admins.txt'
SUPER_ADMIN = 6261701933

bot = telebot.TeleBot(TELEGRAM_TOKEN)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

TEMP_TOKENS = {}

# --- UTILS ---
def generate_random_str(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_file_content(path):
    try:
        file = repo.get_contents(path)
        return file.decoded_content.decode().splitlines(), file.sha
    except: return [], None

def is_authorized(user_id):
    if user_id == SUPER_ADMIN: return True
    admins, _ = get_file_content(FILE_ADMINS)
    return str(user_id) in admins

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def main_menu(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Access Denied! Use /Rg <token> to register.")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔑 Key Generate", callback_data="btn_gen"))
    markup.add(types.InlineKeyboardButton("❌ Key Block", callback_data="btn_block"))
    markup.add(types.InlineKeyboardButton("🗑️ Delete Keys", callback_data="btn_del"))
    markup.add(types.InlineKeyboardButton("👥 Bot Referral", callback_data="btn_ref"))
    bot.send_message(message.chat.id, "🔱 *NEXA MASTER MENU*", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['Rg'])
def register(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "❌ Usage: /Rg <token>")
    token = args[1]
    if token in TEMP_TOKENS:
        admins, sha = get_file_content(FILE_ADMINS)
        if str(message.from_user.id) not in admins:
            admins.append(str(message.from_user.id))
            repo.update_file(FILE_ADMINS, "Add Admin", "\n".join(admins), sha)
            del TEMP_TOKENS[token]
            bot.reply_to(message, "✅ Registration Successful! Type /start")
    else: bot.reply_to(message, "❌ Invalid or Expired Token!")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "btn_gen":
        msg = bot.send_message(call.message.chat.id, "🔢 How many keys to generate? (1-1000)")
        bot.register_next_step_handler(msg, process_key_generation)
    elif call.data == "btn_ref":
        token = generate_random_str(8)
        TEMP_TOKENS[token] = True
        bot.send_message(call.message.chat.id, f"🎟️ *Referral Token:* `{token}`\nSend this to your friend to use with /Rg", parse_mode='Markdown')
    # Add other handlers for block/delete as needed

def process_key_generation(message):
    try:
        qty = int(message.text)
        keys, sha = get_file_content(FILE_KEYS)
        new_keys = [generate_random_str(10) for _ in range(qty)]
        repo.update_file(FILE_KEYS, f"Gen {qty} keys", "\n".join(keys + new_keys), sha)
        bot.send_message(message.chat.id, f"✅ {qty} Keys Generated!\n\n`" + "\n".join(new_keys) + "`", parse_mode='Markdown')
    except: bot.send_message(message.chat.id, "❌ Invalid input.")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.polling(none_stop=True)
    
