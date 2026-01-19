
import pandas as pd
import numpy as np

# Create dummy data
dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
data = []
for d in dates:
    data.append({'date': d, 'group': 'A', 'val': 10})
    data.append({'date': d, 'group': 'B', 'val': 20})

df = pd.DataFrame(data)

# Sort strictly
df = df.sort_values(['group', 'date'])
df_idx = df.set_index('date')

print("Index:", df_idx.index)

# Groupby rolling
try:
    g = df_idx.groupby('group')['val']
    r = g.rolling('3D').mean()
    print("\nRolling result index:", r.index)
    print("\nRolling result values:\n", r)
    
    # Assign back
    # df_idx['rolled'] = r.values # Check if this works
    # Or align?
    
    # Verify alignment
    # r has index (group, date)
    # df_idx has index (date)
    # But df_idx is sorted by group, then date.
    
    # Let's see if we can align easily
    r_reset = r.reset_index(level=0, drop=True) # Drop group level, keep date
    print("\nReset result index:", r_reset.index)
    
    # If duplicate dates exist (which they do, one for A, one for B), 
    # r_reset has duplicate dates.
    # df_idx has duplicate dates.
    # Because df_idx is sorted by group, date:
    # A-1, A-2, ... B-1, B-2...
    # r is:
    # A-1, A-2, ... B-1, B-2...
    # So direct assignment should work?
    
    df_idx['rolled'] = r.values
    print("\nAssigned successfully.")
    print(df_idx.head())
    print(df_idx.tail())

except Exception as e:
    print(f"\nError: {e}")
