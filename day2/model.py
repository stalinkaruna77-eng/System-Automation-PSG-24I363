import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
data = pd.read_csv("day2/data/sensor_history.csv")
X = data[["temperature", "pressure", "vibration", "rpm", "current"]]
y = data["state"]
model = DecisionTreeClassifier(random_state=42)
model.fit(X, y)
predictions = model.predict(X)
print("Actual states:",list(y))
print("Predicted states:",list(predictions))
print("Accuracy:", accuracy_score(y, predictions)*100,"%")