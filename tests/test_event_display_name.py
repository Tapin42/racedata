import json
from pathlib import Path

from racedata.providers.rtrt.points import event_display_name_from_conf

FIXTURES = Path(__file__).parent / "fixtures"


def test_event_display_name_from_multisport_conf():
    conf = json.loads((FIXTURES / "multisport_conf.json").read_text())
    assert (
        event_display_name_from_conf(conf)
        == "USA Triathlon Multisport National Championships Festival"
    )


def test_event_display_name_from_venice_conf():
    conf = json.loads((FIXTURES / "venice703_conf.json").read_text())
    assert event_display_name_from_conf(conf) == "IRONMAN 70.3 Venice-Jesolo"


def test_event_display_name_from_usat_conf():
    conf = json.loads((FIXTURES / "usat_olympic_conf.json").read_text())
    assert event_display_name_from_conf(conf) == "USA Triathlon Nationals"
