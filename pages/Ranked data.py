import streamlit as st
import pandas as pd
import pickle

# Configure page to use full width
st.set_page_config(
    page_title="Ranked data",
    page_icon="🔬",
    layout="wide",  # This makes it use full width
)

# Function to load dataset
def load_dataset(dataset_type):
    filename = "data/dashboard_data_full.pickle" if dataset_type == 'full' else "data/dashboard_data_grouped.pickle"
    with open(filename, "rb") as f:
        return pickle.load(f)

# Initialize session state
if 'current_df' not in st.session_state:
    st.session_state.current_df = 'full'

if 'rankings' not in st.session_state:
    st.session_state.rankings = {'full': {}, 'grouped': {}}

# hierarchical_weights are already initialized in the weighting scheme page

# Toggle for dataset selection
show_all_data = st.sidebar.toggle(
    "Show all data", 
    value=st.session_state.current_df == 'full',
    help="Toggle between full dataset and grouped dataset"
)

# Update current_df based on toggle
new_df_type = 'full' if show_all_data else 'grouped'

# Load dataset and apply ranking if toggle changed or df not loaded
if st.session_state.current_df != new_df_type or 'df' not in st.session_state:
    st.session_state.current_df = new_df_type
    
    # Load fresh dataset
    st.session_state.df = load_dataset(st.session_state.current_df)
    
    # Apply ranking if exists
    current_rankings = st.session_state.rankings.get(st.session_state.current_df, {})
    if current_rankings:
        st.session_state.df['Final Score'] = st.session_state.df.index.map(current_rankings).fillna(0)
        st.session_state.df = st.session_state.df.sort_values('Final Score', ascending=False)

# Toggle filter for old phases
filter_old_phases = st.sidebar.toggle(
    "Hide phases completed 5+ years ago", 
    value=False,
    #help="Show only entries where 'Highest phase completed 5 years ago' is False"
)

# Function to calculate effective weight for each column
def get_effective_weight(column_name):
    for param_name, param_data in st.session_state.hierarchical_weights.items():
        if column_name in param_data['sub_params']:
            param_weight = param_data['weight']
            sub_weight = param_data['sub_params'][column_name]
            effective_weight = (param_weight / 100) * (sub_weight / 100) * 100
            return effective_weight
    return None

# Create a copy of the dataframe to modify column names
df_display = st.session_state.df.copy()

# Apply filter to dataframe if toggle is on
if filter_old_phases:
    df_to_display = df_display[df_display['Highest Phase Completed 5yrs Ago'] == False].copy()
    dataset_name = "full" if show_all_data else "grouped"
    st.sidebar.caption(f"Showing {len(df_to_display)} of {len(st.session_state.df)} entries ({dataset_name} dataset)")
else:
    df_to_display = df_display.copy()
    dataset_name = "full" if show_all_data else "grouped"
    st.sidebar.caption(f"Showing {len(df_to_display)} entries ({dataset_name} dataset)")

# Update column names to include weights in brackets
new_column_names = {}
for col in df_to_display.columns:
    effective_weight = get_effective_weight(col)
    if effective_weight is not None:
        new_column_names[col] = f"{col} [{effective_weight:.2f}%]"
    else:
        new_column_names[col] = col

# Rename columns
df_to_display = df_to_display.rename(columns=new_column_names)

# Reorder columns to put Final Score first if it exists
if 'Final Score' in df_to_display.columns:
    cols = ['Final Score'] + [col for col in df_to_display.columns if col != 'Final Score']
    df_to_display = df_to_display[cols]

# Display the dataframe with updated column names, hiding index
st.dataframe(df_to_display, use_container_width=True, hide_index=True)
