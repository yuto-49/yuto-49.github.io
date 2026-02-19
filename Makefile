# ============================================
# Yuto Portfolio - Makefile
# ============================================

PYTHON      := python3
VENV        := venv
PIP         := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
UVICORN     := $(VENV)/bin/uvicorn

BACKEND_DIR := backend
BACKEND_PORT := 8000
FRONTEND_PORT := 3000

DOCKER_IMAGE := yuto-portfolio
DOCKER_TAG   := latest

# ============================================
# Setup
# ============================================

.PHONY: setup
setup: venv install env ## Full local setup (venv + deps + .env)

venv: ## Create virtual environment
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "Virtual environment ready."

.PHONY: install
install: venv ## Install Python dependencies
	$(PIP) install -r requirements.txt

.PHONY: env
env: ## Create .env from template if missing
	@test -f $(BACKEND_DIR)/.env || ( \
		echo "ANTHROPIC_API_KEY=your_key_here" > $(BACKEND_DIR)/.env && \
		echo "DISABLE_RAG=false" >> $(BACKEND_DIR)/.env && \
		echo "PRELOAD_RAG=false" >> $(BACKEND_DIR)/.env && \
		echo "Created $(BACKEND_DIR)/.env — add your ANTHROPIC_API_KEY" \
	)

# ============================================
# Development
# ============================================

.PHONY: backend
backend: ## Start backend (FastAPI + uvicorn, hot-reload)
	cd $(BACKEND_DIR) && ../$(UVICORN) app:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

.PHONY: frontend
frontend: ## Start frontend (static file server)
	$(PYTHON) -m http.server $(FRONTEND_PORT)

.PHONY: dev
dev: ## Start both frontend and backend
	@echo "Starting backend on :$(BACKEND_PORT) and frontend on :$(FRONTEND_PORT)..."
	@make backend & make frontend

# ============================================
# API Testing
# ============================================

.PHONY: health
health: ## Check backend health
	@curl -s http://localhost:$(BACKEND_PORT)/health | $(PYTHON) -m json.tool

.PHONY: api-test
api-test: ## Test the agent API endpoint
	@curl -s -X POST http://localhost:$(BACKEND_PORT)/api/agent \
		-H "Content-Type: application/json" \
		-d '{"mode":"summary","agentType":"consultant","profile":{"name":"Test","background":"CS","skills":["Python"],"experience":"2 years","interests":["AI"]}}' \
		| $(PYTHON) -m json.tool

.PHONY: api-docs
api-docs: ## Open FastAPI auto-generated docs
	@echo "Opening http://localhost:$(BACKEND_PORT)/docs"
	@open http://localhost:$(BACKEND_PORT)/docs 2>/dev/null || xdg-open http://localhost:$(BACKEND_PORT)/docs 2>/dev/null || echo "Visit http://localhost:$(BACKEND_PORT)/docs"

# ============================================
# Production
# ============================================

.PHONY: prod
prod: ## Start backend in production mode (no reload)
	cd $(BACKEND_DIR) && ../$(UVICORN) app:app --host 0.0.0.0 --port $(BACKEND_PORT)

# ============================================
# Docker
# ============================================

.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

.PHONY: docker-run
docker-run: ## Run Docker container
	docker run -p $(BACKEND_PORT):$(BACKEND_PORT) \
		--env-file $(BACKEND_DIR)/.env \
		-e PORT=$(BACKEND_PORT) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: docker-stop
docker-stop: ## Stop running Docker container
	@docker ps -q --filter ancestor=$(DOCKER_IMAGE):$(DOCKER_TAG) | xargs -r docker stop

# ============================================
# Deployment
# ============================================

.PHONY: deploy-render
deploy-render: ## Deploy to Render (push to trigger auto-deploy)
	git push origin main

.PHONY: freeze
freeze: ## Update requirements.txt from venv
	$(PIP) freeze > requirements.txt

# ============================================
# Cleanup
# ============================================

.PHONY: clean
clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

.PHONY: clean-all
clean-all: clean ## Remove venv and all caches
	rm -rf $(VENV)

# ============================================
# Help
# ============================================

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
