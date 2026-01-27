import pandas as pd
import matplotlib.pyplot as plt
import io

# ---------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------
# For the purpose of this exercise, I have embedded a subset of 
# real Global Temperature Anomaly data (NASA GISTEMP) as a CSV string.
# In a real scenario, you would use: df = pd.read_csv('filename.csv')

csv_data = """Year,Global_Anomaly_C,CO2_Concentration_ppm
2000,0.39,369.55
2001,0.53,371.14
2002,0.63,373.28
2003,0.61,375.80
2004,0.53,377.52
2005,0.67,379.80
2006,0.63,381.90
2007,0.66,383.79
2008,0.54,385.60
2009,0.65,387.43
2010,0.72,389.90
2011,0.61,391.65
2012,0.65,393.85
2013,0.67,396.52
2014,0.74,398.65
2015,0.90,400.83
2016,1.01,404.24
2017,0.92,406.55
2018,0.85,408.52
2019,0.97,411.44
2020,1.02,414.24
2021,0.85,416.45
2022,0.89,418.56
2023,1.17,421.08
"""

# Read the string as if it were a file
df = pd.read_csv(io.StringIO(csv_data))

# ---------------------------------------------------------
# 2. CLEAN DATA
# ---------------------------------------------------------
# Check for null values (Simulated cleaning step)
if df.isnull().values.any():
    print("Missing values detected. Filling with mean...")
    df = df.fillna(df.mean())
else:
    print("Data is clean: No missing values detected.")

# Ensure Year is treated as an integer (optional, but good practice)
df['Year'] = df['Year'].astype(int)

# ---------------------------------------------------------
# 3. ANALYSIS
# ---------------------------------------------------------
mean_temp = df['Global_Anomaly_C'].mean()
median_temp = df['Global_Anomaly_C'].median()
max_temp = df['Global_Anomaly_C'].max()
min_temp = df['Global_Anomaly_C'].min()

# Correlation between Year and Temperature (Trend)
correlation = df['Year'].corr(df['Global_Anomaly_C'])

print("\n--- GLOBAL TEMPERATURE ANALYSIS (2000-2023) ---")
print(f"Mean Anomaly: {mean_temp:.2f}°C")
print(f"Median Anomaly: {median_temp:.2f}°C")
print(f"Highest Anomaly: {max_temp:.2f}°C")
print(f"Lowest Anomaly: {min_temp:.2f}°C")
print(f"Correlation (Year vs Temp): {correlation:.4f} (Strong Positive Trend)")

# ---------------------------------------------------------
# 4. VISUALIZATION
# ---------------------------------------------------------
plt.figure(figsize=(12, 6))

# Plot 1: Line Chart for Temperature Trend
plt.subplot(1, 2, 1)
plt.plot(df['Year'], df['Global_Anomaly_C'], marker='o', linestyle='-', color='r', label='Temp Anomaly')
plt.title('Global Temperature Anomalies (2000-2023)')
plt.xlabel('Year')
plt.ylabel('Deviation from Baseline (°C)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Plot 2: Bar Chart comparing earlier vs later averages
# Split data into two decades for comparison
decade_1 = df[df['Year'] <= 2010]['Global_Anomaly_C'].mean()
decade_2 = df[df['Year'] > 2010]['Global_Anomaly_C'].mean()

plt.subplot(1, 2, 2)
bars = plt.bar(['2000-2010', '2011-2023'], [decade_1, decade_2], color=['blue', 'orange'])
plt.title('Average Temperature Comparison')
plt.ylabel('Avg Anomaly (°C)')
plt.ylim(0, 1.2)

# Add value labels on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, round(yval, 2), ha='center', va='bottom')

plt.tight_layout()
plt.show()