FROM docker-registry.ebrains.eu/hdc-services-image/base-image:python-3.10.12-v2 AS production-environment

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

COPY poetry.lock pyproject.toml ./
RUN poetry run pip install setuptools==65.6.3
RUN poetry install --no-dev --no-interaction

COPY alembic.ini .
COPY app ./app
COPY attachments ./attachments
COPY COPYRIGHT .
COPY ldap_query_config.yaml .
COPY LICENSE .
COPY migrations ./migrations
COPY poetry.lock .
COPY pyproject.toml .

FROM production-environment AS auth-image

RUN chown -R app:app /app
USER app

CMD ["python3", "-m", "app"]

FROM production-environment AS development-environment

RUN poetry install --no-interaction


FROM development-environment AS alembic-image

ENV ALEMBIC_CONFIG=alembic.ini

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
RUN chown -R app:app /app
USER app

ENTRYPOINT ["python3", "-m", "alembic"]

CMD ["upgrade", "head"]
