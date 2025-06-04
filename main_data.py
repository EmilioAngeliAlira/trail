import streamlit as st
import pandas as pd
import pickle

# Configure page to use full width
st.set_page_config(
    page_title="Data Dashboard",
    page_icon="🔬",
    layout="wide",  # This makes it use full width
    initial_sidebar_state="collapsed"  # Hide sidebar for more space
)

# Initialize session state for df
if 'df' not in st.session_state:
    with open("data/main_data.pickle", "rb") as f:
        st.session_state.df = pickle.load(f)

# Initialize session state for hierarchical_weights if not exists
if 'hierarchical_weights' not in st.session_state: 
    st.session_state.hierarchical_weights = {
        'Commercial Viability': {
            'weight': 30.00,
            'sub_params': {
                'Prevalence and Incidence': 20,
                'market size score': 20,
                'Direct Competition Score': 50,
                'Indirect Competition Score': 10
            }
        },
        'Unmet Needs': {
            'weight': 12.00,
            'sub_params': {
                'clinical burden score': 32.50,
                'direct and indirect economical burden score': 62.50,
                'mortality score': 5.00
            }
        },
        'Target Company Characteristics': {
            'weight': 4.00,
            'sub_params': {
                'Company Overall Score': 50,
                'Geography Score': 50
            }
        },
        'Clinical Characteristics': {
            'weight': 7.00,
            'sub_params': {
                'Biological target score': 15.00,
                'Treatment Type Score': 5.00,
                'Development Phase Score': 40.00,
                'Number of investigated Indications Score': 15.00,
                'Therapeutic Area Score': 25.00
            }
        },
        'Time to Market': {
            'weight': 15.00,
            'sub_params': {
                'Regulatory Score': 15.00,
                'CT Timeline Score': 85.00
            }
        },
        'Clinical Development Feasibility': {
            'weight': 12.00,
            'sub_params': {
                'PoC Score': 33.33,
                'CT Enrollment Score': 33.33,
                'CT Outlook Score': 33.34
            }
        },
        'Internal Production Fit': {
            'weight': 20.00,
            'sub_params': {
                'Molecule Type Score': 100
            }
        }
    }

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

# Update column names to include weights in brackets
new_column_names = {}
for col in df_display.columns:
    effective_weight = get_effective_weight(col)
    if effective_weight is not None:
        new_column_names[col] = f"{col} [{effective_weight:.2f}%]"
    else:
        new_column_names[col] = col


# Rename columns
df_display = df_display.rename(columns=new_column_names)

# Reorder columns to put Final Score first if it exists
if 'Final Score' in df_display.columns:
    cols = ['Final Score'] + [col for col in df_display.columns if col != 'Final Score']
    df_display = df_display[cols]

# Display the dataframe with updated column names, hiding index
st.dataframe(df_display, use_container_width=True, hide_index=True)
