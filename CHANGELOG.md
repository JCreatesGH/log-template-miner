# Changelog

All notable changes are documented here, following
[Keep a Changelog](https://keepachangelog.com/) and [SemVer](https://semver.org/).

## [0.3.0]

### Added
- **Model persistence** — `TemplateMiner.to_dict()` / `to_json()` snapshot a trained miner, and
  `from_dict()` / `from_json()` rebuild it ready to `match`/`extract`/`add_log`. Train offline,
  serialize, and reload to classify a live stream without retraining. Reload preserves cluster
  ids and bumps the id counter so further training never collides.
- CLI `--save PATH` writes the trained miner as JSON.

## [0.2.0]

### Added
- **Parameter extraction**: `extract_parameters(template, line)` and
  `TemplateMiner.extract(line)` recover the actual variable values behind a
  matched line, turning a raw line into a `(template, params)` pair.
- Masking gains `<URL>` (whole http(s) URLs) and `<ID>` (hash/SHA-style hex
  tokens), while plain numbers stay `<NUM>`.

## [0.1.0]

### Added
- A dependency-free, Drain-style `TemplateMiner`: variable masking, online
  positional clustering, read-only `match()`, frequency-ordered `top()`, and a
  `logminer` CLI.
