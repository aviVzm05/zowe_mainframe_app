# Zowe Mainframe Authentication App

A secure Streamlit-based application for mainframe operations using z/OSMF.

## Features

- Secure mainframe authentication
- Dataset download and upload capabilities
- Encrypted credential storage
- Session management
- Certificate handling
- Comprehensive logging

## Prerequisites

- Python 3.8 or higher
- OpenSSL (for certificate conversion)
- Access to a z/OSMF enabled mainframe
- Valid mainframe credentials
- SSL certificate (if required by your mainframe)

# Linux/Mac
`export ZOWE_CERTIFICATE_PATH=/path/to/your/cert.cer`

# Windows Command Prompt
`set ZOWE_CERTIFICATE_PATH=C:\path\to\your\cert.cer`

# Windows PowerShell
`$env:ZOWE_CERTIFICATE_PATH="C:\path\to\your\cert.cer"`

## Project Structure

```
zowe_app/
├── .streamlit/
│   ├── secrets.toml          # Active configuration (not in version control)
│   └── secrets.example.toml  # Example configuration template
├── logs/                     # Application logs directory
│   └── zowe_auth_*.log      # Log files with timestamps
├── pages/                    # Streamlit additional pages
│   ├── 1_Download_Dataset.py # Dataset download functionality
│   └── 2_Upload_Dataset.py   # Dataset upload functionality
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── auth_utils.py         # Authentication utilities
│   └── security_utils.py     # Security and encryption utilities
├── .env                      # Environment variables (not in version control)
├── .gitignore               # Git ignore rules
├── Home.py                  # Main application entry point
├── README.md                # Project documentation
└── requirements.txt         # Python dependencies

# Runtime-generated directories (not in version control)
├── .keys/                   # Encryption keys storage
└── .zowe/                   # Zowe profile storage
```

### Key Directories and Files

- `.streamlit/`: Contains application configuration
- `logs/`: Application logs with timestamps
- `pages/`: Additional Streamlit pages for dataset operations
- `utils/`: Helper modules for authentication and security
- `.keys/`: Runtime directory for encryption keys (auto-generated)
- `.zowe/`: Runtime directory for Zowe profiles

## Installation

1. Create and activate a virtual environment (recommended):
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Security Implementation

### Credential Encryption
The application uses the following security measures to protect sensitive information:

1. **Fernet Symmetric Encryption**
   - Uses cryptography.fernet for secure encryption
   - Automatically generates and manages encryption keys
   - Keys are stored separately from profiles in `.keys` directory
   - Implements secure key rotation capabilities

2. **Secure Profile Management**
   ```python
   # Example of how credentials are handled
   secure_profile.secure_property("password", password)  # Encrypted
   secure_profile.secure_property("user", userid)       # Encrypted
   secure_profile.secure_property("host", host)         # Not encrypted
   ```

3. **Session Management**
   - Sessions expire after 8 hours
   - Automatic cleanup of sensitive data
   - Secure session state management
   - Force re-authentication after expiry

4. **Secure Storage**
   - Encrypted credentials in memory
   - No plain-text passwords in logs
   - Secure cleanup after session end
   - Protected profile storage

### Certificate Handling

1. **Certificate Processing**
   ```bash
   # Convert .cer to .pem format
   openssl x509 -inform DER -in cert.cer -out cert.pem
   ```

2. **Certificate Security**
   - Automatic format detection
   - Secure conversion process
   - Path validation
   - Access control verification

### Security Best Practices

1. **File Security**
   - Add `.keys/` to .gitignore
   - Secure permissions on key files
   - Regular key rotation
   - Secure file cleanup

2. **Production Deployment**
   ```bash
   # Set secure permissions for key directory
   chmod 600 .keys/encryption.key
   ```

3. **Environment Variables**
   ```bash
   # Optional: Use environment for key management
   export ZOWE_ENCRYPTION_KEY=your_base64_key
   ```

4. **Additional Security Measures**
   - Rate limiting on authentication
   - Session timeout controls
   - Secure error handling
   - Audit logging

## Usage

### Authentication
1. Start the application:
   ```bash
   streamlit run Home.py
   ```

2. Enter credentials:
   - Mainframe host
   - User ID
   - Password
   - Certificate path (if required)

3. Security Status:
   - Green check: Successfully authenticated
   - Red X: Authentication failed
   - Yellow warning: Session expired

### Dataset Operations

1. **Download Dataset**
   - Navigate to Download page
   - Enter dataset name
   - Specify local path
   - Download and preview

2. **Upload Dataset**
   - Navigate to Upload page
   - Select local file
   - Enter target dataset
   - Configure dataset properties

## Logging

The application implements comprehensive logging:

# Log levels

- DEBUG # Detailed debugging information
- INFO # General operational events
- WARNING # Warning messages
- ERROR # Error events

Log files are stored in `logs/` directory with timestamp:
```
logs/
├── zowe_auth_20240315_143022.log
└── zowe_auth_20240315_143156.log
```

## Security Recommendations

1. **Key Management**
   - Regularly rotate encryption keys
   - Secure key storage
   - Implement key backup procedures

2. **Access Control**
   - Implement IP-based restrictions
   - Add two-factor authentication
   - Regular security audits

3. **Monitoring**
   - Monitor failed login attempts
   - Track session durations
   - Audit file operations

4. **Compliance**
   - Regular security updates
   - Compliance documentation
   - Security policy enforcement

## Troubleshooting

### Common Security Issues

1. **Session Expiry**
   ```python
   "Session expired. Please login again!"
   # Solution: Re-authenticate
   ```

2. **Certificate Issues**
   ```python
   "Certificate file not found"
   # Check file path and permissions
   ```

3. **Encryption Errors**
   ```python
   "Decryption failed"
   # Check key file integrity
   ```

## Support and Resources

- [Zowe Python SDK Documentation](https://github.com/zowe/zowe-client-python-sdk)
- [Cryptography Documentation](https://cryptography.io/en/latest/)
- [Streamlit Security](https://docs.streamlit.io/library/advanced-features/security)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Contacts

For security issues, please contact:
- Security Team: security@your-org.com
- Maintainers: maintainers@your-org.com

## Configuration

This application uses Streamlit's secrets management for configuration. To set up:

1. Create a `.streamlit/secrets.toml` file based on `secrets.example.toml`
2. Update the values in your `secrets.toml` with your environment-specific settings
3. For production deployment, use Streamlit Cloud's secrets management

Never commit the actual `secrets.toml` file to version control.