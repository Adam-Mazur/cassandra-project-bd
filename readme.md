# project big data


## reset database

docker exec cas1 cqlsh -e "DROP KEYSPACE cinema;"


## running

### setup 

docker compose up
uv sync

### backend

Później, po paru minutach:

cd backend
uv run -m fastapi src/main.py


### admin
cd admin
uv run streamlit run app.py


### user
cd user
uv run streamlit run app.py

## dependencies

Single `uv.lock` at the root manages all three components as a uv workspace:

- `backend` — FastAPI + cassandra-driver
- `admin` — Streamlit + httpx
- `user` — Streamlit + httpx

To install deps for a specific component: `uv sync --package backend` (or `admin` / `user`).



 
