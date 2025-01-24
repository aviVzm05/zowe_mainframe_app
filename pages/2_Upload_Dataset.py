import streamlit as st
from zowe.zos_files_for_zowe_sdk import Datasets
from utils.auth_utils import get_or_create_connection
import logging
import os
from tempfile import NamedTemporaryFile

st.title("Upload Dataset")

# Get authenticated connection
profile_manager = get_or_create_connection()

# Create form for dataset upload
with st.form("upload_form"):
    dataset_name = st.text_input("Target Dataset Name (e.g., 'USERID.DATA.SET')")
    uploaded_file = st.file_uploader("Choose a file to upload")
    
    # Add dataset allocation options
    st.subheader("Dataset Properties (Optional)")
    dsorg = st.selectbox("Dataset Organization", 
                        options=["PO", "PS"],
                        index=1,
                        help="PO=Partitioned, PS=Sequential")
    recfm = st.selectbox("Record Format",
                        options=["FB", "VB", "F", "V"],
                        index=0,
                        help="FB=Fixed Blocked, VB=Variable Blocked, F=Fixed, V=Variable")
    lrecl = st.number_input("Logical Record Length", 
                           min_value=0,
                           value=80,
                           help="Length of each record")
    
    submit = st.form_submit_button("Upload to Dataset")
    
    if submit and uploaded_file is not None:
        try:
            datasets_api = Datasets(profile_manager)
            
            # Save uploaded file temporarily
            with st.spinner('Uploading dataset...'):
                # Use a secure temporary file
                with NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name
                
                try:
                    # Create dataset if it doesn't exist
                    try:
                        datasets_api.create(
                            dataset_name,
                            dsorg=dsorg,
                            recfm=recfm,
                            lrecl=lrecl if lrecl > 0 else None
                        )
                    except Exception as create_error:
                        logging.warning(f"Dataset might already exist: {str(create_error)}")
                    
                    # Upload to mainframe
                    datasets_api.write(dataset_name, temp_path)
                    st.success(f"File uploaded successfully to dataset {dataset_name}")
                
                finally:
                    # Cleanup
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                
        except Exception as e:
            st.error(f"Failed to upload dataset: {str(e)}")
            logging.error(f"Dataset upload failed: {str(e)}", exc_info=True) 