## Description

This is the advanced stock data crawler which crawls data by tickers from wide variety of external sources and aggregates all collected data into local MongoDB storage.

Current data sources:
- https://www.webull.com
- https://stockbeep.com
- http://openinsider.com
- https://shortsqueeze.com
- https://stonks.news
- https://tradingview.com
- https://simplywall.st
- https://beststocks.ru

## Capabilities

1. Crawl full actual data by single ticker
2. Crawl full actual data by all tickers (available in tinkoff, you can easily change on your tickers set)
3. Generate report based on collected data using AI
4. Deploy telegram-bot for remote access to collected data

## Usage

Use `--help` for more info.

#### Crawler

Get full report by ticker:
```
crawler.py ticker <ticker>
```

Get full report by all tickers available in Tinkoff:
```
crawler.py crawl <tinkoff-token>
```

Read webull feed by ticker:
```
crawler.py webull_feed <ticker>
```
![Feed](https://i.ibb.co/RDtzphw/image.png)

Read webull comments to feed post:
```
crawler.py webull_comments <post-id>
```

#### Analyzer

Generate human-readable report by collected data (with AI):
```
analyzer.py report [--no-history]
```

Generate json data file by latest data:
```
analyzer.py latestdata --to-file <filename>
```

## Collected data example

```
{'_': {'wallstIdentity': '743F0744-8987-4339-B565-DEE3A93E9934',
       'webullIdentity': '913256135'},
 'anal': {'buyCount': 36,
          'buyCountRatio': 0.8372093023255814,
          'consensus': 'buy',
          'sellCount': 0,
          'targetCost': 186.92,
          'targetCostToCurrentRatio': 1.097399166324194},
 'beststocksAnalytics': {'analysts': 'StrongBuy',
                         'analystsPriceOverYearPotential': 0.1234,
                         'analystsTop': 'StrongBuy',
                         'analystsTopPriceOverYearPotential': 0.1442,
                         'bloggers': 'Bullish',
                         'bloggersBullish': 0.89,
                         'fundamental': 1.455673,
                         'hedge': 'Decreased',
                         'hedgeLastQuaterStocks': -3953456,
                         'insiders': 'SoldShares',
                         'insidersLast3MonthsSum': -1350750,
                         'investorsAllStat': {'attitude': 'VeryPositive',
                                              'avgSizeInPortfolio': 0.2018,
                                              'holdingPortfolios': 0.08404403336385198,
                                              'last30DaysTotalChange': 0.0015,
                                              'last7DaysTotalChange': 0.0038},
                         'investorsTopStat': {'attitude': 'VeryNegative',
                                              'avgSizeInPortfolio': 0.1557,
                                              'holdingPortfolios': 0.10849779219608903,
                                              'last30DaysTotalChange': -0.0426,
                                              'last7DaysTotalChange': -0.0003},
                         'news': {'attitude': 'Positive',
                                  'bearish': 0.2174,
                                  'bullish': 0.7826,
                                  'score': 0.7058},
                         'putCallRatio': 0.45367024462468,
                         'scoreRatio': 0.9,
                         'technical': 'Positive'},
 'closenessToHighest': 0.9310702962720018,
 'closenessToLowest': 0.682263840779663,
 'currentCost': 170.33,
 'dividend': {'annualYield': 0.00516,
              'has': True,
              'upcoming': {'amount': None, 'date': None, 'yeild': None}},
 'eps': 5.61,
 'exchangeCode': 'NASDAQ',
 'flows': {'inflow': 5425916816.1678,
           'inflowToOutflowRatio': 1.285172564178245,
           'largeflow': 1297542805.4556,
           'outflow': 4221936390.0265},
 'heldSharesRatio': 0.999278830326555,
 'holders': {'avgCost': 159.0151,
             'avgCostToCurrentRatio': 0.9335707156695825,
             'profitableSharesRatio': 0.73734},
 'income': {'netIncome': 94680000000.0,
            'netIncomeTrend': 0.058385622959090396,
            'netIncomeTrendLatest': 0.20528527580140757,
            'netIncomeYoyTrend': 0.5215126239747423,
            'netIncomeYoyTrendLatest': 4.9478072019055634,
            'operatingIncome': 108949000000.0,
            'operatingIncomeTrend': 0.04683047961226738,
            'operatingIncomeTrendLatest': 0.20351727899472036,
            'operatingIncomeYoyTrend': 1.62082278963896,
            'operatingIncomeYoyTrendLatest': 5.199394864824989,
            'revenue': 365817000000.0,
            'revenueTrend': 0.0390108770344646,
            'revenueTrendLatest': 0.10517666190129372,
            'revenueYoyTrend': 0.21935660605311552,
            'revenueYoyTrendLatest': 1.5926361189072802},
 'insiders': {'owend_%': 0.06},
 'name': 'Apple',
 'options': [{'direction': 'down',
              'expectedCost': 133,
              'expectedCostToCurrentRatio': 0.780837198379616,
              'expireDate': datetime.datetime(2022, 2, 4, 0, 0)},
             {'direction': 'up',
              'expectedCost': 250,
              'expectedCostToCurrentRatio': 1.4677390946985263,
              'expireDate': datetime.datetime(2022, 2, 11, 0, 0)},
             {'direction': 'up',
              'expectedCost': 275,
              'expectedCostToCurrentRatio': 1.6145130041683788,
              'expireDate': datetime.datetime(2022, 2, 18, 0, 0)},
             {'direction': 'up',
              'expectedCost': 250,
              'expectedCostToCurrentRatio': 1.4677390946985263,
              'expireDate': datetime.datetime(2022, 2, 25, 0, 0)},
             {'direction': 'up',
              'expectedCost': 250,
              'expectedCostToCurrentRatio': 1.4677390946985263,
              'expireDate': datetime.datetime(2022, 3, 4, 0, 0)},
             {'direction': 'up',
              'expectedCost': 210,
              'expectedCostToCurrentRatio': 1.232900839546762,
              'expireDate': datetime.datetime(2022, 3, 11, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2022, 3, 18, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2022, 4, 14, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2022, 5, 20, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2022, 6, 17, 0, 0)},
             {'direction': 'down',
              'expectedCost': 49,
              'expectedCostToCurrentRatio': 0.28767686256091113,
              'expireDate': datetime.datetime(2022, 7, 15, 0, 0)},
             {'direction': 'down',
              'expectedCost': 79,
              'expectedCostToCurrentRatio': 0.4638055539247343,
              'expireDate': datetime.datetime(2022, 8, 19, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2022, 9, 16, 0, 0)},
             {'direction': 'down',
              'expectedCost': 49,
              'expectedCostToCurrentRatio': 0.28767686256091113,
              'expireDate': datetime.datetime(2022, 10, 21, 0, 0)},
             {'direction': 'down',
              'expectedCost': 49,
              'expectedCostToCurrentRatio': 0.28767686256091113,
              'expireDate': datetime.datetime(2022, 11, 18, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2023, 1, 20, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2023, 3, 17, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2023, 6, 16, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2023, 9, 15, 0, 0)},
             {'direction': 'up',
              'expectedCost': 300,
              'expectedCostToCurrentRatio': 1.7612869136382316,
              'expireDate': datetime.datetime(2024, 1, 19, 0, 0)}],
 'pe': 30.38,
 'sectors': 'Phones & Handheld Devices|Computers, Phones & Household '
            'Electronics',
 'short': {'date': datetime.datetime(2022, 1, 14, 0, 0),
           'daysToCover': 1.0,
           'sharesCount': 90492581,
           'sharesRatio': 0.005540010141804665},
 'social_guess': {'next_day': {'bears': 89,
                               'bullRatio': 0.7129000000000001,
                               'bulls': 221},
                  'overall': {'bears': 3776, 'bullRatio': 0.65, 'bulls': 6989},
                  'robinhood': {'rank': 11}},
 'technical': {'breakout_magnitude': 2.1,
               'ta': {'day': {'ma': 0.8,
                              'oscillators': 0.09090909,
                              'summary': 0.44545455},
                      'week': {'ma': 0.93333333,
                               'oscillators': 0,
                               'summary': 0.46666667}},
               'trend_comment': '5D high'},
 'totalShares': 16334371000,
 'trend': {'costTrend1Y': 0.12032401883050867,
           'costTrend5Y': 0.26171702342781483,
           'currentCostToFareTrend1YRatio': 1.0101462699075816,
           'currentCostToFareTrend5YRatio': 1.1887667486347955,
           'latestRecordDate': datetime.datetime(2017, 2, 3, 0, 0)},
 'wallstAnalytics': {'financialHealthRatio': 0.5,
                     'futurePerformanceRatio': 0.3333333333333333,
                     'future_annualGrowthForecast': 0.039341,
                     'pastPerformanceRatio': 0.6666666666666666,
                     'past_annualPerformance': 0.136913,
                     'totalScoreRatio': 0.4166666666666667,
                     'unfairValueRatio': 0.16666666666666666,
                     'unfair_discountPercents': 6.807}}

```