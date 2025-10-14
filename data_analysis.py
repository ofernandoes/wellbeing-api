import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np 

# Define the file paths
LOG_FILE_PATH = os.path.join("data_logs", "wellbeing_log.csv")
CHART_FILE_NAME = "wellbeing_full_report.png" 

def generate_wellbeing_charts(log_file=LOG_FILE_PATH, chart_file=CHART_FILE_NAME):
    """
    Reads the log data and generates a composite chart with 5 panels:
    1. Mood Trend, 2. Temp Trend, 3. Sleep Trend, 4. Exercise Trend, 5. Mood vs. Temp Scatter.
    """
    
    if not os.path.exists(log_file):
        print(f"[Chart] Skipping chart generation: Log file not found at {log_file}.")
        return None

    try:
        # 1. Read the data
        df = pd.read_csv(log_file)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Clean data: Drop rows that might be missing the required correlation columns
        columns_to_check = ['SleepHours', 'ExerciseMinutes']
        for col in columns_to_check:
            if col in df.columns:
                # Ensure values are float/numeric before dropping NaNs
                df[col] = pd.to_numeric(df[col], errors='coerce') 
                df = df.dropna(subset=[col])
        
        if df.empty or len(df) < 2:
            print("[Chart] Skipping chart generation: Not enough data points (min 2 required).")
            return None

        # Determine the number of plots needed (5 panels total)
        num_panels = 5 
        
        # 2. Create the figure and subplots
        fig = plt.figure(figsize=(12, 4 * num_panels)) # Dynamically adjust height
        gs = fig.add_gridspec(num_panels, 1)
        
        # --- Subplot 1: Mood Score Trend ---
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(df['Timestamp'], df['MoodScore'], marker='o', linestyle='-', color='#5B9BD5', label='Mood Score')
        ax1.set_title('Emotional Wellbeing Trend Over Time', fontsize=14)
        ax1.set_ylabel('Mood Score (1-5)', fontsize=10)
        ax1.set_yticks(range(1, 6))
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='upper left')

        # --- Subplot 2: Environmental Temperature Trend ---
        ax2 = fig.add_subplot(gs[1, 0], sharex=ax1) 
        ax2.plot(df['Timestamp'], df['Temperature'], marker='s', linestyle='-', color='#ED7D31', label='Temperature (°C)')
        ax2.set_title('Environmental Temperature Trend Over Time', fontsize=14)
        ax2.set_ylabel('Temperature (°C)', fontsize=10)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper left')
        
        # --- Subplot 3: Sleep Duration Trend ---
        ax3 = fig.add_subplot(gs[2, 0], sharex=ax1) 
        ax3.plot(df['Timestamp'], df['SleepHours'], marker='^', linestyle='-', color='#3CB371', label='Sleep Hours')
        ax3.set_title('Sleep Duration Trend Over Time', fontsize=14)
        ax3.set_ylabel('Sleep Hours', fontsize=10)
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.legend(loc='upper left')
        
        # --- Subplot 4: Exercise Duration Trend ---
        ax4 = fig.add_subplot(gs[3, 0], sharex=ax1) 
        ax4.plot(df['Timestamp'], df['ExerciseMinutes'], marker='x', linestyle='-', color='#9467BD', label='Exercise Minutes')
        ax4.set_title('Exercise Duration Trend Over Time', fontsize=14)
        ax4.set_ylabel('Exercise Minutes', fontsize=10)
        ax4.grid(True, linestyle='--', alpha=0.7)
        ax4.legend(loc='upper left')
        
        # --- Subplot 5: Mood vs. Temperature Scatter Plot (Bottom) ---
        ax5 = fig.add_subplot(gs[4, 0])
        ax5.scatter(df['Temperature'], df['MoodScore'], color='gray', alpha=0.7, edgecolors='black')
        
        if len(df['Temperature'].unique()) > 1 and len(df['MoodScore'].unique()) > 1:
            corr = df['Temperature'].corr(df['MoodScore']) 
            line_color = '#4CAF50' if corr >= 0.3 else ('#F44336' if corr <= -0.3 else 'lightgray')
            
            m, b = np.polyfit(df['Temperature'], df['MoodScore'], 1)
            ax5.plot(df['Temperature'], m * df['Temperature'] + b, color=line_color, linestyle='--', linewidth=2, label='Regression Line')
            
        ax5.set_title(f'Mood Score vs. Temperature (Visual Correlation)', fontsize=14)
        ax5.set_xlabel('Temperature (°C)', fontsize=10)
        ax5.set_ylabel('Mood Score (1-5)', fontsize=10)
        ax5.set_yticks(range(1, 6))
        ax5.grid(True, linestyle='--', alpha=0.7)
        
        # Remove tick labels from the shared x-axes
        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)
        plt.setp(ax4.get_xticklabels(), visible=False)

        # 3. Save the figure
        fig.autofmt_xdate(rotation=45)
        plt.tight_layout()
        plt.savefig(chart_file)
        plt.close(fig)

        print(f"\n[Chart] Wellbeing Full Report successfully generated: {chart_file}")
        
        return chart_file

    except Exception as e:
        print(f"\n[Chart] An error occurred during chart generation. Error: {e}")
        return None
