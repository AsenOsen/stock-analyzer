import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from jinja2 import Environment, FileSystemLoader, Template
import sys
import os
import json

HOME_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
stocksData = json.load(open(f'{HOME_DIR}/data.json'))

def _render_template(template:str, **args):
    template = Environment(loader=FileSystemLoader(f'{HOME_DIR}/templates')).get_template(template)
    return template.render(args)

def start(update, context):
    logging.getLogger('START').info(update)
    update.message.reply_text(_render_template('start'), parse_mode= 'HTML')

def help(update, context):
    logging.getLogger('HELP').info(update)
    update.message.reply_text( _render_template('help'), parse_mode= 'HTML')

def render_ticker_report(ticker):
    ticker = ticker.upper()
    report = stocksData.get(ticker)
    if not report:
        return None
    return _render_template('ticker', ticker=ticker, name=report['name'], place=report['place'], total=report['total'], 
        pluses=report['pluses'], neutrals=report['neutrals'], minuses=report['minuses'], growth_prediction=round(report['prediction']*100))

def ticker(update, context):
    logging.getLogger('TICKER').info(update)
    report = render_ticker_report(update.message.text)
    if report:
        msg = report
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
    #print(render_ticker_report('SNAP'))