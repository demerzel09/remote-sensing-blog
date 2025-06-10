#!/usr/bin/env python
from sentinelhub import SHConfig
import os, requests, json
cfg = SHConfig()
cfg.sh_client_id = os.getenv("SENTINELHUB_CLIENT_ID")
cfg.sh_client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET")
cfg.sh_base_url = "https://sh.dataspace.copernicus.eu"
cfg.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
print("ID:", cfg.sh_client_id[:6] if cfg.sh_client_id else None)
print("TOKEN URL:", cfg.sh_token_url)
# トークン取得テスト
r = requests.post(
    cfg.sh_token_url,
    data={
        "grant_type": "client_credentials",
        "client_id": cfg.sh_client_id,
        "client_secret": cfg.sh_client_secret,
    },
    timeout=10,
)
print("Status:", r.status_code)
print("Sample response:", json.loads(r.text) | {"access_token": "..."} )
