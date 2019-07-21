CONTAINERS := $(shell docker ps -a -q --filter name=prod-airflow)
IMAGE_TAG := rkells/prod-airflow:latest
SERVICE := webserver
EXECUTOR := Local
ENV_FILE := dev.env
AIRFLOW_TESTING := False


.PHONY: build
build:
	docker build . -t $(IMAGE_TAG)

.PHONY: test
test: docrm build
	AIRFLOW_TESTING=True ENV_FILE=$(ENV_FILE) docker-compose -f docker-compose-$(EXECUTOR)Executor.yml run \
	webserver

.PHONY: debug
debug: docrm build
	ENV_FILE=$(ENV_FILE) docker-compose -f docker-compose-$(EXECUTOR)Executor.yml up -d --remove-orphans 

.PHONY: run
run: docrm build
	docker run \
	--env-file $(ENV_FILE) \
	-v $(shell pwd)/dags/:/usr/local/airflow/dags \
	-v $(shell pwd)/test/:/usr/local/airflow/test \
    -v $(shell pwd)/plugins/:/usr/local/airflow/plugins \
	-d -p 8080:8080 $(IMAGE_TAG) $(SERVICE)

# Helpers
.PHONY: clean
clean: dockerclean

.PHONY: dockerclean
dockerclean: docrm
	docker image prune

.PHONY: docstop
docstop:
	docker stop $(CONTAINERS) 2>/dev/null || true

.PHONY: docrm
docrm: docstop
	docker rm $(CONTAINERS) 2>/dev/null || true
