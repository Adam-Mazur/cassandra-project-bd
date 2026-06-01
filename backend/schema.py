from pydantic import BaseModel
from uuid import UUID


class MovieIn(BaseModel):
    title: str
    duration: int


class CinemaIn(BaseModel):
    name: str
    location: str
    capacity: int


class UserIn(BaseModel):
    name: str
    email: str


class ReservationIn(BaseModel):
    user_id: UUID
    movie_id: UUID
    cinema_id: UUID
    seat_number: int


class ReservationUpdateIn(BaseModel):
    new_seat_number: int


class BulkReservationIn(BaseModel):
    user_id: UUID
    movie_id: UUID
    cinema_id: UUID
    seat_numbers: list[int]
