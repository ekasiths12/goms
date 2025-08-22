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
    try:
        # Get credentials from environment
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            return jsonify({
                'error': 'GOOGLE_CREDENTIALS environment variable not set',
                'message': 'Please configure Google OAuth2 credentials in Railway'
            }), 400
        
        # Parse credentials
        creds_data = json.loads(credentials_json)
        
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds_data, f)
            temp_credentials_path = f.name
        
        try:
            # Create OAuth2 flow
            flow = InstalledAppFlow.from_client_secrets_file(
                temp_credentials_path, SCOPES)
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store flow in session for callback
            session['oauth2_flow'] = flow
            
            return jsonify({
                'auth_url': auth_url,
                'message': 'OAuth2 flow initialized successfully'
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_credentials_path)
            
    except Exception as e:
        return jsonify({
            'error': 'Failed to initialize OAuth2 flow',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2callback', methods=['GET'])
def oauth2_callback():
    """Handle OAuth2 callback from Google"""
    try:
        # Get authorization code from request
        code = request.args.get('code')
        if not code:
            return jsonify({
                'error': 'No authorization code received',
                'message': 'OAuth2 callback failed'
            }), 400
        
        # Get flow from session
        flow = session.get('oauth2_flow')
        if not flow:
            return jsonify({
                'error': 'No OAuth2 flow found in session',
                'message': 'Please restart the OAuth2 flow'
            }), 400
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        
        # Store credentials in session
        session['oauth2_credentials'] = {
            'token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'token_uri': flow.credentials.token_uri,
            'client_id': flow.credentials.client_id,
            'client_secret': flow.credentials.client_secret,
            'scopes': flow.credentials.scopes
        }
        
        # Clear flow from session
        session.pop('oauth2_flow', None)
        
        return jsonify({
            'message': 'OAuth2 authentication successful!',
            'status': 'authenticated'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'OAuth2 callback failed',
            'message': str(e)
        }), 500

@oauth2_bp.route('/oauth2/status', methods=['GET'])
def oauth2_status():
    """Check OAuth2 authentication status"""
    try:
        # Check if we have credentials in session
        credentials = session.get('oauth2_credentials')
        if credentials:
            return jsonify({
                'status': 'authenticated',
                'message': 'OAuth2 credentials are available'
            })
        
        # Check if we have environment credentials
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if credentials_json:
            creds_data = json.loads(credentials_json)
            if 'type' in creds_data and creds_data['type'] == 'service_account':
                return jsonify({
                    'status': 'service_account',
                    'message': 'Using service account authentication'
                })
            else:
                return jsonify({
                    'status': 'needs_oauth2',
                    'message': 'OAuth2 credentials available but not authenticated'
                })
        
        return jsonify({
            'status': 'not_configured',
            'message': 'No Google Drive credentials configured'
        })
        
    except Exception as e:
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
        session.pop('oauth2_flow', None)
        
        return jsonify({
            'message': 'OAuth2 credentials cleared successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to clear OAuth2 credentials',
            'message': str(e)
        }), 500
