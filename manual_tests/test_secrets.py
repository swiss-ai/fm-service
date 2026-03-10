import secrets

print(f"sk-rc-{secrets.token_urlsafe(16)}")
