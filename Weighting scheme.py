import streamlit as st
import pandas as pd
import pickle

# Configure page to use full width
st.set_page_config(
    page_title="Weighting scheme",
    page_icon="🔬",
    layout="wide",  # This makes it use full width
)

# Add this after your imports and before the page config
st.markdown("""
<style>
.horizontal-line {
    border-top: 1px solid #e0e0e0;
    margin: 20px 0;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

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

# Load both datasets at startup
if 'df_full_original' not in st.session_state or 'df_grouped_original' not in st.session_state:
    st.session_state.df_full_original, st.session_state.df_grouped_original = load_both_datasets()

# Set current df type to grouped by default
if 'current_df' not in st.session_state:
    st.session_state.current_df = 'grouped'

# Initialize ranking dictionaries
if 'rankings' not in st.session_state:
    st.session_state.rankings = {'full': {}, 'grouped': {}}

# Initialize processed dataframes if they don't exist
if 'df_full_processed' not in st.session_state:
    st.session_state.df_full_processed = st.session_state.df_full_original.copy()
if 'df_grouped_processed' not in st.session_state:
    st.session_state.df_grouped_processed = st.session_state.df_grouped_original.copy()

# Load hierarchical weights from pickle file
if 'hierarchical_weights' not in st.session_state:
    st.session_state.hierarchical_weights = load_hierarchical_weights()

total_main_weight = 0
updated_weights = {}

for param_name, param_data in st.session_state.hierarchical_weights.items():
    # Create two columns for each parameter block - wider layout
    left_col, uu, right_col = st.columns([1,0.5, 1])
    
    st.markdown('<div class="horizontal-line"></div>', unsafe_allow_html=True)
    # Left column: Main parameter
    with left_col:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{param_name}")
        with col2:
            main_weight = st.number_input(
                f"Weight % for {param_name}",
                min_value=0.0,
                max_value=100.0,
                value=param_data['weight'],
                step=0.1,
                key=f"main_{param_name}",
                label_visibility="collapsed"
            )
        
        total_main_weight += main_weight

    with right_col:
        sub_weights = {}
        total_sub_weight = 0
        
        for sub_param, sub_weight in param_data['sub_params'].items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{sub_param}")
            with col2:
                weight = st.number_input(
                    f"Sub-weight % for {sub_param}",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(sub_weight),
                    step=0.1,
                    key=f"sub_{param_name}_{sub_param}",
                    label_visibility="collapsed"
                )
                sub_weights[sub_param] = weight
                total_sub_weight += weight
        
        # Show sub-parameter total
        if abs(total_sub_weight - 100.0) > 0.1:
            st.warning(f"Total: {total_sub_weight:.1f}% (should be 100%)")
        else:
            st.success(f"Total: {total_sub_weight:.1f}%")
        
        updated_weights[param_name] = {
            'weight': main_weight,
            'sub_params': sub_weights
        }

if abs(total_main_weight - 100.0) > 0:
   st.error(f"**{total_main_weight:.1f}%**, main parameters should total 100%")
else:
   st.success(f"**{total_main_weight:.1f}%**, main parameters total is correct")
st.markdown('<div class="horizontal-line"></div>', unsafe_allow_html=True)

# Show weight summary table
if st.expander("📋 Weight Summary", expanded=False):
    summary_data = []
    for param_name, param_data in updated_weights.items():
        for sub_param, sub_weight in param_data['sub_params'].items():
            effective_weight = (param_data['weight'] / 100) * (sub_weight / 100) * 100
            summary_data.append({
                'Parameter': param_name,
                'Sub-parameter': sub_param,
                'Parameter Weight %': f"{param_data['weight']:.1f}%",
                'Sub-parameter Weight %': f"{sub_weight:.1f}%",
                'Effective Weight %': f"{effective_weight:.2f}%"
            })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Only enable apply button if weights are valid
weights_valid = abs(total_main_weight - 100.0) == 0
all_sub_valid = all(abs(sum(data['sub_params'].values()) - 100.0) == 0 for data in updated_weights.values())

if st.button("Apply the weights", use_container_width=True, disabled=not (weights_valid and all_sub_valid)):
    if weights_valid and all_sub_valid:
        # Save current weights to session state
        st.session_state.hierarchical_weights = updated_weights
        
        # Get current filter states from session state (set by the ranked data page)
        filters = {
            'filter_rare_only': st.session_state.get('filter_rare_only', False),
            'filter_company_size': st.session_state.get('filter_company_size', False),
            'filter_innovative_only': st.session_state.get('filter_innovative_only', False)
        }
        
        # Apply filters and weights function
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
        
        # Apply filters and weights to both datasets
        df_full_processed, df_grouped_processed = apply_filters_and_weights(
            st.session_state.df_full_original, 
            st.session_state.df_grouped_original, 
            updated_weights, 
            filters
        )
        
        # Store processed dataframes
        st.session_state.df_full_processed = df_full_processed.sort_values('FINAL SCORE', ascending=False)
        st.session_state.df_grouped_processed = df_grouped_processed.sort_values('FINAL SCORE', ascending=False)
        
        st.success("The dataset has been reranked!")
