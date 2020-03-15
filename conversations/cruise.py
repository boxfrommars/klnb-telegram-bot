import json
import os
import re
from datetime import datetime, timedelta
from operator import itemgetter

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import tz
from telegram import Update
from telegram.ext import CallbackContext


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
        {'url': 'https://news.yandex.ru/society.rss', 'dt_format': '%d %b %Y %H:%M:%S %z'}
    ]

    for feed in feeds:
        d = feedparser.parse(feed['url'])

        for item in d['entries']:
            has_needle_in_title = any(needle in item['title'].lower() for needle in needles)
            has_needle_in_summary = any(needle in item['summary'].lower() for needle in needles)

            if has_needle_in_title or has_needle_in_summary:
                dt = datetime.strptime(item['published'], feed['dt_format']).astimezone(tz=current_tz)
                countries_news.append({
                    'title': item['title'],
                    'link': item['link'],
                    'published_origin': item['published'],
                    'published': dt.strftime(dt_format),
                    'published_dt': dt
                })

    # TASS JSON
    tass_feed_url = ('https://tass.ru/live/api/v1/get_feed'
                     '?timestamp=1684054129&limit=100&slug=obschestvo'
                     '&theme=%D0%A0%D0%B0%D1%81%D0%BF%D1%80%D0%BE%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0'
                     '%B8%D0%B5%20%D0%BA%D0%BE%D1%80%D0%BE%D0%BD%D0%B0%D0%B2%D0%B8%D1%80%D1%83%D1%81%D0%B0%20'
                     '%D0%BD%D0%BE%D0%B2%D0%BE%D0%B3%D0%BE%20%D1%82%D0%B8%D0%BF%D0%B0')

    tass_news = requests.get(tass_feed_url).json().get('data', {}).get('news', [])

    for news_item in tass_news:
        if any(needle in news_item['title'].lower() for needle in needles):
            dt = datetime.fromisoformat(news_item['publish_date']).astimezone(tz=current_tz)
            countries_news.append({
                'title': news_item['title'],
                'link': news_item['link'],
                'published_origin': news_item['publish_date'],
                'published': dt.strftime(dt_format),
                'published_dt': dt
            })

    # RIA HTML
    base_url = 'https://ria.ru'
    start_urls = [
        f'{base_url}/category_rasprostranenie-novogo-koronavirusa+location_Finland/',
        f'{base_url}/category_rasprostranenie-novogo-koronavirusa+location_Estonia/',
        f'{base_url}/category_rasprostranenie-novogo-koronavirusa+location_Sweden/',
    ]

    countries_news = []
    for start_url in start_urls:
        req = requests.get(start_url)
        soup = BeautifulSoup(req.content, 'html.parser')
        news_items = soup.find("div", id="page").find_all(class_='list-item')

        for news_item in news_items:
            schema_h = news_item.find(class_='schema_org')
            link = schema_h.find(attrs={"itemprop": "url"}).get('content')
            title = schema_h.find(attrs={"itemprop": "name"}).get('content')
            human_dt = news_item.find(class_='list-item__date').get_text()
            dt = parse_datetime(human_dt, current_tz)

            countries_news.append({
                'title': title,
                'link': f'{base_url}{link}',
                'published_origin': human_dt,
                'published': dt.strftime(dt_format),
                'published_dt': dt
            })

    countries_news = sorted(countries_news, key=itemgetter('published_dt'), reverse=True)

    message += '*Последние новости*\n\n'
    for news_item in countries_news:
        if ((datetime.now(tz=current_tz) - news_item['published_dt']).total_seconds() / (60 * 60)) < 16:
            newsline = f"{news_item['title']}\n{news_item['published']} | {news_item['link']}\n\n".replace('_', '\\_')
            if (len(message) + len(newsline)) > 4096:
                break
            else:
                message += newsline

    update.message.reply_markdown(text=message, disable_web_page_preview=True)


def parse_datetime(st, tzinfo):
    monthes_map = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                   'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    time_part = re.findall(r'\d{2}:\d{2}', st)[0].split(':')
    hour = int(time_part[0])
    minutes = int(time_part[1])

    if 'Вчера' in st:
        dt = (datetime.now(tz=tzinfo) - timedelta(days=1)).replace(
            hour=hour, minute=minutes, second=0, microsecond=0
        )
    elif ',' in st:
        datepart = re.findall(r'(.+),', st)[0].split()
        day = int(datepart[0])
        month = int(monthes_map.index(datepart[1])) + 1
        year = 2020
        dt = datetime(year=year, month=month, day=day, hour=hour, minute=minutes, tzinfo=tzinfo)
    else:
        dt = datetime.now(tz=tzinfo).replace(
            hour=hour, minute=minutes, second=0, microsecond=0
        )
    return dt
