import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np

# ==========================================
# 1. CONFIGURATION SECTION (EDIT THESE)
# ==========================================
# File names of the data you downloaded
CROP_FILE = 'crops_state.csv'
POP_FILE = 'population_state.csv'

# Column names in your CROP dataset
CROP_STATE_COL = 'state'
CROP_YEAR_COL = 'date'
CROP_AREA_COL = 'planted_area'
CROP_PROD_COL = 'production'

# Column names in your POPULATION dataset
POP_STATE_COL = 'state'
POP_YEAR_COL = 'date'
POP_COUNT_COL = 'population'

# ==========================================
# 2. DATA LOADING & CLEANING
# ==========================================
print("Loading datasets...")
try:
    df_crop = pd.read_csv(CROP_FILE)
    df_pop = pd.read_csv(POP_FILE)
except FileNotFoundError as e:
    print(f"ERROR: Could not find your CSV files. Make sure they are in the same folder as this script. Details: {e}")
    exit()

print("Cleaning state names for merging...")
# Standardize text to avoid mismatches (e.g., 'Selangor ' vs 'SELANGOR')
df_crop[CROP_STATE_COL] = df_crop[CROP_STATE_COL].astype(str).str.strip().str.upper()
df_pop[POP_STATE_COL] = df_pop[POP_STATE_COL].astype(str).str.strip().str.upper()

# Map common DOSM variations
state_mapping = {
    'W.P. KUALA LUMPUR': 'KUALA LUMPUR',
    'W.P. LABUAN': 'LABUAN',
    'W.P. PUTRAJAYA': 'PUTRAJAYA',
    'PULAU PINANG': 'PENANG',
    'NEGERI SEMBILAN': 'N. SEMBILAN'
}
df_crop[CROP_STATE_COL] = df_crop[CROP_STATE_COL].replace(state_mapping)
df_pop[POP_STATE_COL] = df_pop[POP_STATE_COL].replace(state_mapping)

# ==========================================
# 3. MERGING DATASETS
# ==========================================
print("Merging crop and population data...")
df_merged = pd.merge(
    df_crop, 
    df_pop, 
    left_on=[CROP_YEAR_COL, CROP_STATE_COL], 
    right_on=[POP_YEAR_COL, POP_STATE_COL], 
    how='inner'
)

# Clean up duplicate columns from merge if any
if CROP_STATE_COL != POP_STATE_COL:
    df_merged = df_merged.drop(columns=[POP_STATE_COL])
if CROP_YEAR_COL != POP_YEAR_COL:
    df_merged = df_merged.drop(columns=[POP_YEAR_COL])

# ==========================================
# 4. FEATURE ENGINEERING (THE METRICS)
# ==========================================
print("Calculating Yield and Sufficiency metrics...")

# Drop rows where Area or Population is 0 or NaN to prevent division by zero
df_merged = df_merged.dropna(subset=[CROP_AREA_COL, POP_COUNT_COL, CROP_PROD_COL])
df_merged = df_merged[(df_merged[CROP_AREA_COL] > 0) & (df_merged[POP_COUNT_COL] > 0)]

# Metric 1: Yield Efficiency (Tonnes per Hectare)
df_merged['Yield_Per_Hectare'] = df_merged[CROP_PROD_COL] / df_merged[CROP_AREA_COL]

# Metric 2: Production Sufficiency (Tonnes per Person)
df_merged['Production_Per_Capita'] = df_merged[CROP_PROD_COL] / df_merged[POP_COUNT_COL]

# ==========================================
# 5. CALCULATING THE SFPI (INDEX CREATION)
# ==========================================
print("Generating the Sustainable Food Production Index (SFPI)...")

scaler = MinMaxScaler()

# Normalize the metrics to a 0-1 scale so they can be combined equally
df_merged[['Norm_Yield', 'Norm_Sufficiency']] = scaler.fit_transform(
    df_merged[['Yield_Per_Hectare', 'Production_Per_Capita']]
)

# SFPI Formula: 50% Yield Efficiency + 50% Sufficiency
df_merged['SFPI_Raw'] = (df_merged['Norm_Yield'] * 0.5) + (df_merged['Norm_Sufficiency'] * 0.5)

# Scale it to a 0-100 score (much easier to read on a PowerBI gauge or map)
df_merged['SFPI_Score'] = np.round(df_merged['SFPI_Raw'] * 100, 2)

# ==========================================
# 6. EXPORT FOR POWERBI
# ==========================================
# Keep only the columns necessary for the dashboard to keep the file lightweight
final_columns = [
    CROP_STATE_COL, 
    CROP_YEAR_COL, 
    CROP_AREA_COL, 
    CROP_PROD_COL, 
    POP_COUNT_COL,
    'Yield_Per_Hectare', 
    'Production_Per_Capita', 
    'SFPI_Score'
]
df_final = df_merged[final_columns]

output_filename = 'PowerBI_Ready_SFPI_Data.csv'
df_final.to_csv(output_filename, index=False)

print(f"\nSUCCESS! Your data is ready.")
print(f"File saved as: {output_filename}")
print(f"You can now import this directly into PowerBI.")