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
    ) -> UUID:
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
    def add_cinema(name: str, location: str) -> bool:
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
    ) -> UUID:
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
        for reservation in self.reservations:
            if reservation["reservation_id"] == reservation_id:
                reservation["seat_number"] = new_seat_number
                return True
        return False

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

    def add_cinema(self, name: str, location: str) -> bool:
        cinema_id = uuid4()
        cinema = {"cinema_id": cinema_id, "name": name, "location": location}
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
