from database import SessionLocal, engine
from init_db import init_db
import crud
import models
import forecasting
from datetime import datetime, timedelta
import random
import numpy as np

def demo_forecasting():
    print("\n--- Forecasting Demo: Setup ---")
    init_db()
    db = SessionLocal()
    
    try:
        # 1. Create Data
        loc = crud.create_location(db, "Prediction Store", "store")
        cat = crud.create_category(db, "Predictable Items")
        prod = crud.create_product(db, "Seasonal Widget", 20.0, cat.id)
        emp = crud.create_employee(db, "forecaster", "admin", "hash", loc.id)
        
        print(f"Generating 90 days of historical sales for {prod.name}...")
        
        start_date = datetime.now() - timedelta(days=90)
        
        # Pattern: Base 10 + Random(0-5) + Weekend Boost(5) + Linear Trend (0.1 per day)
        transactions_to_add = []
        details_to_add = []
        
        for i in range(90):
            current_date = start_date + timedelta(days=i)
            
            # Demand Logic
            base = 10
            noise = random.randint(0, 5)
            weekend = 5 if current_date.weekday() >= 5 else 0
            trend = i * 0.1
            
            quantity = int(base + noise + weekend + trend)
            
            if quantity > 0:
                # Manually create transaction to set historical date
                # Note: 'created_at' is server_default=now(), so we must explicitly set it if allowed or update after
                # SQLAlchemy allows setting on init
                trans = models.Transaction(
                    selling_location_id=loc.id,
                    employee_id=emp.id,
                    total_amount=quantity * 20.0,
                    status='completed',
                    created_at=current_date,
                    employee=emp, # Relationship population helps flush sometimes
                    selling_location=loc
                )
                db.add(trans)
                db.flush() # Get ID
                
                detail = models.TransactionDetail(
                    transaction_id=trans.id,
                    product_id=prod.id,
                    quantity=quantity,
                    unit_price=20.0,
                    unit_cost_at_sale=10.0
                )
                db.add(detail)
        
        db.commit()
        print("Historical data generated.")

        # 2. Forecasting Pipeline
        print("\n--- Running ETL & Feature Engineering ---")
        df = forecasting.fetch_sales_data(engine, loc.id, prod.id)
        print(f"Data Fetched: {len(df)} rows.")
        # print(df.tail())
        
        df_features = forecasting.prepare_features(df)
        print(f"Features Prepared: {len(df_features)} rows (after lagging).")
        # print(df_features.tail())

        # 3. Model Training
        print("\n--- Training Model (XGBoost) ---")
        model, std_dev = forecasting.train_model(df_features)
        print(f"Model Trained. Residual Std Dev: {std_dev:.2f}")

        # 4. Reorder Point Calculation
        print("\n--- Calculating Reorder Point ---")
        rp, details = forecasting.calculate_reorder_point(model, df_features, std_dev)
        
        print(f"Projected Demand (Next 7 Days): {details['expected_lead_time_demand']:.2f}")
        print(f"Safety Stock (95% Service): {details['safety_stock']:.2f}")
        print(f"CALCULATED REORDER POINT: {rp:.2f}")
        print(f"Daily Predictions: {[round(x,1) for x in details['daily_predictions']]}")
        
        print("\nFORECASTING DEMO COMPLETED SUCCESSFULLY!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEMO FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    demo_forecasting()
