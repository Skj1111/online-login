import telebot
from github import Github
from flask import Flask
import os, threading, time

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- SECURE CONFIG ---
# Tokens ko Environment Variables se uthaya ja raha hai
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = 'Skj1111/online-login'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Nexa Mod Bot is Securely Connected!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.polling(none_stop=True)
    
