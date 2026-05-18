# racedata

Provider-agnostic race timing data library. RTRT.me is the first backend.

## Install

```bash
pip install -e ".[dev]"
pytest
```

## Usage

```python
from racedata.providers.rtrt.client import RtrtClient, SessionCredentials
from racedata.providers.rtrt.service import RtrtProvider
from racedata.providers.rtrt.ulink import credentials_for_ulink, resolve_ulink

client = RtrtClient(SessionCredentials.new_session("appid"))
resolution = resolve_ulink(client, "https://rtrt.me/ulink/...")
provider = RtrtProvider(client)
```
