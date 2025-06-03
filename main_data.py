import streamlit as st
import pickle

# Load and display data
@st.cache_data
def load_data():
    with open("data/main_data.pickle", "rb") as f:
        return pickle.load(f)

df = load_data()
st.title("Data Analysis Dashboard")
st.dataframe(df, use_container_width=True)
