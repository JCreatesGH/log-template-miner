from logminer import mask_variables


def test_masks_common_variables():
    assert mask_variables("user 4821 from 10.0.0.5 ok") == "user <NUM> from <IP> ok"
    assert "<UUID>" in mask_variables("id 550e8400-e29b-41d4-a716-446655440000")
    assert "<TS>" in mask_variables("2026-06-04T10:00:00Z started")
    assert mask_variables("GET /api/v1/users 200").startswith("GET <PATH>")


def test_masks_floats_as_single_num():
    # Floats used to split into "<NUM>.<NUM>"; now they collapse to one <NUM>.
    assert mask_variables("request took 3.14 ms") == "request took <NUM> ms"
    assert mask_variables("cpu at 99.9 percent") == "cpu at <NUM> percent"


def test_masks_urls_and_hash_ids():
    assert mask_variables("GET https://api.example.com/v1/users?id=7 200").split()[1] == "<URL>"
    assert mask_variables("commit a1b2c3d4 merged") == "commit <ID> merged"
    # a plain number stays <NUM>, and an all-letter hex word is left alone
    assert mask_variables("count 12345678 done") == "count <NUM> done"
    assert mask_variables("the cafe opened") == "the cafe opened"
