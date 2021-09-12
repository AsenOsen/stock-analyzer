import pymongo
import datetime
import math
import itertools

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
		return [
			# company is relient
			'getStableGrowing',
			'getOperatingEffective',
			'getOccupationGrowing',	
			'getProfitable',
			# company fall recently
			'getFallen',
			'getHoldersInLoss',
			'getCostBelowFareCost',
			'getDevelopingUnderestimated',			
			# smart heads interested in company
			'getInsiderBuying',
			'getTopInvestorsBuying',	
			'getBigFishesBuying',
			# company continues growing
			'getOccupationGrowthBegan',
			'getAggressor',
			# positve behaviour
			'getAnalyticsRecommendBuy',
			'getOptionsPositive',
			'getGoodNewsBackground',
			# independent analitycs postitive
			'getGoodScoreWallst',	
			'getGoodScoreBeststocks',
			#
			'getResistance5dayBreakout',
			'getMoneyFlowIn',
			'getTechnicallyGood',	
			'getTightShorts',
			'getDividendsPaying',			
			'getHyped',
			'getSocialAttitudeGood'
		]

	def getTickersRating(self):
		indicators = {}
		for stock in self._any_():
			if not stock['ticker'] in indicators: 
				indicators[stock['ticker']]= {}
				indicators[stock['ticker']]['name'] = stock['name'] if 'name' in stock else None
				indicators[stock['ticker']]['cost'] = stock['currentCost'] if 'currentCost' in stock else None
				indicators[stock['ticker']]['indicators'] = []
				indicators[stock['ticker']]['rating'] = 0
		treats = TickerRating.getIndicators()
		rateInc = len(treats)
		for treat in treats:
			for stock in getattr(self, treat)():
				indicators[stock['ticker']]['indicators'].append(treat)
				indicators[stock['ticker']]['rating'] += 2**rateInc
			rateInc -= 1 # the lower the treat the lesser its rate
		return indicators

	def printTickerRating(now):
		rating = None
		while True:
			try:
				rating = TickerRating(now).getTickersRating()
				break
			except Exception as e:
				now -= datetime.timedelta(days=1)
				continue
		for item in sorted(rating.items(), key=lambda x: x[1]['rating']):
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
			for indicatorGroup in itertools.combinations(TickerRating.getIndicators(), number):
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
		print("="*100)
		plus = 0
		for item in sorted(bestTickersHistoryStats.items(), key=lambda x: x[1]['best_ratio']):
			print(f"{item[0]} - {item[1]['best_ratio']}")
			plus += 1 if item[1]['best_ratio']>1 else 0
		print(f"--- {plus/len(bestTickersHistoryStats.items())}% growth")
		''' show complex rating '''
		print("="*100)
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
		print("="*100)
		# sort by diff
		for item in sorted(tickerComplexRatingBestWorstDiff.items(), key=lambda item: item[1]['best']+item[1]['worst'], reverse=True):
			print(f"{item[0]} : diff={item[1]['best']+item[1]['worst']}, total={item[1]['total']}")
		print("="*100)
		# sort by total
		for item in sorted(tickerComplexRatingBestWorstDiff.items(), key=lambda item: item[1]['total'], reverse=True):
			print(f"{item[0]} : total={item[1]['total']}, diff={item[1]['best']+item[1]['worst']}")
		print("="*100)


date_from = datetime.datetime(2021,6,27)
#date_till= datetime.datetime(2021,7,28)
date_till = datetime.datetime.now()
TickerRating.printTickerRating(date_till)
TickerRating.printIndicatorCorrelation(date_from, date_till, deepness=4)
