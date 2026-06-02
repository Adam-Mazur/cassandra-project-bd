from backend.schema import CinemaIn, MovieIn, ReservationIn, UserIn, ReservationUpdateIn, BulkReservationIn
from backend.database import Database, get_db, lifespan
from cassandra import OperationTimedOut, Unavailable
from cassandra.cluster import NoHostAvailable
from fastapi import Depends, FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from uuid import UUID


app = FastAPI(lifespan=lifespan)


@app.exception_handler(NoHostAvailable)
@app.exception_handler(OperationTimedOut)
@app.exception_handler(Unavailable)
async def cassandra_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/movies")
def list_movies(db: Database = Depends(get_db)):
    return db.get_movies()


@app.post("/movies")
def create_movie(movie: MovieIn, db: Database = Depends(get_db)):
    db.add_movie(movie.title, movie.duration)
    return {"ok": True}


@app.get("/cinemas")
def list_cinemas(db: Database = Depends(get_db)):
    return db.get_cinemas()


@app.post("/cinemas")
def create_cinema(cinema: CinemaIn, db: Database = Depends(get_db)):
    db.add_cinema(cinema.name, cinema.location, cinema.capacity)
    return {"ok": True}


@app.get("/users")
def list_users(db: Database = Depends(get_db)):
    return db.get_users()


@app.post("/users")
def create_user(user: UserIn, db: Database = Depends(get_db)):
    db.add_user(user.name, user.email)
    return {"ok": True}


@app.get("/reservations")
def list_reservations(db: Database = Depends(get_db)):
    return db.get_reservations()


@app.post("/reservations")
def create_reservation(reservation: ReservationIn, db: Database = Depends(get_db)):
    reservation_id = db.make_reservation(
        reservation.user_id,
        reservation.movie_id,
        reservation.cinema_id,
        reservation.seat_number,
    )
    if reservation_id is None:
        raise HTTPException(status_code=409, detail="Seat already taken or invalid")
    return {"reservation_id": reservation_id}


@app.post("/reservations/bulk")
def create_reservations_bulk(reservation: BulkReservationIn, db: Database = Depends(get_db)):
    return {"results": db.make_reservations(
        reservation.user_id,
        reservation.movie_id,
        reservation.cinema_id,
        reservation.seat_numbers,
    )}


@app.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: UUID, db: Database = Depends(get_db)):
    return {"ok": db.cancel_reservation(reservation_id)}


@app.put("/reservations/{reservation_id}")
def update_reservation(
    reservation_id: UUID,
    update: ReservationUpdateIn,
    db: Database = Depends(get_db),
):
    return {"ok": db.change_reservation(reservation_id, update.new_seat_number)}


@app.delete("/reservations")
def delete_reservations(reservation_ids: list[UUID], db: Database = Depends(get_db)):
    return {"ok": db.cancel_reservations(reservation_ids)}
