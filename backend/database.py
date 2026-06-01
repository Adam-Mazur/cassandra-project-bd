from contextlib import asynccontextmanager
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from fastapi import FastAPI, Request
from abc import ABC, abstractmethod
from uuid import uuid4, UUID


class Database(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def make_reservation(
        user_id: UUID, movie_id: UUID, cinema_id: UUID, seat_number: int
    ) -> UUID | None:
        pass

    @abstractmethod
    def change_reservation(reservation_id: UUID, new_seat_number: int) -> bool:
        pass

    @abstractmethod
    def get_reservations() -> list[dict]:
        pass

    @abstractmethod
    def get_movies() -> list[dict]:
        pass

    @abstractmethod
    def get_cinemas() -> list[dict]:
        pass

    @abstractmethod
    def get_users() -> list[dict]:
        pass

    @abstractmethod
    def add_movie(title: str, duration: int) -> bool:
        pass

    @abstractmethod
    def add_cinema(name: str, location: str, capacity: int) -> bool:
        pass

    @abstractmethod
    def add_user(name: str, email: str) -> bool:
        pass

    @abstractmethod
    def cancel_reservation(reservation_id: UUID) -> bool:
        pass

    @abstractmethod
    def cancel_reservations(reservation_ids: list[UUID]) -> bool:
        pass


class InMemoryDatabase(Database):
    def __init__(self):
        self.reservations = []
        self.movies = []
        self.cinemas = []
        self.users = []

    def connect(self):
        print("Connected to in-memory database")

    def disconnect(self):
        print("Disconnected from in-memory database")
        self.reservations = None
        self.movies = None
        self.cinemas = None
        self.users = None

    def make_reservation(
        self, user_id: UUID, movie_id: UUID, cinema_id: UUID, seat_number: int
    ) -> UUID | None:
        if seat_number < 0:
            return None
        for cinema in self.cinemas:
            if cinema["cinema_id"] == cinema_id:
                if seat_number >= cinema["capacity"]:
                    return None
                break

        for reservation in self.reservations:
            if (
                reservation["movie_id"] == movie_id
                and reservation["cinema_id"] == cinema_id
                and reservation["seat_number"] == seat_number
            ):
                return None

        reservation_id = uuid4()
        reservation = {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "movie_id": movie_id,
            "cinema_id": cinema_id,
            "seat_number": seat_number,
        }
        self.reservations.append(reservation)
        return reservation_id

    def change_reservation(self, reservation_id: UUID, new_seat_number: int) -> bool:
        if new_seat_number < 1:
            return False
        for cinema in self.cinemas:
            if cinema["cinema_id"] == reservation_id:
                if new_seat_number > cinema["capacity"]:
                    return False
                break

        target_reservation = None
        for reservation in self.reservations:
            if reservation["reservation_id"] == reservation_id:
                target_reservation = reservation
            if (
                reservation["movie_id"] == target_reservation["movie_id"]
                and reservation["cinema_id"] == target_reservation["cinema_id"]
                and reservation["seat_number"] == new_seat_number
            ):
                return False

        if target_reservation is None:
            return False

        target_reservation["seat_number"] = new_seat_number
        return True

    def get_reservations(self):
        return self.reservations

    def get_movies(self):
        return self.movies

    def get_cinemas(self):
        return self.cinemas

    def get_users(self):
        return self.users

    def add_movie(self, title: str, duration: int) -> bool:
        movie_id = uuid4()
        movie = {"movie_id": movie_id, "title": title, "duration": duration}
        self.movies.append(movie)
        return True

    def add_cinema(self, name: str, location: str, capacity: int) -> bool:
        cinema_id = uuid4()
        cinema = {
            "cinema_id": cinema_id,
            "name": name,
            "location": location,
            "capacity": capacity,
        }
        self.cinemas.append(cinema)
        return True

    def add_user(self, name: str, email: str) -> bool:
        user_id = uuid4()
        user = {"user_id": user_id, "name": name, "email": email}
        self.users.append(user)
        return True

    def cancel_reservation(self, reservation_id: UUID) -> bool:
        for reservation in self.reservations:
            if reservation["reservation_id"] == reservation_id:
                self.reservations.remove(reservation)
                return True
        return False

    def cancel_reservations(self, reservation_ids: list[UUID]) -> bool:
        success = True
        for reservation_id in reservation_ids:
            if not self.cancel_reservation(reservation_id):
                success = False
        return success


class CassandraDatabase(Database):
    def __init__(
        self,
        contact_points: list[str] | None = None,
        port: int = 9042,
        keyspace: str = "movie_reservations",
    ):
        self.contact_points = contact_points or ["127.0.0.1", "127.0.0.2"]
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None

    def connect(self):
        if self.session is not None:
            return

        self.cluster = Cluster(contact_points=self.contact_points, port=self.port)
        self.session = self.cluster.connect()
        self.session.default_consistency_level = ConsistencyLevel.LOCAL_QUORUM
        self.session.execute(
            f"CREATE KEYSPACE IF NOT EXISTS {self.keyspace} WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}"
        )
        self.session.set_keyspace(self.keyspace)
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS movies (movie_id uuid PRIMARY KEY, title text, duration int)"
        )
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS cinemas (cinema_id uuid PRIMARY KEY, name text, location text, capacity int)"
        )
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id uuid PRIMARY KEY, name text, email text)"
        )
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS reservations ("
            "movie_id uuid, cinema_id uuid, seat_number int, "
            "reservation_id uuid, user_id uuid, "
            "PRIMARY KEY ((movie_id, cinema_id), seat_number))"
        )
        self.session.execute(
            "CREATE TABLE IF NOT EXISTS reservations_by_id ("
            "reservation_id uuid PRIMARY KEY, "
            "movie_id uuid, cinema_id uuid, seat_number int)"
        )

    def disconnect(self):
        if self.session is not None:
            self.session.shutdown()
            self.session = None
        if self.cluster is not None:
            self.cluster.shutdown()
            self.cluster = None

    def make_reservation(
        self, user_id: UUID, movie_id: UUID, cinema_id: UUID, seat_number: int
    ) -> UUID | None:
        if seat_number < 0:
            return None

        cinema = self.session.execute(
            "SELECT cinema_id, capacity FROM cinemas WHERE cinema_id = %s",
            (cinema_id,),
        ).one()
        if cinema is None or cinema.capacity is None or seat_number > cinema.capacity:
            return None

        reservation_id = uuid4()
        result = self.session.execute(
            "INSERT INTO reservations (movie_id, cinema_id, seat_number, reservation_id, user_id) "
            "VALUES (%s, %s, %s, %s, %s) IF NOT EXISTS",
            (movie_id, cinema_id, seat_number, reservation_id, user_id),
        )
        if not result.one().applied:
            return None
        self.session.execute(
            "INSERT INTO reservations_by_id (reservation_id, movie_id, cinema_id, seat_number) "
            "VALUES (%s, %s, %s, %s)",
            (reservation_id, movie_id, cinema_id, seat_number),
        )
        return reservation_id

    def change_reservation(self, reservation_id: UUID, new_seat_number: int) -> bool:
        if new_seat_number < 0:
            return False

        lookup = self.session.execute(
            "SELECT movie_id, cinema_id, seat_number FROM reservations_by_id WHERE reservation_id = %s",
            (reservation_id,),
        ).one()
        if lookup is None:
            return False

        reservation = self.session.execute(
            "SELECT user_id FROM reservations WHERE movie_id = %s AND cinema_id = %s AND seat_number = %s",
            (lookup.movie_id, lookup.cinema_id, lookup.seat_number),
        ).one()
        if reservation is None:
            return False

        cinema = self.session.execute(
            "SELECT capacity FROM cinemas WHERE cinema_id = %s",
            (lookup.cinema_id,),
        ).one()
        if cinema is None or cinema.capacity is None or new_seat_number > cinema.capacity:
            return False

        if lookup.seat_number == new_seat_number:
            return True

        result = self.session.execute(
            "INSERT INTO reservations (movie_id, cinema_id, seat_number, reservation_id, user_id) "
            "VALUES (%s, %s, %s, %s, %s) IF NOT EXISTS",
            (lookup.movie_id, lookup.cinema_id, new_seat_number, reservation_id, reservation.user_id),
        )
        if not result.one().applied:
            return False

        self.session.execute(
            "DELETE FROM reservations WHERE movie_id = %s AND cinema_id = %s AND seat_number = %s",
            (lookup.movie_id, lookup.cinema_id, lookup.seat_number),
        )
        self.session.execute(
            "UPDATE reservations_by_id SET seat_number = %s WHERE reservation_id = %s",
            (new_seat_number, reservation_id),
        )
        return True

    def get_reservations(self):
        return [
            row._asdict()
            for row in self.session.execute(
                "SELECT reservation_id, user_id, movie_id, cinema_id, seat_number FROM reservations"
            )
        ]

    def get_movies(self):
        return [
            row._asdict()
            for row in self.session.execute(
                "SELECT movie_id, title, duration FROM movies"
            )
        ]

    def get_cinemas(self):
        return [
            row._asdict()
            for row in self.session.execute(
                "SELECT cinema_id, name, location, capacity FROM cinemas"
            )
        ]

    def get_users(self):
        return [
            row._asdict()
            for row in self.session.execute("SELECT user_id, name, email FROM users")
        ]

    def add_movie(self, title: str, duration: int) -> bool:
        result = self.session.execute(
            "INSERT INTO movies (movie_id, title, duration) VALUES (%s, %s, %s) IF NOT EXISTS",
            (uuid4(), title, duration),
        )
        return result.one().applied

    def add_cinema(self, name: str, location: str, capacity: int) -> bool:
        result = self.session.execute(
            "INSERT INTO cinemas (cinema_id, name, location, capacity) VALUES (%s, %s, %s, %s) IF NOT EXISTS",
            (uuid4(), name, location, capacity),
        )
        return result.one().applied

    def add_user(self, name: str, email: str) -> bool:
        result = self.session.execute(
            "INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s) IF NOT EXISTS",
            (uuid4(), name, email),
        )
        return result.one().applied

    def cancel_reservation(self, reservation_id: UUID) -> bool:
        row = self.session.execute(
            "SELECT movie_id, cinema_id, seat_number FROM reservations_by_id WHERE reservation_id = %s",
            (reservation_id,),
        ).one()
        if row is None:
            return False
        result = self.session.execute(
            "DELETE FROM reservations WHERE movie_id = %s AND cinema_id = %s AND seat_number = %s IF EXISTS",
            (row.movie_id, row.cinema_id, row.seat_number),
        )
        if result.one().applied:
            self.session.execute(
                "DELETE FROM reservations_by_id WHERE reservation_id = %s",
                (reservation_id,),
            )
            return True
        return False

    def cancel_reservations(self, reservation_ids: list[UUID]) -> bool:
        success = True
        for reservation_id in reservation_ids:
            success = self.cancel_reservation(reservation_id) and success
        return success


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = CassandraDatabase(
        contact_points=["127.0.0.1", "127.0.0.2"],
        port=9042,
        keyspace="cinema",
    )
    app.state.db.connect()
    try:
        yield
    finally:
        app.state.db.disconnect()


def get_db(request: Request) -> Database:
    return request.app.state.db