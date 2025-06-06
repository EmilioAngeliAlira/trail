import streamlit as st
import pandas as pd
import pickle

# Configure page to use full width
st.set_page_config(
    page_title="Ranked data",
    page_icon="🔬",
    layout="wide",  # This makes it use full width
)

# Initialize session state for hierarchical_weights if not exists
if 'hierarchical_weights' not in st.session_state: 
    st.session_state.hierarchical_weights = {
        'Commercial Viability': {
            'weight': 30.00,
            'sub_params': {
                'Prevalence Score': 10,
                'Incidence Score': 10,
                'Market Size Score': 20,
                'Direct Competition Score': 50,
                'Indirect Competition Score': 10
            }
        },
        'Unmet Needs': {
            'weight': 12.00,
            'sub_params': {
                'Clinical Burden Score': 32.5,
                'Direct And Indirect Economic Burden Score': 62.5,
                'Mortality Score': 5
            }
        },
        'Target Company Characteristics': {
            'weight': 4.00,
            'sub_params': {
                'Company Score': 50,
                'Geography Score': 50
            }
        },
        'Clinical Characteristics': {
            'weight': 7.00,
            'sub_params': {
                'Biological Target Score': 15,
                'Treatment Type Score': 15,
                'Development Phase Score': 40,
                'Number of investigated Indications Score': 15,
                'Therapeutic Area Score': 15
            }
        },
        'Time to Market': {
            'weight': 15.00,
            'sub_params': {
                'Regulatory Score': 15,
                'CT Timeline Score': 85
            }
        },
        'Clinical Development Feasibility': {
            'weight': 12.00,
            'sub_params': {
                'PoC Score': 33.4,
                'CT Enrollment Score': 33.3,
                'CT Outlook Score': 33.3
            }
        },
        'Molecule Type': {
            'weight': 20.00,
            'sub_params': {
                'Molecule Type Score': 100
            }
        }
    }

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
    
# Always load fresh dataset and apply filters
st.session_state.df = load_dataset(st.session_state.current_df)

# Apply filters if enabled and using full dataset
if st.session_state.current_df == 'full':
    if ('filter_rare_only' in st.session_state and st.session_state.filter_rare_only):
        st.session_state.df = st.session_state.df[st.session_state.df['Prevalence Classification'].isin(['ULTRA RARE', 'RARE'])]
    if ('filter_company_size' in st.session_state and st.session_state.filter_company_size):
        st.session_state.df = st.session_state.df[st.session_state.df['Company Size Classification'].isin(['Medium', 'Small'])]
    if ('filter_trial_status' in st.session_state and st.session_state.filter_trial_status):
        st.session_state.df = st.session_state.df[st.session_state.df['Trial Status'] == 'Completed']

# Apply ranking if exists
current_rankings = st.session_state.rankings.get(st.session_state.current_df, {})
if current_rankings:
    st.session_state.df['FINAL SCORE'] = st.session_state.df.index.map(current_rankings).fillna(0)
    st.session_state.df = st.session_state.df.sort_values('FINAL SCORE', ascending=False)

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
    st.sidebar.caption(f"Showing {len(df_to_display)} of {len(st.session_state.df)} entries")
else:
    df_to_display = df_display.copy()
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
    cols = ['FINAL SCORE'] + [col for col in df_to_display.columns if col !='FINAL SCORE']
    df_to_display = df_to_display[cols]

df_to_display = df_to_display[[col for col in df_to_display.columns if  col != 'Highest Phase Completed 5yrs Ago']]

# Display the dataframe with updated column names, hiding index
st.dataframe(df_to_display, use_container_width=True, hide_index=True)
