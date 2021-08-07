import requests
import json
import datetime
import time
import pymongo
import statistics
import numpy
import argparse
import pprint
import tabulate
import textwrap
import urllib3

class HttpApi:

	def _request_internal(self, host, path, headers = {}, body = None, protocol = 'https://'):
		headers['User-Agent'] = 'okhttp/3.12.1'
		headers['Host'] = host
		url = protocol + host + path
		urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		if not body:	
			response = requests.get(url, headers = headers, timeout=5, verify=False).content
		else:
			response = requests.post(url, headers = headers, data = body, timeout=5, verify=False).content
		return response

	def request(self, host, path, headers = {}, body = None, protocol = 'https://'):
		try:
			return self._request_internal(host, path, headers, body, protocol)
		except:
			time.sleep(2)
			return self._request_internal(host, path, headers, body, protocol)


class JsonApi(HttpApi):

	def _getJson(self, host, path, headers = {}, body = None):
		response = self.request(host, path, headers, body)
		return json.loads(response) if response else None


class TinkoffApi(JsonApi):

	def tinkoffGetMarketStocks(self, token):
		response = self._getJson("api-invest.tinkoff.ru", "/openapi/market/stocks", {
			"Authorization":"Bearer %s" % token,
			"Accept": "application/json"
			}
		)
		return response


class StockbeepApi(JsonApi):

	# global siglethon cache
	breakouts = None
	trendings = None

	def getBreakoutStocks(self):
		if StockbeepApi.breakouts == None:
			StockbeepApi.breakouts = self._getJson('stockbeep.com', f'/table-data/breakout-stocks?country=us&time-zone=-180&sort-column=sd&sort-order=desc&_={int(time.time()*1000)}')
		return StockbeepApi.breakouts

	def getTrendingStocks(self):
		if StockbeepApi.trendings == None:
			StockbeepApi.trendings = self._getJson('stockbeep.com', f'/table-data/trending-stocks?country=us&time-zone=-180&sort-column=sd&sort-order=desc&_={int(time.time()*1000)}')
		return StockbeepApi.trendings


class OpeninsiderApi(HttpApi):

	# global siglethon cache
	lastweekpurchases = None

	def getLastWeekPurchases(self):
		if OpeninsiderApi.lastweekpurchases == None:
			OpeninsiderApi.lastweekpurchases = self.request('openinsider.com', '/top-insider-purchases-of-the-week', protocol='http://')
		from bs4 import BeautifulSoup
		soup = BeautifulSoup(OpeninsiderApi.lastweekpurchases, 'lxml')
		table = soup.find_all("table", {"class": "tinytable"})
		tickerStat = {}
		for record in table[0].find_all("tr"):
			fields = record.find_all("td")
			if len(fields)<12:
				continue
			ticker = fields[3].text.strip()
			qty = float(fields[9].text.replace(',','').strip()) 
			bought = float(fields[12].text.replace(',','').replace('$','').strip()) 
			if ticker not in tickerStat:
				tickerStat[ticker] = {}
			tickerStat[ticker]['money'] = tickerStat[ticker]['money']+bought if 'money' in tickerStat[ticker] else bought
			tickerStat[ticker]['qty'] = tickerStat[ticker]['qty']+qty if 'qty' in tickerStat[ticker] else qty
		return tickerStat


class StonksApi(JsonApi):

	# global siglethon cache
	wsb = None
	robinhood = None
	buildId = None

	def _getBuildId(self):
		if not StonksApi.buildId:
			data = str(self.request('stonks.news', ''))
			import re
			m = re.search('buildId"\:"(.*?)"', data)
			if m:
				StonksApi.buildId = m.group(1)
		return StonksApi.buildId

	def getWSBTop(self):
		if StonksApi.wsb == None:
			StonksApi.wsb = self._getJson('stonks.news', f'/_next/data/{self._getBuildId()}/summary.json')
		return StonksApi.wsb

	def	getRobinhoodTop(self):
		if StonksApi.robinhood == None:
			StonksApi.robinhood = self._getJson('stonks.news', f'/_next/data/{self._getBuildId()}/robinhood-top-100.json')
		return StonksApi.robinhood


class WallstApi(JsonApi):

	# global siglethon cache
	identity = None
	score = None

	def getIdentityByTicker(self, tickerName):
		if self.identity == None:
			body = '{"query":"%s"}' % (tickerName)
			headers = {"x-algolia-api-key": "be7c37718f927d0137a88a11b69ae419", "x-algolia-application-id": "17IQHZWXZW"}
			search = self._getJson('17iqhzwxzw-dsn.algolia.net','/1/indexes/companies/query', headers=headers, body = body)
			for hit in search['hits']:
				if hit['uniqueSymbol'].split(':')[1] == tickerName:
					self.identity = hit['objectID']
					break
				for listing in hit['listings']:
					if listing['uniqueSymbol'].split(':')[1] == tickerName:
						self.identity = hit['objectID']
						break
		return self.identity

	def getScore(self, tickerName):
		identity = self.getIdentityByTicker(tickerName)
		if self.score == None: 
			self.score = self._getJson('api.simplywall.st', f'/api/company/{identity}?include=score%2Cscore.snowflake')
		return self.score


class BeststocksApi(JsonApi):

	# global siglethon cache
	fullstats = None
	investors = None
	news = None

	def getFullStats(self, tickerName):
		if self.fullstats == None:
			headers = {'accept': 'application/json'}
			self.fullstats = self._getJson('beststocks.ru', f'/api/stocks?mode=full&ticker%5B0%5D={tickerName}&limit=1', headers=headers)
		return self.fullstats

	def getInvestorStats(self, tickerName):
		if self.investors == None:
			headers = {'accept': 'application/json'}
			self.investors = self._getJson('beststocks.ru', f'/api/stocks/{tickerName}/investor-statistic', headers=headers)
		return self.investors

	def getNewsStats(self, tickerName):
		if self.news == None:
			headers = {'accept': 'application/json'}
			self.news = self._getJson('beststocks.ru', f'/api/stocks/{tickerName}/news-sentiment', headers=headers)
		return self.news


class WebullApi(JsonApi):

	# cache
	responseSearchList = None
	responseChipQuery = None
	responseTickerGetTickerRealTime = None
	responseCapitalFlow = None
	responseSecuritiesAnalysis = None
	responseShortInterest = None
	responseInstitutionalHoldings = None
	responseInstitutionsDistribution = None
	responseTrendLastYear = None
	responseTrend5Y = None
	responseBriefInfo = None
	responseOptions = None
	responseGuess = None
	responseInsiderList = None
	responseInsiderInfo = None
	responseDividends = None

	def getSearchList(self, tickerName):
		if self.responseSearchList == None:
			self.responseSearchList = self._getJson('quotes-gw.webullfintech.com','/api/search/list?pageSize=20&pageIndex=1&busiModel=10000&keyword=%s' % (tickerName))
		return self.responseSearchList

	def getChipQuery(self, tickerId, startDate, endDate):
		if self.responseChipQuery == None:
			self.responseChipQuery = self._getJson('quotes-gw.webullfintech.com','/api/quotes/chip/query?tickerId=%s&startDate=%s&endDate=%s' % (tickerId, startDate, endDate))
		return self.responseChipQuery

	def getTickerGetTickerRealTime(self, tickerId):
		if self.responseTickerGetTickerRealTime == None:
			self.responseTickerGetTickerRealTime = self._getJson('quotes-gw.webullfintech.com','/api/quotes/ticker/getTickerRealTime?includeSecu=1&tickerId=%s' % (tickerId))
		return self.responseTickerGetTickerRealTime

	def getTickerFinancial(self, tickerId):
		return self._getJson('quotes-gw.webullfintech.com','/api/information/financial/index?tickerId=%s' % (tickerId))

	def getCapitalFlow(self, tickerId):
		if self.responseCapitalFlow == None:
			self.responseCapitalFlow = self._getJson('quotes-gw.webullfintech.com','/api/wlas/meteor/capitalflow/ticker?tickerId=%s&showHis=true&version=1' % (tickerId))
		return self.responseCapitalFlow

	def getSecuritiesAnalysis(self, tickerId):
		if self.responseSecuritiesAnalysis == None:
			self.responseSecuritiesAnalysis = self._getJson('quotes-gw.webullfintech.com','/api/information/securities/analysis?tickerId=%s&type=toolkit' % (tickerId))
		return self.responseSecuritiesAnalysis

	def getShortInterest(self, tickerId):
		if self.responseShortInterest == None:
			self.responseShortInterest = self._getJson('quotes-gw.webullfintech.com','/api/information/brief/shortInterest?tickerId=%s' % (tickerId))
		return self.responseShortInterest

	'''
	def getInstitutionalHoldings(self, tickerId):
		if self.responseInstitutionalHoldings == None:
			self.responseInstitutionalHoldings = self._getJson('securitiesapi.webullfintech.com','/api/securities/stock/v5/%s/institutionalHolding' % (tickerId))
		return self.responseInstitutionalHoldings

	def getInstitutionsDistribution(self, tickerId):
		if self.responseInstitutionsDistribution == None:
			self.responseInstitutionsDistribution = self._getJson('quotes-gw.webullfintech.com','/api/information/brief/holdersDetail?tickerId=%s&hasNum=0&pageSize=20&type=2' % (tickerId))
		return self.responseInstitutionsDistribution
	'''

	def getBriefInfo(self, tickerId):
		if self.responseBriefInfo == None:
			self.responseBriefInfo = self._getJson('quotes-gw.webullfintech.com','/api/information/stock/brief?tickerId=%s' % (tickerId))
		return self.responseBriefInfo

	def getTickerTrendLastYear(self, tickerId):
		if self.responseTrendLastYear == None:
			self.responseTrendLastYear = self._getJson('quoteapi.webullfintech.com','/api/quote/v2/tickerTrends/%s?trendType=y1' % (tickerId))
		return self.responseTrendLastYear

	def getTickerTrendFiveYear(self, tickerId):
		if self.responseTrend5Y == None:
			self.responseTrend5Y = self._getJson('quoteapi.webullfintech.com','/api/quote/v2/tickerTrends/%s?trendType=y5' % (tickerId))
		return self.responseTrend5Y

	def getOptions(self, tickerId):
		if self.responseOptions == None:
			# [3,2,4] - regular\weekly\quaterly
			body = '{"count":50,"expireCycle":[3,2,4],"type":0,"tickerId":%s,"direction":"all"}' % (tickerId)
			self.responseOptions = self._getJson('quotes-gw.webullfintech.com','/api/quote/option/strategy/list', body = body)
		return self.responseOptions

	def getFeed(self, tickerId):
		return self._getJson('quotes-gw.webullfintech.com','/api/social/feed/ticker/%s/posts?size=200' % (tickerId))

	def getFeedItemComments(self, uuid):
		return self._getJson('quotes-gw.webullfintech.com','/api/social/feed/post/%s/comments' % (uuid))

	def getGuess(self, tickerId):
		if self.responseGuess == None:
			self.responseGuess = self._getJson('quotes-gw.webullfintech.com','/api/social/guess/queryGuessInfoByTicker/%s' % (tickerId))
		return self.responseGuess

	'''
	def getInsiderList(self, tickerId):
		if self.responseInsiderList == None:
			body = '{"tickerId":%s, "pageSize":100, "acquireType": 1}' % (tickerId)
			self.responseInsiderList = self._getJson('quotes-gw.webullfintech.com','/api/information/company/queryInsiderList', body = body)
		return self.responseInsiderList
	'''

	def getInsiderInfo(self, tickerId):
		if self.responseInsiderInfo == None:
			self.responseInsiderInfo = self._getJson('quotes-gw.webullfintech.com','/api/information/company/queryInsiderDetail?tickerId=%s' % (tickerId))
		return self.responseInsiderInfo

	def getDividendinfo(self, tickerId):
		if self.responseDividends == None:
			self.responseDividends = self._getJson('securitiesapi.webullfintech.com',f'/api/securities/stock/v5/{tickerId}/dividendes')
		return self.responseDividends


class TickerInfo:

	tickerName = None
	tickerId = None
	webull_api = None
	stockbeep_api = None
	openinsider_api = None	
	stonks_api = None
	wallst_api = None
	beststocks_api = None

	def __init__(self, tickerName):
		# webull interprets "." as " "
		self.tickerName = tickerName.replace('.',' ')
		self.webull_api = WebullApi()
		self.stockbeep_api = StockbeepApi()
		self.openinsider_api = OpeninsiderApi()
		self.stonks_api = StonksApi()
		self.wallst_api = WallstApi()
		self.beststocks_api = BeststocksApi()

	def _callWithException(self, func):
		try:
			func()
		except Exception as e:
			print(f"{type(e).__name__} | {e}:{e.__traceback__.tb_next.tb_next.tb_lineno}")

	def loadInternal(self):
		data = self.webull_api.getSearchList(self.tickerName)
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
		data = self.webull_api.getChipQuery(self.tickerId, startDate.strftime('%Y-%m-%d'), endDate.strftime('%Y-%m-%d'))
		if not data:
			data = self.webull_api.getChipQuery(self.tickerId, startDate.strftime('%Y-%m-%d'), endDate.strftime('%Y-%m-%d'))
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
		data = self.webull_api.getTickerGetTickerRealTime(self.tickerId)
		if not data:
			raise Exception('fillCapitalFlow: missing ticker real time info')
		if not 'close' in data:
			raise Exception('fillCapitalFlow: unknown current cost')
		info['currentCost'] = float(data['close'])
		info['name'] = data['name']
		info['totalShares'] = int(data['totalShares']) if 'totalShares' in data else None
		info['pe'] = float(data['peTtm']) if 'peTtm' in data else None  # Trailing Twelve Months
		info['eps'] = float(data['epsTtm']) if 'epsTtm' in data else None # Trailing Twelve Months
		info['closenessToHighest'] = info['currentCost'] / float(data['fiftyTwoWkHigh'])  if 'fiftyTwoWkHigh' in data else None
		info['heldSharesRatio'] = float(data['outstandingShares'])/int(data['totalShares']) if 'outstandingShares' in data else None

	def fillTickerFinancials(self, info):
		data = self.webull_api.getTickerFinancial(self.tickerId)
		if 'simpleStatement' not in data or len(data['simpleStatement']) == 0:
			raise Exception('fillTickerFinancials: missing all info')
		incomeData = data['simpleStatement'][0]
		if incomeData['title'] == 'Income Statement':
			info['income'] = {
				'revenueTrend': self.calcTrendSlope([float(o['revenue']['value']) for o in incomeData['list'] if 'value' in o['revenue']])[0],
				'revenueTrendLatest': self.calcTrendSlope([float(o['revenue']['value']) for o in incomeData['list'] if 'value' in o['revenue']][-2:])[0],
				'revenueYoyTrend': self.calcTrendSlope([float(o['revenue']['yoy']) for o in incomeData['list'] if 'yoy' in o['revenue']])[0],
				'revenueYoyTrendLatest': self.calcTrendSlope([float(o['revenue']['yoy']) for o in incomeData['list'] if 'yoy' in o['revenue']][-2:])[0],
				'operatingIncomeTrend': self.calcTrendSlope([float(o['operatingIncome']['value']) for o in incomeData['list'] if 'value' in o['operatingIncome']])[0],
				'operatingIncomeTrendLatest': self.calcTrendSlope([float(o['operatingIncome']['value']) for o in incomeData['list'] if 'value' in o['operatingIncome']][-2:])[0],
				'operatingIncomeYoyTrend': self.calcTrendSlope([float(o['operatingIncome']['yoy'])  for o in incomeData['list'] if 'yoy' in o['operatingIncome']])[0],
				'operatingIncomeYoyTrendLatest': self.calcTrendSlope([float(o['operatingIncome']['yoy'])  for o in incomeData['list'] if 'yoy' in o['operatingIncome']][-2:])[0],
				'netIncomeTrend': self.calcTrendSlope([float(o['netIncomeAfterTax']['value']) for o in incomeData['list'] if 'value' in o['netIncomeAfterTax']])[0],
				'netIncomeTrendLatest': self.calcTrendSlope([float(o['netIncomeAfterTax']['value']) for o in incomeData['list'] if 'value' in o['netIncomeAfterTax']][-2:])[0],
				'netIncomeYoyTrend': self.calcTrendSlope([float(o['netIncomeAfterTax']['yoy'])  for o in incomeData['list'] if 'yoy' in o['netIncomeAfterTax']])[0],
				'netIncomeYoyTrendLatest': self.calcTrendSlope([float(o['netIncomeAfterTax']['yoy'])  for o in incomeData['list'] if 'yoy' in o['netIncomeAfterTax']][-2:])[0],
				}
			latest = incomeData['list'][len(incomeData['list'])-1]
			try:
				info['income']['revenue'] = float(latest['revenue']['value'])
			except:
				pass
			try:
				info['income']['operatingIncome'] = float(latest['operatingIncome']['value'])
			except:
				pass
			try:
				info['income']['netIncome'] = float(latest['netIncomeAfterTax']['value'])
			except:
				pass

	def fillCapitalFlow(self, info):
		data = self.webull_api.getCapitalFlow(self.tickerId)
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
		data = self.webull_api.getSecuritiesAnalysis(self.tickerId)
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
		data = self.webull_api.getShortInterest(self.tickerId)
		if len(data)>0:
			sharesRatio = float(data[0]['shortInterst']) / info['totalShares'] if 'totalShares'in info else None
			info['short'] =  {
				'date': datetime.datetime.strptime(data[0]['settlementDate'], "%Y-%m-%d"),
				'sharesCount': int(data[0]['shortInterst']),
				'sharesRatio': sharesRatio,
				'daysToCover': float(data[0]['daysToCover'])
			}
	
	'''
	def fillInstitutionHoldings(self, info):
		data = self.webull_api.webullSecuritiesInstitutionalHoldings(self.tickerId)
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
		data = self.webull_api.webullSecuritiesInstitutionsDistribution(self.tickerId)
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
	'''

	def calcTrendSlope(self, values):
		if len(values)<2:
			return (0, 0) 
		# define the power of values by max value
		extent = 0
		maxValue = max(values)
		while abs(maxValue) > 1:
			maxValue /= 10
			extent += 1
		# scale all x/y-values between 0 and 1
		values = [value/(10.0**extent) for value in values]
		measures = [i*(1.0/len(values)) for i in range(0, len(values))]
		# k
		xs = numpy.array(measures, dtype=numpy.float64)
		ys = numpy.array(values, dtype=numpy.float64)
		k = (((statistics.mean(xs)*statistics.mean(ys)) - statistics.mean(xs*ys)) /
		     ((statistics.mean(xs)**2) - statistics.mean(xs**2)))

		# b: y = kx+b => b = y-kx => b = ys-k*xs => b = mean(ys[i]-k*xs[i])
		b = statistics.mean([ys[i]-k*xs[i] for i in range(0, len(values))])
		latestValue = k*xs[len(xs)-1]+b
		latestValueTrendOffset = ys[len(ys)-1] / latestValue if not latestValue==0 else 0

		# look slope grapics
		'''
		from matplotlib import pyplot as plt 
		plt.plot(xs,ys) 
		trend = k * xs + b
		plt.plot(xs,trend) 
		plt.show()
		'''
		
		return (k, latestValueTrendOffset)

	def fillTrend(self, info):
		data = self.webull_api.getTickerTrendLastYear(self.tickerId)
		costYear = []
		for day in data['tickerKDatas']:
			if day['forwardKData']:
				costYear.insert(0, float(day['forwardKData']['close']))
		data = self.webull_api.getTickerTrendFiveYear(self.tickerId)
		costAll = []
		latestCost = None
		for day in data['tickerKDatas']:
			if 'forwardKData' in day:
				costAll.insert(0, float(day['forwardKData']['close']))
			if 'tradeTime' in day:
				latestCost = datetime.datetime.strptime(day['tradeTime'].split("T")[0], "%Y-%m-%d")

		trend1Y = self.calcTrendSlope(costYear)
		trend5Y = self.calcTrendSlope(costAll)

		info['trend'] = {
			'costTrend1Y': trend1Y[0],
			'costTrend5Y': trend5Y[0],
			'latestRecordDate': latestCost,
			'currentCostToFareTrend1YRatio': trend1Y[1],
			'currentCostToFareTrend5YRatio': trend5Y[1],
		}

	def fillSectors(self, info):
		data = self.webull_api.getBriefInfo(self.tickerId)
		if not data:
			raise Exception('fillSectors: missing sectors info')
		if not 'sectors' in data:
			raise Exception('fillSectors: empty sectors info')
		sectors = []
		for sector in data['sectors']:
			sectors.append(sector['name'])
		info['sectors'] = '|'.join(sectors)

	def fillOptions(self, info):
		data = self.webull_api.getOptions(self.tickerId)
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
			
			# look graphical representation
			'''
			print("---------------------------- " + str(baseDate))
			print(optionCostExpectation) # https://jsfiddle.net/canvasjs/RxeP6/
			'''

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
		# webull
		data = self.webull_api.getGuess(self.tickerId)
		info['social_guess'] = {}
		if data and 'bullTotal' in data:
			info['social_guess']['next_day'] = {
				'bulls': data['bullTotal'],
				'bears': data['bearTotal'],
				'bullRatio': data['bullPct'] / 100.0 if data['bullTotal']>0 else None
			}
			info['social_guess']['overall'] = {
				'bulls': data['guessCountInfo']['bullNum'],
				'bears': data['guessCountInfo']['bearNum'],
				'bullRatio': data['guessCountInfo']['bullPct'] / 100.0 if data['guessCountInfo']['bullNum']>0 else None
			}
		# wsb
		data = self.stonks_api.getWSBTop()
		if data and 'pageProps' in data and 'items' in data['pageProps']:
			for stock in data['pageProps']['items']:
				if stock['symbol'] == self.tickerName:
					info['social_guess']['wsb'] = {
						'mentions': stock['count'] if 'count' in stock else -1, 
						'popularity': stock['popularity'] if 'popularity' in stock else -1
					}
		# robinhood
		data = self.stonks_api.getRobinhoodTop()
		if data and 'pageProps' in data and 'items' in data['pageProps']:
			for stock in data['pageProps']['items']:
				if stock['symbol'] == self.tickerName:
					info['social_guess']['robinhood'] = {
						'rank': stock['basetable_id'] if 'basetable_id' in stock else -1
					}

	def fillTechnicalAnal(self, info):
		data = self.stockbeep_api.getBreakoutStocks()
		if not 'technical' in info:
			info['technical'] = {}
		for stock in data['data']:
			# <a href> tag parse
			if f">{self.tickerName}<" in stock['sscode']:
				info['technical']['breakout_magnitude'] = float(stock['sd']) # resistance for latest 5 day 
		data = self.stockbeep_api.getTrendingStocks()
		for stock in data['data']:
			# <a href> tag parse
			if f">{self.tickerName}<" in stock['sscode']:
				info['technical']['trend_comment'] = stock['sscomment'] 

	def fillInsiderPurchases(self, info):
		data = self.openinsider_api.getLastWeekPurchases()
		info['insiders'] = {}
		if self.tickerName in data:
			info['insiders'] = {}
			info['insiders']['purchasedPrice'] = round(data[self.tickerName]['money'], 2)
			info['insiders']['purchasedSharesToAllRatio'] = data[self.tickerName]['qty'] / float(info['totalShares'])
		data = self.webull_api.getInsiderInfo(self.tickerId)
		if 'owend' in data:
			info['insiders']['owend_%'] = float(data['owend'])

	def fillDividendInfo(self, info):
		data = self.webull_api.getDividendinfo(self.tickerId)
		if data and 'plans' in data and len(data['plans'])>0:
			latest = data['plans'][0]
			if 'payDate' not in latest or 'perShare' not in latest:
				raise Exception('fillDividendInfo: no data')
			published = datetime.datetime.strptime(latest['payDate'], "%Y-%m-%d")
			if published > (datetime.datetime.now() - datetime.timedelta(days=365)):
				info['dividendes'] = {
					'perShare_%': (float(latest['perShare'].split(' ')[1]) / info['currentCost'] * 100) if 'currentCost' in info and info['currentCost'] != 0 else None
					}

	def fillWallstAnalytics(self, info):
		score = self.wallst_api.getScore(self.tickerName)
		try:
			score = score['data']['score']['data']
		except:
			raise Exception('fillWallstAnalytics: no data')
		info['wallstAnalytics'] = {
			'unfairValueRatio': int(score['value']) / 6.0,
			'futurePerformanceRatio': int(score['future']) / 6.0,
			'pastPerformanceRatio': int(score['past']) / 6.0,
			'financialHealthRatio': int(score['health']) / 6.0,
			'totalScoreRatio': (int(score['total']) - int(score['income'])) / 24.0,
		}

	def fillBeststocksAnalytics(self, info):
		info['beststocksAnalytics'] = {}
		# stats
		try:
			fullStats = self.beststocks_api.getFullStats(self.tickerName)['data'][0]
			info['beststocksAnalytics'] = {
				'scoreRatio': fullStats['analysis']['smartScore'] / 10.0,
				'analysts': fullStats['analysis']['analystConsensus'],
				'analystsTop': fullStats['analysis']['topAnalystsRecommendationConsensus'],
				'analystsPriceOverYearPotential': fullStats['analysis']['pricePotential'],
				'analystsTopPriceOverYearPotential': fullStats['analysis']['topAnalystsPricePotential'],
				'bloggers': fullStats['analysis']['bloggerConsensus'],
				'bloggersBullish': fullStats['analysis']['bloggerBullishSentiment'],
				'insiders': fullStats['analysis']['insiderTrend'],
				'insidersLast3MonthsSum': fullStats['analysis']['insidersLast3MonthsSum'],
				'hedge': fullStats['analysis']['hedgeFundTrend'],
				'hedgeLastQuaterStocks': fullStats['analysis']['hedgeFundTrendValue'],
				'technical': fullStats['analysis']['sma'],
				'fundamental': fullStats['analysis']['fundamentalsReturnOnEquity']
			}
		except:
			print("Exception | fillBeststocksAnalytics: could not extract full stats from beststocks")
		### investors
		try:
			investorStats = self.beststocks_api.getInvestorStats(self.tickerName)
			info['beststocksAnalytics']['investorsTopStat'] = {
				'avgSizeInPortfolio': investorStats['bestInvestorStatsOverview']['averageAllocation'],
				'last7DaysTotalChange': investorStats['bestInvestorStatsOverview']['percentOverLast7Days'],
				'last30DaysTotalChange': investorStats['bestInvestorStatsOverview']['percentOverLast30Days'],
				'holdingPortfolios': investorStats['bestInvestorStatsOverview']['portfoliosHoldingStock'] / (investorStats['bestInvestorStatsOverview']['numberOfPortfolios'] or 1),
				'attitude': investorStats['bestInvestorStatsOverview']['sentiment']
			}
			info['beststocksAnalytics']['investorsAllStat'] = {
				'avgSizeInPortfolio': investorStats['investorStatsOverview']['averageAllocation'],
				'last7DaysTotalChange': investorStats['investorStatsOverview']['percentOverLast7Days'],
				'last30DaysTotalChange': investorStats['investorStatsOverview']['percentOverLast30Days'],
				'holdingPortfolios': investorStats['investorStatsOverview']['portfoliosHoldingStock'] / (investorStats['investorStatsOverview']['numberOfPortfolios'] or 1),
				'attitude': investorStats['investorStatsOverview']['sentiment']
			}
		except:
			print("Exception | fillBeststocksAnalytics: could not extract investors stats from beststocks")
		### news
		newsStats = self.beststocks_api.getNewsStats(self.tickerName)
		info['beststocksAnalytics']['news'] = {
			'bearish': newsStats['bullishBearish']['stockBearish'] if 'bullishBearish' in newsStats else None,
			'bullish': newsStats['bullishBearish']['stockBullish'] if 'bullishBearish' in newsStats else None,
			'score': newsStats['newsScore']['stockScore'] if 'newsScore' in newsStats else None,
			'attitude': newsStats['newsScore']['stockScoreSentiment'] if 'newsScore' in newsStats else None
		}

	def fillSettings(self, info):
		info['_'] = {
			'webullIdentity': self.tickerId,
			'wallstIdentity': self.wallst_api.getIdentityByTicker(self.tickerName)
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
		self._callWithException(lambda: self.fillTechnicalAnal(info))
		self._callWithException(lambda: self.fillInsiderPurchases(info))
		self._callWithException(lambda: self.fillDividendInfo(info))
		self._callWithException(lambda: self.fillWallstAnalytics(info))
		self._callWithException(lambda: self.fillBeststocksAnalytics(info))
		self._callWithException(lambda: self.fillSettings(info))
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
		stocks = TinkoffApi().tinkoffGetMarketStocks(token)
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
		data = WebullApi().getFeed(ticker.load())
		self.printFeedData(data)

	def printFeedItemComments(self, uuid):
		data = WebullApi().getFeedItemComments(uuid)
		comments = []
		for item in data: 
			comments.append(item['comment'])
		self.printFeedData(comments)


UserInterface().go()