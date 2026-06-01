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

### pen-tests
```
uv run pytest stress_test/ -v -s
```
-v — shows each test name and pass/fail
-s — lets the print() output from test 4 (seat split) show in the terminal



## Reset database

```sh
docker exec cas1 cqlsh -e "DROP KEYSPACE cinema;"
docker exec cas1 cqlsh -e "CREATE KEYSPACE cinema WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};"
```
