from logminer import TemplateMiner, extract_parameters


def test_clusters_similar_lines():
    miner = TemplateMiner(similarity_threshold=0.5)
    logs = [
        "User alice logged in from 10.0.0.1",
        "User bob logged in from 10.0.0.2",
        "User carol logged in from 192.168.1.9",
        "Disk usage at 80 percent",
        "Disk usage at 95 percent",
    ]
    clusters = miner.mine(logs)
    # two distinct templates
    assert len(clusters) == 2
    templates = {c.template_str() for c in clusters}
    assert "User <*> logged in from <IP>" in templates
    assert "Disk usage at <NUM> percent" in templates


def test_counts_and_top_ordering():
    miner = TemplateMiner()
    for _ in range(3):
        miner.add_log("cache miss for key abc")
    miner.add_log("startup complete")
    top = miner.top()
    assert top[0].count == 3
    assert top[0].template_str().startswith("cache miss")


def test_different_length_lines_separate():
    miner = TemplateMiner()
    miner.add_log("a b c")
    miner.add_log("a b c d")
    assert len(miner.clusters) == 2


def test_wildcards_only_where_tokens_differ():
    miner = TemplateMiner(mask=False, similarity_threshold=0.4)
    miner.add_log("connect to host alpha port 22")
    c = miner.add_log("connect to host beta port 22")
    assert c.template_str() == "connect to host <*> port 22"
    assert c.count == 2


def test_examples_retained():
    miner = TemplateMiner()
    c = miner.add_log("job 1 failed")
    miner.add_log("job 2 failed")
    assert len(c.examples) >= 1


def test_match_is_read_only():
    miner = TemplateMiner()
    trained = miner.add_log("user alice logged in from 10.0.0.1")
    before = trained.count
    hit = miner.match("user bob logged in from 10.0.0.2")
    assert hit is trained
    assert trained.count == before          # match() must not mutate
    assert miner.match("totally unrelated message with many other words here") is None


def test_extract_parameters_at_mask_positions():
    template = ["user", "<NUM>", "from", "<IP>", "ok"]
    assert extract_parameters(template, "user 4821 from 10.0.0.5 ok") == ["4821", "10.0.0.5"]
    assert extract_parameters(template, "wrong length line") == []


def test_miner_extract_returns_cluster_and_params():
    miner = TemplateMiner()
    miner.add_log("user 4821 from 10.0.0.5 ok")
    miner.add_log("user 9999 from 10.0.0.9 ok")     # template: user <NUM> from <IP> ok
    result = miner.extract("user 1234 from 10.0.0.1 ok")
    assert result is not None
    cluster, params = result
    assert params == ["1234", "10.0.0.1"]
    before = cluster.count
    miner.extract("user 5 from 10.0.0.2 ok")        # extract() is read-only
    assert cluster.count == before
    assert miner.extract("nothing like the trained templates at all here") is None


def test_extract_includes_wildcard_values():
    miner = TemplateMiner(similarity_threshold=0.5)
    miner.add_log("connection from alice closed")
    miner.add_log("connection from bob closed")     # 'alice'/'bob' -> <*>
    _, params = miner.extract("connection from carol closed")
    assert params == ["carol"]


def test_round_trips_through_dict_and_json():
    miner = TemplateMiner(similarity_threshold=0.6, mask=True)
    miner.mine([
        "User alice logged in from 10.0.0.1",
        "User bob logged in from 10.0.0.2",
        "Disk usage at 80 percent",
    ])
    restored = TemplateMiner.from_json(miner.to_json())
    # config + clusters survive
    assert restored.threshold == 0.6 and restored.mask is True
    assert {c.template_str() for c in restored.top()} == {c.template_str() for c in miner.top()}
    assert {c.count for c in restored.top()} == {c.count for c in miner.top()}
    # a reloaded miner classifies a new line against its templates
    hit = restored.match("User dave logged in from 10.0.0.9")
    assert hit is not None and hit.template_str() == "User <*> logged in from <IP>"


def test_reloaded_miner_keeps_training_with_unique_ids():
    miner = TemplateMiner()
    miner.mine(["job 1 failed", "job 2 failed"])
    restored = TemplateMiner.from_dict(miner.to_dict())
    existing_ids = {c.id for c in restored.clusters}
    new = restored.add_log("a brand new unrelated startup message here now")  # new cluster
    assert new.id not in existing_ids                     # no id collision after reload
    assert restored.match("job 3 failed") is not None     # old templates still match
