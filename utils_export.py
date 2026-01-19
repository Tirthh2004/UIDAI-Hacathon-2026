import streamlit as st
import pandas as pd
from datetime import datetime

def render_export_button(data_df, file_label, key_unique):
    """
    Renders a download button aligned to the right.
    """
    if data_df is None or data_df.empty:
        return

    # 1. Create columns to push button to the right (85% empty, 15% button)
    col_space, col_btn = st.columns([0.85, 0.15])
    
    with col_btn:
        # 2. Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d")
        file_name = f"UIDAI_{file_label}_{timestamp}.csv"
        
        # 3. Convert to CSV
        csv = data_df.to_csv(index=False).encode('utf-8')
        
        # 4. The Button
        st.download_button(
            label="📥 Download .csv report",
            data=csv,
            file_name=file_name,
            mime="text/csv",
            key=f"btn_export_{key_unique}"
        )