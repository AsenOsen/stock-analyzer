import pandas
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import json

# model predicts [5%,] growth at [50, ] days 
class AI:

	historyFile = None
	historyData = None
	sampleSize = None
	modelFile = None
	modelInfo = {}
	activeModel = None

	def create(historyFile, historySampleSize = None, modelFile = 'ai_model.joblib'):
		ai = AI()
		ai.historyFile = historyFile
		ai.sampleSize = historySampleSize
		ai.modelFile = modelFile
		ai.activeModel = ai._trainModel()
		return ai

	def load(historyFile, modelFile = 'ai_model.joblib'):
		ai = AI()
		ai.historyFile = historyFile
		ai.modelFile = modelFile
		ai.activeModel = joblib.load(ai.modelFile)
		return ai

	def printModelInfo(self):
		print(json.dumps(self.modelInfo, indent=4))
		print(json.dumps(self._getFeaturesImportance(), indent=4))

	def getPrediction(self, features:dict):
		data = []
		for feature in self._getFeatures():
			if feature in features:
				data.append(1 if features[feature] else 0)
		return self.activeModel.predict([data])[0]

	def _getFeaturesImportance(self):
		importances = list(self.activeModel.feature_importances_)
		feature_importances = [(feature, round(importance, 2)) for feature, importance in zip(self._getFeatures(), importances)]
		feature_importances = sorted(feature_importances, key = lambda x: x[1], reverse = True)
		return {pair[0]:pair[1] for pair in feature_importances}

	def _loadHistory(self):
		if self.historyData is None:
			self.historyData = pandas.read_csv(self.historyFile).query('days_diff >= 50')
		return self.historyData

	def _getFeatures(self):
		return list(self._loadHistory().columns)

	def _trainModel(self):
		features = self._loadHistory().sample(n=self.sampleSize) if self.sampleSize else self._loadHistory()
		features['has_growth'] = [1 if growth>5 else 0 for growth in features['growth_percent']]
		labels = np.array(features['has_growth'])
		features = features.drop(['has_growth', 'growth_percent', 'days_diff'], axis = 1)
		features = np.array(features)
		train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size = 0.2, random_state = 1337)
		model = RandomForestRegressor(n_estimators = 100, max_depth=15, min_samples_leaf=1,random_state = 1337).fit(train_features, train_labels)
		# store
		joblib.dump(model, self.modelFile)
		# evaluate
		predictions = model.predict(test_features)
		bar = 0.5
		percentiles = [[0.05, 0.95], [0.1, 0.9], [0.15, 0.85], [0.2, 0.8], [bar, bar]]
		self.modelInfo = {
			'features':{
				'train': len(train_features),
				'test': len(test_features),
			},
			'training': {}
		}
		for percentile in percentiles:
			hits_growth, actual_growth, hits_fall, actual_fall, total = 0, 0, 0, 0, 0
			for i in range(0, len(predictions)):
				# pass out of percentile values
				if percentile[0]<=predictions[i]<=percentile[1]:
					continue
				# collect growth predictions
				if test_labels[i]==1:
					hits_growth += 1 if predictions[i]>bar else 0
					actual_growth += 1
				# collect fall predictions
				if test_labels[i]==0:
					hits_fall += 1 if predictions[i]<bar else 0
					actual_fall += 1
				total += 1
			self.modelInfo['training'][str(int(percentile[0]*100))] = {
				'growth': round(hits_growth/actual_growth, 4),
				'fall': round(hits_fall/actual_fall, 4),
				'hits_growth': hits_growth,
				'hits_fall': hits_fall,
				'total': total
			}
		return model

if __name__ == '__main__':
	ai = AI.create(historyFile='history.csv', historySampleSize=700000, modelFile = 'ai_model.tmp.joblib')
	ai.printModelInfo()