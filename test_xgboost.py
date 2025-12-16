import xgboost
import numpy as np
print("XGBoost imported.")
X = np.random.rand(10, 5)
y = np.random.rand(10)
print("Data created.")
model = xgboost.XGBRegressor(n_estimators=10)
model.fit(X, y)
print("XGBoost trained.")
