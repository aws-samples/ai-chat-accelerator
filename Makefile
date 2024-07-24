app := ai-chatbot
platform := linux/amd64

all: help

.PHONY: help
help: Makefile
	@echo
	@echo " Choose a make command to run"
	@echo
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo

## init: run this once to initialize a new python project
.PHONY: init
init:
	python3 -m venv .venv
	direnv allow .

## install: install project dependencies
.PHONY: install
install:
	python3 -m pip install --upgrade pip
	pip install -r requirements.txt
	pip freeze > piplock.txt

## start: run local project
.PHONY: start
start:
	clear
	@echo ""
	git ls-files | grep -v iac | entr -r python main.py

## baseimage: build base image
.PHONY: baseimage
baseimage:
	docker build -t ai-chatbot.base:0.1.0 -f Dockerfile.base --platform ${platform} .

## deploy: build and deploy container
.PHONY: deploy
deploy:
	./deploy.sh ${app} ${platform}

## up: run the app locally using docker compose
.PHONY: up
up:
	docker compose build && docker compose up -d && docker compose logs -f

## down: stop the app
.PHONY: down
down:
	docker compose down

## start-docker: run local project using docker compose
.PHONY: start-docker
start-docker:
	clear
	@echo ""
	git ls-files | grep -v iac | entr -r make up
