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


todo:
- Cancellation of more reservations/entries then one at a time (in frontend)
- – See reservation and see who made it (see an entry in the database) - to  jest dla admina ale fajnie by było zobaczyć też imiona osób
- Application can work on every node in cluster - to nie wiem czy jest
- Error handling - zobaczy czy jest wszędzie
- Stress Test 1: The client makes the same request very quickly.
- Stress Test 2: Two or more clients make the possible requests randomly
- Stress Test 4: (only for pairs) constant cancellations and seat occupancy.
- Stress Test 5: (only for pairs) Make large group cancellation of many reservations.