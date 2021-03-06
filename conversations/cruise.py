import json
import os
import re
from datetime import datetime, timedelta, date
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

    # EXCHANGE RATES
    exchange_rates_url = 'https://meduza.io/api/misc/stock/all'
    exchange_rates = requests.get(exchange_rates_url).json()

    usd = exchange_rates.get('usd').get('current')
    eur = exchange_rates.get('eur').get('current')
    message += f'`$ {usd} | € {eur}`\n\n'

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
        f'{base_url}/category_-koronavirus-covid-19+location_Finland/',
        f'{base_url}/category_-koronavirus-covid-19+location_Estonia/',
        f'{base_url}/category_-koronavirus-covid-19+location_Sweden/'
    ]

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

            tags = news_item.find_all(class_='list-tag__text')
            tags = list(map(lambda t: t.get_text(), tags))

            about_covid = any('коронавирус' in t.lower() for t in tags)
            about_sport = any('спорт' in t.lower() for t in tags)

            if about_covid and not about_sport:
                countries_news.append({
                    'title': title,
                    'link': f'{base_url}{link}',
                    'published_origin': human_dt,
                    'published': dt.strftime(dt_format),
                    'published_dt': dt
                })

    # MOBY NEWS
    headers = {'Accept-Language': 'ru-RU,ru'}
    req = requests.get('https://stpeterline.com/company-news', headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')

    body = soup.find("div", id="newsMain")
    news_items = body.find_all(class_='one')

    for news_item in news_items:
        # title = news_item.find(class_='name').get_text()
        description = news_item.find(class_='description').get_text()
        link = news_item.find('a').get('href')

        human_dt = news_item.find(class_='date').get_text()
        human_dt_parts = list(map(int, human_dt.split('.')))

        dt = date(year=human_dt_parts[2], month=human_dt_parts[1], day=human_dt_parts[0])
        now = datetime.now(tz=current_tz)

        if dt == now.date():
            dt = now
        else:
            dt = datetime(dt.year, dt.month, dt.day, hour=23, minute=59, second=59, tzinfo=current_tz)

        countries_news.append({
            'title': description,
            'link': f'{link}',
            'published_origin': human_dt,
            'published': dt.strftime(dt_format),
            'published_dt': dt
        })

    countries_news = sorted(countries_news, key=itemgetter('published_dt'), reverse=True)

    message += '*Последние новости*\n\n'
    already_processed = []
    for news_item in countries_news:
        is_fresh = ((datetime.now(tz=current_tz) - news_item['published_dt']).total_seconds() / (60 * 60)) < 16
        is_uniq = news_item['link'] not in already_processed
        if is_fresh and is_uniq:
            newsline = f"{news_item['title']}\n{news_item['published']} | {news_item['link']}\n\n".replace('_', '\\_')
            if (len(message) + len(newsline)) > 4096:
                break
            else:
                already_processed.append(news_item['link'])
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
        datepart = re.findall('(.+),', st)[0].split()
        day = int(datepart[0])
        month = int(monthes_map.index(datepart[1])) + 1
        if len(datepart) == 3:
            year = int(datepart[2])
        else:
            year = datetime.now(tz=tzinfo).year
        dt = datetime(year=year, month=month, day=day, hour=hour, minute=minutes, tzinfo=tzinfo)
    else:
        dt = datetime.now(tz=tzinfo).replace(
            hour=hour, minute=minutes, second=0, microsecond=0
        )
    return dt
