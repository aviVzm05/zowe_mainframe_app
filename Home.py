import streamlit as st
# Update these imports
from zowe.core_for_zowe_sdk import ProfileManager
from zowe.zosmf_for_zowe_sdk import Zosmf
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from utils.auth_utils import init_session_state
from utils.security_utils import SecureProfileManager
from typing import Dict
import json

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"zowe_auth_{timestamp}.log")
    
    # Configure logging format and level
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Suppress excessive logging from urllib3
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()

def validate_cert(cert_path):
    """Validate certificate format and convert if necessary"""
    if not cert_path:
        logger.debug("No certificate path provided")
        return None
        
    cert_file = Path(cert_path)
    if not cert_file.exists():
        logger.error(f"Certificate file not found: {cert_path}")
        raise ValueError(f"Certificate file not found: {cert_path}")
    
    logger.info(f"Processing certificate: {cert_path}")
    
    # If it's already .pem, return as is
    if cert_file.suffix.lower() == '.pem':
        logger.debug("Certificate is already in PEM format")
        return str(cert_file)
    
    # For .cer files, try to determine format and convert if needed
    if cert_file.suffix.lower() == '.cer':
        try:
            logger.debug("Attempting to process .cer certificate")
            # Try reading as text/PEM format
            with open(cert_file, 'r') as f:
                content = f.read()
            if '-----BEGIN CERTIFICATE-----' in content:
                logger.info("Certificate is in PEM format, converting extension")
                new_path = str(cert_file.with_suffix('.pem'))
                with open(new_path, 'w') as f:
                    f.write(content)
                return new_path
            else:
                logger.info("Certificate appears to be in DER format, converting to PEM")
                new_path = str(cert_file.with_suffix('.pem'))
                os.system(f'openssl x509 -inform DER -in "{cert_path}" -out "{new_path}"')
                return new_path
        except Exception as e:
            logger.error(f"Failed to process certificate: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to process certificate: {str(e)}")
    
    logger.error("Unsupported certificate format")
    raise ValueError("Unsupported certificate format. Please provide .cer or .pem file")

def get_mainframe_hosts() -> Dict[str, str]:
    """Get mainframe hosts from Streamlit secrets"""
    try:
        return st.secrets["mainframe_hosts"]
    except Exception as e:
        logger.warning(f"Failed to load hosts from secrets: {e}")
        # Fallback to default hosts if secrets not configured
        return {
            "Development": "devplex.test.com",
            "Production": "prdplex.prod.com"
        }

# Use the function where needed
MAINFRAME_HOSTS = get_mainframe_hosts()

# Add security settings
def get_security_config():
    """Get security configuration from secrets"""
    try:
        return {
            "session_timeout": timedelta(minutes=st.secrets["security"]["session_timeout_minutes"]),
            "max_attempts": st.secrets["security"]["max_login_attempts"],
            "lockout_duration": timedelta(minutes=st.secrets["security"]["lockout_duration_minutes"])
        }
    except Exception as e:
        logger.warning(f"Failed to load security config from secrets: {e}")
        return {
            "session_timeout": timedelta(minutes=30),
            "max_attempts": 3,
            "lockout_duration": timedelta(minutes=15)
        }

def get_certificate_path():
    """Get certificate path from environment variable"""
    cert_path = os.getenv('ZOWE_CERTIFICATE_PATH')
    if cert_path:
        logger.info(f"Using certificate from environment: {cert_path}")
        try:
            return validate_cert(cert_path)
        except Exception as e:
            logger.error(f"Certificate validation failed: {str(e)}")
            raise ValueError(f"Invalid certificate in environment variable: {str(e)}")
    logger.debug("No certificate path found in environment")
    return None

def authenticate_mainframe(userid, password, host):
    logger.info(f"Attempting authentication for user {userid} to host {host}")
    try:
        # Get certificate from environment
        cert_path = get_certificate_path()
        
        # Create profile manager with app name
        logger.debug("Creating profile manager")
        profile_manager = ProfileManager(appname='zowe')
        
        # Create a zosmf-type profile
        profile_name = f"zosmf_profile_{userid.lower()}"
        logger.debug(f"Setting up profile: {profile_name}")
        
        # Create connection dictionary
        connection = {
            "host": host,
            "port": 443,
            "user": userid,
            "password": password,
            "protocol": "https",
            "reject_unauthorized": True
        }
        
        if cert_path:
            logger.debug(f"Adding certificate to connection")
            connection["cert_file"] = cert_path
        
        # Test z/OSMF connection first
        logger.info("Testing z/OSMF connection")
        try:
            zosmf = Zosmf(connection)
            zosmf_info = zosmf.get_info()
        except Exception as e:
            logger.error(f"Z/OSMF connection test failed: {str(e)}")
            raise ValueError(f"Connection failed: {str(e)}")
        
        # If connection successful, save the profile
        # Set the base profile properties
        profile_manager.set_property("profiles.base.properties.host", host)
        profile_manager.set_property("profiles.base.properties.port", 443)
        profile_manager.set_property("profiles.base.properties.protocol", "https")
        profile_manager.set_property("profiles.base.properties.rejectUnauthorized", True)
        
        # Set the zosmf profile properties
        profile_manager.set_property(f"profiles.{profile_name}.type", "zosmf")
        profile_manager.set_property(f"profiles.{profile_name}.properties.host", host)
        profile_manager.set_property(f"profiles.{profile_name}.properties.port", 443)
        profile_manager.set_property(f"profiles.{profile_name}.properties.user", userid)
        profile_manager.set_property(f"profiles.{profile_name}.properties.password", password)
        profile_manager.set_property(f"profiles.{profile_name}.properties.rejectUnauthorized", True)
        
        if cert_path:
            profile_manager.set_property(f"profiles.{profile_name}.properties.certFile", cert_path)
        
        # Set as default profile
        profile_manager.set_property("defaults.zosmf", profile_name)
        
        # Save profile to disk
        logger.debug("Saving profile")
        profile_manager.save()
        
        # Create secure wrapper
        secure_profile = SecureProfileManager(profile_manager)
        
        # Store in session state
        st.session_state.auth_success = True
        st.session_state.secure_profile = secure_profile
        st.session_state.auth_time = datetime.now()
        st.session_state.profile_name = profile_name
        st.session_state.connection = connection  # Store connection for reuse
        
        logger.info(f"Successfully connected to z/OSMF version: {zosmf_info.get('zosmf_version', 'unknown')}")
        return True, f"Successfully connected to z/OSMF! Server version: {zosmf_info.get('zosmf_version', 'unknown')}"
        
    except Exception as e:
        st.session_state.auth_success = False
        st.session_state.secure_profile = None
        st.session_state.connection = None
        logger.error(f"Authentication failed: {str(e)}", exc_info=True)
        return False, f"Connection failed: {str(e)}"

def validate_userid(userid: str) -> bool:
    """Validate mainframe userid format"""
    if not userid:
        return False
    # Add your specific userid validation rules
    return len(userid) <= 8 and userid.isalnum()

def main():
    st.title("Mainframe z/OSMF Authentication")
    
    # Initialize session state
    init_session_state()
    
    # Check session expiry
    if st.session_state.auth_success and hasattr(st.session_state, 'secure_profile'):
        if st.session_state.secure_profile.is_expired():
            st.warning("Session expired. Please login again.")
            st.session_state.auth_success = False
            st.session_state.secure_profile.cleanup()
            st.session_state.secure_profile = None
            st.rerun()
    
    # Show logout button if already authenticated
    if st.session_state.auth_success:
        st.write(f"Connected to: {st.session_state.current_host}")
        if st.button("Logout"):
            try:
                if hasattr(st.session_state, 'secure_profile') and st.session_state.secure_profile:
                    st.session_state.secure_profile.cleanup()
                if hasattr(st.session_state, 'profile_name'):
                    # Clean up profile file
                    profile_path = os.path.join(os.path.expanduser("~"), ".zowe", "profiles", f"{st.session_state.profile_name}.yaml")
                    if os.path.exists(profile_path):
                        os.remove(profile_path)
            except Exception as e:
                logger.error(f"Logout cleanup failed: {str(e)}")
            finally:
                # Clear session state
                for key in ['auth_success', 'secure_profile', 'current_host', 'profile_name', 'auth_time', 'connection']:
                    if key in st.session_state:
                        del st.session_state[key]
            st.rerun()
        
        st.success("You are logged in! Use the sidebar to navigate to other pages.")
        return
    
    # Display certificate status
    cert_path = os.getenv('ZOWE_CERTIFICATE_PATH')
    if cert_path:
        st.info("Certificate configured ✓")
    else:
        st.warning("No certificate configured in environment")
    
    with st.form("login_form"):
        environment = st.selectbox(
            "Select Mainframe Environment",
            options=list(MAINFRAME_HOSTS.keys()),
            help="Choose the mainframe environment to connect to"
        )
        
        host = MAINFRAME_HOSTS[environment]
        st.info(f"Selected Host: {host}")
        
        userid = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not all([userid, password]):
                st.error("Please fill in all required fields")
            elif not validate_userid(userid):
                st.error("Invalid User ID format")
            else:
                with st.spinner('Attempting to connect...'):
                    success, message = authenticate_mainframe(
                        userid, 
                        password, 
                        host
                    )
                if success:
                    st.session_state.current_host = host
                    st.success(message)
                else:
                    st.error(message)

if __name__ == "__main__":
    main() 