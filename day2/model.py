import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
data=pd.read_csv("day2/data/day2_sample.csv")
x=data[["temperature","pressure","vibration","rpm","current"]]
y=data["state"]
model=DecisionTreeClassifier(random_state=100)
model.fit(x,y)
predictions=model.predict(x)
print("Actual states:",list(y))
print("Predicted states:",list(predictions))
print("Accuracy: ",accuracy_score(y,predictions)*100,"%")