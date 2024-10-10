import os

USERNAME = "demo"
PASSWORD = "demo"

CRT_FILE = os.getenv("CRT_FILE", "certs/RootCA.crt")
KEY_FILE = os.getenv("KEY_FILE", "certs/RootCA.key")

ALGO = "RS256"
ISSUER = os.getenv("ISSUER", "Example Issuer")  # The value as in the compose.yaml
