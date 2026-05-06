import logging
import json
from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import os
from datetime import datetime
from waitress import serve

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cache for models and metadata
cached_data = {
    'model': None,
    'metadata': None
}

def load_resources():
    """Load model and metadata once at startup."""
    try:
        # Load Model
        model_path = 'artifacts/best_model.pkl'
        if os.path.exists(model_path):
            cached_data['model'] = joblib.load(model_path)
            logger.info("Successfully loaded best_model.pkl")
        
        # Load Metadata
        meta_path = 'artifacts/model_metadata.json'
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                cached_data['metadata'] = json.load(f)
                logger.info(f"Using model: {cached_data['metadata'].get('model_name')}")
    except Exception as e:
        logger.error(f"Error loading resources: {str(e)}")

# Initialize on startup
load_resources()

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metadata')
def get_metadata():
    if cached_data['metadata']:
        return jsonify(cached_data['metadata'])
    return jsonify({'error': 'Metadata not found'}), 404

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Input Validation
        bhk = data.get('bhk')
        prop_type = data.get('type')
        area = data.get('area')
        status = data.get('status')

        if None in [bhk, prop_type, area, status]:
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            bhk = int(bhk)
            area = float(area)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid numeric values for BHK or Area'}), 400

        if area < 500 or area > 10000:
            return jsonify({'error': 'Area must be between 500 and 10,000 sqft'}), 400
        
        if bhk <= 0:
            return jsonify({'error': 'BHK must be a positive value'}), 400

        # Model Execution
        if cached_data['model'] is None:
            load_resources() # Try reloading if missing
            if cached_data['model'] is None:
                return jsonify({'error': 'Prediction engine is offline'}), 503

        input_df = pd.DataFrame([[bhk, prop_type, area, status]], 
                               columns=['BHK', 'Type', 'Area', 'Status'])
        
        prediction_per_sqft = cached_data['model'].predict(input_df)[0]
        total_price = prediction_per_sqft * area
        
        # Metrics & Range
        low_estimate = total_price * 0.95
        high_estimate = total_price * 1.05
        
        # Comparison logic
        if status == "Ready to move":
            other_status = "Under construction"
            other_price = total_price / 1.1
        else:
            other_status = "Ready to move"
            other_price = total_price * 1.1

        logger.info(f"Prediction successful: {prop_type} | {area}sqft | Value: {total_price:.2f}")

        return jsonify({
            'success': True,
            'prediction': round(total_price, 2),
            'price_per_sqft': round(prediction_per_sqft, 2),
            'range_low': round(low_estimate, 2),
            'range_high': round(high_estimate, 2),
            'model_info': cached_data['metadata'],
            'comparison': {
                'current_status': status,
                'current_price': round(total_price, 2),
                'other_status': other_status,
                'other_price': round(other_price, 2)
            }
        })

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An internal error occurred during prediction'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))

    try:
        logger.info(f"Starting production server with Waitress on port {port}...")
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        logger.warning("Waitress not found. Falling back to Flask dev server.")
        app.run(host='0.0.0.0', port=port, debug=True)
