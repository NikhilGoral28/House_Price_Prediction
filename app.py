import streamlit as st
import pandas as pd
import joblib
import os

# Set page configuration
st.set_page_config(page_title="House Price Predictor", layout="centered")

# Custom CSS for premium feel
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stNumberInput, .stSelectbox {
        margin-bottom: 20px;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
    }
    .result-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-top: 30px;
    }
    .price-value {
        font-size: 2.5em;
        color: #27ae60;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏡 House Price Prediction")
st.write("Enter the details of the property to get an estimated market price.")

# Load the model
@st.cache_resource
def load_model():
    model_path = 'artifacts/house_price_model.pkl'
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

model = load_model()

if model is None:
    st.error("Model not found! Please ensure artifacts/house_price_model.pkl exists.")
else:
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        bhk = st.number_input("Number of BHK", min_value=1, max_value=10, value=2)
        area = st.number_input("Area (sq. ft.)", min_value=100, max_value=10000, value=1000)
        
    with col2:
        prop_type = st.selectbox("Property Type", ["Apartment", "Independent house", "Villa", "Studio apartment", "Row bunglow"])
        status = st.selectbox("Status", ["Ready to move", "Under construction"])

    # Predict button
    if st.button("Predict Price"):
        # Prepare input data
        input_df = pd.DataFrame([[bhk, prop_type, area, status]], 
                               columns=['BHK', 'Type', 'Area', 'Status'])
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        
        # Display results
        st.markdown(f"""
            <div class="result-box">
                <h3>Estimated Price</h3>
                <div class="price-value">₹ {prediction:,.2f}</div>
                <p>Calculated based on current market trends</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Machine Learning Model for House Price Prediction")
