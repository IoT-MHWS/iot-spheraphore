FROM python:3.11-alpine

# change to any directory
WORKDIR /backend
RUN pip install --upgrade pip

# set to your poetry version
RUN pip install poetry==1.4.1
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main

COPY backend/app ./app

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
