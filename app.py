from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
GRAPH_MESSAGES_ENDPOINT = "https://graph.microsoft.com/v1.0/me/messages"
GRAPH_SCOPE = "https://graph.microsoft.com/.default offline_access"


@dataclass
class AccountInput:
    email: str
    password: str
    refresh_token: str
    client_id: str

    @classmethod
    def from_line(cls, line: str) -> Optional["AccountInput"]:
        raw = line.strip()
        if not raw:
            return None

        parts = [part.strip() for part in raw.split("|")]
        if len(parts) < 4:
            raise ValueError(
                "Mỗi dòng cần đúng định dạng: email|password|refresh_token|client_id"
            )

        return cls(
            email=parts[0],
            password=parts[1],
            refresh_token=parts[2],
            client_id=parts[3],
        )


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    tenant: str,
    client_secret: Optional[str] = None,
) -> str:
    payload = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": GRAPH_SCOPE,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    response = requests.post(
        TOKEN_ENDPOINT.format(tenant=tenant),
        data=payload,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Không nhận được access_token từ Microsoft OAuth2.")
    return token


def fetch_messages(access_token: str, top: int = 10) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "$select": "from,subject,receivedDateTime,bodyPreview",
        "$orderby": "receivedDateTime desc",
        "$top": str(top),
    }

    response = requests.get(
        GRAPH_MESSAGES_ENDPOINT,
        headers=headers,
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("value", [])


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    errors = []

    if request.method == "POST":
        raw_accounts = request.form.get("accounts", "")
        use_graph_api = request.form.get("use_graph_api") == "on"
        use_oauth2 = request.form.get("use_oauth2") == "on"

        if not use_graph_api:
            errors.append("Bạn cần bật Graph API.")
        if not use_oauth2:
            errors.append("Bạn cần bật OAuth2.")

        tenant = os.getenv("MS_TENANT", "common")
        client_secret = os.getenv("MS_CLIENT_SECRET")

        if not errors:
            for idx, line in enumerate(raw_accounts.splitlines(), start=1):
                try:
                    account = AccountInput.from_line(line)
                    if account is None:
                        continue

                    access_token = refresh_access_token(
                        account.refresh_token,
                        account.client_id,
                        tenant,
                        client_secret,
                    )
                    messages = fetch_messages(access_token)
                    results.append(
                        {
                            "line": idx,
                            "email": account.email,
                            "message_count": len(messages),
                            "messages": messages,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"Dòng {idx}: {exc}")

    return render_template("index.html", results=results, errors=errors)


if __name__ == "__main__":
    app.run(debug=True)
