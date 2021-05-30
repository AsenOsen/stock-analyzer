import requests
import json
import datetime
import pymongo
import statistics
import numpy
import argparse
import pprint
import tabulate
import textwrap
import urllib3


class Api:

	responseWebullSearchList = None
	responseWebullChipQuery = None
	responseWebullTickerGetTickerRealTime = None
	responseWebullCapitalFlow = None
	responseWebullSecuritiesAnalysis = None
	responseWebullShortInterest = None
	responseWebullInstitutionalHoldings = None
	responseWebullInstitutionsDistribution = None
	responseWebullTrendLastYear = None
	responseWebullTrend5Y = None
	responseWebullBriefInfo = None
	responseWebullOptions = None
	responseWebullGuess = None

	def _getJson(self, host, path, headers = {}, body = None):
		headers['User-Agent'] = 'okhttp/3.12.1'
		headers['Host'] = host
		url = "https://" + host + path
		urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		if not body:	
			response = requests.get(url, headers = headers, timeout=5, verify=False).content
		else:
			response = requests.post(url, headers = headers, data = body, timeout=5, verify=False).content
		return json.loads(response) if response else None

	def webullQuotesSearchList(self, tickerName):
		if self.responseWebullSearchList == None:
			self.responseWebullSearchList = self._getJson('quotes-gw.webullfintech.com','/api/search/list?pageSize=20&pageIndex=1&busiModel=10000&keyword=%s' % (tickerName))
		return self.responseWebullSearchList

	def webullQuotesChipQuery(self, tickerId, startDate, endDate):
		if self.responseWebullChipQuery == None:
			self.responseWebullChipQuery = self._getJson('quotes-gw.webullfintech.com','/api/quotes/chip/query?tickerId=%s&startDate=%s&endDate=%s' % (tickerId, startDate, endDate))
		return self.responseWebullChipQuery

	def webullQuotesTickerGetTickerRealTime(self, tickerId):
		if self.responseWebullTickerGetTickerRealTime == None:
			self.responseWebullTickerGetTickerRealTime = self._getJson('quotes-gw.webullfintech.com','/api/quotes/ticker/getTickerRealTime?includeSecu=1&tickerId=%s' % (tickerId))
		return self.responseWebullTickerGetTickerRealTime

	def webullQuotesTickerFinancial(self, tickerId):
		return self._getJson('quotes-gw.webullfintech.com','/api/information/financial/index?tickerId=%s' % (tickerId))

	def webullQuotesCapitalFlow(self, tickerId):
		if self.responseWebullCapitalFlow == None:
			self.responseWebullCapitalFlow = self._getJson('quotes-gw.webullfintech.com','/api/wlas/meteor/capitalflow/ticker?tickerId=%s&showHis=true&version=1' % (tickerId))
		return self.responseWebullCapitalFlow

	def webullQuotesSecuritiesAnalysis(self, tickerId):
		if self.responseWebullSecuritiesAnalysis == None:
			self.responseWebullSecuritiesAnalysis = self._getJson('quotes-gw.webullfintech.com','/api/information/securities/analysis?tickerId=%s&type=toolkit' % (tickerId))
		return self.responseWebullSecuritiesAnalysis

	def webullQuotesShortInterest(self, tickerId):
		if self.responseWebullShortInterest == None:
			self.responseWebullShortInterest = self._getJson('quotes-gw.webullfintech.com','/api/information/brief/shortInterest?tickerId=%s' % (tickerId))
		return self.responseWebullShortInterest

	def webullSecuritiesInstitutionalHoldings(self, tickerId):
		if self.responseWebullInstitutionalHoldings == None:
			self.responseWebullInstitutionalHoldings = self._getJson('securitiesapi.webullfintech.com','/api/securities/stock/v5/%s/institutionalHolding' % (tickerId))
		return self.responseWebullInstitutionalHoldings

	def webullSecuritiesInstitutionsDistribution(self, tickerId):
		if self.responseWebullInstitutionsDistribution == None:
			self.responseWebullInstitutionsDistribution = self._getJson('quotes-gw.webullfintech.com','/api/information/brief/holdersDetail?tickerId=%s&hasNum=0&pageSize=20&type=2' % (tickerId))
		return self.responseWebullInstitutionsDistribution

	def webullQuotesBriefInfo(self, tickerId):
		if self.responseWebullBriefInfo == None:
			self.responseWebullBriefInfo = self._getJson('quotes-gw.webullfintech.com','/api/information/stock/brief?tickerId=%s' % (tickerId))
		return self.responseWebullBriefInfo

	def webullQuotesTickerTrendLastYear(self, tickerId):
		if self.responseWebullTrendLastYear == None:
			self.responseWebullTrendLastYear = self._getJson('quoteapi.webullfintech.com','/api/quote/v2/tickerTrends/%s?trendType=y1' % (tickerId))
		return self.responseWebullTrendLastYear

	def webullQuotesTickerTrendFiveYear(self, tickerId):
		if self.responseWebullTrend5Y == None:
			self.responseWebullTrend5Y = self._getJson('quoteapi.webullfintech.com','/api/quote/v2/tickerTrends/%s?trendType=y5' % (tickerId))
		return self.responseWebullTrend5Y

	def webullQuotesOptions(self, tickerId):
		if self.responseWebullOptions == None:
			# [3,2,4] - regular\weekly\quaterly
			body = '{"count":50,"expireCycle":[3,2,4],"type":0,"tickerId":%s,"direction":"all"}' % (tickerId)
			self.responseWebullOptions = self._getJson('quotes-gw.webullfintech.com','/api/quote/option/strategy/list', body = body)
		return self.responseWebullOptions

	def webullQuotesFeed(self, tickerId):
		return self._getJson('quotes-gw.webullfintech.com','/api/social/feed/ticker/%s/posts?size=200' % (tickerId))

	def webullQuotesFeedItemComments(self, uuid):
		return self._getJson('quotes-gw.webullfintech.com','/api/social/feed/post/%s/comments' % (uuid))

	def webullQuotesGuess(self, tickerId):
		if self.responseWebullGuess == None:
			self.responseWebullGuess = self._getJson('quotes-gw.webullfintech.com','/api/social/guess/queryGuessInfoByTicker/%s' % (tickerId))
		return self.responseWebullGuess

	def tinkoffGetMarketStocks(self, token):
		response = self._getJson("api-invest.tinkoff.ru", "/openapi/market/stocks", {
			"Authorization":"Bearer %s" % token,
			"Accept": "application/json"
			}
		)
		return response


class TickerInfo:

	tickerName = None
	tickerId = None
	api = None	

	def __init__(self, tickerName):
		# webull interprets "." as " "
		self.tickerName = tickerName.replace('.',' ')
		self.api = Api()

	def _callWithException(self, func):
		try:
			func()
		except Exception as e:
			print(str(type(e).__name__) + " | " + str(e))

	def loadInternal(self):
		data = self.api.webullQuotesSearchList(self.tickerName)
		if 'stocks' not in data:
			raise Exception('ticker not found')
		for item in data['stocks']['datas']:
			if item['ticker']['symbol'] == self.tickerName and item['ticker']['template'] == 'stock' and item['ticker']['regionCode'] == "US":
				self.tickerId = item['id']
				break
		if not self.tickerId:
			raise Exception('ticker not found')

	def load(self):
		self._callWithException(lambda: self.loadInternal())
		return self.tickerId

	def fillCostDistribution(self, info):
		endDate = datetime.datetime.now()
		startDate = (endDate - datetime.timedelta(days=7))
		data = self.api.webullQuotesChipQuery(self.tickerId, startDate.strftime('%Y-%m-%d'), endDate.strftime('%Y-%m-%d'))
		if not data:
			raise Exception('fillCostDistribution: missing distribution data')
		if not 'data' in data or not data['data']:
			raise Exception('fillCostDistribution: empty distribution data')
		avgCost = float(data['data'][0]['avgCost'])
		profitableSharesRatio = float(data['data'][0]['closeProfitRatio'])
		avgCostToCurrentRatio = 0
		if 'currentCost' in info:
			currentCost = 0.01 if info['currentCost']==0 else info['currentCost']
			avgCostToCurrentRatio = float(avgCost) / currentCost
		info['holders'] = {
			'avgCost': avgCost,
			'avgCostToCurrentRatio': avgCostToCurrentRatio,
			'profitableSharesRatio': profitableSharesRatio
		} 

	def fillTickerRealTime(self, info):
		data = self.api.webullQuotesTickerGetTickerRealTime(self.tickerId)
		if not data:
			raise Exception('fillCapitalFlow: missing ticker real time info')
		if not 'close' in data:
			raise Exception('fillCapitalFlow: unknown current cost')
		info['currentCost'] = float(data['close'])
		info['name'] = data['name']
		info['totalShares'] = int(data['totalShares'])
		info['pe'] = float(data['peTtm']) # Trailing Twelve Months
		info['eps'] = float(data['epsTtm']) # Trailing Twelve Months
		info['heldSharesRatio'] = float(data['outstandingShares'])/int(data['totalShares'])

	def fillTickerFinancials(self, info):
		data = self.api.webullQuotesTickerFinancial(self.tickerId)
		incomeData = data['simpleStatement'][0]
		if incomeData['title'] == 'Income Statement':
			latest = incomeData['list'][len(incomeData['list'])-1]
			info['income'] = {
				'revenue': float(latest['revenue']['value']),
				'operatingIncome': float(latest['operatingIncome']['value']),
				'revenueYoyTrend': self.calcTrendSlope([float(o['revenue']['yoy']) for o in incomeData['list'] if 'yoy' in o['revenue']])[0],
				'operatingIncomeYoyTrend': self.calcTrendSlope([float(o['operatingIncome']['yoy'])  for o in incomeData['list'] if 'yoy' in o['operatingIncome']])[0],
				'netIncome': float(latest['netIncomeAfterTax']['value']),
				'netIncomeYoyTrend': self.calcTrendSlope([float(o['netIncomeAfterTax']['yoy'])  for o in incomeData['list'] if 'yoy' in o['netIncomeAfterTax']])[0],
				}

	def fillCapitalFlow(self, info):
		data = self.api.webullQuotesCapitalFlow(self.tickerId)
		if not data:
			raise Exception('fillCapitalFlow: missing capital flow info')
		if not 'latest' in data:
			raise Exception('fillCapitalFlow: empty capital flow info')
		retailInflow = data['latest']['item']['retailInflow']
		institutionsInflow = data['latest']['item']['majorInflow']
		retailOutflow = data['latest']['item']['retailOutflow']
		institutionsOutflow = data['latest']['item']['majorOutflow']
		totalInflow = retailInflow + institutionsInflow
		totalOutflow = retailOutflow + institutionsOutflow
		if totalOutflow==0: totalOutflow += 0.01
		info['flows'] = {
			'inflow': totalInflow,
			'outflow': totalOutflow,
			'inflowToOutflowRatio': totalInflow / float(totalOutflow)
		}

	def fillAnalytics(self, info):
		data = self.api.webullQuotesSecuritiesAnalysis(self.tickerId)
		if not data:
			raise Exception('fillAnalytics: missing analysis')
		if not 'targetPrice' in data:
			raise Exception('fillAnalytics: missing targetPrice')
		if not 'rating' in data:
			raise Exception('fillAnalytics: missing rating')
		targetCost = float(data['targetPrice']['mean'])
		buyCount = data['rating']['ratingSpread']['buy'] + data['rating']['ratingSpread']['strongBuy']
		targetCostToCurrentRatio = 0
		if 'currentCost' in info:
			currentCost = 0.01 if info['currentCost']==0 else info['currentCost']
			targetCostToCurrentRatio = float(targetCost) / currentCost
		analyticsCount = float(data['rating']['ratingAnalysisTotals'])
		buyCountRatio = 0 if analyticsCount==0 else buyCount/float(analyticsCount)
		info['anal'] = {
			'targetCost': targetCost,
			'targetCostToCurrentRatio': targetCostToCurrentRatio,
			'buyCount': buyCount,
			'buyCountRatio': buyCountRatio,
			'consensus': data['rating']['ratingAnalysis']
		} 

	def fillShortInterest(self, info):
		data = self.api.webullQuotesShortInterest(self.tickerId)
		if len(data)>0:
			sharesRatio = float(data[0]['shortInterst']) / info['totalShares'] if 'totalShares'in info else 0
			info['short'] =  {
				'date': datetime.datetime.strptime(data[0]['settlementDate'], "%Y-%m-%d"),
				'sharesCount': int(data[0]['shortInterst']),
				'sharesRatio': sharesRatio,
				'daysToCover': float(data[0]['daysToCover'])
			}
	
	def fillInstitutionHoldings(self, info):
		data = self.api.webullSecuritiesInstitutionalHoldings(self.tickerId)
		if not data:
			raise Exception('fillInstitutions: missing institutionHolding info')
		if not 'institutionHolding' in data or not data['institutionHolding']:
			raise Exception('fillInstitutions: empty institutionHolding info')
		info['institutions'] = {
			'ratio': float(data['institutionHolding']['stat']['holdingRatio']),
			'ratioChange': float(data['institutionHolding']['stat']['holdingRatioChange']),
			'count': int(data['institutionHolding']['stat']['holdingCount']),
			'institutionsIncreased': int(data['institutionHolding']['increase']['institutionalCount']),
			'institutionsNew': int(data['institutionHolding']['newPosition']['institutionalCount']),
			'institutionsDecrease': int(data['institutionHolding']['decrease']['institutionalCount']),
			'institutionsSoldout': int(data['institutionHolding']['soldOut']['institutionalCount']),
		}

	def fillInstitutionDistribution(self, info):
		data = self.api.webullSecuritiesInstitutionsDistribution(self.tickerId)
		if not 'institutions' in info:
			info['institutions'] = {}
		info['institutions']['major'] = []
		for institution in data:
			if institution['ownerName'] in ('VANGUARD GROUP INC', 'BLACKROCK INC.'):
				info['institutions']['major'].append({
					"name":institution['ownerName'],
					'changeRatio': float(institution['changeRatio'].replace("%","")),
					'date': datetime.datetime.strptime(institution['date'], "%Y-%m-%d"),
					})

	def fillInstitution(self, info):
		self._callWithException(lambda: self.fillInstitutionHoldings(info))
		self._callWithException(lambda: self.fillInstitutionDistribution(info))

	def calcTrendSlope(self, cost):
		if len(cost)<2:
			return (0, 0) 
		days = [day for day in range(len(cost))]
		xs = numpy.array(days, dtype=numpy.float64)
		ys = numpy.array(cost, dtype=numpy.float64)
		k = (((statistics.mean(xs)*statistics.mean(ys)) - statistics.mean(xs*ys)) /
		     ((statistics.mean(xs)**2) - statistics.mean(xs**2)))
		
		b = (statistics.mean(ys)) - (k * (len(cost)/2))
		fareCost = k*xs[len(xs)-1]+b
		trendOffset = ys[len(ys)-1] / fareCost

		'''
		from matplotlib import pyplot as plt 
		plt.plot(xs,ys) 
		trend = k * xs + b
		plt.plot(xs,trend) 
		plt.show()
		'''
		
		return (k, trendOffset)

	def fillTrend(self, info):
		data = self.api.webullQuotesTickerTrendLastYear(self.tickerId)
		costYear = []
		for day in data['tickerKDatas']:
			if day['forwardKData']:
				costYear.insert(0, float(day['forwardKData']['close']))
		data = self.api.webullQuotesTickerTrendFiveYear(self.tickerId)
		costAll = []
		for day in data['tickerKDatas']:
			if day['forwardKData']:
				costAll.insert(0, float(day['forwardKData']['close']))

		trend1Y = self.calcTrendSlope(costYear)
		trend5Y = self.calcTrendSlope(costAll)

		info['trend'] = {
			'costTrend1Y': trend1Y[0],
			'costTrend5Y': trend5Y[0],
			'currentCostToFareTrend1YRatio': trend1Y[1],
			'currentCostToFareTrend5YRatio': trend5Y[1],
		}

	def fillSectors(self, info):
		data = self.api.webullQuotesBriefInfo(self.tickerId)
		if not data:
			raise Exception('fillSectors: missing sectors info')
		if not 'sectors' in data:
			raise Exception('fillSectors: empty sectors info')
		sectors = []
		for sector in data['sectors']:
			sectors.append(sector['name'])
		info['sectors'] = '|'.join(sectors)

	def fillOptions(self, info):
		data = self.api.webullQuotesOptions(self.tickerId)
		if not data:
			raise Exception('fillOptions: missing options info')
		if not 'expireDateList' in data:
			raise Exception('fillOptions: empty expireDateList info')
		now = datetime.datetime.now()
		info['options'] = []
		if not 'currentCost' in info:
			return
		currentCost = info['currentCost']
		prevDate = None
		for option in data['expireDateList']:
			baseDate = datetime.datetime.strptime(option['from']['date'], "%Y-%m-%d")
			if not prevDate == None and baseDate<prevDate:
				raise Exception('unordered option')
			prevDate = baseDate
			optionsMap = {}
			for group in option['groups']:
				for callGroup in group['call']:
					optionsMap[callGroup['option']] = 'call'
				for callGroup in group['put']:
					optionsMap[callGroup['option']] = 'put'

			optionCostExpectation = {}
			
			for optionItem in option['data']:
				if not datetime.datetime.strptime(optionItem['expireDate'], "%Y-%m-%d") == baseDate:
					raise Exception('date mismatch')
				optionTickerId = optionItem['tickerId']
				strike = float(optionItem['strikePrice'])
				# somehow not each item contains openInterest field
				if not 'openInterest' in optionItem:
					continue
				optionCount = int(optionItem['openInterest'])
				optionType = optionsMap[optionTickerId]
				if optionType == "call":
					for cost in range(int(strike), int(currentCost*3)):
						optionCostExpectation[cost] = optionCount if cost not in optionCostExpectation else optionCostExpectation[cost]+optionCount
				if optionType == "put":
					for cost in range(0, int(strike)):
						optionCostExpectation[cost] = optionCount if cost not in optionCostExpectation else optionCostExpectation[cost]+optionCount
			#print("---------------------------- " + str(baseDate))
			#print(optionCostExpectation) # https://jsfiddle.net/canvasjs/RxeP6/
			biggestCostDistribution = 0
			biggestExpectedCost = 0
			for cost in optionCostExpectation:
				if optionCostExpectation[cost]>=biggestCostDistribution:
					biggestExpectedCost = cost
					biggestCostDistribution = optionCostExpectation[cost]
			biggestCostDistributionStart = -1
			biggestCostDistributionEnd = -1
			for cost in optionCostExpectation:
				if optionCostExpectation[cost]==biggestCostDistribution:
					if biggestCostDistributionStart==-1:
						biggestCostDistributionStart = cost
						biggestCostDistributionEnd = cost
					else:
						biggestCostDistributionEnd = cost

			# no options this day
			if len(optionCostExpectation.keys()) == 0:
				continue

			expectedCost = 0
			direction = ""
			if biggestCostDistributionStart==0:
				expectedCost = biggestCostDistributionEnd
				direction = "down"
			elif biggestCostDistributionEnd==max(optionCostExpectation.keys()):
				expectedCost = biggestCostDistributionStart
				direction = "up"
			else:
				expectedCost = biggestCostDistributionStart
				direction = "to " + str(biggestCostDistributionEnd)

			if 'currentCost' in info:
				currentCost = 0.01 if info['currentCost']==0 else info['currentCost']
				expectedCostToCurrentRatio = float(expectedCost) / currentCost

			info['options'].append({
				'expireDate': baseDate,
				'expectedCost': expectedCost,
				'expectedCostToCurrentRatio':  expectedCostToCurrentRatio,
				'direction': direction
				})

	def fillGuess(self, info):
		data = self.api.webullQuotesGuess(self.tickerId)
		if not data:
			raise Exception('fillGuess: missing guess info')
		if not 'bullTotal' in data:
			raise Exception('fillGuess: empty guess info')
		info['social_guess'] = {
			'next_day': {
				'bulls': data['bullTotal'],
				'bears': data['bearTotal'],
				'bullRatio': data['bullPct'] / 100.0 if data['bullTotal']>0 else 0
			},
			'overall': {
				'bulls': data['guessCountInfo']['bullNum'],
				'bears': data['guessCountInfo']['bearNum'],
				'bullRatio': data['guessCountInfo']['bullPct'] / 100.0 if data['guessCountInfo']['bullNum']>0 else 0
			}
		}

	def collect(self):
		info = {}
		self._callWithException(lambda: self.fillTickerRealTime(info))
		self._callWithException(lambda: self.fillTickerFinancials(info))
		self._callWithException(lambda: self.fillCostDistribution(info))
		self._callWithException(lambda: self.fillCapitalFlow(info))
		self._callWithException(lambda: self.fillAnalytics(info))
		self._callWithException(lambda: self.fillShortInterest(info))
		#self._callWithException(lambda: self.fillInstitution(info))
		self._callWithException(lambda: self.fillGuess(info))
		self._callWithException(lambda: self.fillTrend(info))
		self._callWithException(lambda: self.fillSectors(info))
		self._callWithException(lambda: self.fillOptions(info))
		
		return info

class Storage:

	def __init__(self):
		self.client = pymongo.MongoClient('localhost', 27017)
		self.db = self.client.webull
		collectionName = datetime.datetime.now().strftime('tickers_%G_%m_%d')
		self.collection = self.db[collectionName]
		self.collection.create_index("ticker", unique=True)

	def insert(self, ticker, jsonData):
		jsonData["ticker"] = ticker
		self.collection.update_one(
			{"ticker": ticker},
			{"$set":jsonData},
			upsert=True)

	def contains(self, ticker):
		return self.collection.find_one({"ticker":ticker}) is not None


class Crawler:

	storage = None

	def enumerateTinkoffTickers(self, token):
		api = Api()
		stocks = api.tinkoffGetMarketStocks(token)
		tickers = []
		for stock in stocks['payload']['instruments']:
			tickerName = stock['ticker']
			stockType = stock['type']
			if stockType == "Stock":
				tickers.append(tickerName)
			else:
				raise Exception('unknown stock type = ' + stockType)
		return tickers

	def getStorage(self):
		if not self.storage:
			self.storage = Storage()
		return self.storage

	def crawlTicker(self, tickerName):
		ticker = TickerInfo(tickerName)
		return ticker.collect() if ticker.load() else None

	def crawlTickersDaily(self, token):
		tickers = self.enumerateTinkoffTickers(token)
		progress = 0
		total = len(tickers)
		print ("Total = " + str(total))
		for tickerName in tickers:
			print("Ticker = " + tickerName + " [%s%%]"%(str(round(progress/float(total) * 100, 2))))
			if not self.getStorage().contains(tickerName):	
				try:
					info = self.crawlTicker(tickerName)
					if info:
						self.getStorage().insert(tickerName, info)
				except Exception as e:
					print("Error | " + str(e))
			else:
				print('already exists in storage')
			progress += 1


class UserInterface:

	def __init__(self):
		parser = argparse.ArgumentParser(description='Webull Stock Crawler')
		subparsers = parser.add_subparsers(dest="command", help='Commands')
		crawl = subparsers.add_parser('crawl', help='Crawl all tickers to DB')
		crawl.add_argument('token', help='Tinkoff auth token')
		ticker = subparsers.add_parser('ticker', help='Crawls single ticker and prints')
		ticker.add_argument('ticker', help='Ticker')
		feed = subparsers.add_parser('feed', help='Feed by ticker')
		feed.add_argument('ticker', help='Ticker')
		feedComments = subparsers.add_parser('comments', help='Feed comments by uuid')
		feedComments.add_argument('id', help='ID of feed item')
		self.args = parser.parse_args()

	def go(self):
		if self.args.command == 'crawl':
			self.runCrawler(self.args.token)
		elif self.args.command == 'ticker':
			self.hitTicker(self.args.ticker)
		elif self.args.command == 'feed':
			self.printFeed(self.args.ticker)
		elif self.args.command == 'comments':
			self.printFeedItemComments(self.args.id)

	def runCrawler(self, token):
		crawler = Crawler()
		crawler.crawlTickersDaily(token)

	def hitTicker(self, ticker):
		crawler = Crawler()
		pprint.pprint(crawler.crawlTicker(ticker))

	def printFeedData(self, data):
		feed = []
		for message in data:
			feed.append({
				'time':  datetime.datetime.fromtimestamp(message['createTime']/1000),
				'msg':   message['content']['txt'] if 'txt' in message['content'] else "<not a text>",
				'+': message['counter']['thumbUps'],
				'-': message['counter']['thumbDowns'],
				'c': message['counter']['comments'],
				'id': message['uuid']
				})
		for msg in feed:
			msg['msg'] = '\n'.join(textwrap.wrap(msg['msg'], width=50))
		print(tabulate.tabulate(feed, headers='keys', tablefmt="grid"))

	def printFeed(self, ticker):
		ticker = TickerInfo(ticker)
		data = Api().webullQuotesFeed(ticker.load())
		self.printFeedData(data)

	def printFeedItemComments(self, uuid):
		data = Api().webullQuotesFeedItemComments(uuid)
		comments = []
		for item in data: 
			comments.append(item['comment'])
		self.printFeedData(comments)


UserInterface().go()