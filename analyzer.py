import pymongo
import datetime
import math
import itertools
import argparse

class Storage:
	def __init__(self, date):
		client = pymongo.MongoClient('localhost', 27017)
		db = client.webull
		self.collectionName = date.strftime('tickers_%G_%m_%d')
		if self.collectionName in db.list_collection_names():
			self.collection = db[self.collectionName]
		else:
			raise Exception('collection not exists')

	def select(self, query, aggregate=False):
		data = self.collection.find(query) if not aggregate else self.collection.aggregate(query)
		return list(data)

	def getTicker(self, ticker):
		return self.collection.find_one({'ticker': ticker})


class TickerRating():

	def __init__(self, date):
		self.selector = Storage(date)

	# treat
	def getHoldersInLoss(self):
		return self.selector.select(
			{
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.5}, 
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1.05}
			}
		)

	# treat: no fall bets
	def getOptionsPositive(self):
		return self.selector.select(
			{
				'$and': [
					{'options': {'$exists':True}},
					{'options': {'$not': {'$elemMatch':{'direction': 'down'}}}},
					{'options': {'$not': {'$elemMatch':{'expectedCostToCurrentRatio':{'$lt': 1}}}}}
				]
			}
		)

	# treat
	def getAnalyticsRecommendBuy(self):
		return self.selector.select(
			{
				'anal.buyCountRatio':{'$exists':True, '$gte':0.7}, 
				'anal.buyCount':{'$exists':True, '$gte':5}, 
				'anal.targetCostToCurrentRatio':{'$exists':True, '$gt':1}, 
			}
		)

	# treat
	def getSocialAttitudeGood(self):
		return self.selector.select(
			{
				'social_guess.overall.bullRatio':{'$exists':True, '$gt':0.7}, 
				'social_guess.overall.bulls':{'$exists':True, '$gt':20},
				'heldSharesRatio':{'$gte':0.7}
			}
		)

	# treat: current cost should be better
	def getCostBelowFareCost(self):
		return self.selector.select(
			{
				# growing trend during 1 year and 5 years
				'trend.costTrend1Y':{'$exists':True, '$gt':0}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0},
				# fare cost is below trend for 1 year and 5 years
				'trend.currentCostToFareTrend1YRatio':{'$exists':True, '$lt':0.97}, 
				'trend.currentCostToFareTrend5YRatio':{'$exists':True, '$lt':0.97}
			}
		)

	# treat
	def getStableGrowing(self):
		return self.selector.select(
			{
				'trend.costTrend5Y':{'$exists':True, '$gt':0.01},
				'trend.costTrend1Y':{'$exists':True, '$gt':0.01}
			}
		)

	# treat
	def getTechnicallyGood(self):
		return self.selector.select(
			{
				'pe': {'$exists':True, '$lte': 30, '$gte': 0},
				'eps':{'$exists':True, '$gte':0},
			}
		)		

	# treat: cost trend worse than revenue trend
	def getDevelopingUnderestimated(self):
		return self.selector.select(
			[
				{
					'$addFields':{
						'trend_farness_5Y':{'$subtract':['$income.revenueTrend', '$trend.costTrend5Y']},
						'trend_farness_1Y':{'$subtract':['$income.revenueTrendLatest', '$trend.costTrend1Y']}
					}
				},
				{
					'$match':{
						'income.revenueTrend':{'$exists':True, '$gt':0}, 
						'trend_farness_5Y':{'$gt':0}, 
						'trend_farness_1Y':{'$gt':0}
						}
					}
			], 
			True
		)

	# treat: market occupation increasing because revenue growing from year to year and it keep going
	def getOccupationGrowing(self):
		return self.selector.select(
			{
				'income.revenueTrend':{'$exists':True, '$gt':0.1},
				'income.revenueTrendLatest':{'$exists':True, '$gt':0}
			}
		)

	# treat: company has excessive money after all operating expenses
	def getProfitable(self):
		return self.selector.select(
			{
				'income.netIncome':{'$exists':True, '$gt':0}
			}
		)

	# treat: good managed because more and more money settles on company`s balance
	def getOperatingEffective(self):
		return self.selector.select(
			{
				'income.operatingIncomeYoyTrend':{'$exists':True, '$gt':0},
				'income.operatingIncome':{'$exists':True, '$gt':0}
			}
		)

	# treat: company taking more and more every year
	def getAggressor(self):
		return self.selector.select(
			{
				# latest year trend up
				'income.operatingIncomeYoyTrendLatest':{'$exists':True, '$gt':0},
				'income.revenueYoyTrendLatest':{'$exists':True, '$gt':0},
				# overall trend up
				'income.operatingIncomeYoyTrend':{'$exists':True, '$gt':0},
				'income.revenueYoyTrend':{'$exists':True, '$gt':0}
			}
		)

	# treat: company`s revenue serged to heaven
	def getOccupationGrowthBegan(self):
		return self.selector.select(
			{
				'$expr': {'$gt': ['$income.revenueYoyTrendLatest', '$income.revenueYoyTrend']},
				'income.revenueYoyTrendLatest': {'$exists':True, '$gt':0}
			}
		)

	# treat: possible short squeeze
	def getTightShorts(self):
		return self.selector.select(
			{
				'short.daysToCover':{'$exists':True, '$gte':3.5}
			}
		)

	# treat: soon growth
	def getResistance5dayBreakout(self):
		return self.selector.select(
			{
				'technical.breakout_magnitude':{'$exists':True}
			}
		)

	# treat: insiders know something
	def getInsiderBuying(self):
		return self.selector.select(
			{
				'insiders.purchasedPrice':{'$exists':True}
			}
		)

	# treat: most investors bought recently
	def getMoneyFlowIn(self):
		return self.selector.select(
			{
				'flows.inflowToOutflowRatio':{'$exists':True, '$gt':1.1}
			}
		)

	# treat
	def getDividendsPaying(self):
		return self.selector.select(
			{
				'dividendes.perShare_%':{'$exists':True, '$gt':0}
			}
		)

	# treat: blowing from every corner
	def getHyped(self):
		return self.selector.select(
			{
				'$or':[
					{'social_guess.wsb':{'$exists':True}},
					{'social_guess.robinhood':{'$exists':True}}
				]
			}
		)

	# treat
	def getGoodNewsBackground(self):
		return self.selector.select(
			{
				'beststocksAnalytics.news.bullish':{'$exists':True, '$gte':0.85},
				'beststocksAnalytics.news.attitude':{'$exists':True, "$in":["Positive"]}
			}
		)

	# treat
	def getTopInvestorsBuying(self):
		return self.selector.select(
			{
				'beststocksAnalytics.investorsTopStat.last7DaysTotalChange':{'$exists':True, '$gt':0}
			}
		)

	# treat: lower at least 15% then 52-week highest price
	def getFallen(self):
		return self.selector.select(
			{
				'closenessToHighest':{'$exists':True, '$lte':0.85}
			}
		)

	# treat: good according to alternative analytics
	def getGoodScoreBeststocks(self):
		return self.selector.select(
			{
				'beststocksAnalytics.scoreRatio':{'$exists':True, '$gte':0.75}
			}
		)

	# treat: large purchases was detected (probably hedge funds)
	def getBigFishesBuying(self):
		return self.selector.select(
			{
				'flows.largeflow':{'$exists':True, '$gt':0}
			}
		)

	# treat: good according to alternative analytics
	def getGoodScoreWallst(self):
		return self.selector.select(
			{
				'$or':[
					{
						'wallstAnalytics.totalScoreRatio':{'$gte':0.75}
					},
					{
						'wallstAnalytics.unfairValueRatio':{'$gte':0.75},
						'wallstAnalytics.futurePerformanceRatio':{'$gte':0.75},
						'wallstAnalytics.financialHealthRatio':{'$gte':0.75}
					}
				]
			}
		)

	# treat: technical
	def _any_(self):
		return self.selector.select({})

	def getIndicators():
		return {
			# company is relient
			'getStableGrowing': {'in':'Стабильный рост цены (в течение 1 года и 5 лет)', 'out':'Нет стабильного роста цены (в течение 1 года и 5 лет)'},
			'getOperatingEffective': {'in':'Эффективно управляется (растет темп прибыли из года в год)', 'out':'Неэффективно управляется (темп прибыли не растет из года в год)'},
			'getOccupationGrowing': {'in':'Стабильно захватывает долю рынка (выручка растет из года в год)', 'out':'Стагнирует (выручка не растет из года в год)'},
			'getProfitable': {'in':'Прибыльная', 'out':'Убыточная'},
			# company fall recently
			'getFallen': {'in':'Упала относительно хаев за последний год', 'out':'Близко к хаям за последний год'},
			'getHoldersInLoss': {'in':'Много держателей в минусе', 'out':'Много держателей в плюсе'},
			'getCostBelowFareCost': {'in':'Цена ниже справедливой (той, что должна быть согласно тренду)', 'out':'Цена выше справедливой (той, что должна быть согласно тренду)'},
			'getDevelopingUnderestimated': {'in':'Недооценена (прибыль растет быстрее цены)', 'out':'Переоценена (цена растет быстрее прибыли)'},
			# smart heads interested in company
			'getInsiderBuying': {'in':'Закупаются инсайдеры', 'out':'Инсайдеры не закупались за последнее время'},
			'getTopInvestorsBuying': {'in':'Закупаются лучшие инвесторы', 'out':'Лучшие инвесторы не закупались за последнее время'},
			'getBigFishesBuying': {'in':'Закупаются крупные игроки', 'out':'Крупные игроки не закупались за последнее время'},
			'getAnalyticsRecommendBuy': {'in':'Уверенные рекомендации к покупке от большинства аналитиков', 'out':'Нет уверенных рекомендации к покупке от большинства аналитиков'},
			# company continues growing
			'getOccupationGrowthBegan': {'in':'Замечен скачек захвата доли рынка за последний год', 'out':'За последний год не было скачка захвата доли рынка'},
			'getAggressor': {'in':'Агрессор (активно наращивает прибыль и забирает долю рынка)', 'out':'Заторможенность (не активно наращивает прибыль и долю рынка)'},
			# positve behaviour
			'getOptionsPositive': {'in':'На 100% бычий настрой по опционам', 'out':'Нет на 100% бычьего настроя по опционам'},
			'getGoodNewsBackground': {'in':'Позитивный новостной фон', 'out':'Нет позитивного новостного фона'},
			# independent analitycs postitive
			'getGoodScoreWallst': {'in':'Высокая оценка независимым аналитическим сервисом simplywall.st', 'out':'Невысокая оценка независимым аналитическим сервисом simplywall.st'},
			'getGoodScoreBeststocks': {'in':'Высокая оценка независимым аналитическим сервисом beststocks.ru', 'out':'Невысокая оценка независимым аналитическим сервисом beststocks.ru'},
			#
			'getResistance5dayBreakout': {'in':'Прорыв линии сопротивления за последние 5 дней', 'out':'Не было прорыва линии сопротивления за последние 5 дней'},
			'getMoneyFlowIn': {'in':'Акции чаще покупают, чем продают', 'out':'Акции чаще продают, чем покупают'},
			'getTechnicallyGood': {'in':'Технически сильная (хорошие показатели PE/EPS)', 'out':'Технически слабая (плохие показатели PE/EPS)'},
			'getTightShorts': {'in':'Тугие шорты', 'out':'Нет большого объема шорт-позиций'},
			'getDividendsPaying': {'in':'Платит дивиденды', 'out':'Не платит дивиденды'},
			'getHyped': {'in':'Хайповая', 'out':'Не хайповая'},
			'getSocialAttitudeGood': {'in':'Бычий социальный настрой', 'out':'Нет бычьего социального настроя'}
		}

	def getTickersRating(self):
		indicators = {}
		for stock in self._any_():
			if not stock['ticker'] in indicators: 
				indicators[stock['ticker']]= {}
				indicators[stock['ticker']]['name'] = stock['name'] if 'name' in stock else None
				indicators[stock['ticker']]['cost'] = stock['currentCost'] if 'currentCost' in stock else None
				indicators[stock['ticker']]['indicators'] = []
				indicators[stock['ticker']]['rating'] = 0
		treats = TickerRating.getIndicators().keys()
		rateInc = len(treats)
		for treat in treats:
			for stock in getattr(self, treat)():
				indicators[stock['ticker']]['indicators'].append(treat)
				indicators[stock['ticker']]['rating'] += 2**rateInc
			rateInc -= 1 # the lower the treat the lesser its rate
		return indicators

	def _getLatestRating(closestDate):
		while True:
			try:
				return TickerRating(closestDate).getTickersRating()
			except Exception as e:
				closestDate -= datetime.timedelta(days=1)
				continue

	def getTickerReport(ticker:str):
		ticker = ticker.upper()
		tickers = TickerRating._getLatestRating(datetime.datetime.now())
		if not ticker in tickers:
			return None
		indicators = TickerRating.getIndicators()
		report = {
			'ticker': ticker,
			'place': sum(1 for item in tickers if tickers[item]['rating']>tickers[ticker]['rating']) + 1,
			'total': len(tickers.keys()),
			'name': tickers[ticker]['name'],
			'pluses': [],
			'minuses': []
			}
		for indicator in tickers[ticker]['indicators']:
			report['pluses'].append(indicators[indicator]['in'])
		for indicator in set(indicators.keys())-set(tickers[ticker]['indicators']):
			report['minuses'].append(indicators[indicator]['out'])
		return report

	def printTickerReport(ticker:str):
		report = TickerRating.getTickerReport(ticker)
		print(f"${ticker}({report['name']}): {report['place']} место среди {report['total']} тикеров\n")
		for plus in report['pluses']: print(f" + {plus}")
		for minus in report['minuses']: print(f" - {minus}")

	def printTickersRating(now):
		for item in sorted(TickerRating._getLatestRating(now).items(), key=lambda x: x[1]['rating']):
			print("%20s (%-10s): %s" % (
				"%s[%2s,%3s]" % (item[0], len(item[1]['indicators']), item[1]['rating']),
				str(item[1]['name'])[:10],
				' + '.join(item[1]['indicators'])
			))

	def printIndicatorCorrelation(start, end, deepness):
		bestTickersHistoryStats = {}
		current = start
		prevRatings = []
		indicatorMultipleRating = {}
		for number in range(1,deepness+1):
			for indicatorGroup in itertools.combinations(TickerRating.getIndicators().keys(), number):
				indicatorMultipleRating['+'.join(indicatorGroup)] = {'rating': 0, 'hits':set(), 'group': indicatorGroup}
		while current<=end:
			try:
				print(current)
				rating = TickerRating(current)
			except:
				current += datetime.timedelta(days=1)
				continue
			curRating = rating.getTickersRating()

			# go through all previous days
			for prevRating in prevRatings:
				indicatorForDay = {complexName:{'was':0, 'become':0, 'hits':set()} for complexName in indicatorMultipleRating}
				'''  HISTORY GROWTH STATS '''
				for item in sorted(prevRating.items(), key=lambda x: x[1]['rating'])[-5:]:
					ticker = item[0]
					if ticker not in bestTickersHistoryStats:
						bestTickersHistoryStats[ticker] = {'first_price': prevRating[ticker]['cost'], 'best_ratio': 0}
				for ticker in bestTickersHistoryStats:
					if ticker in curRating and curRating[ticker]['cost'] is not None and bestTickersHistoryStats[ticker]['first_price'] is not None:
						ratio = curRating[ticker]['cost']/float(bestTickersHistoryStats[ticker]['first_price'])
						bestTickersHistoryStats[ticker]['best_ratio'] = bestTickersHistoryStats[ticker]['best_ratio'] if ratio < bestTickersHistoryStats[ticker]['best_ratio'] else ratio
				''' COMPLEX RATING ''' 
				# go through all ticker in specific previous day
				for ticker in prevRating:
					if ticker in curRating and curRating[ticker]['cost'] is not None and prevRating[ticker]['cost'] is not None:
						# go through all ticker`s indicators in that previous day
						for number in range(1,deepness+1): 
							for indicatorGroup in itertools.combinations(prevRating[ticker]['indicators'], number):
								complexName = '+'.join(indicatorGroup)
								indicatorForDay[complexName]['was'] += prevRating[ticker]['cost']
								indicatorForDay[complexName]['become'] += curRating[ticker]['cost']
								indicatorMultipleRating[complexName]['hits'].add(ticker)
				# calculate each indicator performance for specific day
				for complexName in indicatorForDay:
					if indicatorForDay[complexName]['was'] != 0:
						# ..as relative change
						indicatorMultipleRating[complexName]['rating'] += (indicatorForDay[complexName]['become']-indicatorForDay[complexName]['was']) / indicatorForDay[complexName]['was']
			prevRatings.append(curRating)
			current += datetime.timedelta(days=1)
		''' show history stats '''
		print("="*100 + " (best by rating history growth score)")
		plus = 0
		for item in sorted(bestTickersHistoryStats.items(), key=lambda x: x[1]['best_ratio']):
			print(f"{item[0]} - {item[1]['best_ratio']}")
			plus += 1 if item[1]['best_ratio']>1 else 0
		print(f"--- {plus/len(bestTickersHistoryStats.items())}% growth")
		''' show complex rating '''
		print("="*100 + "(complex ratings score)")
		tickerComplexRatingBestWorstDiff = {}
		indicators = {k:v for k,v in sorted(indicatorMultipleRating.items(), key=lambda item: item[1]['rating'], reverse=True)}
		for indicator in indicators:
			# determine current tickers having this indicator
			currentTickersUnderIndicator = []
			for ticker in prevRatings[-1]:
				if set(indicatorMultipleRating[indicator]['group']).issubset(set(prevRatings[-1][ticker]['indicators'])):
					currentTickersUnderIndicator.append(ticker)
					# calculate best/worst rating prevalence
					if ticker not in tickerComplexRatingBestWorstDiff:
						tickerComplexRatingBestWorstDiff[ticker] = {'total':0}
					if 'best' not in tickerComplexRatingBestWorstDiff[ticker] or indicatorMultipleRating[indicator]['rating']>tickerComplexRatingBestWorstDiff[ticker]['best']:
						tickerComplexRatingBestWorstDiff[ticker]['best'] = indicatorMultipleRating[indicator]['rating']
					if 'worst' not in tickerComplexRatingBestWorstDiff[ticker] or indicatorMultipleRating[indicator]['rating']<tickerComplexRatingBestWorstDiff[ticker]['worst']:
						tickerComplexRatingBestWorstDiff[ticker]['worst'] = indicatorMultipleRating[indicator]['rating']
					tickerComplexRatingBestWorstDiff[ticker]['total'] += indicatorMultipleRating[indicator]['rating'] 
			# output
			print(f"= {indicator} = {round(indicatorMultipleRating[indicator]['rating'], 3)} | tickers(hits={len(indicatorMultipleRating[indicator]['hits'])}, now={len(currentTickersUnderIndicator)}) = {', '.join(currentTickersUnderIndicator[:20])}")
		print("="*100 + " (best+worst score)")
		# sort by diff
		for item in sorted(tickerComplexRatingBestWorstDiff.items(), key=lambda item: item[1]['best']+item[1]['worst'], reverse=True):
			print(f"{item[0]} : best+worst={item[1]['best']+item[1]['worst']}, total={item[1]['total']}")
		print("="*100 + " (overall combinations sum score)")
		# sort by total
		for item in sorted(tickerComplexRatingBestWorstDiff.items(), key=lambda item: item[1]['total'], reverse=True):
			print(f"{item[0]} : totalSum={item[1]['total']}, diff={item[1]['best']+item[1]['worst']}")
		print("="*100)


class UserInterface:

	def __init__(self):
		parser = argparse.ArgumentParser(description='Collected stocks data analyzer')
		subparsers = parser.add_subparsers(dest="command", help='Commands')
		fullreport = subparsers.add_parser('fullreport', help='Print full report for all tickers')
		fullreport.add_argument('--no-corr', dest='nocorr', action='store_true', default=False, help='Without correlation calculation')
		ticker = subparsers.add_parser('ticker', help='Report for single ticker')
		ticker.add_argument('ticker', help='Ticker')
		self.args = parser.parse_args()

	def go(self):
		if self.args.command == 'fullreport':
			self.fullreport(self.args.nocorr)
		elif self.args.command == 'ticker':
			self.ticker(self.args.ticker)

	def fullreport(self, without_correlation):
		date_from = datetime.datetime(2021,6,27)
		#date_till= datetime.datetime(2021,7,28)
		date_till = datetime.datetime.now()
		TickerRating.printTickersRating(date_till)
		if not without_correlation:
			TickerRating.printIndicatorCorrelation(date_from, date_till, deepness=4)

	def ticker(self, tickerName):
		TickerRating.printTickerReport(tickerName)

if __name__ == '__main__':
	UserInterface().go()