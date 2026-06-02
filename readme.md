# Big data project

## short description
A cinema reservation system built on **Apache Cassandra** (via Docker), demonstrating distributed database design for a Big Data course. The project includes a **FastAPI REST** backend, an admin panel (**Streamlit**) for managing cinemas, movies, and screenings, a user panel for browsing and reserving seats, and a suite of **stress tests** using multithreading to simulate concurrent reservations, bulk cancellations, and fault-tolerance under node failure.


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

