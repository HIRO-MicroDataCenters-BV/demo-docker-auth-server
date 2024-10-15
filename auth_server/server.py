from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .auth import (
    InvalidToken,
    Option,
    create_token,
    create_token_option,
    load_cert_and_key,
    validate_token,
)
from .config import CRT_FILE, KEY_FILE, PASSWORD, USERNAME

app = FastAPI()
security = HTTPBasic()


async def get_jwt_token(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    return credentials.password


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def authorize(opt: Option) -> list[str]:
    return opt.actions


@app.get("/auth")
async def auth(
    token: str = Depends(get_jwt_token),
) -> JSONResponse:
    return JSONResponse(content={"token": token, "access_token": token})


@app.get("/get-token")
async def get_token(
    service: str,
    scope: str,
    account: str = "",
    username: str = Depends(get_current_user),
) -> JSONResponse:
    public_key, private_key = load_cert_and_key(CRT_FILE, KEY_FILE)

    opt = create_token_option(service, account, scope)
    actions = authorize(opt)

    if not actions:
        raise HTTPException(status_code=403, detail="Unauthorized actions")

    try:
        tk = create_token(public_key, private_key, opt, actions)
        return JSONResponse(
            content={"token": tk.token, "access_token": tk.access_token}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")


@app.get("/validate")
async def validate(
    token: str = Depends(get_jwt_token),
) -> JSONResponse:
    public_key, _ = load_cert_and_key(CRT_FILE, KEY_FILE)
    try:
        validate_token(token, public_key)
        return JSONResponse(content={"status": "OK"})
    except InvalidToken as e:
        return JSONResponse(
            content={
                "errors": [
                    {
                        "code": "UNAUTHORIZED",
                        "message": "authentication required",
                        "detail": str(e),
                    },
                ],
            },
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Registry Realm"'},
        )
