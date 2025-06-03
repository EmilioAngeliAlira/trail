import streamlit as st
import pandas as pd
import pickle

st.title("Weight Configuration")

# Initialize session state if not exists
if 'df' not in st.session_state:
    with open("data/main_data.pickle", "rb") as f:
        st.session_state.df = pickle.load(f)

if 'weights' not in st.session_state:
    st.session_state.weights = {
        'Direct Competition Score': 50.0,
        'Indirect Competition Score': 50.0
    }

# Create editable table with current weights
weights_df = pd.DataFrame({
    'Variable': ['Direct Competition Score', 'Indirect Competition Score'],
    'Weight': [st.session_state.weights['Direct Competition Score'], 
              st.session_state.weights['Indirect Competition Score']]
})

# Display editable table
edited_df = st.data_editor(weights_df, use_container_width=True, hide_index=True)

# Rerank button
if st.button("Rerank"):
    # Update weights in session state
    st.session_state.weights = {
        'Direct Competition Score': edited_df.iloc[0]['Weight'],
        'Indirect Competition Score': edited_df.iloc[1]['Weight']
    }
    
    # Reload original data
    with open("data/main_data.pickle", "rb") as f:
        df = pickle.load(f)
    
    # Calculate weighted final score
    direct_weight = st.session_state.weights['Direct Competition Score'] / 100
    indirect_weight = st.session_state.weights['Indirect Competition Score'] / 100
    
    df['Final Score'] = (df['Direct Competition Score'] * direct_weight + 
                        df['Indirect Competition Score'] * indirect_weight)
    
    # Sort by final score descending
    df = df.sort_values('Final Score', ascending=False)
    
    # Update session state
    st.session_state.df = df
    
    st.success("Data reranked successfully!")
    st.rerun()
