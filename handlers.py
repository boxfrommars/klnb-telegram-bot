import logging
import os
import random
import re

from typing import Callable

from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from conversations.two_men_talk import TwoMenTalkConversation
# from conversations.cruise import cruise_info
from filters.antispam import AntispamFilter, SpamPreventer
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


spam_preventer = SpamPreventer({
    # 'cruise': {'delay': 300},
    # 'labi': {'delay': 60},
})
two_men_talk = TwoMenTalkConversation()


def regex(pattern: str):
    # shorthand for Filters.regex with ignorecase pattern
    return Filters.regex(re.compile(pattern, re.IGNORECASE))


def antispam(group: str = 'default'):
    return AntispamFilter(spam_preventer, group)


def choice(choices: list, content_type: str = 'text') \
        -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext) -> None:
        if update.message is None:
            logger.warning('Empty message text')
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
    regex(r'\bслабо\b') & antispam('weak'),
    choice(['Слабейше']))

iphone_handler = MessageHandler(
    regex(r'\bайфон') & antispam('iphone'),
    choice([
        'Похоже, тут необходимо некое алаверды',
        'Может всё же алаверды?',
        'Мы начали забывать о старинном обычае (алаверды)',
        'Много слов, мало алаверды',
        'Своеобразное алаверды, пожалуйста'
    ]))

alaverdi_handler = MessageHandler(
    regex(r'\bалаверд') & antispam('alaverdi'),
    choice(['+++', '<3']))

sad_handler = MessageHandler(
    regex(r'^:\($') & antispam('sad-cat'),
    choice(['sad-cat.webp'], content_type='photo'))

bodnya_handler = MessageHandler(
    regex(r'(\bбодн)|(\b(бэд(а|у|ом|е)?)\b)') & antispam('bodnya'),
    choice(['bodnya.webp'], content_type='photo'))

awesome_selyan_handler = MessageHandler(
    Filters.user(username='SelianArtem') & Filters.text
    & (~Filters.forwarded) & TextCountFilter(30)
    & antispam('awesome_selyan'),
    choice(['Артём Сергеевич, вашими устами да мёд бы пить']))

labi_handler = MessageHandler(
    regex(r'\bлаби\b') & antispam('labi'),
    choice(['Лаби']))

kuban_handler = MessageHandler(
    regex(r'\bкубан') & antispam('kuban'),
    choice([
        'Ой, в моем сердце ты, Кубань!',
        'Слава Кубани!',
        'Юго-Восточная Европа — это мы!',
        'Ты Кубань, ты наша родина!',
        'Мы живем в лучшем крае, солнечном рае!',
        'Если есть на свете рай — это Краснодарский край!'
    ]))

krd_handler = MessageHandler(
    regex(r'(\bкраснодар)|(\bкрд\b)') & antispam('kuban'),
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
    ]))

cruise_handler = MessageHandler(
    regex(r'круиз') & antispam('cruise'),
    choice([
        'Да никому уже неинтересен этот круиз',
        'Ото жили нормально без всяких круизов и ещё тысячу лет проживём'
    ]))

kashin_handler = MessageHandler(
    regex(r'кашин') & antispam('kashin'),
    choice([
        'Привет пользователю рука в жопе!',
        'Кстати, а как там густопсовые?'
    ]))

# cruise_handler = MessageHandler(
#     regex(r'круиз') & antispam('cruise'),
#     cruise_info)
