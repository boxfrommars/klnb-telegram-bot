import logging
import random
import re

from telegram.ext import MessageHandler, Filters

from conversations.two_men_talk import TwoMenTalkConversation

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def choice(choices):
    def func(update, context):
        if update.message is None:
            logger.warning('Empty message text')
            return
        update.message.reply_text(text=random.choice(choices))

    return func


two_men_talk = TwoMenTalkConversation()


def collector(update, context):
    if update.message is None:
        logger.warning('Empty message text')
        return

    is_two_men_conversation = two_men_talk.handle(update.message)

    if is_two_men_conversation:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=random.choice(['Мужиками сидим', 'Разговор двух мужчин'])
        )

    logger.info('len: %s %s', update.message.from_user.username, len(two_men_talk.conversation))


weak_handler = MessageHandler(
    Filters.regex(re.compile(r'\bслабо\b', re.IGNORECASE)),
    choice(['Слабейше']))

iphone_handler = MessageHandler(
    Filters.regex(re.compile(r'\bайфон', re.IGNORECASE)),
    choice([
        'Похоже, тут необходимо некое алаверды',
        'Может всё же алаверды?',
        'Мы начали забывать о старинном обычае (алаверды)',
        'Много слов, мало алаверды',
        'Своеобразное алаверды, пожалуйста'
    ]))

alaverdi_handler = MessageHandler(
    Filters.regex(re.compile(r'\bалаверд', re.IGNORECASE)),
    choice(['+++', '<3']))

kuban_handler = MessageHandler(
    Filters.regex(re.compile(r'\bкубан', re.IGNORECASE)),
    choice([
        'Ой, в моем сердце ты, Кубань!',
        'Слава Кубани!',
        'Юго-Восточная Европа — это мы!',
        'Ты Кубань, ты наша родина!',
        'Мы живем в лучшем крае, солнечном рае!',
        'Если есть на свете рай — это Краснодарский край!'
    ]))

krd_handler = MessageHandler(
    Filters.regex(re.compile(r'(\bкраснодар|\bкрд\b)', re.IGNORECASE)),
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
