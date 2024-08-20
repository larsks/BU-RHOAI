import pytest

import mutate


GROUPS = {
    "group1": ["testuser1"],
    "group2": ["testuser2"],
}


class FakeProvider:
    def group_members(self, group_name):
        return GROUPS[group_name]


@pytest.fixture()
def fake_provider():
    return FakeProvider()


@pytest.fixture()
def app():
    app = mutate.create_app(
        PROVIDER=FakeProvider,
        LABEL_NAME="testlabel",
        TESTING=True,
        GROUPS=",".join(GROUPS.keys()),
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def groups():
    return GROUPS.keys()
