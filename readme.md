# project big data


## reset database

docker exec cas1 cqlsh -e "DROP KEYSPACE cinema;"


## running

### backend
docker compose up

Później, po paru minutach:

cd backend
uv run -m fastapi src/main.py


### admin
cd admin
uv run streamlit run app.py



 
