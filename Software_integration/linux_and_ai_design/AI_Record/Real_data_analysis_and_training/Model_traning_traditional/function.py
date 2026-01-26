import pandas as pd
import numpy as np 
import seaborn as sns
import joblib
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta

"""Load saved scalers for inverse transformation"""
scaler_va = joblib.load('pkl/scaler_va.pkl')
scaler_pfn = joblib.load('pkl/scaler_pfn.pkl') 
scaler_mapping = joblib.load('pkl/scaler_mapping.pkl')
scaler_latency = joblib.load('pkl/scaler_latency.pkl')
scaler_index = joblib.load('pkl/scaler_index.pkl')

def hex_to_int(hex_str):
    """Convert hex string to integer efficiently - handles multiple formats"""
    return hex_str.apply(lambda x: int(str(x).replace("0x",''),16)).astype(np.int64)



def inverse_transform_sequence(sequence_data):
    """Convert scaled sequence back to original values"""
    # sequence_data = np.array(sequence_data)
    result = []
    for data in sequence_data:
        original_data = [
            scaler_va.inverse_transform(data[0].reshape(-1,1)).astype(np.int64)[0][0],
            scaler_pfn.inverse_transform(data[1].reshape(-1,1)).astype(np.int64)[0][0],
            scaler_index.inverse_transform(data[2].reshape(-1,1)).astype(np.int64)[0][0],
            scaler_mapping.inverse_transform(data[3].reshape(-1,1)).astype(np.int64)[0][0],
            scaler_latency.inverse_transform(data[4].reshape(-1, 1)).astype(np.int64)[0][0],
        ]
        result.append(original_data)
    return np.array(result)

# More efficient vectorized version
def inverse_transform_sequence_vectorized(sequence_data):
    """Vectorized version for better performance"""
    sequence_data = np.array(sequence_data)
    
    va_original = scaler_va.inverse_transform(sequence_data[:, 0].reshape(-1, 1)).flatten().astype(np.int64)
    pfn_original = scaler_pfn.inverse_transform(sequence_data[:, 1].reshape(-1, 1)).flatten().astype(np.int64)
    folio_original = scaler_index.inverse_transform(sequence_data[:, 2].reshape(-1, 1)).flatten().astype(np.int64)
    mapping_original = scaler_mapping.inverse_transform(sequence_data[:, 3].reshape(-1, 1)).flatten().astype(np.int64)
    latency_original = scaler_latency.inverse_transform(sequence_data[:, 4].reshape(-1, 1)).flatten().astype(np.int64)
    
    return np.column_stack([va_original, pfn_original, folio_original, mapping_original, latency_original])

def inverse_transform_sequence_hex_vectorized(sequence_data):
    original_data = inverse_transform_sequence_vectorized(sequence_data)
    df_display = pd.DataFrame(original_data, 
                             columns=['VA', 'PFN', 'Folio_Index', 'Mapping', 'Latency_mcs'])
    
    # Add calculated columns
    df_display['VA_Hex'] = df_display['VA'].apply(lambda x: f"0x{x:x}")
    df_display['PFN_Hex'] = df_display['PFN'].apply(lambda x: f"0x{x:x}")
    df_display['Mapping_Hex'] = df_display['Mapping'].apply(lambda x: f"0x{x:x}")
    df_display['Latency_ns'] = df_display['Latency_mcs'] * 1000
    
    return np.array(df_display[['VA_Hex','PFN_Hex', 'Folio_Index', 'Mapping_Hex', 'Latency_ns']])

# ---------- Enhanced Display Functions ----------
def display_sequence_table(sequence_data, sequence_type="Input", seq_idx=0):
    """Display sequence in a formatted table"""
    original_data = inverse_transform_sequence_vectorized(sequence_data)
    
    # Create DataFrame with proper column names
    df_display = pd.DataFrame(original_data, 
                             columns=['VA', 'PFN', 'Folio_Index', 'Mapping', 'Latency_mcs'])
    
    # Add calculated columns
    df_display['VA_Hex'] = df_display['VA'].apply(lambda x: f"0x{x:x}")
    df_display['PFN_Hex'] = df_display['PFN'].apply(lambda x: f"0x{x:x}")
    df_display['Mapping_Hex'] = df_display['Mapping'].apply(lambda x: f"0x{x:x}")
    df_display['Latency_ns'] = df_display['Latency_mcs'] * 1000
    df_display['Time_Step'] = range(len(df_display))
    
    # Reorder columns
    display_cols = ['Time_Step', 'VA_Hex','PFN_Hex', 'Folio_Index', 'Mapping_Hex', 'Latency_ns']
    
    print(f"\n{'='*100}")
    print(f"{sequence_type} Sequence [{seq_idx}] - {len(sequence_data)} Events")
    print(f"{'='*100}")
    print(df_display[display_cols].to_string(index=False))
    
    # Statistical summary
    print(f"\nStatistical Summary:")
    print(f"VA Range: 0x{df_display['VA'].min():x} - 0x{df_display['VA'].max():x}")
    print(f"PFN Range: {df_display['PFN'].min()} - {df_display['PFN'].max()}")
    print(f"Latency: {df_display['Latency_ns'].min():.0f} - {df_display['Latency_ns'].max():.0f} ns (Avg: {df_display['Latency_ns'].mean():.0f} ns)")