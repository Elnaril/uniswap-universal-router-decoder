def test_get_default_deadline(codec):
    assert 79 < codec.get_default_deadline() - codec.get_default_deadline(100) < 81


def test_get_default_expiration(codec):
    assert -1 < codec.get_default_expiration() - codec.get_default_expiration(30*24*3600) < 1


def test_get_max_expiration(codec):
    assert codec.get_max_expiration() == 2**48 - 1
