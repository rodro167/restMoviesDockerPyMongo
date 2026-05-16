"""
Smoke test: Hits every endpoint of the REST Movies API and reports results.

Prerequisites:
  - MongoDB running with collections set up (run setup_db.py first)
  - Flask app running (python mongoRestMovies.py)
  - pip install requests

Usage:
  python smoke_test.py                              # local
  BASE_URL=http://34.60.109.187:4000 python smoke_test.py  # remote
"""
import os
import sys
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:4000").rstrip("/")
PASS = 0
FAIL = 0
TOKEN = None
MOVIE_ID = None
USER_ID = None


def log(status, method, path, code, detail=""):
    icon = "PASS" if status else "FAIL"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}{icon}{reset}  {method:7s} {path:45s} -> {code}  {detail}")


def test(method, path, expected_codes, json=None, auth=True):
    """Run a single API call and check the status code."""
    global PASS, FAIL
    headers = {}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    url = f"{BASE_URL}{path}"
    try:
        resp = requests.request(method, url, json=json, headers=headers, timeout=10)
    except requests.ConnectionError:
        log(False, method, path, "CONN_ERR", "Is the server running?")
        FAIL += 1
        return None

    if not isinstance(expected_codes, (list, tuple)):
        expected_codes = [expected_codes]

    ok = resp.status_code in expected_codes
    if ok:
        PASS += 1
    else:
        FAIL += 1
    log(ok, method, path, resp.status_code,
        f"(expected {expected_codes})" if not ok else "")
    return resp


# =========================================================================
print("\n========== REST Movies API — Smoke Test ==========\n")

# ---- 1. Health check ----
print("[1] Server reachable")
r = test("POST", "/login", [401], json={"username": "", "password": ""}, auth=False)
if r is None:
    print("\n  Cannot reach the server. Make sure it's running on port 4000.")
    sys.exit(1)

# ---- 2. Register + Login ----
print("\n[2] Auth: register & login")
test_user = {"username": "smoke_test_user", "password": "Test1234!"}

r = test("POST", "/users/register", [201, 409], json=test_user, auth=False)
if r and r.status_code == 201:
    USER_ID = r.json().get("insertedId")

r = test("POST", "/login", [200], json=test_user, auth=False)
if r and r.status_code == 200:
    TOKEN = r.json().get("access_token")
    print(f"         Token acquired: {TOKEN[:30]}...")
else:
    print("\n  Login failed — cannot continue without a token.")
    sys.exit(1)

# Bad credentials
test("POST", "/login", [401], json={"username": "nobody", "password": "wrong"}, auth=False)

# ---- 3. Movies — READ ----
print("\n[3] Movies — READ endpoints")
test("GET", "/movies/", [200])
test("GET", "/movies/title/Shawshank", [200])
test("GET", "/movies/actor/Morgan Freeman", [200])
test("POST", "/movies/actors", [200], json={"actors": ["Tim Robbins", "Morgan Freeman"]})
test("GET", "/movies/country/USA", [200])
test("POST", "/movies/countries", [200], json={"countries": ["USA", "UK"]})
test("GET", "/movies/genre/Drama", [200])
test("POST", "/movies/genres", [200], json={"genres": ["Drama", "Comedy"]})
test("GET", "/movies/director/Frank Darabont", [200])
test("POST", "/movies/directors", [200], json={"directors": ["Frank Darabont"]})
test("GET", "/movies/year/1994", [200])
test("GET", "/movies/year/before/2000", [200])
test("GET", "/movies/year/after/1990", [200])
test("GET", "/movies/runtime/142", [200])
test("GET", "/movies/runtime/lessthan/200", [200])
test("GET", "/movies/runtime/morethan/100", [200])

# ---- 4. Movies — CREATE, UPDATE, DELETE ----
print("\n[4] Movies — WRITE endpoints")
new_movie = {
    "title": "Smoke Test Movie",
    "year": 2026,
    "runtime": 90,
    "genres": ["Test"],
    "directors": ["Test Director"],
    "cast": ["Actor A", "Actor B"],
    "countries": ["Testland"],
}
r = test("POST", "/movies/", [201], json=new_movie)
if r and r.status_code == 201:
    MOVIE_ID = r.json().get("insertedId")
    print(f"         Created movie: {MOVIE_ID}")

if MOVIE_ID:
    test("PUT", f"/movies/{MOVIE_ID}", [200], json={"year": 2027})
    test("GET", f"/movies/year/2027", [200])

# ---- 5. Ratings & Comments (new features) ----
print("\n[5] Ratings & Comments")
if MOVIE_ID:
    # Rate
    test("POST", "/movies/rate", [201], json={"movieId": MOVIE_ID, "stars": 8})
    # Update rating (same user → upsert)
    test("POST", "/movies/rate", [200], json={"movieId": MOVIE_ID, "stars": 9})
    # Invalid stars
    test("POST", "/movies/rate", [400], json={"movieId": MOVIE_ID, "stars": 0})
    test("POST", "/movies/rate", [400], json={"movieId": MOVIE_ID, "stars": 11})
    test("POST", "/movies/rate", [400], json={"movieId": MOVIE_ID, "stars": "abc"})
    # Missing movieId
    test("POST", "/movies/rate", [400], json={"stars": 5})

    # Comment
    test("POST", "/movies/comment", [201], json={"movieId": MOVIE_ID, "comment": "Great test movie!"})
    test("POST", "/movies/comment", [201], json={"movieId": MOVIE_ID, "comment": "Second comment"})
    # Empty comment
    test("POST", "/movies/comment", [400], json={"movieId": MOVIE_ID, "comment": ""})
    test("POST", "/movies/comment", [400], json={"movieId": MOVIE_ID, "comment": "   "})

    # Get stars
    r = test("GET", f"/movies/{MOVIE_ID}/stars", [200])
    if r and r.status_code == 200:
        data = r.json()
        print(f"         Avg rating: {data.get('averageRating')} "
              f"({data.get('totalRatings')} ratings)")

    # Get comments
    r = test("GET", f"/movies/{MOVIE_ID}/comments", [200])
    if r and r.status_code == 200:
        data = r.json()
        print(f"         Total comments: {data.get('totalComments')}")

    # Non-existent movie
    test("POST", "/movies/rate", [404], json={"movieId": "000000000000000000000000", "stars": 5})
    test("GET", "/movies/000000000000000000000000/stars", [404])
    test("GET", "/movies/000000000000000000000000/comments", [404])
    # Invalid ObjectId
    test("GET", "/movies/not-a-valid-id/stars", [400])

# ---- 6. Auth-protected access without token ----
print("\n[6] Auth guards (no token)")
test("GET", "/movies/", [401, 422], auth=False)
test("POST", "/movies/rate", [401, 422], auth=False)

# ---- 7. Users — management ----
print("\n[7] User management")
if USER_ID:
    test("PUT", f"/users/{USER_ID}/password", [200], json={"password": "NewPass5678!"})
    # Re-login with new password
    test("POST", "/login", [200], json={"username": "smoke_test_user", "password": "NewPass5678!"}, auth=False)
    # Old password should fail
    test("POST", "/login", [401], json=test_user, auth=False)

# ---- 8. Cleanup ----
print("\n[8] Cleanup")
if MOVIE_ID:
    # Clean up ratings & comments for this movie
    test("DELETE", f"/movies/{MOVIE_ID}", [200])

if USER_ID:
    test("DELETE", f"/users/{USER_ID}", [200])

# ---- Summary ----
total = PASS + FAIL
print(f"\n{'='*50}")
print(f"  RESULTS:  {PASS}/{total} passed", end="")
if FAIL:
    print(f"  |  \033[91m{FAIL} FAILED\033[0m")
else:
    print(f"  |  \033[92mALL PASSED\033[0m")
print(f"{'='*50}\n")

sys.exit(0 if FAIL == 0 else 1)
