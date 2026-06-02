import unittest
import threading
import random
import time
import httpx

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

    def _reserve_bulk(self, user_id, seat_numbers):
        r = _post("/reservations/bulk", {
            "user_id": str(user_id),
            "movie_id": str(self.movie_id),
            "cinema_id": str(self.cinema_id),
            "seat_numbers": seat_numbers,
        })
        return [item["seat_number"] for item in r.json()["results"] if item["success"]]

    # Test: backend alive 
    def test_test1_backend_alive(self):
        r = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)

    #  test: single reservation succeeds
    def test_test2_single_reservation(self):
        self._clear_reservations()

        ok = self._reserve(self.user_a_id, seat_number=1)
        self.assertTrue(ok, "Expected reservation to succeed but got null reservation_id")

    # Test: double booking is rejected
    def test_test3_no_double_booking(self):
        self._clear_reservations()

        first = self._reserve(self.user_a_id, seat_number=1)
        second = self._reserve(self.user_b_id, seat_number=1)

        self.assertTrue(first, "First reservation should succeed")
        self.assertFalse(second, "Duplicate reservation should be rejected")


    # StressTest 1: ohe client makes the same request very quickly
    def test_stress_1_rapid_same_seat(self):
        self._clear_reservations()

        results = []

        def try_reserve():
            results.append(self._reserve(self.user_a_id, seat_number=1))

        threads = [threading.Thread(target=try_reserve) for _ in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = sum(results)
        print(f"\n  {successes} / {len(threads)} attempts succeeded")
        self.assertEqual(successes, 1, "Exactly one reservation should succeed for a single seat")


    # Stress Test 2: multiple clients make random reservations concurrently
    def test_stress_2_random_concurrent_clients(self):
        self._clear_reservations()
        errors = []
        latencies = []

        def random_client(user_id):
            for _ in range(100):
                seat = random.randint(1, self.capacity)
                start = time.time()
                try:
                    r = _post("/reservations", {
                        "user_id": str(user_id),
                        "movie_id": str(self.movie_id),
                        "cinema_id": str(self.cinema_id),
                        "seat_number": seat,
                    })
                    if r.status_code not in (200, 409):
                        errors.append(f"Unexpected status {r.status_code}")
                except Exception as e:
                    errors.append(str(e))
                latencies.append(time.time() - start)

        threads = [
            threading.Thread(target=random_client, args=(uid,))
            for uid in [self.user_a_id, self.user_b_id,]
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        avg_ms = (sum(latencies) / len(latencies)) * 1000
        max_ms = max(latencies) * 1000
        print(f"\n  {len(latencies)} requests — avg {avg_ms:.0f}ms, max {max_ms:.0f}ms")

        self.assertFalse(errors, f"Unexpected errors: {errors}")
        self.assertLess(avg_ms, 500, "Average latency too high (>500ms)")

        all_res = _get("/reservations")
        seats = [r["seat_number"] for r in all_res
                 if str(r["movie_id"]) == str(self.movie_id)
                 and str(r["cinema_id"]) == str(self.cinema_id)]
        self.assertEqual(len(seats), len(set(seats)), "Double bookings detected")


    # stresstest 3:  Immediate occupancy of all seats/reservations on 2 clients. (It should look as 2 parties/persons try to make as many as possible reservation at a same time and result should be that both are able to make have reservations, not 1 party/person takes all reservations.)
    def test_3_two_users_race_for_all_seats(self):
        self._clear_reservations()

        results_a, results_b = [], []
        all_seats = list(range(1, self.capacity + 1))

        t_a = threading.Thread(target=lambda: results_a.extend(self._reserve_bulk(self.user_a_id, all_seats)))
        t_b = threading.Thread(target=lambda: results_b.extend(self._reserve_bulk(self.user_b_id, all_seats)))

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



    # Stress Test 4: bots constantly reserve and cancel a small overlapping pool of seats
    def test_stress_4_cancel_and_rebook(self):
        self._clear_reservations()
        errors = []
        ITERATIONS = 100
        SEAT_POOL = list(range(1, 6))  # 4 bots fight over 5 seats

        def bot(user_id):
            for _ in range(ITERATIONS):
                seat = random.choice(SEAT_POOL)
                r = _post("/reservations", {
                    "user_id": str(user_id),
                    "movie_id": str(self.movie_id),
                    "cinema_id": str(self.cinema_id),
                    "seat_number": seat,
                })
                if r.status_code not in (200, 409):
                    errors.append(f"Unexpected status {r.status_code}")
                    continue
                res_id = r.json().get("reservation_id")
                if res_id:
                    httpx.delete(f"{BASE_URL}/reservations/{res_id}", timeout=TIMEOUT)

        users = [self.user_a_id, self.user_b_id]
        threads = [threading.Thread(target=bot, args=(u,)) for u in users]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertFalse(errors, f"Unexpected errors: {errors}")

        all_res = _get("/reservations")
        seats = [r["seat_number"] for r in all_res
                 if str(r["movie_id"]) == str(self.movie_id)
                 and str(r["cinema_id"]) == str(self.cinema_id)]
        self.assertEqual(len(seats), len(set(seats)), "Double bookings found after cancel/rebook stress")

    # Stress Test 5: Make large group cancellation of many reservations.
    def test_stress_5_bulk_cancel(self):
        self._clear_reservations()

        booked = self._reserve_bulk(self.user_a_id, list(range(1, self.capacity + 1)))
        self.assertEqual(len(booked), self.capacity, "Could not fill all seats before cancel test")

        all_res = _get("/reservations")
        ids = [r["reservation_id"] for r in all_res
               if str(r["movie_id"]) == str(self.movie_id)
               and str(r["cinema_id"]) == str(self.cinema_id)]

        start = time.time()
        r = _delete("/reservations", ids)
        elapsed = time.time() - start

        print(f"\n  Cancelled {len(ids)} reservations in {elapsed:.2f}s")
        self.assertTrue(r.json().get("ok"), "Bulk cancel failed")

        all_res = _get("/reservations")
        remaining = [r for r in all_res
                     if str(r["movie_id"]) == str(self.movie_id)
                     and str(r["cinema_id"]) == str(self.cinema_id)]
        self.assertEqual(len(remaining), 0, "Some reservations were not cancelled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
