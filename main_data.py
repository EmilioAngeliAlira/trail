import streamlit as st
import pandas as pd
import pickle



# Initialize session state
if 'df' not in st.session_state:
    with open("data/main_data.pickle", "rb") as f:
        st.session_state.df = pickle.load(f)





# Custom CSS for styling
st.markdown("""
<style>
    .param-title {
        font-weight: bold;
        font-size: 16px;
        color: #000000;
        margin-bottom: 15px;
    }
    .sub-param-title {
        font-weight: bold;
        font-size: 16px;
        color: #000000;
        margin-bottom: 15px;
    }
    .param-section {
        margin-bottom: 30px;
    }
    .horizontal-line {
        border-top: 2px solid #e0e0e0;
        margin: 25px 0;
    }
</style>
""", unsafe_allow_html=True)



total_main_weight = 0
updated_weights = {}

for param_name, param_data in st.session_state.hierarchical_weights.items():
    # Create two columns for each parameter block - wider layout
    left_col, uu, line_col, right_col = st.columns([1, 0.3, 0.1, 2])
    
    # Left column: Main parameter
    with left_col:
        st.markdown(f'<div class="param-title">{param_name}</div>', unsafe_allow_html=True)
        
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

    with line_col:
        st.markdown("""
        <div style="
            border-left: 2px solid #e0e0e0;
            height: 300px;
            margin: 0 auto;
        "></div>
        """, unsafe_allow_html=True)
    
    # Right column: Sub-parameters for this main parameter
    with right_col:
        st.markdown(f'<div class="sub-param-title">Sub-parameters</div>', unsafe_allow_html=True)
        
        sub_weights = {}
        total_sub_weight = 0
        
        for sub_param, sub_weight in param_data['sub_params'].items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {sub_param}")
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
    
    # Add horizontal line between parameters
    st.markdown('<div class="horizontal-line"></div>', unsafe_allow_html=True)


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
        
        # Reload original data
        with open("data/main_data.pickle", "rb") as f:
            df = pickle.load(f)
        
        # Calculate hierarchical weighted score
        df['Final Score'] = 0
        
        for param_name, param_data in updated_weights.items():
            param_weight = param_data['weight'] / 100
            
            # Calculate weighted sub-parameter score for this parameter
            param_score = 0
            for sub_param, sub_weight in param_data['sub_params'].items():
                if sub_param in df.columns:
                    sub_weight_norm = sub_weight / 100
                    # Only multiply if it's a numeric score column
                    try:
                        numeric_values = pd.to_numeric(df[sub_param], errors='coerce').fillna(0)
                        param_score += numeric_values * sub_weight_norm
                    except:
                        # Skip non-numeric columns
                        continue
            
            # Add this parameter's contribution to final score
            df['Final Score'] += param_score * param_weight
        
        # Sort by final score descending
        df = df.sort_values('Final Score', ascending=False)
        
        # Update session state
        st.session_state.df = df
        
        st.success("Data reranked successfully with hierarchical weights")
    else:
        st.error("❌ Please ensure all weights total 100% before reranking")
