import pymongo
import datetime
import math

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
		#query['ticker'] = 'SPLK'
		data = self.collection.find(query) if not aggregate else self.collection.aggregate(query)
		#print(len(list(data)))
		return list(data)

	def getTicker(self, ticker):
		return self.collection.find_one({'ticker': ticker})

class Analyzer:

	def __init__(self, start, end):
		self.start = start
		self.end = end

	def getDifference(self, prev, curr):
		stocksPrev = [stock['ticker'] for stock in prev]
		stocksCurr = [stock['ticker'] for stock in curr]
		missingPrev = list(set(stocksCurr) - set(stocksPrev))
		missingCurr = list(set(stocksPrev) - set(stocksCurr))
		result = {"new":[],"gone":[]}
		for stock in prev:
			if stock['ticker'] in missingCurr:
				# put previous day stock object by ticker
				result['gone'].append(stock)
		for stock in curr:
			if stock['ticker'] in missingPrev:
				# put current day stock object by ticker
				result['new'].append(stock)
		return result

	# repalce previous day stock objects with current day stock object
	def actualizeDifference(self, diff, selector):
		# "or" in case if ticker missing that day
		diff['gone'] = [selector.getTicker(gone['ticker']) or gone for gone in diff['gone']]
		return diff

	def dump(self, cyclicData):
		self.printCyclicData(cyclicData)

	def getCyclicData(self, query, portfolioPutPerc = 15):
		date = self.start
		previous = []
		tickerTable = {}
		cyclicData = {'cyclic':[]}
		tickerTotalProfitDB = {}
		########################
		portfolioBought = 0
		portfolioSold = 0
		portfolioState = {}

		while date<=self.end: 
			cyclicIndex = date
			try:
				selector = Storage(date)
			except:
				#cyclicData['cyclic'][cyclicIndex] = None
				date += datetime.timedelta(days=1)
				continue

			current = query(selector)
			diff = self.getDifference(previous, current)
			diff = self.actualizeDifference(diff, selector)
			previous = current

			# calculate gone tickers growth
			totalChange = 0
			for gone in diff['gone']:
				if 'currentCost' in gone and 'currentCost' in tickerTable[gone['ticker']]:
					if int(tickerTable[gone['ticker']]['currentCost']) == 0:
						change = 0
					else:
						change = round((gone['currentCost'] / tickerTable[gone['ticker']]['currentCost'] - 1) * 100, 2)
				else:
					change = None
				gone['__costChange'] = change
				if change:
					# store ticker profit individually
					tickerTotalProfitDB[gone['ticker']] = change if not gone['ticker'] in tickerTotalProfitDB else tickerTotalProfitDB[gone['ticker']]+change
				# store total amount of profit through all tickers
				totalChange += change if change else 0
				# portfolio
				if gone['ticker'] in portfolioState:
					if 'currentCost' in gone:
						moneySum = 10000 * (portfolioState[gone['ticker']]['__fin_result']/float(portfolioPutPerc))
						count = math.ceil(moneySum / portfolioState[gone['ticker']]['currentCost']) 		
						portfolioBought += portfolioState[gone['ticker']]['currentCost']*count
						portfolioSold += gone['currentCost']*count
						del portfolioState[gone['ticker']]


			# add new tickers for futher calculation
			for new in diff['new']:
				tickerTable[new['ticker']] = new
				new["__fin_result"] = round(tickerTotalProfitDB[new['ticker']] if new['ticker'] in tickerTotalProfitDB else 0, 2)
				# portfolio
				if new["__fin_result"]>=portfolioPutPerc:
					if 'currentCost' in new and new['currentCost']>0:
						portfolioState[new['ticker']] = new

			cyclicData['cyclic'].append({
				'date': date,
				'gone': {
					'stocks': diff['gone'],
					'cost': totalChange
				},
				'new': {
					'stocks': diff['new']
				}
			})

			date += datetime.timedelta(days=1)

		# calculate left growth on current
		totalChange = 0
		for item in previous:
			if 'currentCost' in item and 'currentCost' in tickerTable[item['ticker']]:
				if int(tickerTable[item['ticker']]['currentCost']) == 0:
					change = 0
				else:
					change = round((item['currentCost'] / tickerTable[item['ticker']]['currentCost'] - 1) * 100, 2)
			else:
				change = None		
			item['__costChange'] = change
			totalChange += change if type(change)==float else 0

		cyclicData['current'] = {
			'stocks': previous,
			'cost': totalChange
		}
		cyclicData['forEachTickerProfit'] = tickerTotalProfitDB
		cyclicData['portfolioIncome'] = (portfolioSold/portfolioBought) if portfolioBought>0 else 0

		return cyclicData

	def printCyclicData(self, data):
		# daily
		for day in data['cyclic']:
			print("\n%s %s %s" % ("="*10, day['date'], "="*40))
			print("---------- New(%s): %s\n---------- Gone(%s): %s\n---------- Total %% = %s" % (
				len(day['new']['stocks']),
				','.join([
					f"{stock['ticker']}({(str(stock['__fin_result']) if '__fin_result' in stock else '?')}%)" for stock in day['new']['stocks']]
					),
				len(day['gone']['stocks']),
				','.join([
					f"{stock['ticker']}({(str(stock['__costChange']) if stock['__costChange'] is not None else '?')}%)" for stock in day['gone']['stocks']]
					),
				day['gone']['cost']
				))	
		# now
		nowCount = len(data['current']['stocks'])
		nowData = ','.join([stock['ticker'] + "("+(f"{stock['__costChange']}" if stock['__costChange'] is not None else '?')+"%)" for stock in data['current']['stocks']]) 
		print("\n\n%s NOW(%s) %s\n%s\n%s Total %% = %s\n\n" % (
			"#"*20, 
			nowCount, 
			"#"*20, 
			nowData, 
			"#"*50, 
			data['current']['cost']
		))
		print()
		for key,val in sorted(data['forEachTickerProfit'].items(), key=lambda item: item[1]):
			print(f"{key} = {round(val,2)}")
		print()
		print(f"Portfolio income = {data['portfolioIncome']}")

	def getTopHoldersInLoss(self):
		return self.getCyclicData(lambda selector: selector.select(
			{
				'holders.profitableSharesRatio':{'$exists':True}
			})
		.sort([('holders.profitableSharesRatio', pymongo.ASCENDING)])
		.limit(50))

	def getTopPotentialIncome(self):
		return self.getCyclicData(lambda selector: selector.select(
			{
				'holders.avgCostToCurrentRatio':{'$exists':True}
			})
		.sort([('holders.avgCostToCurrentRatio', pymongo.DESCENDING)])
		.limit(50))
		
	def getFallenWithSuperTrend(self):
		return self.getCyclicData(lambda selector: selector.select(
			{
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.55}, 
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1}, 
				# must recover because good trend
				'anal.buyCountRatio':{'$exists':True, '$gte':0.3}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0.2}
			})
		)

	def getBestCompaniesFallen(self):
		return self.getCyclicData(lambda selector: selector.select(
			{
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.85}, 
				# best companies
				'flows.inflowToOutflowRatio':{'$exists':True, '$gt':0.5}, 
				'anal.buyCountRatio':{'$exists':True, '$gte':0.7}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0.25},
				'trend.costTrend1Y':{'$exists':True, '$gt':0.1}
			})
		)

	def getBullyAttitudeWithPositiveTrendFallen(self):
		return self.getCyclicData(lambda selector: selector.select(
			{
				# options
				'options':{
					'$exists':True,
					'$not': {
						'$elemMatch':{
							'expectedCostToCurrentRatio':{'$lt': 1}
							}
						}
					},
				# actial (no outsiders)
				'trend.costTrend1Y':{'$exists':True, '$gt':0}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0}, 
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.8},
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1}
			})
		)


class TickerRating():

	def __init__(self, date):
		self.selector = Storage(date)

	# treat
	def getHoldersInLoss(self):
		return self.selector.select(
			{
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.55}, 
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1}, 
			}
		)

	# treat
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
			}
		)

	# treat
	def getSocialAttitudeGood(self):
		return self.selector.select(
			{
				'social_guess.overall.bullRatio':{'$exists':True, '$gt':0.7}, 
				'social_guess.overall.bulls':{'$exists':True, '$gt':5},
				'heldSharesRatio':{'$gte':0.7}
			}
		)

	# treat: current cost must be better
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
	def getSteepGrowing(self):
		return self.selector.select(
			{
				'trend.costTrend5Y':{'$exists':True, '$gt':0.25},
				'trend.costTrend1Y':{'$exists':True, '$gt':0.1}
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

	# treat: cost trend must be better
	def getDevelopingUnderestimated(self):
		return self.selector.select(
			[
				{'$addFields':{'trend_farness':{'$subtract':['$income.revenueYoyTrend', '$trend.costTrend5Y']}}},
				{'$match':{'income.revenueYoyTrend':{'$exists':True, '$gt':0}, 'trend_farness':{'$gt':0}}}
			], 
			True
		)

	# treat: good managed
	def getOperatingEffective(self):
		return self.selector.select(
			{
				'income.operatingIncomeYoyTrend':{'$exists':True, '$gt':0}
			}
		)

	# treat
	def getTightShorts(self):
		return self.selector.select(
			{
				'short.daysToCover':{'$exists':True, '$gte':3.5}
			}
		)

	# treat: technical
	def _any_(self):
		return self.selector.select({})

	def getIndicators():
		return [
			'getHoldersInLoss',
			'getOptionsPositive',
			'getAnalyticsRecommendBuy',
			'getSocialAttitudeGood',
			'getCostBelowFareCost',
			'getTechnicallyGood',
			'getDevelopingUnderestimated',
			'getOperatingEffective',
			'getTightShorts',
			'getSteepGrowing'
		]

	def getTickersRating(self):
		treats = TickerRating.getIndicators() + ['_any_'] # to consider empty-indicators stocks
		indicators = {}
		for treat in treats:
			for stock in getattr(self, treat)():
				if not stock['ticker'] in indicators: 
					indicators[stock['ticker']]= {}
					indicators[stock['ticker']]['indicators'] = []
				if not treat == '_any_':
					indicators[stock['ticker']]['indicators'].append(treat)
				indicators[stock['ticker']]['cost'] = stock['currentCost'] if 'currentCost' in stock else None

		return indicators

	def printTickerRating(now):
		rating = None
		while True:
			try:
				rating = TickerRating(now).getTickersRating()
				break
			except:
				now -= datetime.timedelta(days=1)
				continue
		sortableSet = []
		for ticker in rating:
			sortableSet.append({
				'indicators': rating[ticker]['indicators'],
				'ticker': ticker,
				'cost': rating[ticker]['cost'] if 'cost' in rating[ticker] else None
				})
		for item in sorted(sortableSet, key=lambda x: len(x['indicators'])):
			print("%10s : %s" % (
				"%s[%s]" % (item['ticker'], len(item['indicators'])),
				' + '.join(item['indicators'])
			))

	def printIndicatorCorrelation(start, end):
		current = start
		prevRatings = []
		indicatorRating = {indicatorName:0 for indicatorName in TickerRating.getIndicators()}
		while current<=end:
			try:
				rating = TickerRating(current)
			except:
				current += datetime.timedelta(days=1)
				continue
			curRating = rating.getTickersRating()
			# go through all current tickers
			for ticker in curRating:
				# go through all previous days
				for prevRating in prevRatings:
					if ticker in prevRating and curRating[ticker]['cost'] is not None and prevRating[ticker]['cost'] is not None:
						# go through all indicators in that previous day
						for indicator in prevRating[ticker]['indicators']:
							# increase indicator rating by (now_price-prev_price)
							if prevRating[ticker]['cost']>0 and curRating[ticker]['cost']/prevRating[ticker]['cost'] >= 1.1:
								indicatorRating[indicator] += curRating[ticker]['cost']-prevRating[ticker]['cost']
			prevRatings.append(curRating)
			current += datetime.timedelta(days=1)
		for indicator in indicatorRating:
			print(f"{indicator} = {round(indicatorRating[indicator])}")


#analyzer = Analyzer(datetime.datetime(2020,12,5), datetime.datetime.now())
#analyzer = Analyzer(datetime.datetime(2020,12,5), datetime.datetime(2021,5,1))
#analyzer.dump(analyzer.getTopHoldersInLoss()) # 77%
#analyzer.dump(analyzer.getTopPotentialIncome()) # 77%
#analyzer.dump(analyzer.getFallenWithSuperTrend()) # 87%
#analyzer.dump(analyzer.getBestCompaniesFallen()) # 77%
#analyzer.dump(analyzer.getBullyAttitudeWithPositiveTrend()) # 58%
#analyzer.dump(analyzer.getBullyAttitudeWithPositiveTrendFallen()) # 69%
#analyzer.dump(analyzer.getSuperAttitude()) # 55%
#analyzer.dump(analyzer.getGrowingUnderestimated()) 
#analyzer.dump(analyzer.getCostTrendDeviatedRevenueTrend()) 
#analyzer.dump(analyzer.getGrowingUnderestimated()) 

TickerRating.printTickerRating(datetime.datetime.now())
TickerRating.printIndicatorCorrelation(datetime.datetime(2021,1,1), datetime.datetime.now())
