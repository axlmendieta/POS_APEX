import pandas as pd
import numpy as np
from sqlalchemy import text
from datetime import timedelta
import xgboost as xgb
from sklearn.metrics import root_mean_squared_error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_sales_data(engine, location_id: int, product_id: int):
    """
    Fetches daily sales volume for a product at a location.
    Returns a DataFrame indexed by date with 'daily_sales_volume'.
    """
    query = text("""
        SELECT 
            DATE(t.created_at) as sale_date,
            SUM(td.quantity) as daily_sales_volume
        FROM transactions t
        JOIN transaction_details td ON t.id = td.transaction_id
        WHERE t.selling_location_id = :location_id
          AND td.product_id = :product_id
          AND t.status = 'completed'
        GROUP BY DATE(t.created_at)
        ORDER BY sale_date
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"location_id": location_id, "product_id": product_id})

    if df.empty:
        return df

    # Convert to datetime and set index
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df.set_index('sale_date', inplace=True)

    # Reindex to ensure all days are covered (fill gaps with 0)
    full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(full_idx, fill_value=0)
    df.index.name = 'sale_date'
    
    return df

def prepare_features(df):
    """
    Generates lag and temporal features.
    """
    df = df.copy()
    
    # Lag Features
    df['lag_1'] = df['daily_sales_volume'].shift(1) # Used for iterative prediction
    df['lag_7_sum'] = df['daily_sales_volume'].shift(1).rolling(window=7).sum()
    df['lag_30_sum'] = df['daily_sales_volume'].shift(1).rolling(window=30).sum()
    
    # Temporal Features
    df['day_of_week'] = df.index.dayofweek
    df['day_of_month'] = df.index.day
    df['month'] = df.index.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Drop NaNs created by lags
    df.dropna(inplace=True)
    return df

def train_model(df):
    """
    Trains an XGBoost regressor to predict daily_sales_volume.
    Returns model and residual standard deviation.
    """
    features = ['lag_1', 'lag_7_sum', 'lag_30_sum', 'day_of_week', 'day_of_month', 'month', 'is_weekend']
    target = 'daily_sales_volume'
    
    X = df[features]
    y = df[target]
    
    # Simple Train/Test Split (last 7 days as test to gauge RMSE)
    split_idx = len(df) - 7
    if split_idx < 1:
        # Not enough data, train on all
        model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
        model.fit(X, y)
        residuals = y - model.predict(X)
        rmse = np.sqrt(np.mean(residuals**2))
    else:
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        logger.info(f"Model Training RMSE (Last 7 Days): {rmse:.2f}")
        
        # Refit on full data for future prediction
        model.fit(X, y)
        residuals = y - model.predict(X)

    std_dev = np.std(residuals)
    return model, std_dev

def calculate_reorder_point(model, current_df, std_dev, lead_time_days=7, service_level_z=1.645):
    """
    Calculates RP = Expected_Lead_Time_Demand + Safety_Stock.
    Iteratively predicts next N days.
    Returns: RP, details_dict
    """
    # Start with the last known data row
    last_date = current_df.index.max()
    historical_sales = current_df['daily_sales_volume'].tolist() 
    
    predictions = []
    
    for i in range(1, lead_time_days + 1):
        future_date = last_date + timedelta(days=i)
        
        # Calculate features dynamically based on historical_sales + new predictions
        # Note: slicing with negative indices handles the rolling window
        
        lag_1 = historical_sales[-1]
        lag_7_sum = sum(historical_sales[-7:])
        lag_30_sum = sum(historical_sales[-30:]) if len(historical_sales) >= 30 else sum(historical_sales) * (30/len(historical_sales))
        
        features = {
            'lag_1': [lag_1],
            'lag_7_sum': [lag_7_sum],
            'lag_30_sum': [lag_30_sum],
            'day_of_week': [future_date.dayofweek],
            'day_of_month': [future_date.day],
            'month': [future_date.month],
            'is_weekend': [1 if future_date.dayofweek >= 5 else 0]
        }
        
        X_future = pd.DataFrame(features)
        
        # Predict
        pred = model.predict(X_future)[0]
        pred = max(0.0, float(pred)) # No negative sales
        predictions.append(pred)
        
        # Append prediction to history so next iteration's lags use it
        historical_sales.append(pred)
    
    expected_lead_time_demand = sum(predictions)
    
    # Safety Stock Calculation
    # SS = Z * sigma_d * sqrt(L)
    safety_stock = service_level_z * std_dev * np.sqrt(lead_time_days)
    
    reorder_point = expected_lead_time_demand + safety_stock
    
    return reorder_point, {
        "expected_lead_time_demand": expected_lead_time_demand,
        "safety_stock": safety_stock,
        "daily_predictions": predictions,
        "std_dev_residuals": std_dev
    }
