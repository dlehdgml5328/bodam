"""OAuth authentication service for social login."""

from __future__ import annotations

import os
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status


SocialProvider = Literal["naver", "google", "kakao"]


class OAuthError(Exception):
    """Base exception for OAuth errors."""


class OAuthService:
    """Service for handling OAuth authentication with social providers."""

    def __init__(self) -> None:
        # Naver OAuth
        self.naver_client_id = os.getenv("NAVER_LOGIN_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_LOGIN_CLIENT_SECRET")
        self.naver_redirect_uri = os.getenv(
            "NAVER_REDIRECT_URI", "http://localhost:3000/auth/naver/callback"
        )

        # Google OAuth
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback"
        )

        # Kakao OAuth
        self.kakao_client_id = os.getenv("KAKAO_CLIENT_ID")
        self.kakao_redirect_uri = os.getenv(
            "KAKAO_REDIRECT_URI", "http://localhost:3000/auth/kakao/callback"
        )

    def get_authorization_url(self, provider: SocialProvider, state: str) -> str:
        """Generate OAuth authorization URL for the given provider."""
        if provider == "naver":
            return self._get_naver_auth_url(state)
        elif provider == "google":
            return self._get_google_auth_url(state)
        elif provider == "kakao":
            return self._get_kakao_auth_url(state)
        else:
            raise OAuthError(f"Unsupported provider: {provider}")

    def _get_naver_auth_url(self, state: str) -> str:
        """Generate Naver OAuth authorization URL."""
        if not self.naver_client_id:
            raise OAuthError("Naver OAuth not configured")

        params = {
            "response_type": "code",
            "client_id": self.naver_client_id,
            "redirect_uri": self.naver_redirect_uri,
            "state": state,
        }
        return f"https://nid.naver.com/oauth2.0/authorize?{urlencode(params)}"

    def _get_google_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        if not self.google_client_id:
            raise OAuthError("Google OAuth not configured")

        params = {
            "response_type": "code",
            "client_id": self.google_client_id,
            "redirect_uri": self.google_redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    def _get_kakao_auth_url(self, state: str) -> str:
        """Generate Kakao OAuth authorization URL."""
        if not self.kakao_client_id:
            raise OAuthError("Kakao OAuth not configured")

        params = {
            "response_type": "code",
            "client_id": self.kakao_client_id,
            "redirect_uri": self.kakao_redirect_uri,
            "state": state,
        }
        return f"https://kauth.kakao.com/oauth/authorize?{urlencode(params)}"

    async def get_access_token(
        self, provider: SocialProvider, code: str, state: str
    ) -> str:
        """Exchange authorization code for access token."""
        if provider == "naver":
            return await self._get_naver_access_token(code, state)
        elif provider == "google":
            return await self._get_google_access_token(code)
        elif provider == "kakao":
            return await self._get_kakao_access_token(code)
        else:
            raise OAuthError(f"Unsupported provider: {provider}")

    async def _get_naver_access_token(self, code: str, state: str) -> str:
        """Get access token from Naver."""
        if not self.naver_client_id or not self.naver_client_secret:
            raise OAuthError("Naver OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nid.naver.com/oauth2.0/token",
                params={
                    "grant_type": "authorization_code",
                    "client_id": self.naver_client_id,
                    "client_secret": self.naver_client_secret,
                    "code": code,
                    "state": state,
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Naver access token: {response.text}")

            data = response.json()
            if "access_token" not in data:
                raise OAuthError("No access token in Naver response")

            return data["access_token"]

    async def _get_google_access_token(self, code: str) -> str:
        """Get access token from Google."""
        if not self.google_client_id or not self.google_client_secret:
            raise OAuthError("Google OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "code": code,
                    "redirect_uri": self.google_redirect_uri,
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Google access token: {response.text}")

            data = response.json()
            if "access_token" not in data:
                raise OAuthError("No access token in Google response")

            return data["access_token"]

    async def _get_kakao_access_token(self, code: str) -> str:
        """Get access token from Kakao."""
        if not self.kakao_client_id:
            raise OAuthError("Kakao OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.kakao_client_id,
                    "redirect_uri": self.kakao_redirect_uri,
                    "code": code,
                },
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Kakao access token: {response.text}")

            data = response.json()
            if "access_token" not in data:
                raise OAuthError("No access token in Kakao response")

            return data["access_token"]

    async def get_user_info(
        self, provider: SocialProvider, access_token: str
    ) -> dict[str, str]:
        """Get user information from the social provider."""
        if provider == "naver":
            return await self._get_naver_user_info(access_token)
        elif provider == "google":
            return await self._get_google_user_info(access_token)
        elif provider == "kakao":
            return await self._get_kakao_user_info(access_token)
        else:
            raise OAuthError(f"Unsupported provider: {provider}")

    async def _get_naver_user_info(self, access_token: str) -> dict[str, str]:
        """Get user info from Naver."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Naver user info: {response.text}")

            data = response.json()
            if data.get("resultcode") != "00":
                raise OAuthError(f"Naver API error: {data.get('message')}")

            user_data = data.get("response", {})
            return {
                "social_id": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name") or user_data.get("nickname"),
                "provider": "naver",
            }

    async def _get_google_user_info(self, access_token: str) -> dict[str, str]:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Google user info: {response.text}")

            data = response.json()
            return {
                "social_id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "provider": "google",
            }

    async def _get_kakao_user_info(self, access_token: str) -> dict[str, str]:
        """Get user info from Kakao."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError(f"Failed to get Kakao user info: {response.text}")

            data = response.json()
            kakao_account = data.get("kakao_account", {})
            profile = kakao_account.get("profile", {})

            return {
                "social_id": str(data.get("id")),
                "email": kakao_account.get("email"),
                "name": profile.get("nickname"),
                "provider": "kakao",
            }


__all__ = ["OAuthService", "OAuthError", "SocialProvider"]
