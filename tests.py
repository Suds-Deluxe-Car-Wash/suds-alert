"""
Suds Alert — Tests
===================
Run: python -m pytest tests.py -v
"""

import pytest
from app import extract_location_from_channel, resolve_routing


class TestLocationExtraction:
    def test_valid_channel(self):
        assert extract_location_from_channel("kyle-management") == "kyle"

    def test_valid_channel_with_hash(self):
        assert extract_location_from_channel("#kyle-management") == "kyle"

    def test_hyphenated_location(self):
        assert extract_location_from_channel("hwy-6-management") == "hwy-6"

    def test_multi_word_location(self):
        assert extract_location_from_channel("san-marcos-ww-management") == "san-marcos-ww"

    def test_invalid_channel(self):
        assert extract_location_from_channel("general") is None

    def test_empty_channel(self):
        assert extract_location_from_channel("") is None

    def test_none_channel(self):
        assert extract_location_from_channel(None) is None


class TestRouting:
    def test_group_a_channel(self):
        result = resolve_routing("kyle-management")
        assert result is not None
        assert result["location"] == "kyle"
        assert result["group"] == "group_a"
        assert result["region"] == "Central Texas / Austin"
        names = [r["name"] for r in result["recipients"]]
        assert "tom" in names
        assert "rick" in names
        assert "shahan" in names

    def test_group_b_channel(self):
        result = resolve_routing("bissonnet-management")
        assert result is not None
        assert result["location"] == "bissonnet"
        assert result["group"] == "group_b"
        assert result["region"] == "Houston"
        names = [r["name"] for r in result["recipients"]]
        assert "andy" in names
        assert "roman" in names
        assert "shahan" in names

    def test_unknown_channel(self):
        result = resolve_routing("random-channel")
        assert result is None

    def test_shahan_always_notified(self):
        """Shahan should be in every routing group."""
        for channel in ["kyle-management", "bissonnet-management", "stafford-management", "georgetown-management"]:
            result = resolve_routing(channel)
            assert result is not None
            names = [r["name"] for r in result["recipients"]]
            assert "shahan" in names, f"Shahan not in routing for {channel}"

    def test_all_group_a_channels(self):
        group_a_channels = [
            "austin-management", "commerce-management", "culebra-management",
            "georgetown-management", "kyle-management", "round-rock-management",
            "san-marcos-ww-management", "sm35-management",
        ]
        for channel in group_a_channels:
            result = resolve_routing(channel)
            assert result is not None, f"No routing for {channel}"
            assert result["group"] == "group_a", f"{channel} not in group_a"

    def test_all_group_b_channels(self):
        group_b_channels = [
            "bissonnet-management", "hwy-6-management", "pasadena-management",
            "stafford-management", "sugar-land-management", "tomball-management",
        ]
        for channel in group_b_channels:
            result = resolve_routing(channel)
            assert result is not None, f"No routing for {channel}"
            assert result["group"] == "group_b", f"{channel} not in group_b"
