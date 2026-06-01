import httpx

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 5


def _get(path: str) -> list | dict:
    try:
        r = httpx.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to backend at {BASE_URL}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Backend error {e.response.status_code}: {e.response.text}")


def _post(path: str, data: dict) -> dict:
    try:
        r = httpx.post(f"{BASE_URL}{path}", json=data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to backend at {BASE_URL}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Backend error {e.response.status_code}: {e.response.text}")


def get_movies() -> list:
    return _get("/movies")


def get_cinemas() -> list:
    return _get("/cinemas")


def get_users() -> list:
    return _get("/users")


def get_reservations() -> list:
    return _get("/reservations")


def create_user(name: str, email: str) -> dict:
    return _post("/users", {"name": name, "email": email})


def make_reservations_bulk(user_id: str, movie_id: str, cinema_id: str, seat_numbers: list[int]) -> dict:
    return _post("/reservations/bulk", {
        "user_id": user_id,
        "movie_id": movie_id,
        "cinema_id": cinema_id,
        "seat_numbers": seat_numbers,
    })


def make_reservation(user_id: str, movie_id: str, cinema_id: str, seat_number: int) -> dict:
    return _post("/reservations", {
        "user_id": user_id,
        "movie_id": movie_id,
        "cinema_id": cinema_id,
        "seat_number": seat_number,
    })


def update_reservation(reservation_id: str, new_seat_number: int) -> dict:
    try:
        r = httpx.put(
            f"{BASE_URL}/reservations/{reservation_id}",
            json={"new_seat_number": new_seat_number},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to backend at {BASE_URL}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Backend error {e.response.status_code}: {e.response.text}")


def cancel_reservation(reservation_id: str) -> dict:
    try:
        r = httpx.delete(f"{BASE_URL}/reservations/{reservation_id}", timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        raise ConnectionError(f"Cannot connect to backend at {BASE_URL}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Backend error {e.response.status_code}: {e.response.text}")
