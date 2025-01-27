import praw
from flask import Blueprint, request, current_app, redirect, url_for
import uuid
import requests
import json


reddit_bp = Blueprint('reddit', __name__,  url_prefix='/reddit')



@reddit_bp.route('/test', methods=['GET'])
def test():
    return {'message': 'Reddit Blueprint is working'}

@reddit_bp.route('/login', methods=['GET'])
def reddit_login():
    reddit = praw.Reddit(
        client_id=current_app.config['REDDIT_CLIENT_ID'],
        client_secret=current_app.config['REDDIT_CLIENT_SECRET'],
        redirect_uri=current_app.config['REDDIT_REDIRECT_URI'],
        user_agent=current_app.config['REDDIT_USER_AGENT']
    )

    return redirect(reddit.auth.url(scopes=current_app.config['REDDIT_SCOPES'], 
                                    state=str(uuid.uuid4()), 
                                    duration="permanent"))
    

@reddit_bp.route('/auth_callback', methods=['GET'])
def reddit_auth_callback():
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    error = request.args.get('error', '')
    error_description = request.args.get('error_description', '')
    