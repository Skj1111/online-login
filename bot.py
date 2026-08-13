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

# --- CONFIGURATION ---
# ⚠️ Yahan apne asli tokens daalein (Ya Render Environment Variables use karein)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8843405427:AAHXSRDJyVqNqP5FUl0bZgic_xeRSNOc30w')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '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')
REPO_NAME = 'Skj1111/online-login'
FILE_KEYS = 'keys.txt'
FILE_ADMINS = 'admins.txt'
SUPER_ADMIN = 6261701933

bot = telebot.TeleBot(TELEGRAM_TOKEN)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

TEMP_TOKENS = {}

# --- UTILS ---
def generate_random_str(length=10):
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
    if not is_authorized(call.from_user.id): return
    
    if call.data == "btn_gen":
        msg = bot.send_message(call.message.chat.id, "🔢 How many keys to generate? (1-1000)")
        bot.register_next_step_handler(msg, process_key_generation)
    
    elif call.data == "btn_ref":
        token = generate_random_str(8)
        TEMP_TOKENS[token] = True
        bot.send_message(call.message.chat.id, f"🎟️ *Referral Token:* `{token}`\nSend this to your friend to use with /Rg", parse_mode='Markdown')
    
    elif call.data == "btn_block" or call.data == "btn_del":
        keys, _ = get_file_content(FILE_KEYS)
        if not keys: return bot.send_message(call.message.chat.id, "❌ No keys found!")
        markup = types.InlineKeyboardMarkup()
        for k in keys[:10]: # Show first 10 keys
            action = "block" if call.data == "btn_block" else "del"
            markup.add(types.InlineKeyboardButton(f"{k}", callback_data=f"act_{action}_{k}"))
        bot.send_message(call.message.chat.id, "Select a key:", reply_markup=markup)

    elif call.data.startswith("act_"):
        _, action, key = call.data.split("_")
        keys, sha = get_file_content(FILE_KEYS)
        if key in keys:
            keys.remove(key)
            repo.update_file(FILE_KEYS, f"{action} {key}", "\n".join(keys), sha)
            bot.edit_message_text(f"✅ Key `{key}` {action}ED!", call.message.chat.id, call.message.message_id)

def process_key_generation(message):
    try:
        qty = int(message.text)
        if 1 <= qty <= 1000:
            keys, sha = get_file_content(FILE_KEYS)
            new_batch = [generate_random_str(10) for _ in range(qty)]
            repo.update_file(FILE_KEYS, f"Gen {qty} keys", "\n".join(keys + new_batch), sha)
            bot.send_message(message.chat.id, f"✅ {qty} Keys Generated!\n\n`" + "\n".join(new_batch) + "`", parse_mode='Markdown')
        else: bot.send_message(message.chat.id, "❌ Limit: 1-1000.")
    except: bot.send_message(message.chat.id, "❌ Invalid input.")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.polling(none_stop=True)
    
