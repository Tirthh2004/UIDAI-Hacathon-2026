
import pandas as pd
import numpy as np
from forensic_analysis import ForensicAnalyzer
import time

# Create dummy data
dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='D')
states = ['StateA', 'StateB']
districts = ['Dist1', 'Dist2']
pincodes = ['110001', '110002']

data = []
for d in dates:
    for s in states:
        for dist in districts:
            for p in pincodes:
                data.append({
                    'date': d,
                    'state': s,
                    'district': dist,
                    'pincode': p,
                    'age_0_5': np.random.randint(0, 10),
                    'age_5_17': np.random.randint(0, 10),
                    'age_18_greater': np.random.randint(0, 50)
                })

enrol_df = pd.DataFrame(data)

bio_df = enrol_df.copy()
bio_df['bio_age_5_17'] = np.random.randint(0, 5, size=len(bio_df))
bio_df['bio_age_17_'] = np.random.randint(0, 5, size=len(bio_df))
bio_df = bio_df[['date', 'state', 'district', 'pincode', 'bio_age_5_17', 'bio_age_17_']]

demo_df = enrol_df.copy()
demo_df['demo_age_5_17'] = np.random.randint(0, 5, size=len(demo_df))
demo_df['demo_age_17_'] = np.random.randint(0, 5, size=len(demo_df))
demo_df = demo_df[['date', 'state', 'district', 'pincode', 'demo_age_5_17', 'demo_age_17_']]

print(f"Data shape: {enrol_df.shape}")

# Run analysis
start_time = time.time()
analyzer = ForensicAnalyzer(enrol_df, bio_df, demo_df)
results = analyzer.run_analysis()
end_time = time.time()

print(f"Analysis took {end_time - start_time:.2f} seconds")
print(results.head())
print("Columns:", results.columns)
