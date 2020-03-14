import json
import logging
import os
import random
import re
from datetime import datetime
from operator import itemgetter
from typing import Callable

import feedparser
import requests
from dateutil import tz
from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from conversations.two_men_talk import TwoMenTalkConversation
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
    'cruise': {'delay': 60}
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


def cruise_info(update: Update, context: CallbackContext):
    fname = os.environ.get('CRUISE_FILE')

    with open(fname) as json_file:
        data = json.load(json_file)
        message = '```\n'

        for country in data:
            row = data[country]
            message += (
                f"{country:<8} infctd: {row.get('infected'):<5}"
                f"dths: {row.get('deaths'):<3}"
                f"recvrd: {row.get('recovered')}\n")

        message += '```\n'

    needles = ['эстони', 'швеци', 'финлянд', 'хельсинк', 'таллин', 'стокгольм']
    current_tz = tz.gettz('Europe/Moscow')
    dt_format = '%H:%M %d.%m'
    countries_news = []

    # RSS
    feeds = [
            {'url': 'https://rss.newsru.com/russia/', 'dt_format': '%a, %d %b %Y %H:%M:%S %z'},
            {'url': 'https://rss.newsru.com/world/', 'dt_format': '%a, %d %b %Y %H:%M:%S %z'},
            {'url': 'https://www.interfax.ru/rss.asp', 'dt_format': '%a, %d %b %Y %H:%M:%S %z'},
            {'url': 'https://ria.ru/export/rss2/index.xml', 'dt_format': '%a, %d %b %Y %H:%M:%S %z'},
            {'url': 'https://news.yandex.ru/society.rss', 'dt_format': '%d %b %Y %H:%M:%S %z'}
    ]

    for feed in feeds:
        d = feedparser.parse(feed['url'])

        logger.info('%s %s', len(d['entries']), feed['url'])

        for item in d['entries']:
            has_needle_in_title = any(needle in item['title'].lower() for needle in needles)
            has_needle_in_summary = any(needle in item['summary'].lower() for needle in needles)

            if has_needle_in_title or has_needle_in_summary:
                dt = datetime.strptime(item['published'], feed['dt_format']).astimezone(tz=current_tz)
                if ((datetime.now(tz=current_tz) - dt).total_seconds() / (60 * 60)) < 16:
                    countries_news.append({
                        'title': item['title'],
                        'link': item['link'],
                        'published_origin': item['published'],
                        'published': dt.strftime(dt_format),
                        'published_dt': dt
                    })

    # TASS JSON
    news_feed_url = ('https://tass.ru/live/api/v1/get_feed'
                     '?timestamp=1684054129&limit=100&slug=obschestvo'
                     '&theme=%D0%A0%D0%B0%D1%81%D0%BF%D1%80%D0%BE%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0'
                     '%B8%D0%B5%20%D0%BA%D0%BE%D1%80%D0%BE%D0%BD%D0%B0%D0%B2%D0%B8%D1%80%D1%83%D1%81%D0%B0%20'
                     '%D0%BD%D0%BE%D0%B2%D0%BE%D0%B3%D0%BE%20%D1%82%D0%B8%D0%BF%D0%B0')

    tass_news = requests.get(news_feed_url).json().get('data', {}).get('news', [])

    for news_item in tass_news:
        if any(needle in news_item['title'].lower() for needle in needles):
            dt = datetime.fromisoformat(news_item['publish_date']).astimezone(tz=current_tz)
            if ((datetime.now(tz=current_tz) - dt).total_seconds() / (60 * 60)) < 16:
                countries_news.append({
                    'title': news_item['title'],
                    'link': news_item['link'],
                    'published_origin': news_item['publish_date'],
                    'published': dt.strftime(dt_format),
                    'published_dt': dt
                })

    countries_news = sorted(countries_news, key=itemgetter('published_dt'), reverse=True)

    message += '*Последние новости*\n\n'
    for news_item in countries_news:
        newsline = f"{news_item['title']}\n{news_item['published']} | {news_item['link']}\n\n".replace('_', '\\_')
        if (len(message) + len(newsline)) > 4096:
            break
        else:
            message += newsline

    update.message.reply_markdown(text=message, disable_web_page_preview=True)


cruise_handler = MessageHandler(
    regex(r'круиз') & antispam('cruise'),
    cruise_info)
