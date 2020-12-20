import pymongo
import datetime

class Storage:
	def __init__(self, date):
		client = pymongo.MongoClient('localhost', 27017)
		db = client.webull
		self.collectionName = date.strftime('tickers_%G_%m_%d')
		if self.collectionName in db.list_collection_names():
			self.collection = db[self.collectionName]
		else:
			raise Exception('collection not exists')

	def select(self, query):
		#query['ticker'] = 'SPLK'
		return self.collection.find(query)

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

	def getCyclicData(self, query):
		date = self.start
		previous = []
		tickerTable = {}
		cyclicData = {'cyclic':[]}
		while date<=self.end: 
			cyclicIndex = date
			try:
				selector = Storage(date)
			except:
				#cyclicData['cyclic'][cyclicIndex] = None
				date += datetime.timedelta(days=1)
				continue

			current = list(query(selector))
			diff = self.getDifference(previous, current)
			diff = self.actualizeDifference(diff, selector)
			previous = current

			# calculate gone tickers growth
			totalChange = 0
			for gone in diff['gone']:
				change = round((gone['currentCost'] / tickerTable[gone['ticker']]['currentCost'] - 1) * 100, 2) if 'currentCost' in gone else None
				gone['__costChange'] = change
				totalChange += change if change else 0
			# add new tickers for futher calculation
			for new in diff['new']:
				tickerTable[new['ticker']] = new

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
			change = round((item['currentCost'] / tickerTable[item['ticker']]['currentCost'] - 1) * 100, 2) if 'currentCost' in item else None
			item['__costChange'] = change
			totalChange += change if type(change)==float else 0

		cyclicData['current'] = {
			'stocks': previous,
			'cost': totalChange
		}

		return cyclicData

	def printCyclicData(self, data):
		for day in data['cyclic']:
			# daily
			print("\n%s %s %s" % ("="*10, day['date'], "="*40))
			print("---------- New(%s): %s\n---------- Gone(%s): %s\n---------- Total %% = %s" % (
				len(day['new']['stocks']),
				','.join([stock['ticker'] for stock in day['new']['stocks']]),
				len(day['gone']['stocks']),
				','.join([stock['ticker'] + "("+(str(stock['__costChange']) if stock['__costChange'] is not None else '?')+"%)" for stock in day['gone']['stocks']]),
				day['gone']['cost']
				))	
		# now
		nowCount = len(data['current']['stocks'])
		nowData = ','.join([stock['ticker'] + "("+(str(stock['__costChange']) if stock['__costChange'] is not None else '?')+"%)" for stock in data['current']['stocks']])
		print("\n\n%s NOW(%s) %s\n%s\n%s Total %% = %s\n\n" % (
			"#"*20, 
			nowCount, 
			"#"*20, 
			nowData, 
			"#"*50, 
			data['current']['cost']
		))

	def getCyclicDelta1(self, query):
		self.printCyclicData(self.getCyclicData(query))

	def getCyclicDelta2(self, query):
		date = self.start
		previous = []
		tickerTable = {}
		while date<=self.end: 
			print("\n%s %s %s" % ("="*10, date, "="*40))

			try:
				selector = Storage(date)
			except:
				print("<missing date>")
				continue
			finally:
				date += datetime.timedelta(days=1)
			current = list(query(selector))
			diff = self.getDifference(previous, current)
			diff = self.actualizeDifference(diff, selector)
			previous = current
			
			# calculate gone tickers growth
			totalChange = 0
			for gone in diff['gone']:
				change = round((gone['currentCost'] / tickerTable[gone['ticker']]['currentCost'] - 1) * 100, 2) if 'currentCost' in gone else '?'
				tickerTable[gone['ticker']] = change
				totalChange += change if type(change)==float else 0
			# add new tickers for futher calculation
			for new in diff['new']:
				tickerTable[new['ticker']] = new

			print("---------- New(%s): %s\n---------- Gone(%s): %s\n---------- Total %% = %s" % (
				len(diff['new']),
				','.join([stock['ticker'] for stock in diff['new']]),
				len(diff['gone']),
				','.join([stock['ticker'] + "("+str(tickerTable[stock['ticker']])+"%)" for stock in diff['gone']]),
				totalChange
				))	

		# calculate left growth on current
		totalChange = 0
		for item in previous:
			change = round((item['currentCost'] / tickerTable[item['ticker']]['currentCost'] - 1) * 100, 2) if 'currentCost' in item else '?'
			tickerTable[item['ticker']] = change
			totalChange += change if type(change)==float else 0

		# display current state
		nowCount = len(previous)
		nowData = ','.join([stock['ticker'] + "("+str(tickerTable[stock['ticker']])+"%)" for stock in previous])
		print("\n\n%s NOW(%s) %s\n%s\n%s Total %% = %s\n\n" % ("#"*20, nowCount, "#"*20, nowData, "#"*50, totalChange))

	def getTopHoldersInLoss(self, firstCount):
		self.getCyclicDelta(lambda selector: selector.select(
			{
				'holders.profitableSharesRatio':{'$exists':True}
			})
		.sort([('holders.profitableSharesRatio', pymongo.ASCENDING)])
		.limit(firstCount))

	def getTopPotentialIncome(self, firstCount):
		self.getCyclicDelta2(lambda selector: selector.select(
			{
				'holders.avgCostToCurrentRatio':{'$exists':True}
			})
		.sort([('holders.avgCostToCurrentRatio', pymongo.DESCENDING)])
		.limit(firstCount))
		
	def getFallenWithSuperTrend(self):
		self.getCyclicDelta2(lambda selector: selector.select(
			{
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.55}, 
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1}, 
				# must recover because good trend
				'anal.buyCountRatio':{'$exists':True, '$gte':0.3}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0.5}
			})
		)

	def getBestCompaniesFallen(self):
		self.getCyclicDelta2(lambda selector: selector.select(
			{
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.85}, 
				# best companies
				'flows.inflowToOutflowRatio':{'$exists':True, '$gt':0.8}, 
				'anal.buyCountRatio':{'$exists':True, '$gte':0.7}, 
				'trend.costTrend5Y':{'$exists':True, '$gt':0.25},
				'trend.costTrend1Y':{'$exists':True, '$gt':0.05}
			})
		)

	def getBullyAttitudeWithPositiveTrend(self):
		self.getCyclicDelta2(lambda selector: selector.select(
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
				# social 
				'social_guess.overall.bullRatio':{'$exists':True, '$gt':0.5}, 
				'social_guess.overall.bulls':{'$exists':True, '$gt':0}
			})
		)

	def getBullyAttitudeWithPositiveTrendFallen(self):
		self.getCyclicDelta2(lambda selector: selector.select(
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
				# social
				'social_guess.overall.bullRatio':{'$exists':True, '$gt':0.5}, 
				'social_guess.overall.bulls':{'$exists':True, '$gt':0},
				# fallen
				'holders.profitableSharesRatio':{'$exists':True, '$lte':0.8},
				'holders.avgCostToCurrentRatio':{'$exists':True, '$gt':1}
			})
		)
		
	def getSuperAttitude(self):
		self.getCyclicDelta2(lambda selector: selector.select(
			{
			 	# society attitude
				'social_guess.overall.bullRatio':{'$exists':True, '$gt':0.75}, 
				'social_guess.overall.bulls':{'$exists':True, '$gt':0},
				# analytics attitude
				'anal.buyCountRatio':{'$exists':True, '$gte':0.75}, 
				'anal.buyCount':{'$exists':True, '$gte':5}, 
				# traders attitude
				'options':{
					'$exists':True,
					'$not': {
						'$elemMatch':{
							'direction': 'down'
							}
						}
					}
			})
		)


analyzer = Analyzer(datetime.datetime(2020,12,5), datetime.datetime.now() - datetime.timedelta(days=1))
#analyzer.getTopHoldersInLoss(50)
#analyzer.getTopPotentialIncome(50)
#analyzer.getFallenWithSuperTrend()
#analyzer.getBestCompaniesFallen()
#analyzer.getBullyAttitudeWithPositiveTrend()
#analyzer.getBullyAttitudeWithPositiveTrendFallen()
analyzer.getSuperAttitude()