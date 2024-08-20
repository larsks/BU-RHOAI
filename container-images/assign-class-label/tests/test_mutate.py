import base64
import json

import mutate


REQUEST_HAS_USER = {
    "request": {
        "uid": "1234",
        "object": {
            "metadata": {
                "labels": {
                    "opendatahub.io/user": "testuser1",
                }
            }
        },
    }
}

REQUEST_NO_USER = {
    "request": {
        "uid": "1234",
        "object": {"metadata": {"labels": {}}},
    }
}


def test_invalid_path(client):
    """We expect a 404 response for invalid paths"""
    res = client.get("/test-path")
    assert res.status_code == 404


def test_invalid_method(client):
    """We expect a 405 ("method not allowed") response if we GET /mutate
    instead of POST"""
    res = client.get("/mutate")
    assert res.status_code == 405


def test_invalid_media_type(client):
    """We expect a 415 ("unsupported media type") response if our request does
    not have content-type "application/json"."""
    res = client.post("/mutate")
    assert res.status_code == 415


def test_health(client):
    """We expect a 200 response from the /healthz endpoint"""
    res = client.get("/healthz")
    assert res.status_code == 200


def test_provider_failure():
    class ErrorProvider:
        def group_members(self, group_name):
            raise Exception("test exception")

    app = mutate.create_app(
        PROVIDER=ErrorProvider,
        LABEL_NAME="testlabel",
        TESTING=True,
        GROUPS="group1,group2",
    )

    client = app.test_client()

    res = client.post(
        "/mutate", headers={"content-type": "application/json"}, json=REQUEST_HAS_USER
    )

    assert res.status_code == 500
    assert "failed to process groups" in res.text


def test_not_json(client):
    """We expect a 400 ("bad request") response if we submit something that is not
    actually JSON data"""
    res = client.post(
        "/mutate",
        headers={"content-type": "application/json"},
        data="Ceci n'est pas JSON",
    )
    assert res.status_code == 400


def test_empty_json(client):
    """We expect a 400 ("bad request") response if we submit a request that does not
    contain required fields."""
    res = client.post("/mutate", headers={"content-type": "application/json"}, json={})
    assert res.status_code == 400


def test_valid_patch_when_user_exists(client):
    """We expect a valid patch if our request is for a user that exists and is a member
    of a configured group."""

    expected_patch = [
        {
            "op": "add",
            "path": "/metadata/labels/testlabel",
            "value": "group1",
        }
    ]
    res = client.post(
        "/mutate", headers={"content-type": "application/json"}, json=REQUEST_HAS_USER
    )
    assert res.status_code == 200
    assert res.json["response"]["allowed"]
    have_patch = json.loads(base64.b64decode(res.json["response"]["patch"]))
    assert have_patch == expected_patch


def test_no_patch_when_no_user(client):
    """We expect no patch if assign_class_labels is unable to map a user to a group."""

    res = client.post(
        "/mutate", headers={"content-type": "application/json"}, json=REQUEST_NO_USER
    )
    assert res.status_code == 200
    assert res.json["response"]["allowed"]
    assert "patch" not in res.json["response"]
