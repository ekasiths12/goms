from flask import Blueprint, request, session, redirect, url_for, jsonify, current_app
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os
import tempfile

oauth2_bp = Blueprint('oauth2', __name__)

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

@oauth2_bp.route('/oauth2/init', methods=['GET'])
def oauth2_init():
    """Initialize OAuth2 flow"""
    print("🔍 OAuth2 init endpoint called")
    try:
        # Get credentials from environment
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        print(f"🔍 GOOGLE_CREDENTIALS found: {'Yes' if credentials_json else 'No'}")
        
        if not credentials_json:
            print("❌ No GOOGLE_CREDENTIALS environment variable found")
            return jsonify({
                'error': 'GOOGLE_CREDENTIALS environment variable not set',
                'message': 'Please configure Google OAuth2 credentials in Railway'
            }), 400
        
        # Parse credentials
        try:
            creds_data = json.loads(credentials_json)
            print(f"🔍 Credentials parsed successfully, type: {creds_data.get('type', 'unknown')}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse GOOGLE_CREDENTIALS JSON: {e}")
            return jsonify({
                'error': 'Invalid GOOGLE_CREDENTIALS JSON format',
                'message': f'JSON parsing error: {str(e)}'
            }), 400
        
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds_data, f)
            temp_credentials_path = f.name
            print(f"🔍 Created temporary credentials file: {temp_credentials_path}")
        
        try:
            # Create OAuth2 flow
            print("🔍 Creating OAuth2 flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                temp_credentials_path, SCOPES)
            
            # Determine the correct redirect URI based on the request
            if request.headers.get('Host', '').startswith('localhost'):
                redirect_uri = 'http://localhost:8000/oauth2callback'
            else:
                redirect_uri = 'https://goms.up.railway.app/oauth2callback'
            
            print(f"🔍 Using redirect URI: {redirect_uri}")
            
            # Check if the credentials already have redirect_uris defined
            has_redirect_uris = 'redirect_uris' in creds_data.get('web', {})
            print(f"🔍 Credentials have redirect_uris: {has_redirect_uris}")
            
            # Generate authorization URL
            print("🔍 Generating authorization URL...")
            if has_redirect_uris:
                # Don't pass redirect_uri explicitly if it's already in credentials
                auth_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
            else:
                # Pass redirect_uri explicitly if not in credentials
                auth_url, state = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent',
                    redirect_uri=redirect_uri
                )
            print(f"🔍 Authorization URL generated: {auth_url}")
            print(f"🔍 Authorization URL (first 100 chars): {auth_url[:100]}...")
            
            # Store only the necessary flow data in session (not the entire flow object)
            session['oauth2_flow_data'] = {
                'client_config': creds_data,
                'scopes': SCOPES,
                'state': state,
                'redirect_uri': redirect_uri,
                'has_redirect_uris': has_redirect_uris
            }
            print("🔍 OAuth2 flow data stored in session")
            
            return jsonify({
                'auth_url': auth_url,
                'message': 'OAuth2 flow initialized successfully'
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_credentials_path)
            print(f"🔍 Cleaned up temporary file: {temp_credentials_path}")
            
    except Exception as e:
        print(f"❌ OAuth2 init error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to initialize OAuth2 flow',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2callback', methods=['GET'])
def oauth2_callback():
    """Handle OAuth2 callback from Google"""
    print("🔍 OAuth2 callback endpoint called")
    try:
        # Get authorization code from request
        code = request.args.get('code')
        if not code:
            print("❌ No authorization code received")
            return jsonify({
                'error': 'No authorization code received',
                'message': 'OAuth2 callback failed'
            }), 400
        
        # Get flow data from session
        flow_data = session.get('oauth2_flow_data')
        if not flow_data:
            print("❌ No OAuth2 flow data found in session")
            return jsonify({
                'error': 'No OAuth2 flow data found in session',
                'message': 'Please restart the OAuth2 flow'
            }), 400
        
        # Create temporary credentials file to recreate the flow
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(flow_data['client_config'], f)
            temp_credentials_path = f.name
        
        try:
            # Recreate InstalledAppFlow from stored data
            flow = InstalledAppFlow.from_client_secrets_file(
                temp_credentials_path, flow_data['scopes'])
            
            # Use the stored redirect URI
            redirect_uri = flow_data.get('redirect_uri', 'https://goms.up.railway.app/oauth2callback')
            print(f"🔍 Using stored redirect URI: {redirect_uri}")
            
            # Check if the credentials already have redirect_uris defined
            has_redirect_uris = flow_data.get('has_redirect_uris', False)
            print(f"🔍 Credentials have redirect_uris: {has_redirect_uris}")
            
            # Exchange authorization code for tokens
            if has_redirect_uris:
                # Don't pass redirect_uri explicitly if it's already in credentials
                flow.fetch_token(code=code)
            else:
                # Pass redirect_uri explicitly if not in credentials
                flow.fetch_token(code=code, redirect_uri=redirect_uri)
            
            # Store credentials in session
            session['oauth2_credentials'] = {
                'token': flow.credentials.token,
                'refresh_token': flow.credentials.refresh_token,
                'token_uri': flow.credentials.token_uri,
                'client_id': flow.credentials.client_id,
                'client_secret': flow.credentials.client_secret,
                'scopes': flow.credentials.scopes
            }
            
            print("🔍 OAuth2 credentials stored in session")
            
        finally:
            # Clean up temporary file
            os.unlink(temp_credentials_path)
        
        # Clear flow data from session
        session.pop('oauth2_flow_data', None)
        
        return jsonify({
            'message': 'OAuth2 authentication successful!',
            'status': 'authenticated'
        })
        
    except Exception as e:
        print(f"❌ OAuth2 callback error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'OAuth2 callback failed',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2/status', methods=['GET'])
def oauth2_status():
    """Check OAuth2 authentication status"""
    print("🔍 OAuth2 status endpoint called")
    try:
        # Check if we have credentials in session
        credentials = session.get('oauth2_credentials')
        print(f"🔍 OAuth2 credentials in session: {'Yes' if credentials else 'No'}")
        
        if credentials:
            print("🔍 Found OAuth2 credentials in session")
            return jsonify({
                'status': 'authenticated',
                'message': 'OAuth2 credentials are available'
            })
        
        # Check if we have environment credentials
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        print(f"🔍 GOOGLE_CREDENTIALS in environment: {'Yes' if credentials_json else 'No'}")
        
        if credentials_json:
            try:
                creds_data = json.loads(credentials_json)
                print(f"🔍 Credentials type: {creds_data.get('type', 'unknown')}")
                
                if 'type' in creds_data and creds_data['type'] == 'service_account':
                    service_account_email = creds_data.get('client_email', 'Unknown')
                    print(f"🔍 Service account email: {service_account_email}")
                    return jsonify({
                        'status': 'service_account',
                        'message': f'Using service account authentication: {service_account_email}',
                        'service_account_email': service_account_email
                    })
                else:
                    print("🔍 OAuth2 credentials available but not authenticated")
                    return jsonify({
                        'status': 'needs_oauth2',
                        'message': 'OAuth2 credentials available but not authenticated'
                    })
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse credentials JSON: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid credentials format: {str(e)}'
                }), 500
        
        print("🔍 No Google Drive credentials configured")
        return jsonify({
            'status': 'not_configured',
            'message': 'No Google Drive credentials configured'
        })
        
    except Exception as e:
        print(f"❌ OAuth2 status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2/logout', methods=['POST'])
def oauth2_logout():
    """Clear OAuth2 credentials from session"""
    try:
        # Clear OAuth2 credentials from session
        session.pop('oauth2_credentials', None)
        session.pop('oauth2_flow_data', None)
        
        return jsonify({
            'message': 'OAuth2 credentials cleared successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to clear OAuth2 credentials',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2/service-account-info', methods=['GET'])
def service_account_info():
    """Get service account information for debugging"""
    try:
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            return jsonify({
                'error': 'No GOOGLE_CREDENTIALS found'
            }), 400
        
        creds_data = json.loads(credentials_json)
        
        if creds_data.get('type') == 'service_account':
            return jsonify({
                'service_account_email': creds_data.get('client_email'),
                'project_id': creds_data.get('project_id'),
                'folder_id': os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1TLnjpJuMWdllq3VOgw_kH-EyGRISq6cg'),
                'message': f'Share Google Drive folder {os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1TLnjpJuMWdllq3VOgw_kH-EyGRISq6cg")} with {creds_data.get("client_email")}'
            })
        else:
            return jsonify({
                'error': 'Not using service account credentials'
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
