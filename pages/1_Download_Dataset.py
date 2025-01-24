import streamlit as st
from zowe.zos_files_for_zowe_sdk import Datasets
from utils.auth_utils import get_or_create_connection
import logging
import os

st.title("Download Dataset")

# Get authenticated connection
profile_manager = get_or_create_connection()

# Create form for dataset download
with st.form("download_form"):
    dataset_name = st.text_input("Dataset Name (e.g., 'USERID.DATA.SET')")
    download_path = st.text_input("Local Download Path", "downloaded_dataset.txt")
    
    submit = st.form_submit_button("Download Dataset")
    
    if submit:
        try:
            datasets_api = Datasets(profile_manager)
            
            with st.spinner('Downloading dataset...'):
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(download_path) if os.path.dirname(download_path) else '.', exist_ok=True)
                
                # Download the dataset
                datasets_api.download(dataset_name, download_path)
                st.success(f"Dataset downloaded successfully to {download_path}")
                
                # Show preview of downloaded content
                try:
                    with open(download_path, 'r') as f:
                        content = f.read()
                        st.text_area("Dataset Preview", content, height=300)
                except UnicodeDecodeError:
                    st.warning("Unable to preview binary content")
                    
        except Exception as e:
            st.error(f"Failed to download dataset: {str(e)}")
            logging.error(f"Dataset download failed: {str(e)}", exc_info=True) 