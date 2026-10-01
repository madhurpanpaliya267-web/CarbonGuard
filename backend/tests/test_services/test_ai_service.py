import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.ai_service import AIService
from app.repositories.ai_repo import AIRecommendationRepository


class TestAIService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = AIService(self.db)

    def test_init_creates_repo(self):
        assert isinstance(self.service.rec_repo, AIRecommendationRepository)

    def test_get_recommendations_no_filters(self):
        mock_recs = [
            MagicMock(recommendation_type="security", priority="high", is_read=False),
            MagicMock(recommendation_type="carbon", priority="medium", is_read=True),
        ]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations()
        assert len(result) == 2

    def test_get_recommendations_filter_by_type(self):
        mock_recs = [
            MagicMock(recommendation_type="security", priority="high", is_read=False),
            MagicMock(recommendation_type="carbon", priority="medium", is_read=True),
        ]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations(recommendation_type="security")
        assert len(result) == 1
        assert result[0].recommendation_type == "security"

    def test_get_recommendations_filter_by_priority(self):
        mock_recs = [
            MagicMock(recommendation_type="security", priority="high", is_read=False),
            MagicMock(recommendation_type="carbon", priority="high", is_read=True),
            MagicMock(recommendation_type="energy", priority="low", is_read=False),
        ]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations(priority="high")
        assert len(result) == 2

    def test_get_recommendations_filter_unread_only(self):
        mock_recs = [
            MagicMock(recommendation_type="security", priority="high", is_read=False),
            MagicMock(recommendation_type="carbon", priority="medium", is_read=True),
            MagicMock(recommendation_type="energy", priority="low", is_read=False),
        ]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations(unread_only=True)
        assert len(result) == 2
        assert all(not r.is_read for r in result)

    def test_get_recommendations_combined_filters(self):
        mock_recs = [
            MagicMock(recommendation_type="security", priority="high", is_read=False),
            MagicMock(recommendation_type="security", priority="medium", is_read=True),
            MagicMock(recommendation_type="carbon", priority="high", is_read=False),
        ]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations(
            recommendation_type="security", priority="high", unread_only=True
        )
        assert len(result) == 1

    def test_get_recommendations_empty(self):
        self.service.rec_repo.get_all = MagicMock(return_value=[])
        result = self.service.get_recommendations()
        assert len(result) == 0

    def test_generate_creates_recommendations(self):
        self.service.rec_repo.create = MagicMock(side_effect=lambda data: MagicMock(id=1, **data))
        result = self.service.generate()
        assert isinstance(result, list)
        assert len(result) > 0
        assert self.service.rec_repo.create.call_count == len(result)

    def test_generate_calls_engine_with_random_values(self):
        self.service.rec_repo.create = MagicMock(side_effect=lambda data: MagicMock(id=1, **data))
        with patch("app.services.ai_service.generate_recommendations") as mock_gen:
            mock_gen.return_value = [
                {
                    "recommendation_type": "general",
                    "recommendation": "Test rec",
                    "priority": "low",
                    "reason": "Test reason",
                    "confidence": 0.9,
                    "factors": [],
                }
            ]
            self.service.generate()
            mock_gen.assert_called_once()
            call_kwargs = mock_gen.call_args
            assert "active_threats" in call_kwargs.kwargs or call_kwargs.args

    def test_mark_read(self):
        self.service.rec_repo.mark_read = MagicMock(return_value=MagicMock(id=1, is_read=True))
        result = self.service.mark_read(1)
        self.service.rec_repo.mark_read.assert_called_once_with(1)
        assert result.is_read is True

    def test_dismiss(self):
        self.service.rec_repo.dismiss = MagicMock(return_value=MagicMock(id=1, is_dismissed=True))
        result = self.service.dismiss(1)
        self.service.rec_repo.dismiss.assert_called_once_with(1)
        assert result.is_dismissed is True

    def test_generate_stores_json_factors(self):
        self.service.rec_repo.create = MagicMock(side_effect=lambda data: MagicMock(id=1, **data))
        with patch("app.services.ai_service.generate_recommendations") as mock_gen:
            mock_gen.return_value = [
                {
                    "recommendation_type": "security",
                    "recommendation": "Test",
                    "priority": "high",
                    "reason": "Reason",
                    "confidence": 0.85,
                    "factors": [{"factor": "test", "value": 1, "weight": 0.5}],
                }
            ]
            self.service.generate()
            call_data = self.service.rec_repo.create.call_args[0][0]
            assert "factors_json" in call_data
            import json
            factors = json.loads(call_data["factors_json"])
            assert len(factors) == 1
