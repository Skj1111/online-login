import telebot
from telebot import types
from github import Github
from flask import Flask
import os, threading, random, string

# --- WEB SERVER FOR RENDER (Keep-Alive) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Nexa Mod Bot is Online and Secure!"

def run_web():
    # Render automatically sets the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
# Replace 'YOUR_BOT_TOKEN' with the token from @BotFather
TELEGRAM_TOKEN = '8843405427:AAHXSRDJyVqNqP5FUl0bZgic_xeRSNOc30w'

# Replace 'YOUR_GITHUB_TOKEN' with your Personal Access Token (PAT)
GITHUB_TOKEN = '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'

REPO_NAME = 'Skj1111/online-login'
FILE_KEYS = 'keys.txt'
FILE_ADMINS = 'admins.txt'
SUPER_ADMIN = 6261701933  # Your Verified Telegram ID

bot = telebot.TeleBot(TELEGRAM_TOKEN)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- GLOBAL TEMP STORAGE FOR REFERRALS ---
TEMP_TOKENS = {}

# --- UTILITIES ---
def generate_random_str(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_file_content(path):
    try:
        file = repo.get_contents(path)
        return file.decoded_content.decode().splitlines(), file.sha
    except:
        return [], None

def is_authorized(user_id):
    if user_id == SUPER_ADMIN: return True
    admins, _ = get_file_content(FILE_ADMINS)
    return str(user_id) in admins

# --- MENU HANDLERS ---
@bot.message_handler(commands=['start'])
def main_menu(message):
    if not is_authorized(message.from_user.id):
        return bot.reply_to(message, "❌ Access Denied! Please use `/Rg <token>` to register.")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔑 Key Generate", callback_data="btn_gen"),
        types.InlineKeyboardButton("❌ Key Block", callback_data="btn_block"),
        types.InlineKeyboardButton("🗑️ Delete Keys", callback_data="btn_del"),
        types.InlineKeyboardButton("👥 Bot Referral", callback_data="btn_ref")
    )
    bot.send_message(message.chat.id, "🔱 *NEXA MOD MASTER MENU* 🔱\nWelcome Admin!", 
                     parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['Rg'])
def register_referral(message):
    try:
        token = message.text.split()[1]
        if token in TEMP_TOKENS:
            admins, sha = get_file_content(FILE_ADMINS)
            user_id = str(message.from_user.id)
            if user_id not in admins:
                admins.append(user_id)
                content = "\n".join(admins)
                if sha:
                    repo.update_file(FILE_ADMINS, f"Add admin {user_id}", content, sha)
                else:
                    repo.create_file(FILE_ADMINS, "Create admins file", content)
                
                del TEMP_TOKENS[token]
                bot.reply_to(message, "✅ Registration Successful! Type /start to open menu.")
            else:
                bot.reply_to(message, "⚠️ You are already an authorized admin.")
        else:
            bot.reply_to(message, "❌ Invalid or Expired Access Token.")
    except:
        bot.reply_to(message, "❌ Usage: `/Rg YOUR_TOKEN`", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if not is_authorized(call.from_user.id): return
    
    if call.data == "btn_gen":
        msg = bot.send_message(call.message.chat.id, "🔢 Quantity batayein (1-1000):")
        bot.register_next_step_handler(msg, process_key_generation)
        
    elif call.data == "btn_block" or call.data == "btn_del":
        keys, _ = get_file_content(FILE_KEYS)
        if not keys: return bot.answer_callback_query(call.id, "Database is empty!")
        
        markup = types.InlineKeyboardMarkup()
        action = "BLOCK" if call.data == "btn_block" else "DELETE"
        # Limit display to avoid menu character limits
        for k in keys[:30]:
            markup.add(types.InlineKeyboardButton(k, callback_data=f"act_{action}_{k}"))
        bot.edit_message_text(f"Select a Key to {action}:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "btn_ref":
        token = generate_random_str(8)
        TEMP_TOKENS[token] = True
        bot.send_message(call.message.chat.id, f"🎟️ *Unique Access Token:* `{token}`\n\nNaye user ko `/Rg {token}` bhejne ko kahein.", parse_mode='Markdown')

    elif call.data.startswith("act_"):
        _, action, key = call.data.split("_")
        keys, sha = get_file_content(FILE_KEYS)
        if key in keys:
            keys.remove(key)
            repo.update_file(FILE_KEYS, f"{action} key {key}", "\n".join(keys), sha)
            bot.edit_message_text(f"✅ Key `{key}` {action}ED successfully!", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

def process_key_generation(message):
    try:
        qty = int(message.text)
        if 1 <= qty <= 1000:
            keys, sha = get_file_content(FILE_KEYS)
            new_keys = [generate_random_str(10) for _ in range(qty)]
            updated_content = "\n".join(keys + new_keys)
            repo.update_file(FILE_KEYS, f"Generate {qty} keys", updated_content, sha)
            
            # Send keys back to admin
            bot.send_message(message.chat.id, f"✅ {qty} Keys Generated & Uploaded!\n\n`" + "\n".join(new_keys) + "`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Limit: 1-1000.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid input.")

if __name__ == "__main__":
    # Start Web Server in background
    threading.Thread(target=run_web).start()
    # Start Telegram Bot
    print("Bot is starting...")
    bot.polling(none_stop=True)
