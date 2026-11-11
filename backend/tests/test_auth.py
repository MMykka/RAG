BOB = {"username": "bob", "email": "bob@test.local", "password": "secret123"}


# testing register
def test_register(client):
    r = client.post("/api/auth/register", json=BOB)
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "bob"
    assert body["email"] == "bob@test.local"
    assert "password_hash" not in body


def test_duplicate_username(client):
    # register a user
    r = client.post("/api/auth/register", json=BOB)
    assert r.status_code == 201

    # same username, different email
    r = client.post("/api/auth/register", json={**BOB, "email": "other@test.local"})
    assert r.status_code == 409


def test_duplicate_email(client):
    # register a user
    r = client.post("/api/auth/register", json=BOB)
    assert r.status_code == 201

    # different username, same email
    r = client.post("/api/auth/register", json={**BOB, "username": "bob2"})
    assert r.status_code == 409


def test_wrong_password(client):
    # register a user
    r = client.post("/api/auth/register", json=BOB)
    assert r.status_code == 201

    # try to login with the wrong password
    r = client.post("/api/auth/login", json={"username": "bob", "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid username or password"
    assert r.cookies.get("access_token") is None


def test_unknown_username(client):
    # same message as a wrong password, so nobody can find out which usernames exist
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "secret123"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid username or password"


def test_login_sets_the_access_token_cookie(client):
    # register a user
    r = client.post("/api/auth/register", json=BOB)
    assert r.status_code == 201

    # login and check if the access token cookie is set
    r = client.post("/api/auth/login", json={"username": "bob", "password": "secret123"})
    assert r.status_code == 200
    assert r.cookies.get("access_token") is not None


def test_me_endpoint(make_client):
    # make_client registers and logs in "bob", so the client already holds the cookie
    bob = make_client("bob")

    r = bob.get("/api/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "bob"
    assert body["email"] == "bob@test.local"
    assert "password_hash" not in body


def test_me_without_login(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_logout(make_client):
    bob = make_client("bob")

    # logout
    r = bob.post("/api/auth/logout")
    assert r.status_code == 204

    # the cookie is gone, so /me no longer knows who this is
    r = bob.get("/api/auth/me")
    assert r.status_code == 401
