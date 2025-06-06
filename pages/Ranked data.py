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



# Set current df type to full by default
if 'current_df' not in st.session_state:
    st.session_state.current_df = 'grouped'

# Initialize ranking dictionaries
if 'rankings' not in st.session_state:
    st.session_state.rankings = {'full': {}, 'grouped': {}}

# Load only the current dataset
def load_dataset(dataset_type):
    filename = "data/dashboard_data_full.pickle" if dataset_type == 'full' else "data/dashboard_data_grouped.pickle"
    with open(filename, "rb") as f:
        return pickle.load(f)

st.session_state.df = load_dataset(st.session_state.current_df)

if st.session_state.current_df == 'full':
    if ('filter_rare_only' in st.session_state and st.session_state.filter_rare_only):
        st.session_state.df = st.session_state.df[st.session_state.df['Prevalence Classification'].isin(['ULTRA RARE', 'RARE'])]
    if ('filter_company_size' in st.session_state and st.session_state.filter_company_size):
        st.session_state.df = st.session_state.df[st.session_state.df['Company Size Classification'].isin(['Medium', 'Small'])]


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






total_main_weight = 0
updated_weights = {}

for param_name, param_data in st.session_state.hierarchical_weights.items():
    # Create two columns for each parameter block - wider layout
    left_col, uu, right_col, vv, rightright_col = st.columns([1,0.5, 1, 0.5, 1])
    
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
            st.warning(f"⚠️ Total: {total_sub_weight:.1f}% (should be 100%)")
        else:
            st.success(f"✅ Total: {total_sub_weight:.1f}%")
        
        updated_weights[param_name] = {
            'weight': main_weight,
            'sub_params': sub_weights
        }

    
    # Add filter toggles (always show, but only apply to full dataset)
    with rightright_col:
        if param_name == "Commercial Viability":
            if 'filter_rare_only' not in st.session_state:
                st.session_state.filter_rare_only = False
            
            st.session_state.filter_rare_only = st.toggle(
                "Only rare and ultra-rare",
                value=st.session_state.filter_rare_only,
                key="rare_filter_toggle"
            )
        
        elif param_name == "Target Company Characteristics":
            if 'filter_company_size' not in st.session_state:
                st.session_state.filter_company_size = False
            
            st.session_state.filter_company_size = st.toggle(
                "Only Medium/Small companies",
                value=st.session_state.filter_company_size,
                key="company_filter_toggle"
            )
    


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




# Only enable rerank if weights are valid
weights_valid = abs(total_main_weight - 100.0) == 0
all_sub_valid = all(abs(sum(data['sub_params'].values()) - 100.0) == 0 for data in updated_weights.values())

if st.button("Apply the weights and filters", use_container_width=True, disabled=not (weights_valid and all_sub_valid)):
    if weights_valid and all_sub_valid:
        # Save current weights
        st.session_state.hierarchical_weights = updated_weights
        
        # Rerank both datasets and store rankings
        for dataset_type in ['full', 'grouped']:
            df = load_dataset(dataset_type)
            
            # Apply filters only if enabled and dataset is full
            if dataset_type == 'full':
                # Apply rare filter
                if ('filter_rare_only' in st.session_state and st.session_state.filter_rare_only):
                    df = df[df['Prevalence Classification'].isin(['ULTRA RARE', 'RARE'])]
                
                # Apply company size filter
                if ('filter_company_size' in st.session_state and st.session_state.filter_company_size):
                    df = df[df['Company Size Classification'].isin(['Medium', 'Small'])]
            
            # Rest of the existing rerank logic continues here...
            
                    
            # Convert score columns to numeric
            score_cols = [col for param_data in updated_weights.values() for col in param_data['sub_params'].keys()]
            for col in score_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(pd.to_numeric(df[col], errors='coerce').mean())
            
            # Calculate final score using the same logic as your function
            df['FINAL SCORE'] = sum(
                (param_data['weight'] / 100) * sum(
                    df[col] * (sub_weight / 100) for col, sub_weight in param_data['sub_params'].items() 
                    if col in df.columns
                ) for param_data in updated_weights.values()
            )
            
            # Store ranking dictionary (index -> Final Score)
            st.session_state.rankings[dataset_type] = df['FINAL SCORE'].to_dict()
        
        # Update current df with its ranking
        current_rankings = st.session_state.rankings[st.session_state.current_df]
        st.session_state.df = load_dataset(st.session_state.current_df)
        
     
        
        st.session_state.df['FINAL SCORE'] = st.session_state.df.index.map(current_rankings).fillna(0)
        st.session_state.df = st.session_state.df.sort_values('FINAL SCORE', ascending=False)
        
        st.success("Weights and filters applied")
