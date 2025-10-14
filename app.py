	# app.py

from flask import Flask, jsonify, request 
import json
import os
import statistics
from datetime import datetime # ADDED for database timestamps
from api_service import (
    fetch_wellbeing_quote, 
    fetch_weather, 
    # log_wellbeing_data is removed
    fetch_forecast 
) 
from main import analyze_wellbeing_log as get_wellbeing_analysis 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import relationship 

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wellbeing.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- USER MODEL DEFINITION ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    tier = db.Column(db.String(10), default='free', nullable=False) 
    wellbeing_logs = db.relationship('WellbeingData', backref='user', lazy=True) 

    def __repr__(self):
        return f'<User {self.username}, Tier: {self.tier}>'

# --- NEW WELLBEING DATA MODEL (Replaces CSV structure) ---
class WellbeingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Link to the User
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Core User Input
    mood_score = db.Column(db.Integer, nullable=False)
    sleep_hours = db.Column(db.Float, nullable=False)
    exercise_minutes = db.Column(db.Integer, nullable=False)
    
    # External Data
    city = db.Column(db.String(50))
    temperature = db.Column(db.Float)
    
    # Daily Quote
    quote_text = db.Column(db.String(500))
    quote_author = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Log {self.timestamp} - Mood: {self.mood_score}>'

# --- USER TIER SIMULATION FUNCTION ---
def get_current_user():
    # Simulates fetching the logged-in user and creates a dummy user if none exists
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(username='test_user')).scalar_one_or_none()
        if not user:
            dummy_user = User(username='test_user', tier='free')
            db.session.add(dummy_user)
            db.session.commit()
            return dummy_user
        return user

# =================================================================
# FIX: ROOT ROUTE / HEALTH CHECK (NEW CODE ADDED HERE)
# This handles the root URL ('/') and ensures Render's health check receives a 200 OK.
# =================================================================
@app.route('/', methods=['GET'])
def health_check():
    """Returns a simple JSON response to confirm the service is running and healthy."""
    return jsonify({
        "status": "ok",
        "message": "Wellbeing API is running and healthy!"
    }), 200
# =================================================================


# ---------------------------------------
# Endpoint 1: Status & Daily Data
# ---------------------------------------
@app.route('/api/status', methods=['GET'])
def get_status_data():
    current_user = get_current_user() 
    
    try:
        quote_result = fetch_wellbeing_quote() 
        weather_result = fetch_weather("Waltham Forest") 

        response_data = {
            "status": "ok",
            "user_tier": current_user.tier,
            "quote": {
                "text": quote_result.get('quote', 'N/A'),
                "author": quote_result.get('author', 'N/A')
            },
            "weather": {
                "temp": weather_result.get('temp', 'N/A'),
                "feels_like": weather_result.get('feels_like', 'N/A'),
                "advice": "😌 Current weather conditions are generally mild." 
            }
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error on /api/status: {e}"}), 500


# ---------------------------------------
# Endpoint 2: Check-in (Logs Data to DB)
# ---------------------------------------
@app.route('/api/checkin', methods=['POST'])
def checkin():
    current_user = get_current_user() 
    
    try:
        data = request.get_json()

        required_fields = ['mood', 'sleep_hours', 'exercise_done', 'exercise_minutes']
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        quote_result = fetch_wellbeing_quote() 
        weather_result = fetch_weather("Waltham Forest")

        if not quote_result or not weather_result:
             return jsonify({"status": "error", "message": "External API failure preventing log."}), 500

        # Create and save a new database entry (replacing CSV logging)
        new_log = WellbeingData(
            user_id=current_user.id,
            mood_score=int(data['mood']),
            sleep_hours=float(data['sleep_hours']),
            exercise_minutes=int(data['exercise_minutes']),
            city="Waltham Forest",
            temperature=weather_result['temp'],
            quote_text=quote_result['quote'],
            quote_author=quote_result['author']
        )

        db.session.add(new_log)
        db.session.commit()

        return jsonify({"status": "success", "message": "Data logged to database successfully."}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error during checkin: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500


# ---------------------------------------
# Endpoint 3: Analysis (Gated)
# ---------------------------------------
@app.route('/api/analysis', methods=['GET'])
def analysis():
    current_user = get_current_user() 
    
    try:
        current_mood = 4 
        
        # Pass the database models and user ID to the analysis function
        analysis_data = get_wellbeing_analysis(
            current_mood=current_mood, 
            user_tier=current_user.tier, 
            user_id=current_user.id,
            db=db, 
            WellbeingData=WellbeingData
        ) 
        
        return jsonify({
            "status": "success",
            "tier": current_user.tier,
            "report": analysis_data 
        })

    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500


# ---------------------------------------
# Endpoint 4: Forecast
# ---------------------------------------
@app.route('/api/forecast', methods=['GET'])
def get_forecast_data():
    try:
        forecast_result = fetch_forecast("Waltham Forest") 
        
        if "error" in forecast_result:
            return jsonify({"status": "error", "message": forecast_result["error"]}), 500
            
        return jsonify({
            "status": "success",
            "data": forecast_result 
        })

    except Exception as e:
        print(f"Error during forecast fetch: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500 # 💡 SYNTAX ERROR IS FIXED HERE!


if __name__ == '__main__':
    print("--- Starting Flask API Backend with DB ---")
    with app.app_context():
        # Create the database file and table if they don't exist
        db.create_all() 
    # Use 0.0.0.0 for compatibility with Render environment
    app.run(debug=True, host='0.0.0.0')
