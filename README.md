# prod-airflow
[![CircleCI](https://circleci.com/gh/r-kells/prod-airflow/tree/master.svg?style=svg&circle-token=3bed58b792cc11f4231fac6d5100e3e5b49024af)](https://circleci.com/gh/r-kells/prod-airflow/tree/master)
[![Docker Build Status](https://img.shields.io/docker/cloud/automated/rkells/prod-airflow.svg)]()
[![Docker Build Status](https://img.shields.io/docker/cloud/build/rkells/prod-airflow.svg)]()

[![Docker Pulls](https://img.shields.io/docker/pulls/rkells/prod-airflow.svg)]()
[![Docker Stars](https://img.shields.io/docker/stars/rkells/prod-airflow.svg)]()

- [prod-airflow](#prod-airflow)
  - [Information](#Information)
  - [Installation](#Installation)
  - [Makefile Configuration Options](#Makefile-Configuration-Options)
    - [1. ENV_FILE: Environment Variable Handling](#1-ENVFILE-Environment-Variable-Handling)
  - [Build](#Build)
    - [2. EXECUTOR: Executor Type](#2-EXECUTOR-Executor-Type)
  - [Test](#Test)
    - [Included tests](#Included-tests)
    - [Coverage](#Coverage)
  - [Debug](#Debug)
  - [Run](#Run)
  - [Monitoring](#Monitoring)
    - [Canary DAG](#Canary-DAG)
  - [Configurating Airflow](#Configurating-Airflow)
    - [Environment Variables:](#Environment-Variables)
    - [Fernet Key](#Fernet-Key)
    - [Authentication](#Authentication)
    - [Ad hoc query / Connections](#Ad-hoc-query--Connections)
    - [The init_airflow.py DAG](#The-initairflowpy-DAG)
    - [Custom Airflow plugins](#Custom-Airflow-plugins)
    - [Install custom python package](#Install-custom-python-package)
    - [UI Links](#UI-Links)

## Information
This repository was originally forked from Puckel's docker-airflow [repository](https://github.com/puckel/docker-airflow)

* Based on Python (3.7-slim) official Image [python:3.7-slim](https://hub.docker.com/_/python/) and uses the official [Postgres](https://hub.docker.com/_/postgres/) as backend and [Redis](https://hub.docker.com/_/redis/) as queue
* Install [Docker](https://www.docker.com/)
* Install [Docker Compose](https://docs.docker.com/compose/install/)
* Following the Airflow release from [Python Package Index](https://pypi.python.org/pypi/apache-airflow)

## Installation

Pull the image from the Docker repository.

    docker pull rkells/prod-airflow

## Makefile Configuration Options

1. ENV_FILE
2. EXECUTOR

### 1. ENV_FILE: Environment Variable Handling

We use `.env` files to manage docker environment variables. 
This is configurable through specifying the environment variable `ENV_FILE`.
The default file is [dev.env](dev.env), also included [prod.env](prod.env)

    make <command> ENV_FILE=prod.env

## Build

    make build 

Optionally install [Extra Airflow Packages](https://airflow.incubator.apache.org/installation.html#extra-package) and/or python dependencies at build time :

    docker build --rm --build-arg AIRFLOW_DEPS="datadog,dask" -t rkells/prod-airflow .
    docker build --rm --build-arg PYTHON_DEPS="flask_oauthlib>=0.9" -t rkells/prod-airflow .

### 2. EXECUTOR: Executor Type

The default executor type is LocalExecutor for `make test` and `make debug`

    make <command> EXECUTOR=Celery

## Test

The Dockerfile mounts your `/test`, `/dags` and `/plugins` directories to `$AIRFLOW_HOME`.
This helps run your tests in a similar environment to production.

By default, we use the `docker-compose-LocalExecutor.yml` to start the 
webserver and scheduler in the same container, and Postgres in another. 

Therefore you can easily have tests that interact with the database.
	
		make test

To use the Celery Executor:

        make test EXECUTOR=Celery

### Included tests

- [test_dag_smoke.py](test/test_dag_smoke.py)
  - Tests that all DAGs compile
  - Verifies DAG bag loads in under 2 seconds.
  - Verifies all DAGs have `email` and `onwer` set.

### Coverage

`make test` runs unittests with coverage, then prints the results.

## Debug

Similar to testing, we run airflow with docker-compose to replicate a production environment.

    make debug
    # inspect logs
    docker logs -f <containerId>
    # jump into the running container
    docker exec -it <containerId> bash

To debug the CeleryExecutor:

    make debug EXECUTOR=Celery

## Run

By default, docker-airflow runs Airflow with **SequentialExecutor** :

    make run

## Monitoring

Using the DAG [init_airflow.py](dags/init_airflow.py) we automatically setup airflow Charts for monitoring.

Airflow Charts: [localhost:8080/admin/chart/](http://localhost:8080/admin/chart/)

- [Active Task Instances](http://localhost:8080/admin/airflow/chart?chart_id=2&iteration_no=0)

### Canary DAG 

The [canary DAG](dags/canary.py) runs every 5 minutes.

It should have a connection check with a simple SQL query (e.g.” SELECT 1”) for all the critical data sources. 
By default its connected to the default postgres setup.

The “canary” DAG helps to answer the following questions:

- Do all critical connections work.
- How long it takes for the Airflow scheduler to schedule the task (scheduled execution_time — current_time).
- How long the task runs.


## Configurating Airflow

### Environment Variables:
Add Airflow ENV variables to `.env` files and reference them with docker
See [Airflow documentation](http://airflow.readthedocs.io/en/latest/howto/set-config.html#setting-configuration-options) for more details

### Fernet Key
For encrypted connection passwords (in Local or Celery Executor), you must have the same fernet_key. By default docker-airflow generates the fernet_key at startup, you have to set an environment variable in the docker-compose (ie: docker-compose-LocalExecutor.yml) file to set the same key accross containers. To generate a fernet_key :

    docker run rkells/prod-airflow python -c "from cryptography.fernet import Fernet; FERNET_KEY = Fernet.generate_key().decode(); print(FERNET_KEY)"

### Authentication

The config [prod.env](prod.env) enables basic password authentication for Airflow.
Even if you are behind other security walls, this authentication is useful because of the ability to filter DAGs by owner.

See the [documentation](https://airflow.apache.org/security.html?highlight=authentication#password) for setup and other details.

### Ad hoc query / Connections
If you want to use Ad hoc query, make sure you've configured connections:
By default the DAG [init_airflow.py](dags/init_airflow.py) will setup a connection to postgres.

To add other connections:
Go to Admin -> Connections and Edit: set the values (equivalent to values in airflow.cfg/docker-compose*.yml) :
- Host : postgres
- Schema : airflow
- Login : airflow
- Password : airflow

### The init_airflow.py DAG

The [init_airflow.py](dags/init_airflow.py) DAG
runs once and is intended to help configure airflow to bootstrap a new installation, or setup for testing.

As currently configured:
1. Creates a connection to postgres called `my_postgres` from the `Ad-hoc query UI.
2. Creates a pool `mypool` with 10 slots. 
3. Creates the [monitoring charts](#Monitoring).

You are encouraged to extend this DAG for reproducible setup. 

### Custom Airflow plugins

Documentation on plugins can be found [here](https://airflow.apache.org/plugins.html)

### Install custom python package

- Create a file "requirements.txt" with the desired python modules
- The entrypoint.sh script will execute the pip install command (with --user option)

Alternatively, build your image with your desired packages

### UI Links

- Airflow: [localhost:8080](http://localhost:8080/)
- Flower: [localhost:5555](http://localhost:5555/)
