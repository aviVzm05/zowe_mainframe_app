import streamlit as st
import os
import logging

def init_session_state():
    """Initialize session state variables"""
    session_vars = {
        'auth_success': False,
        'secure_profile': None,
        'current_host': None,
        'profile_name': None,
        'auth_time': None
    }
    
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default

def get_or_create_connection():
    """Get existing connection or redirect to login"""
    required_vars = ['auth_success', 'secure_profile']
    
    # Check if all required variables exist
    if not all(var in st.session_state for var in required_vars):
        st.error("Session state corrupted. Please login again!")
        # Clean up any existing session
        cleanup_session()
        st.stop()
    
    # Check authentication status
    if not st.session_state.auth_success or not st.session_state.secure_profile:
        st.error("Please login from the Home page first!")
        cleanup_session()
        st.stop()
    
    # Check if session is expired
    if st.session_state.secure_profile.is_expired():
        st.error("Session expired. Please login again!")
        cleanup_session()
        st.stop()
    
    return st.session_state.secure_profile.profile_manager

def cleanup_session():
    """Clean up session state and profile files"""
    try:
        if hasattr(st.session_state, 'secure_profile') and st.session_state.secure_profile:
            st.session_state.secure_profile.cleanup()
        
        if hasattr(st.session_state, 'profile_name'):
            profile_path = os.path.join(os.path.expanduser("~"), ".zowe", "profiles", 
                                      f"{st.session_state.profile_name}.yaml")
            if os.path.exists(profile_path):
                os.remove(profile_path)
    except Exception as e:
        logging.error(f"Session cleanup failed: {str(e)}")
    finally:
        # Clear all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Reinitialize session state
        init_session_state() 