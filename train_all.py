import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import xgboost as xgb
import joblib
import os

# Load dataset
df = pd.read_csv('Synthetic4_local_housePrice.csv')
df['Status'] = df['Status'].str.strip().str.capitalize()
df['Type'] = df['Type'].str.strip().str.capitalize()
df['Price_per_sqft'] = df['Price'] / df['Area']

X = df[['BHK', 'Type', 'Area', 'Status']]
y = df['Price_per_sqft']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Common Preprocessor
type_order = ['Apartment', 'Row bunglow', 'Independent house']
status_order = ['Under construction', 'Ready to move']

preprocessor = ColumnTransformer(
    transformers=[
        ('ord', OrdinalEncoder(categories=[type_order, status_order]), ['Type', 'Status'])
    ],
    remainder='passthrough'
)

# Model definitions
models = {
    'linear_regression': LinearRegression(),
    'random_forest': RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
    'xgboost': xgb.XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=6, random_state=42)
}

if not os.path.exists('artifacts'):
    os.makedirs('artifacts')

for name, model in models.items():
    print(f"Training {name}...")
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])
    pipeline.fit(X_train, y_train)
    
    filename = f'artifacts/{name}_model.pkl'
    joblib.dump(pipeline, filename)
    print(f"Saved: {filename}")

# Also save the current production name as a copy of xgboost (default)
joblib.dump(models['xgboost'], 'artifacts/house_price_model.pkl') # Keep this for legacy support
print("\nAll models trained and saved in artifacts/")
