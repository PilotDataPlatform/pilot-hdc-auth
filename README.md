# Auth Service

[![Python](https://img.shields.io/badge/python-3.9-brightgreen.svg)](https://www.python.org/)

Manages user related data as well as authentication and permissions. Connects to Keycloak and optionally AD or OpenLDAP

## Getting Started

### Prerequisites

This project is using [Poetry](https://python-poetry.org/docs/#installation) to handle the dependencies. Installtion instruction for poetry can be found at https://python-poetry.org/docs/#installation

### Installation & Quick Start


1. Clone the project.

       git clone https://github.com/PilotDataPlatform/auth.git

2. Install dependencies.

       poetry install

3. Add environment variables into `.env`. Use `.env.schema` as a reference.

4. Run setup scripts for postgres
    - [Create DB](https://github.com/PilotDataPlatform/auth/blob/develop/migrations/scripts/create_db.sql)
    - [Create Schemas](https://github.com/PilotDataPlatform/auth/blob/develop/migrations/scripts/create_schema.sql)

5. Run schema migration using alembic.

       poetry run alembic upgrade head

6. Run application.

       poetry run python run.py


### Startup using Docker

This project can also be started using [Docker](https://www.docker.com/get-started/).

1. To build and start the service within the Docker container, run:

       docker compose up

2. Migrations should run automatically after the previous step. They can also be manually triggered:

       docker compose run --rm alembic upgrade head

## Contribution

You can contribute the project in following ways:

* Report a bug.
* Suggest a feature.
* Open a pull request for fixing issues or adding functionality. Please consider
  using [pre-commit](https://pre-commit.com) in this case.

## Acknowledgements

The development of the HealthDataCloud open source software was supported by the EBRAINS research infrastructure, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3) and H2020 Research and Innovation Action Grant Interactive Computing E-Infrastructure for the Human Brain Project ICEI 800858.

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101058516. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or other granting authorities. Neither the European Union nor other granting authorities can be held responsible for them.

![HDC-EU-acknowledgement](https://hdc.humanbrainproject.eu/img/HDC-EU-acknowledgement.png)
