# Big data project

## Running

### Setup 

```sh
docker compose up
uv sync
```

### Backend

After a few minutes:

```sh
uv run -m fastapi run backend/main.py
```

### Admin
```sh
uv run streamlit run admin/app.py
```

### User
```sh
uv run streamlit run user/app.py
```

## Reset database

```sh
docker exec cas1 cqlsh -e "DROP KEYSPACE cinema;"
docker exec cas1 cqlsh -e "CREATE KEYSPACE cinema WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};"
```
