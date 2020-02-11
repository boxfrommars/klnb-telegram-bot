import logging
import os
import random
import re
from typing import Callable

from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from conversations.spam_preventer import SpamPreventer
from conversations.two_men_talk import TwoMenTalkConversation
from filters.text_count import TextCountFilter

logging.basicConfig(
    filename='logs/bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!")


spam_preventer = SpamPreventer()
two_men_talk = TwoMenTalkConversation()


def decision(prob: float = 0.5) -> bool:
    return random.random() < prob


def choice(choices: list, group: str = 'default', content_type: str = 'text', prob: float = 1) \
        -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext) -> None:
        if update.message is None:
            logger.warning('Empty message text')
            return

        if spam_preventer.is_spam(update.message, group):
            logger.info('spam_prevented: %s', group)
            return

        if not decision(prob):
            logger.info('Bot decided to not reply')
            return

        if content_type == 'text':
            update.message.reply_text(text=random.choice(choices))

        if content_type == 'photo':
            current_folder = os.path.dirname(__file__)
            image_src = os.path.join(current_folder, 'media', 'images', random.choice(choices))
            update.message.reply_photo(photo=open(image_src, 'rb'))

    return func


def collector(update: Update, context: CallbackContext) -> None:
    if update.message is None:
        logger.warning('Empty message text')
        return

    is_two_men_conversation = two_men_talk.handle(update.message)

    if is_two_men_conversation:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=random.choice(['Мужиками сидим', 'Разговор двух мужчин'])
        )


def configure(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        logger.warning('empty command')

    command = str(context.args[0])
    message = update.message
    logger.info('command: %s', command)

    if command == 'enable-spam-filter':
        spam_preventer.enable()
        logger.info('Spam filter enabled by %s', message.from_user.username)
        update.message.reply_text('Spam filter enabled')

    if command == 'disable-spam-filter':
        spam_preventer.disable()
        logger.info('Spam filter disabled by %s', message.from_user.username)
        update.message.reply_text('Spam filter disabled')


weak_handler = MessageHandler(
    Filters.regex(re.compile(r'\bслабо\b', re.IGNORECASE)),
    choice(['Слабейше'], 'weak'))

iphone_handler = MessageHandler(
    Filters.regex(re.compile(r'\bайфон', re.IGNORECASE)),
    choice([
        'Похоже, тут необходимо некое алаверды',
        'Может всё же алаверды?',
        'Мы начали забывать о старинном обычае (алаверды)',
        'Много слов, мало алаверды',
        'Своеобразное алаверды, пожалуйста'
    ], 'iphone'))

alaverdi_handler = MessageHandler(
    Filters.regex(re.compile(r'\bалаверд', re.IGNORECASE)),
    choice(['+++', '<3'], 'alaverdi'))

sad_handler = MessageHandler(
    Filters.regex(re.compile(r'^:\($', re.IGNORECASE)),
    choice(['sad-cat.webp'], 'sad-cat', content_type='photo'))

bodnya_handler = MessageHandler(
    Filters.regex(re.compile(r'(\bбодн)|(\b(бэд(а|у|ом|е)?)\b)', re.IGNORECASE)),
    choice(['bodnya.webp'], 'bodnya', content_type='photo'))

awesome_selyan_handler = MessageHandler(
    Filters.user(username='SelianArtem') & Filters.text & (~Filters.forwarded) & TextCountFilter(30),
    choice(['Артём Сергеевич, вашими устами да мёд бы пить'], 'awesome-selyan'))

kuban_handler = MessageHandler(
    Filters.regex(re.compile(r'\bкубан', re.IGNORECASE)),
    choice([
        'Ой, в моем сердце ты, Кубань!',
        'Слава Кубани!',
        'Юго-Восточная Европа — это мы!',
        'Ты Кубань, ты наша родина!',
        'Мы живем в лучшем крае, солнечном рае!',
        'Если есть на свете рай — это Краснодарский край!'
    ], 'kuban'))

krd_handler = MessageHandler(
    Filters.regex(re.compile(r'(\bкраснодар)|(\bкрд\b)', re.IGNORECASE)),
    choice([
        'Ой, в моем сердце ты, Кубань!',
        'Слава Кубани!',
        'Юго-Восточная Европа — это мы!',
        'Ты Кубань, ты наша родина!',
        'Мы живем в лучшем крае, солнечном рае!',
        'Если есть на свете рай — это Краснодарский край!',
        'Славься, славься, город величавый',
        'Славься град Екатерины!',
        'Наш маленький Париж...',
        'Это ж не собачья глушь, а собачкина столица!'
    ], 'kuban'))
