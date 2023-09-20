FROM python:3.9-buster AS production-environment

ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONIOENCODING=UTF-8 \
    POETRY_VERSION=1.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

ENV TZ=America/Toronto

ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y libsasl2-dev python-dev libldap2-dev libssl-dev vim-tiny less && \
    ln -s /usr/bin/vim.tiny /usr/bin/vim && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /usr/src/app

COPY poetry.lock pyproject.toml ./
RUN poetry run pip install setuptools==65.6.3
RUN poetry install --no-dev --no-interaction

COPY . .

FROM production-environment AS auth-image

CMD ["python3", "-m", "app"]

FROM production-environment AS development-environment

RUN poetry install --no-interaction


FROM development-environment AS alembic-image

ENV ALEMBIC_CONFIG=alembic.ini

COPY . .

ENTRYPOINT ["python3", "-m", "alembic"]

CMD ["upgrade", "head"]
