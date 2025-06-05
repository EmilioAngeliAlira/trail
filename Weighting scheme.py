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


# Initialize session state for hierarchical_weights if not exists
if 'hierarchical_weights' not in st.session_state: 
    st.session_state.hierarchical_weights = {
        'Commercial Viability': {
            'weight': 30.00,
            'sub_params': {
                'Prevalence Score': 10,
                'Irevalence Score': 10,
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






total_main_weight = 0
updated_weights = {}

for param_name, param_data in st.session_state.hierarchical_weights.items():
    # Create two columns for each parameter block - wider layout
    left_col, uu, line_col, right_col = st.columns([1, 0.3, 0.1, 2])
    
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

    
    # Right column: Sub-parameters for this main parameter
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
        if abs(total_sub_weight - 100.0) != 0:
            st.warning(f"⚠️ Total: {total_sub_weight:.1f}% (should be 100%)")
        else:
            st.success(f"✅ Total: {total_sub_weight:.1f}%")
        
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




# Only enable rerank if weights are valid
weights_valid = abs(total_main_weight - 100.0) == 0
all_sub_valid = all(abs(sum(data['sub_params'].values()) - 100.0) == 0 for data in updated_weights.values())


if st.button("Rerank Data", use_container_width=True, disabled=not (weights_valid and all_sub_valid)):
    if weights_valid and all_sub_valid:
        # Save current weights
        st.session_state.hierarchical_weights = updated_weights
        
        # Rerank both datasets and store rankings
        for dataset_type in ['full', 'grouped']:
            df = load_dataset(dataset_type)
            
            # Calculate hierarchical weighted score
            df['Final Score'] = 0
            
            for param_name, param_data in updated_weights.items():
                param_weight = param_data['weight'] / 100
                
                param_score = 0
                for sub_param, sub_weight in param_data['sub_params'].items():
                    if sub_param in df.columns:
                        sub_weight_norm = sub_weight / 100
                        try:
                            numeric_values = pd.to_numeric(df[sub_param], errors='coerce').fillna(0)
                            param_score += numeric_values * sub_weight_norm
                        except:
                            continue
                
                df['Final Score'] += param_score * param_weight
            
            # Store ranking dictionary (index -> Final Score)
            st.session_state.rankings[dataset_type] = df['Final Score'].to_dict()
        
        # Update current df with its ranking
        current_rankings = st.session_state.rankings[st.session_state.current_df]
        st.session_state.df = load_dataset(st.session_state.current_df)
        st.session_state.df['Final Score'] = st.session_state.df.index.map(current_rankings).fillna(0)
        st.session_state.df = st.session_state.df.sort_values('Final Score', ascending=False)
        
        st.success("Datasets reranked successfully")
