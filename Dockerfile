FROM python:3.11-slim

WORKDIR /main

COPY pyproject.toml poetry.lock ./

RUN pip install poetry

COPY . .

RUN poetry install --no-interaction --no-ansi

RUN pip install -e .

EXPOSE 8000

CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]