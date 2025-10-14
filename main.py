# In main.py

# Removed old CSV-related imports as they are now handled by the database
import os
import statistics
from scipy.stats import pearsonr

# --- ANALYSIS HELPERS (Keep these functions unchanged) ---

def get_mood_description(score):
    if score == 5: return "Excellent"
    elif score == 4: return "Good"
    elif score == 3: return "Neutral"
    elif score == 2: return "Poor"
    else: return "Bad"

def get_correlation_feedback(r_value, factor_name):
    r_abs = abs(r_value)
    sign = "positively" if r_value > 0 else "negatively"

    if r_abs >= 0.7: strength = "very strong"
    elif r_abs >= 0.5: strength = "strong"
    elif r_abs >= 0.3: strength = "moderate"
    else: strength = "weak or non-existent"
        
    if strength == "weak or non-existent":
        return f"No significant correlation between mood and {factor_name.lower()}."
    else:
        return f"A **{strength}** correlation (r={r_value:.3f}). Mood tends to change **{sign}** with {factor_name.lower()}."


# --- MODIFIED ANALYSIS FUNCTION ---
# NOTE: Function now accepts db, WellbeingData, and user_id from app.py
def analyze_wellbeing_log(current_mood, user_tier, user_id, db, WellbeingData):
    """
    MODIFIED: Reads the log file from the database for a specific user, 
    calculates stats, and returns a dictionary for the API.
    """
    # 💡 DATA LOADING LOGIC IS NOW A DATABASE QUERY
    logs = db.session.execute(
        db.select(WellbeingData).filter_by(user_id=user_id)
        .order_by(WellbeingData.timestamp.asc())
    ).scalars().all()
    
    # Extract data points from the list of database objects
    temperatures = [log.temperature for log in logs if log.temperature is not None]
    moods = [log.mood_score for log in logs]
    sleep_hours = [log.sleep_hours for log in logs]
    exercise_minutes = [log.exercise_minutes for log in logs]

    data_entries = len(moods)

    if data_entries < 3:
        return {"error": f"Only {data_entries} entries logged. Need a minimum of 3 for analysis."}

    # Calculations
    avg_mood = sum(moods) / data_entries
    today_mood_desc = get_mood_description(current_mood)
    
    # Ensure statistics.stdev can be calculated (requires 2+ entries)
    temp_stdev = statistics.stdev(temperatures) if len(temperatures) > 1 else 0.0
    avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0.0
    
    # --- Analysis Data Structure (Dictionary) ---
    report = {}
    
    # 1. Mood Feedback
    if current_mood > avg_mood: mood_comparison = "Above average. 👍"
    elif current_mood < avg_mood: mood_comparison = "Below average. 😔"
    else: mood_comparison = "In line with average."
        
    report['mood_summary'] = {
        'today_mood': current_mood,
        'today_mood_desc': today_mood_desc,
        'avg_mood': f"{avg_mood:.1f}",
        'comparison_feedback': mood_comparison
    }
    
    # 2. Environmental Feedback
    if temp_stdev > 5.0: temp_fluc_feedback = f"Volatile (Std Dev: {temp_stdev:.1f}°C)."
    else: temp_fluc_feedback = f"Consistent (Std Dev: {temp_stdev:.1f}°C)."

    report['env_summary'] = {
        'avg_temp': f"{avg_temp:.1f}",
        'temp_fluc_feedback': temp_fluc_feedback
    }

    # --- PREMIUM TIER GATING ---
    report['correlations'] = {}
    
    if user_tier == 'premium':
        # Correlation 1: Mood vs. Temperature
        if len(set(temperatures)) > 1 and len(set(moods)) > 1:
            r_temp, _ = pearsonr(temperatures, moods)
            report['correlations']['temperature'] = get_correlation_feedback(r_temp, "Temperature")
        else:
            report['correlations']['temperature'] = "Not enough data variation yet to calculate."

        # Correlation 2: Mood vs. Sleep Hours
        if len(sleep_hours) >= 3 and len(set(sleep_hours)) > 1 and len(set(moods[-len(sleep_hours):])) > 1:
            r_sleep, _ = pearsonr(sleep_hours, moods[-len(sleep_hours):]) 
            report['correlations']['sleep'] = get_correlation_feedback(r_sleep, "Sleep Hours")
        else:
            report['correlations']['sleep'] = "Not enough sleep data variation yet to calculate."
            
        # Correlation 3: Mood vs. Exercise Minutes
        if len(exercise_minutes) >= 3 and len(set(exercise_minutes)) > 1 and len(set(moods[-len(exercise_minutes):])) > 1:
            r_exercise, _ = pearsonr(exercise_minutes, moods[-len(exercise_minutes):]) 
            report['correlations']['exercise'] = get_correlation_feedback(r_exercise, "Exercise Minutes")
        else:
            report['correlations']['exercise'] = "Not enough exercise data variation yet to calculate."

    else:
        report['correlations']['gating_message'] = "Upgrade to Premium to unlock personalized insights!"
        
    return report
