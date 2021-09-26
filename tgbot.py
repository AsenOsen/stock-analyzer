import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from jinja2 import Environment, FileSystemLoader, Template
import analyzer
import sys
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def _render_template(template:str, **args):
    home = os.path.dirname(os.path.abspath(__file__))
    template = Environment(loader=FileSystemLoader(f'{home}/tgbot/templates')).get_template(template)
    return template.render(args)


def start(update, context):
    update.message.reply_text(_render_template('start'), parse_mode= 'HTML')
    logging.getLogger('START').info(update)


def help(update, context):
    update.message.reply_text( _render_template('help'), parse_mode= 'HTML')
    logging.getLogger('HELP').info(update)


def ticker(update, context):
    ticker = update.message.text
    report = analyzer.TickerRating.getTickerReport(ticker)
    msg = _render_template('ticker_404') if not report else _render_template(
        'ticker', ticker=report['ticker'], name=report['name'], place=report['place'], total=report['total'], pluses=report['pluses'], minuses=report['minuses'])
    update.message.reply_text(msg, parse_mode= 'HTML')
    logging.getLogger('TICKER').info(update)


def error(update, context):
    logging.getLogger('ERROR').warning('Update "%s" caused error "%s"', update, context.error)


def startBot(token:str):
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, ticker))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    startBot(sys.argv[1])