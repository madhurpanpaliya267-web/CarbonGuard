from app.services.research_summary_service import ResearchSummaryService


class TestParseControls:
    def test_empty_payload_returns_empty(self):
        assert ResearchSummaryService._parse_controls(None) == []
        assert ResearchSummaryService._parse_controls("") == []

    def test_invalid_json_returns_empty(self):
        assert ResearchSummaryService._parse_controls("{broken") == []
        assert ResearchSummaryService._parse_controls("[not-json") == []

    def test_non_list_returns_empty(self):
        assert ResearchSummaryService._parse_controls('"firewall"') == []
        assert ResearchSummaryService._parse_controls('{"a": 1}') == []

    def test_valid_list_filters_blank_entries(self):
        assert ResearchSummaryService._parse_controls(
            '["firewall", " ", "ids"]'
        ) == ["firewall", "ids"]
