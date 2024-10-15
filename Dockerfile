FROM python:3.12-slim

WORKDIR /app
COPY ./pyproject.toml ./poetry.lock ./

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --without dev,test \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY . /app

CMD ["uvicorn", "auth_server.server:app", "--host", "0.0.0.0", "--port", "8000"]
