import pandas
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

class AI:

	historyFile = None
	historyData = None
	latestFile = None
	sampleSize = None # count
	modelFile = 'ai_model.joblib'

	def __init__(self, historyFile, latestFile):
		self.historyFile = historyFile
		self.latestFile = latestFile

	def printLatestPredictionsByHistory(self):
		self._printer(self._trainModel())

	def printPredictionsBySavedModel(self):
		self._printer(self._loadModel())

	def _printer(self, model):
		print("-"*100, ' (feature importance)')
		self._printFeaturesImportance(model)
		print("-"*100, ' (predictions)')
		self._printPredictions(model, self.latestFile)

	def _loadHistory(self):
		if self.historyData is None:
			self.historyData = pandas.read_csv(self.historyFile)
		return self.historyData

	def _getFeatures(self):
		return list(self._loadHistory().columns)

	def _trainModel(self):
		features = self._loadHistory().sample(n=self.sampleSize) if self.sampleSize else self._loadHistory()
		#features = features.replace({0:False, 1:True})
		features['has_growth'] = features.growth_percent > 0
		labels = np.array(features['has_growth'])
		features = features.drop('has_growth', axis = 1).drop('growth_percent', axis = 1)
		features = np.array(features)
		train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size = 0.2, random_state = 1337)
		model = RandomForestRegressor(n_estimators = 100, max_depth=15, min_samples_leaf=1,random_state = 1337).fit(train_features, train_labels)
		# store
		joblib.dump(model, self.modelFile)
		# evaluate
		predictions = model.predict(test_features)
		bar = 0.5
		percentiles = [[0.05, 0.95], [0.1, 0.9], [0.15, 0.85], [0.2, 0.8], [bar, bar]]
		for percentile in percentiles:
			hits_true, total_true, hits_false, total_false = 0, 0, 0, 0
			for i in range(0, len(predictions)):
				if percentile[0]<=predictions[i]<=percentile[1]:
					continue
				hits_true += 1 if (predictions[i]>bar and test_labels[i]==True) else 0
				total_true += 1 if test_labels[i]==True else 0
				hits_false += 1 if (predictions[i]<bar and test_labels[i]==False) else 0
				total_false += 1 if test_labels[i]==False else 0
			print(f'Accuracy-{int(percentile[0]*100)} (true): {round(hits_true/total_true, 4)}')
			print(f'Accuracy-{int(percentile[0]*100)} (false):{round(hits_false/total_false, 4)}')
		return model

	def _loadModel(self):
		return joblib.load(self.modelFile)

	def _printFeaturesImportance(self, model):
		importances = list(model.feature_importances_)
		feature_importances = [(feature, round(importance, 2)) for feature, importance in zip(self._getFeatures(), importances)]
		feature_importances = sorted(feature_importances, key = lambda x: x[1], reverse = True)
		[print('Variable: {:40} Importance: {}'.format(*pair)) for pair in feature_importances]

	def _printPredictions(self, model, predictDataFile):
		features = pandas.read_csv(predictDataFile)
		features_without_meta = features.drop('name', axis=1).drop('ticker', axis = 1)
		features_without_meta = np.array(features_without_meta)
		features['future_growth_prob'] = model.predict(features_without_meta)
		features.drop(features.columns.difference(['ticker', 'name', 'future_growth_prob']), axis=1, inplace=True)
		features.sort_values(by=['future_growth_prob'], inplace=True)
		features.reset_index(drop=True, inplace=True)
		print(features.to_string())

#AI(historyFile='history.csv', latestFile='latest.csv').printLatestPredictionsByHistory()