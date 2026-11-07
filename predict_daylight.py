import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

TARGET = "sun_201812211200_median"
FEATURES = [
    "layout_area", "layout_perimeter", "layout_compactness",
    "layout_number_of_windows", "layout_window_perimeter",
    "layout_number_of_doors", "layout_door_perimeter",
    "layout_open_perimeter", "layout_mean_walllengths", "layout_std_walllengths",
]

df = pd.read_csv("simulations.csv", usecols=FEATURES + [TARGET], nrows=200_000).dropna()
X_train, X_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=0)

model = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=0)
model.fit(X_train, y_train)

print("R2:", round(r2_score(y_test, model.predict(X_test)), 3))
print(pd.Series(model.feature_importances_, FEATURES).sort_values(ascending=False))