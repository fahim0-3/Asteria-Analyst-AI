.PHONY: install dev migrate seed generate-sample-data test lint format evaluate reset docker-up docker-down
install:
	python -m pip install -e "backend[dev]"
	cd frontend && npm install
dev:
	@echo "Run backend: cd backend && uvicorn app.main:app --reload"
	@echo "Run frontend: cd frontend && npm run dev"
migrate:
	cd backend && alembic upgrade head
seed:
	cd backend && python -c "from app.db.session import SessionLocal; from app.security.auth import seed_users; db=SessionLocal(); seed_users(db); db.close()"
generate-sample-data:
	python scripts/generate_sample_data.py
test:
	cd backend && pytest -q
lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint
format:
	cd backend && ruff format app tests
evaluate:
	python evaluation/run_evaluation.py
reset:
	python scripts/reset_local.py
docker-up:
	docker compose up --build
docker-down:
	docker compose down

