import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from jinja2 import Environment, FileSystemLoader, Template
import analyzer
import sys
import os


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
# loaded once on first run!
latestData = analyzer.LatestTickersRating()


def _render_template(template:str, **args):
    home = os.path.dirname(os.path.abspath(__file__))
    template = Environment(loader=FileSystemLoader(f'{home}/tgbot/templates')).get_template(template)
    return template.render(args)


def start(update, context):
    logging.getLogger('START').info(update)
    update.message.reply_text(_render_template('start'), parse_mode= 'HTML')


def help(update, context):
    logging.getLogger('HELP').info(update)
    update.message.reply_text( _render_template('help'), parse_mode= 'HTML')


def ticker(update, context):
    logging.getLogger('TICKER').info(update)
    ticker = update.message.text
    report = latestData.getLatestTickerReport(ticker)
    if report:
        msg = _render_template('ticker', ticker=report['ticker'], name=report['name'], place=report['place'], total=report['total'], pluses=report['pluses'], minuses=report['minuses'])
        logging.getLogger('TICKER_RESULT').info('SUCCESS')
    else:
        msg = _render_template('ticker_404') 
        logging.getLogger('TICKER_RESULT').info('FAIL')
    update.message.reply_text(msg, parse_mode= 'HTML')


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