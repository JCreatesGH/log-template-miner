from logminer import TemplateMiner


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
