import os
from urllib.parse import urlencode

import requests
import streamlit as st

CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

SCOPES = [
    "https://www.googleapis.com/auth/dataportability.maps.reviews",
    "https://www.googleapis.com/auth/dataportability.maps.starred_places",
    "https://www.googleapis.com/auth/dataportability.saved.collections",
]

st.set_page_config(
    page_title="Google Maps Dashboard",
    page_icon="🗺️",
)

st.title("🗺️ Google Maps Dashboard")

# Google redirected us back with an authorization code
code = st.query_params.get("code")

if code:
    st.info("Google authorization received. Testing access...")

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )

    if token_response.ok:
        token_data = token_response.json()
        access_token = token_data["access_token"]

        check_response = requests.post(
            "https://dataportability.googleapis.com/v1/accessType:check",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=30,
        )

        st.write("Data Portability API status:", check_response.status_code)

        if check_response.ok:
            st.success("Google Data Portability connection works!")
            st.json(check_response.json())
        else:
            st.error("Google accepted OAuth, but Data Portability API failed.")
            st.code(check_response.text)

    else:
        st.error("Google OAuth token exchange failed.")
        st.code(token_response.text)

else:
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    st.write(
        "Connect your Google account to test access to your "
        "Maps reviews, starred places, and saved collections."
    )

    st.link_button("Connect Google Maps", auth_url)