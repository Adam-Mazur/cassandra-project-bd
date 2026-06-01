import unittest
import threading
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10


def _post(path, data):
    return httpx.post(f"{BASE_URL}{path}", json=data, timeout=TIMEOUT)


def _get(path):
    return httpx.get(f"{BASE_URL}{path}", timeout=TIMEOUT).json()

def _delete(path, data):
    return httpx.request("DELETE", f"{BASE_URL}{path}", json=data, timeout=TIMEOUT)


class ReservationStressTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        movies = _get("/movies")
        cinemas = _get("/cinemas")
        users = _get("/users")

        # create stress_test_cinema_1 if not exists and clear all reservations for it
        if not cinemas or not any(c["name"] == "stress_test_cinema_1" for c in cinemas):
            r = httpx.post(f"{BASE_URL}/cinemas", json={"name": "stress_test_cinema_1", "location": "test_location", "capacity" : 100}, timeout=TIMEOUT)
            r.raise_for_status()
            print("Created cinema 'stress_test_cinema_1' for stress testing")
            cinemas = _get("/cinemas")

        if not movies or not any(m["title"] == f"stress_test_movie_1" for m in movies):
            r = httpx.post(f"{BASE_URL}/movies", json={"title": f"stress_test_movie_1", "duration" : 150 }, timeout=TIMEOUT)
            r.raise_for_status()
            print(f"Created movie 'stress_test_movie_1' for stress testing")
            movies = _get("/movies")

        for user_num in range(1, 3):
            if not users or not any(u["name"] == f"stress_test_user_{user_num}" for u in users):
                r = httpx.post(f"{BASE_URL}/users", json={"name": f"stress_test_user_{user_num}", "email" : f"stress_test_movie_{user_num}"}, timeout=TIMEOUT)
                r.raise_for_status()
                print(f"Created user 'stress_test_user_{user_num}' for stress testing")
                users = _get("/users")

        cls.movie_id = next(m["movie_id"] for m in movies if m["title"] == f"stress_test_movie_1")
        cls.cinema_id = next(c["cinema_id"] for c in cinemas if c["name"] == f"stress_test_cinema_1")
        cls.capacity = next(c["capacity"] for c in cinemas if c["name"] == "stress_test_cinema_1")
        cls.user_a_id = next(u["user_id"] for u in users if u["name"] == f"stress_test_user_1")
        cls.user_b_id = next(u["user_id"] for u in users if u["name"] == f"stress_test_user_2")

    def _clear_reservations(self):
        """Delete all reservations for the test movie+cinema."""
        all_res = _get("/reservations")
        target_ids = [
            r["reservation_id"]
            for r in all_res
            if str(r["movie_id"]) == self.movie_id
            and str(r["cinema_id"]) == self.cinema_id
        ]
        if target_ids:
            _delete("/reservations", target_ids)

    def _reserve(self, user_id, seat_number):
        r = _post("/reservations", {
            "user_id": user_id,
            "movie_id": self.movie_id,
            "cinema_id": self.cinema_id,
            "seat_number": seat_number,
        })
        return r.status_code == 200 and r.json().get("reservation_id") is not None

    # Test 1: backend alive 
    def test_1_backend_alive(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)

    #  test 2: single reservation succeeds
    def test_2_single_reservation(self):
        self._clear_reservations()

        ok = self._reserve(self.user_a_id, seat_number=1)
        self.assertTrue(ok, "Expected reservation to succeed but got null reservation_id")

    # Test 3: double booking is rejected
    def test_3_no_double_booking(self):
        self._clear_reservations()

        first = self._reserve(self.user_a_id, seat_number=1)
        second = self._reserve(self.user_b_id, seat_number=1)

        self.assertTrue(first, "First reservation should succeed")
        self.assertFalse(second, "Duplicate reservation should be rejected")

    # Test 4: two users race for every seat — no seat double-booked
    def test_4_two_users_race_for_all_seatsss(self):
        self._clear_reservations()

        results_a, results_b = [], []

        def book_all(user_id, results):
            for seat in range(1, self.capacity + 1):
                if seat == 100:
                    print(f"User {user_id} trying to book seat {seat}...")
                if self._reserve(user_id, seat):
                    results.append(seat)

        t_a = threading.Thread(target=book_all, args=(self.user_a_id, results_a))
        t_b = threading.Thread(target=book_all, args=(self.user_b_id, results_b))

        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        total = len(results_a) + len(results_b)
        print(f"\n  User A: {len(results_a):3d} seats  {sorted(results_a)}")
        print(f"  User B: {len(results_b):3d} seats  {sorted(results_b)}")
        print(f"  Total percent of seats booked: {total} / {self.capacity}")

        overlap = set(results_a) & set(results_b)
        self.assertFalse(overlap, f"Double-booked seats: {overlap}")
        self.assertEqual(total, self.capacity, "Some seats went unclaimed")
        self.assertGreater(len(results_a), 0, "User A got zero seats")
        self.assertGreater(len(results_b), 0, "User B got zero seats")


if __name__ == "__main__":
    unittest.main(verbosity=2)
