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

def initialize_text_filters():
    """Initialize text_filters dictionary with nested structure for full and grouped datasets"""
    if 'text_filters' not in st.session_state:
        # Get string columns from both datasets
        full_cols = st.session_state.df_full_original.select_dtypes(include=['object']).columns.tolist()
        grouped_cols = st.session_state.df_grouped_original.select_dtypes(include=['object']).columns.tolist()
        
        # Initialize nested dictionary structure with all columns (filtering will happen in get_searchable_columns)
        st.session_state.text_filters = {
            'full': {col: "" for col in sorted(full_cols)},
            'grouped': {col: "" for col in sorted(grouped_cols)}
        }

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

def apply_text_filters(df, text_filters_dict):
    """Apply text filters to the dataframe based on the text_filters dictionary for current dataset"""
    filtered_df = df.copy()
    
    for column, search_term in text_filters_dict.items():
        if search_term and column in filtered_df.columns:
            # Apply case-insensitive search for the specific column
            mask = filtered_df[column].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
    
    return filtered_df

def get_searchable_columns(df):
    """Get list of searchable columns (string/object columns) that exist in current dataframe, excluding specified columns"""
    # Define columns to exclude from filters
    columns_not_to_show_in_the_filters_full_dataset = [
        'FINAL SCORE', 'Trial Identifier', 'Prevalence Score', 'Prevalence Rationale',
        'Incidence Score', 'Incidence Rationale', 'Market Size Score', 
        'Market Size Rationale', 'Direct Competition Score',
        'Direct Competition Metric', 'Direct Number of assets commercialized',
        'Direct Number competitors in phase 1',
        'Direct Number competitors in phase 2',
        'Direct Number competitors in phase 3', 'Indirect Competition Score',
        'Indirect Competition Metric',
        'Indirect Number of assets commercialized',
        'Indirect Number competitors in phase 1',
        'Indirect Number competitors in phase 2',
        'Indirect Number competitors in phase 3', 'Clinical Burden Score',
        'Clinical Burden Rationale',
        'Indirect Economic Burden Score',
        'Indirect Economic Burden Rationale', 'Direct Economic Burden Score',
        'Direct Economic Burden Rationale', 'Mortality Score',
        'Mortality Rationale', 'Company Score',
        'Company Size Rationale',
        'Proven Track Record Rationale', 'Acquired', 'Acquired_by',
        'Geography Score', 'Geography Rationale', 'Biological Target Score',
        'References (biological target)', 'Treatment Type Score',
        'Development Phase Score',
        'Number of investigated Idications',
        'Number of investigated Indications Score', 'Therapeutic Area Score',
        'Regulatory Score', 'CT Timeline',
        'CT Timeline Score', 'PoC Score', 'CT Enrollment',
        'CT Enrollment Score', 'CT Outlook', 'CT Outlook Score',
        'Molecule Type Score', 'Direct And Indirect Economic Burden Score',
        'Highest Phase Completed 5yrs Ago'
    ]
    
    columns_not_to_show_in_the_filters_grouped_dataset = [
        'FINAL SCORE', 'Geography Rationale', 'Highest Phase Completed 5yrs Ago', 
        'Prevalence Score', 'Incidence Score', 'Market Size Score', 'Direct Competition Score',
        'Indirect Competition Score', 'Clinical Burden Score',
        'Mortality Score', 'Company Score', 'Geography Score',
        'Biological Target Score', 'Treatment Type Score',
        'Development Phase Score', 'Number of investigated Indications Score',
        'Therapeutic Area Score', 'Regulatory Score', 'CT Timeline Score',
        'PoC Score', 'CT Enrollment Score', 'CT Outlook Score',
        'Molecule Type Score', 'Direct And Indirect Economic Burden Score',
        'Has at least one rare or ultrarare'
    ]
    
    # Get current dataset type
    current_dataset = st.session_state.current_df
    
    # Choose the appropriate exclusion list
    if current_dataset == 'full':
        excluded_columns = columns_not_to_show_in_the_filters_full_dataset
    else:
        excluded_columns = columns_not_to_show_in_the_filters_grouped_dataset
    
    # Get string columns and filter out excluded ones
    string_columns = df.select_dtypes(include=['object']).columns.tolist()
    filtered_columns = [col for col in string_columns if col not in excluded_columns]
    
    return sorted(filtered_columns)

# Initialize text filters
initialize_text_filters()

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

# Toggle filter for old phases
filter_old_phases = st.sidebar.toggle(
    "Hide phases completed 5+ years ago", 
    value=False,
)

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

# Get the current processed dataframe
if st.session_state.current_df == 'full':
    current_df = st.session_state.df_full_processed.copy()
else:
    current_df = st.session_state.df_grouped_processed.copy()

# Enhanced Text Search functionality
st.sidebar.markdown("---")
st.sidebar.caption("**Keyword Search**")

# Get searchable columns that exist in the current dataframe
available_columns = get_searchable_columns(current_df)

# Column selection for text search
search_column = st.sidebar.selectbox(
    "Select column for keyword search:",
    options=available_columns,
    index=0 if available_columns else None,
)

# Text input for search term
if search_column:
    # Get current value for this column from text_filters for current dataset
    current_value = st.session_state.text_filters[st.session_state.current_df].get(search_column, "")
    
    search_text = st.sidebar.text_input(
        f"Search in '{search_column}':",
        value=current_value,
        placeholder="Enter text to search for...",
        key=f"search_{search_column}_{st.session_state.current_df}"
    )
    
    # Update the text_filters dictionary for current dataset
    st.session_state.text_filters[st.session_state.current_df][search_column] = search_text

# Apply ranking if exists
current_rankings = st.session_state.rankings.get(st.session_state.current_df, {})
if current_rankings:
    current_df['FINAL SCORE'] = current_df.index.map(current_rankings).fillna(0)
    current_df = current_df.sort_values('FINAL SCORE', ascending=False)

# Apply text filters
current_df = apply_text_filters(current_df, st.session_state.text_filters[st.session_state.current_df])

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

# Active Filters Popover
with st.sidebar.popover("**Active keywords filters**", icon=":material/filter_list:"):
    
    active_filters = []
    
    # Text search filters - only show non-empty ones for current dataset
    current_text_filters = st.session_state.text_filters[st.session_state.current_df]
    active_text_filters = {col: term for col, term in current_text_filters.items() if term.strip()}
    for column, search_term in active_text_filters.items():
        active_filters.append(f"• **{column}:** '{search_term}'")
    
    if not active_filters:
        st.markdown("*No keyword filters active*")
    else:
        for filter_item in active_filters:
            st.markdown(filter_item)

# Show entry count and search info with horizontal line
st.sidebar.markdown("---")
current_text_filters = st.session_state.text_filters[st.session_state.current_df]
active_text_filters = {col: term for col, term in current_text_filters.items() if term.strip()}

st.sidebar.caption(f"Showing {len(df_to_display)} entries")

# Add Alvotech logo at the bottom of sidebar
st.sidebar.markdown("---")
try:
    # Try to load and display the Alvotech logo
    import os
    logo_path = "data"
    
    # Look for common logo file extensions
    logo_files = []
    if os.path.exists(logo_path):
        for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif']:
            for filename in os.listdir(logo_path):
                if 'alvotech' in filename.lower() and filename.lower().endswith(ext):
                    logo_files.append(os.path.join(logo_path, filename))
                elif 'logo' in filename.lower() and filename.lower().endswith(ext):
                    logo_files.append(os.path.join(logo_path, filename))
    
    if logo_files:
        # Use the first logo file found and center it
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image(logo_files[0], width=150)
    else:
        # If no logo found, show placeholder text
        st.sidebar.markdown("<div style='text-align: center; color: #666;'><em>Alvotech</em></div>", unsafe_allow_html=True)
        
except Exception as e:
    # If there's any error loading the logo, show placeholder text
    st.sidebar.markdown("<div style='text-align: center; color: #666;'><em>Alvotech</em></div>", unsafe_allow_html=True)

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
    st.dataframe(df_to_display, use_container_width=True, hide_index=True, height=800)
else:
    st.info("🔍 No entries match the current filters and search criteria. Try adjusting your filters or search term to see results.")
