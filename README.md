# racedata

Provider-agnostic race timing data library. Backends: RTRT.me and Sportstats (`sportstats.one`).

## Install

```bash
pip install -e ".[dev]"
pytest
```

## Usage

```python
from racedata.providers.factory import provider_for_race
from racedata.resolve import resolve_share_url

resolution = resolve_share_url("https://sportstats.one/event/.../leaderboard/146818")
provider = provider_for_race(
    resolution.race,
    rtrt_credentials=resolution.credentials,
    sportstats_cols=resolution.checkpoint_cols,
)
```

RTRT ulinks and Sportstats leaderboard URLs are detected automatically. Optional env: `SPORTSTATS_API_KEY` for single-athlete lookups.

## License

MIT License. See [LICENSE](LICENSE).
