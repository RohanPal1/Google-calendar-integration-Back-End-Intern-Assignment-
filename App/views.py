# views.py

from django.shortcuts import redirect
from django.views import View
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from rest_framework.views import APIView
from rest_framework.response import Response
from Project.settings import (
    GOOGLE_OAUTH2_CLIENT_ID,
    GOOGLE_OAUTH2_CLIENT_SECRET,
    GOOGLE_OAUTH2_REDIRECT_URI,
    GOOGLE_API_SCOPES,
    GOOGLE_API_TOKEN_FILE
)


class GoogleCalendarInitView(APIView):
    def get(self, request):
        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=GOOGLE_API_SCOPES,
            redirect_uri=GOOGLE_OAUTH2_REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        request.session['oauth2_state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        state = request.session.pop('oauth2_state', '')
        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=GOOGLE_API_SCOPES,
            redirect_uri=GOOGLE_OAUTH2_REDIRECT_URI,
            state=state
        )
        flow.fetch_token(
            authorization_response=request.build_absolute_uri(),
            client_secret=GOOGLE_OAUTH2_CLIENT_SECRET
        )
        credentials = flow.credentials

        # Save the access token to a file or database
        with open(GOOGLE_API_TOKEN_FILE, 'w') as token_file:
            token_file.write(credentials.to_json())

        # Use the access token to retrieve events from the user's calendar
        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(calendarId='primary', maxResults=10).execute()
        events = events_result.get('items', [])

        # Return the events as a response
        return Response(events)
