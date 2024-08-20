import mutate

from models import Pod, Metadata


def test_acl_user_in_group(fake_provider, groups):
    pod = Pod(metadata=Metadata(labels={"opendatahub.io/user": "testuser1"}))
    res = mutate.assign_class_label(fake_provider, pod, groups)
    assert res == "group1"


def test_acl_user_not_in_group(fake_provider, groups):
    pod = Pod(metadata=Metadata(labels={"opendatahub.io/user": "testuser-no-group"}))
    res = mutate.assign_class_label(fake_provider, pod, groups)
    assert res is None


def test_acl_no_user_label(fake_provider, groups):
    pod = Pod(metadata=Metadata())
    res = mutate.assign_class_label(fake_provider, pod, groups)
    assert res is None
