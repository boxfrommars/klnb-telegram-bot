import logging
import random


logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def echo(update, context):

    reply = False

    if update.message is None:
        logger.warning('Empty message text')
        return

    if 'айфон' in update.message.text.lower():
        reply = random.choice([
            'Похоже, тут необходимо некое алаверды',
            'Может всё же алаверды?',
            'Мы начали забывать о старинном обычае (алаверды)',
            'Много слов, мало алаверды',
            'Своеобразное алаверды, пожалуйста'
        ])

    if 'алаверд' in update.message.text.lower():
        reply = random.choice([
            '+++',
            '<3'
        ])

    if any(s in update.message.text.lower() for s in ['кубан']):
        reply = random.choice([
            'Ой, в моем сердце ты, Кубань!',
            'Слава Кубани!',
            'Юго-Восточная Европа — это мы!',
            'Ты Кубань, ты наша родина!',
            'Мы живем в лучшем крае, солнечном рае!',
            'Если есть на свете рай — это Краснодарский край!'
        ])

    if any(s in update.message.text.lower() for s in ['краснодар', 'крд']):
        reply = random.choice([
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
        ])

    if reply:
        update.message.reply_text(text=reply)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

