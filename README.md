# Demo Docker Auth Server
The Auth Server allows you to generate a JWT token using the `/get-token` endpoint. Both the username and password are set to `demo`.
Use the JWT token as the password for the Docker client in the `config.json` file.
The Docker client includes the credentials (username and JWT token) in the header when executing pull or push commands.
The Docker client then makes a request to the Auth Server's `/auth` endpoint, passing the credentials in the header, and retrieves the same JWT token.
Finally, the Docker registry verifies the JWT token and either allows or denies the pull or push command.

## Requirements
Python 3.12+

## Installation
```bash
pip install pre-commit
pre-commit install
```

## Usage
1. Generate certiticates:
    ```bash
    openssl req -x509 -nodes -new -sha256 -days 1024 -newkey rsa:2048 -keyout certs/RootCA.key -out certs/RootCA.pem
    openssl x509 -outform pem -in certs/RootCA.pem -out certs/RootCA.crt
    ```

2. Launch the Registry and Auth Server:
    ```bash
    docker compose build
    docker compose up
    ```

3. Generate a JWT token:
   ```bash
   curl -u demo:demo \
    "http://localhost:8000/get-token?service=Authentication&scope=repository:hello-world:pull,push&account=demo"
   ```
   Response:
   ```json
   {"token":"<token>", "access_token":"<access_token>"}
   ```

4. Configure Docker client auth settings in `$HOME/.docker/config.json`:
   ```json
   {
        "auths": {
            "localhost:5000": {
                "auth": "<credentials>"
            }
        }
    }
   ```
   Where `<credentials>` is a string `demo:<token>` encoded in Base64.

5. Create and push the image:
   ```bash
   docker pull hello-world
   docker tag hello-world localhost:5000/hello-world
   docker push localhost:5000/hello-world
   ```


## Development
1. If you don't have `Poetry` installed run:
    ```bash
    pip install poetry
    ```

2. Install dependencies:
    ```bash
    poetry config virtualenvs.in-project true
    poetry install --no-root --with dev,test
    ```

3. Launch the Auth Server:
    ```bash
    poetry run uvicorn auth_server.server:app --reload
    ```

# Collaboration guidelines
HIRO uses and requires from its partners [GitFlow with Forks](https://hirodevops.notion.site/GitFlow-with-Forks-3b737784e4fc40eaa007f04aed49bb2e?pvs=4)
