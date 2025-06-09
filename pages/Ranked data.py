import streamlit as st
import pandas as pd
import pickle

# Configure page to use full width
st.set_page_config(
    page_title="Ranked data",
    page_icon="🔬",
    layout="wide",  # This makes it use full width
)

# Function to load both datasets at startup
@st.cache_data
def load_both_datasets():
    """Load both datasets and cache them"""
    with open("data/dashboard_data_full.pickle", "rb") as f:
        df_full = pickle.load(f)
    with open("data/dashboard_data_grouped.pickle", "rb") as f:
        df_grouped = pickle.load(f)
    return df_full, df_grouped

# Function to load hierarchical weights
@st.cache_data
def load_hierarchical_weights():
    """Load hierarchical weights from pickle file"""
    with open("data/hierarchical_weights.pickle", "rb") as f:
        return pickle.load(f)

# Load hierarchical weights from pickle file
if 'hierarchical_weights' not in st.session_state:
    st.session_state.hierarchical_weights = load_hierarchical_weights()

# Load both datasets at startup
if 'df_full_original' not in st.session_state or 'df_grouped_original' not in st.session_state:
    st.session_state.df_full_original, st.session_state.df_grouped_original = load_both_datasets()

# Initialize session state
if 'current_df' not in st.session_state:
    st.session_state.current_df = 'full'

if 'rankings' not in st.session_state:
    st.session_state.rankings = {'full': {}, 'grouped': {}}

# Initialize processed dataframes if they don't exist
if 'df_full_processed' not in st.session_state:
    st.session_state.df_full_processed = st.session_state.df_full_original.copy()
if 'df_grouped_processed' not in st.session_state:
    st.session_state.df_grouped_processed = st.session_state.df_grouped_original.copy()

def apply_filters_and_weights(df_full, df_grouped, weights, filters):
    """Apply filters and weights to both dataframes"""
    
    # Apply filters to full dataset
    df_full_filtered = df_full.copy()
    
    if filters.get('filter_rare_only', False):
        if 'Prevalence Classification' in df_full_filtered.columns:
            df_full_filtered = df_full_filtered[df_full_filtered['Prevalence Classification'].isin(['ULTRA RARE', 'RARE'])]
    
    if filters.get('filter_company_size', False):
        if 'Company Size Classification' in df_full_filtered.columns:
            df_full_filtered = df_full_filtered[df_full_filtered['Company Size Classification'].isin(['Medium', 'Small'])]
    
    if filters.get('filter_innovative_only', False):
        if 'Biological Target Score' in df_full_filtered.columns:
            df_full_filtered = df_full_filtered[df_full_filtered['Biological Target Score'] == 3]
    
    # Apply filters to grouped dataset
    df_grouped_filtered = df_grouped.copy()
    
    if filters.get('filter_rare_only', False):
        if 'Has at least one rare or ultrarare' in df_grouped_filtered.columns:
            df_grouped_filtered = df_grouped_filtered[df_grouped_filtered['Has at least one rare or ultrarare'] == True]
    
    if filters.get('filter_company_size', False):
        if 'Company Size Classification' in df_grouped_filtered.columns:
            df_grouped_filtered = df_grouped_filtered[df_grouped_filtered['Company Size Classification'].isin(['Medium', 'Small'])]
    
    if filters.get('filter_innovative_only', False):
        if 'Biological Target Score' in df_grouped_filtered.columns:
            df_grouped_filtered = df_grouped_filtered[df_grouped_filtered['Biological Target Score'] == 3]
    
    # Apply weights to both datasets
    for dataset_name, df in [('full', df_full_filtered), ('grouped', df_grouped_filtered)]:
        # Convert score columns to numeric
        score_cols = [col for param_data in weights.values() for col in param_data['sub_params'].keys()]
        for col in score_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(pd.to_numeric(df[col], errors='coerce').mean())
        
        # Calculate final score
        df['FINAL SCORE'] = sum(
            (param_data['weight'] / 100) * sum(
                df[col] * (sub_weight / 100) for col, sub_weight in param_data['sub_params'].items() 
                if col in df.columns
            ) for param_data in weights.values()
        )
        
        # Store ranking dictionary (index -> Final Score)
        st.session_state.rankings[dataset_name] = df['FINAL SCORE'].to_dict()
    
    return df_full_filtered, df_grouped_filtered

def apply_text_search(df, search_term):
    """Apply text search across all string columns in the dataframe"""
    if not search_term:
        return df
    
    # Get all string/object columns
    string_columns = df.select_dtypes(include=['object']).columns
    
    # Create a mask for rows that contain the search term in any string column
    mask = pd.Series([False] * len(df), index=df.index)
    
    for col in string_columns:
        # Convert to string and search (case-insensitive)
        mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
    
    return df[mask]

# SIDEBAR CONTROLS
st.sidebar.caption("**Dataset view and filters**")
# Toggle for dataset selection
show_all_data = st.sidebar.toggle(
    "Show all data", 
    value=st.session_state.current_df == 'full',
    help="Toggle between full dataset and grouped dataset"
)

# Update current_df based on toggle
st.session_state.current_df = 'full' if show_all_data else 'grouped'

# Initialize and display filters
if 'filter_rare_only' not in st.session_state:
    st.session_state.filter_rare_only = False
filter_rare_only = st.sidebar.toggle("Only rare and ultra-rare", value=st.session_state.filter_rare_only, key="rare_filter_toggle")

if 'filter_company_size' not in st.session_state:
    st.session_state.filter_company_size = False
filter_company_size = st.sidebar.toggle("Only medium and small companies", value=st.session_state.filter_company_size, key="company_filter_toggle")

if 'filter_innovative_only' not in st.session_state:
    st.session_state.filter_innovative_only = False
filter_innovative_only = st.sidebar.toggle("Only innovative", value=st.session_state.filter_innovative_only, key="innovative_filter_toggle")

# Check if any filter has changed and apply filters automatically
filters_changed = (
    filter_rare_only != st.session_state.get('filter_rare_only', False) or
    filter_company_size != st.session_state.get('filter_company_size', False) or
    filter_innovative_only != st.session_state.get('filter_innovative_only', False)
)

if filters_changed:
    # Update session state
    st.session_state.filter_rare_only = filter_rare_only
    st.session_state.filter_company_size = filter_company_size
    st.session_state.filter_innovative_only = filter_innovative_only
    
    # Prepare filter dictionary
    filters = {
        'filter_rare_only': filter_rare_only,
        'filter_company_size': filter_company_size,
        'filter_innovative_only': filter_innovative_only
    }
    
    # Apply filters and weights to both datasets
    df_full_processed, df_grouped_processed = apply_filters_and_weights(
        st.session_state.df_full_original, 
        st.session_state.df_grouped_original, 
        st.session_state.hierarchical_weights, 
        filters
    )
    
    # Store processed dataframes
    st.session_state.df_full_processed = df_full_processed.sort_values('FINAL SCORE', ascending=False)
    st.session_state.df_grouped_processed = df_grouped_processed.sort_values('FINAL SCORE', ascending=False)

# Toggle filter for old phases
filter_old_phases = st.sidebar.toggle(
    "Hide phases completed 5+ years ago", 
    value=False,
)

# Text search functionality
st.sidebar.markdown("---")
st.sidebar.caption("**Text Search**")
search_text = st.sidebar.text_input("Input some text to filter data:", placeholder=" ")

# Initialize search state
if 'current_search' not in st.session_state:
    st.session_state.current_search = ""

# Update search term automatically when it changes
st.session_state.current_search = search_text

# Get the current processed dataframe
if st.session_state.current_df == 'full':
    current_df = st.session_state.df_full_processed.copy()
else:
    current_df = st.session_state.df_grouped_processed.copy()

# Apply ranking if exists
current_rankings = st.session_state.rankings.get(st.session_state.current_df, {})
if current_rankings:
    current_df['FINAL SCORE'] = current_df.index.map(current_rankings).fillna(0)
    current_df = current_df.sort_values('FINAL SCORE', ascending=False)

# Apply text search filter
if st.session_state.current_search:
    current_df = apply_text_search(current_df, st.session_state.current_search)

# Function to calculate effective weight for each column
def get_effective_weight(column_name):
    for param_name, param_data in st.session_state.hierarchical_weights.items():
        if column_name in param_data['sub_params']:
            param_weight = param_data['weight']
            sub_weight = param_data['sub_params'][column_name]
            effective_weight = (param_weight / 100) * (sub_weight / 100) * 100
            return effective_weight
    return None

# Apply filter to dataframe if toggle is on
if filter_old_phases and 'Highest Phase Completed 5yrs Ago' in current_df.columns:
    df_to_display = current_df[current_df['Highest Phase Completed 5yrs Ago'] == False].copy()
else:
    df_to_display = current_df.copy()

# Show entry count and search info with horizontal line
st.sidebar.markdown("---")
if st.session_state.current_search:
    st.sidebar.caption(f"Showing {len(df_to_display)} entries (filtered by: '{st.session_state.current_search}')")
else:
    st.sidebar.caption(f"Showing {len(df_to_display)} entries")

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
if 'FINAL SCORE' in df_to_display.columns:
    cols = ['FINAL SCORE'] + [col for col in df_to_display.columns if col != 'FINAL SCORE']
    df_to_display = df_to_display[cols]

# Remove the 'Highest Phase Completed 5yrs Ago' column from display
df_to_display = df_to_display[[col for col in df_to_display.columns if col not in ['Highest Phase Completed 5yrs Ago','Has at least one rare or ultrarare']]]

# Display the dataframe only if it's not empty
if len(df_to_display) > 0:
    st.dataframe(df_to_display, use_container_width=True, hide_index=True)
else:
    st.info("🔍 No entries match the current filters and search criteria. Try adjusting your filters or search term to see results.")
