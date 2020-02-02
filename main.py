import os
from os.path import join, dirname

from dotenv import load_dotenv
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater

import handlers

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

updater = Updater(token=os.environ.get('TOKEN'), use_context=True)

jq = updater.job_queue
dp = updater.dispatcher

# Handlers
dp.add_handler(CommandHandler('start', handlers.start))
dp.add_handler(MessageHandler(Filters.text, handlers.echo))


# log all errors
dp.add_error_handler(handlers.error)
# Start the Bot
updater.start_polling()
# Run the bot until you press Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT. This should be used most of the time, since
# start_polling() is non-blocking and will stop the bot gracefully.
updater.idle()
