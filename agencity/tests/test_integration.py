"""
Integration Tests for ProofHire Search & Intelligence System

Tests all systems working together:
- V1-V5 Search Engines
- Intelligence Pillars
- Kimi Reasoning (fallback mode)
- RL Reward Model
- Master Orchestrator

Run:
    python -m pytest tests/test_integration.py -v
    python tests/test_integration.py  # Direct run
"""

import asyncio
import pytest
from datetime import datetime

# Test company ID (Confido - known to have network data)
TEST_COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"


class TestV1SearchEngine:
    """Test V1 Gateway Search."""

    def test_import(self):
        """Test that V1 imports correctly."""
        from app.search.engine import SearchEngine
        from app.search.models import SearchTarget
        assert SearchEngine is not None
        assert SearchTarget is not None


class TestV2SearchEngine:
    """Test V2 Tiered Search."""

    def test_import(self):
        """Test that V2 imports correctly."""
        from app.search.engine_v2 import SearchEngineV2, TieredCandidate, SearchResultsV2
        assert SearchEngineV2 is not None

    def test_components(self):
        """Test V2 components."""
        from app.search.network_search import NetworkSearch
        from app.search.readiness import ReadinessScorer
        from app.search.recruiters import RecruiterFinder
        from app.search.warm_path import WarmPathCalculator

        assert NetworkSearch is not None
        assert ReadinessScorer is not None
        assert RecruiterFinder is not None
        assert WarmPathCalculator is not None


class TestV3Intelligence:
    """Test V3 Intelligence System."""

    def test_timing_imports(self):
        """Test timing intelligence imports."""
        from app.intelligence.timing.readiness_scorer import ReadinessScorer
        from app.intelligence.timing.tenure_tracker import TenureTracker
        from app.intelligence.timing.vesting_predictor import VestingPredictor

        assert ReadinessScorer is not None
        assert TenureTracker is not None
        assert VestingPredictor is not None

    def test_activation_imports(self):
        """Test activation intelligence imports."""
        from app.intelligence.activation.reverse_reference import ReverseReferenceGenerator
        from app.intelligence.activation.message_generator import ActivationMessageGenerator

        assert ReverseReferenceGenerator is not None
        assert ActivationMessageGenerator is not None

    def test_expansion_imports(self):
        """Test expansion intelligence imports."""
        from app.intelligence.expansion.colleague_expander import ColleagueExpander
        from app.intelligence.expansion.warm_path_finder import WarmPathFinder

        assert ColleagueExpander is not None
        assert WarmPathFinder is not None

    def test_company_imports(self):
        """Test company intelligence imports."""
        from app.intelligence.company.event_monitor import CompanyEventMonitor
        from app.intelligence.company.layoff_tracker import LayoffTracker
        from app.intelligence.company.alert_generator import AlertGenerator

        assert CompanyEventMonitor is not None
        assert LayoffTracker is not None
        assert AlertGenerator is not None


class TestV4CurationEngine:
    """Test V4 Curation Engine."""

    def test_import(self):
        """Test that V4 imports correctly."""
        from app.services.curation_engine import CandidateCurationEngine
        from app.models.curation import CurationRequest, CurationResponse

        assert CandidateCurationEngine is not None
        assert CurationRequest is not None
        assert CurationResponse is not None


class TestV5UnifiedSearch:
    """Test V5 Unified Search."""

    def test_import(self):
        """Test that V5 imports correctly."""
        from app.services.unified_search import UnifiedSearchEngine, unified_search, Candidate, SearchResult

        assert UnifiedSearchEngine is not None
        assert unified_search is not None

    def test_weights(self):
        """Test scoring weights are correct."""
        from app.services.unified_search import UnifiedSearchEngine

        assert UnifiedSearchEngine.WEIGHT_FIT == 0.50
        assert UnifiedSearchEngine.WEIGHT_WARMTH == 0.30
        assert UnifiedSearchEngine.WEIGHT_TIMING == 0.20


class TestReasoningEngine:
    """Test Kimi K2.5 Reasoning Engine."""

    def test_import(self):
        """Test that reasoning engine imports correctly."""
        from app.services.reasoning import KimiReasoningEngine, kimi_engine

        assert KimiReasoningEngine is not None
        assert kimi_engine is not None

    def test_fallback_query_reasoning(self):
        """Test fallback mode for query reasoning."""
        from app.services.reasoning import kimi_engine

        result = kimi_engine._fallback_query_reasoning(
            role_title="ML Engineer",
            required_skills=["Python", "PyTorch"],
            network_companies=["Google", "Meta"],
            network_schools=["Stanford", "MIT"]
        )

        assert result.primary_query is not None
        assert len(result.expansion_queries) > 0
        assert len(result.reasoning_steps) > 0

    def test_fallback_candidate_analysis(self):
        """Test fallback mode for candidate analysis."""
        from app.services.reasoning import kimi_engine

        candidate = {
            "id": "test-123",
            "full_name": "Test User",
            "current_title": "ML Engineer",
            "headline": "Python ML expert"
        }

        result = kimi_engine._fallback_candidate_analysis(
            candidate=candidate,
            role_title="ML Engineer",
            required_skills=["Python", "PyTorch"]
        )

        assert result.candidate_id == "test-123"
        assert result.skill_score >= 0
        assert len(result.why_consider) > 0


class TestFeedbackCollector:
    """Test Feedback Collection System."""

    def test_import(self):
        """Test that feedback collector imports correctly."""
        from app.services.feedback import FeedbackCollector, feedback_collector, FeedbackAction

        assert FeedbackCollector is not None
        assert feedback_collector is not None

    def test_action_rewards(self):
        """Test action reward values."""
        from app.services.feedback.collector import ACTION_REWARDS, FeedbackAction

        assert ACTION_REWARDS[FeedbackAction.HIRED] == 10
        assert ACTION_REWARDS[FeedbackAction.INTERVIEWED] == 5
        assert ACTION_REWARDS[FeedbackAction.CONTACTED] == 2
        assert ACTION_REWARDS[FeedbackAction.REJECTED] == -5


class TestRewardModel:
    """Test RL Reward Model."""

    def test_import(self):
        """Test that reward model imports correctly."""
        from app.services.rl import RewardModel, reward_model

        assert RewardModel is not None
        assert reward_model is not None

    def test_score_candidate(self):
        """Test scoring a candidate."""
        from app.services.rl import reward_model

        candidate = {
            "id": "test-123",
            "fit_score": 80,
            "warmth_score": 60,
            "timing_score": 40,
            "is_from_network": True
        }

        result = reward_model.score(candidate)

        assert result.candidate_id == "test-123"
        assert 0 <= result.reward_score <= 1
        assert len(result.reasoning) > 0

    def test_get_model_info(self):
        """Test getting model info."""
        from app.services.rl import reward_model

        info = reward_model.get_model_info()

        assert "enabled" in info
        assert "weights" in info
        assert "fit" in info["weights"]


class TestMasterOrchestrator:
    """Test Master Orchestrator."""

    def test_import(self):
        """Test that master orchestrator imports correctly."""
        from app.services.master_orchestrator import MasterOrchestrator, master_orchestrator

        assert MasterOrchestrator is not None
        assert master_orchestrator is not None

    def test_methods_available(self):
        """Test that all methods are available."""
        from app.services.master_orchestrator import master_orchestrator

        assert hasattr(master_orchestrator, "search")
        assert hasattr(master_orchestrator, "quick_search")
        assert hasattr(master_orchestrator, "network_only_search")
        assert hasattr(master_orchestrator, "get_timing_alerts")
        assert hasattr(master_orchestrator, "get_intelligence_summary")
        assert hasattr(master_orchestrator, "record_candidate_action")
        assert hasattr(master_orchestrator, "train_from_feedback")


class TestExternalSearch:
    """Test External Search Services."""

    def test_clado_import(self):
        """Test Clado client import."""
        from app.services.external_search.clado_client import clado_client, CladoClient

        assert CladoClient is not None
        assert clado_client is not None

    def test_pdl_import(self):
        """Test PDL client import."""
        from app.services.external_search.pdl_client import pdl_client, PDLClient

        assert PDLClient is not None
        assert pdl_client is not None

    def test_query_generator_import(self):
        """Test query generator import."""
        from app.services.external_search.query_generator import query_generator, QueryGenerator

        assert QueryGenerator is not None
        assert query_generator is not None


class TestNetworkIndex:
    """Test Network Index Service."""

    def test_import(self):
        """Test network index import."""
        from app.services.network_index import network_index_service, NetworkIndexService

        assert NetworkIndexService is not None
        assert network_index_service is not None


class TestWarmPathFinder:
    """Test Warm Path Finder Service."""

    def test_import(self):
        """Test warm path finder import."""
        from app.services.warm_path_finder import warm_path_finder, WarmPathFinder

        assert WarmPathFinder is not None
        assert warm_path_finder is not None


class TestPredictionLayer:
    """Test Prediction Layer Components."""

    def test_prediction_engine_import(self):
        """Test prediction engine import."""
        from app.services.prediction import PredictionEngine, prediction_engine

        assert PredictionEngine is not None
        assert prediction_engine is not None
        assert prediction_engine._initialized

    def test_all_predictors_import(self):
        """Test all predictor imports."""
        from app.services.prediction import (
            QueryAutocomplete,
            RoleSuggester,
            CandidateSurfacer,
            SkillPredictor,
            WarmPathAlerter,
            InterviewPredictor
        )

        assert QueryAutocomplete is not None
        assert RoleSuggester is not None
        assert CandidateSurfacer is not None
        assert SkillPredictor is not None
        assert WarmPathAlerter is not None
        assert InterviewPredictor is not None

    def test_prediction_engine_components(self):
        """Test prediction engine has all components."""
        from app.services.prediction import prediction_engine

        assert hasattr(prediction_engine, 'autocomplete')
        assert hasattr(prediction_engine, 'role_suggester')
        assert hasattr(prediction_engine, 'candidate_surfacer')
        assert hasattr(prediction_engine, 'skill_predictor')
        assert hasattr(prediction_engine, 'warm_path_alerter')
        assert hasattr(prediction_engine, 'interview_predictor')

    def test_skill_predictor(self):
        """Test skill predictor functionality."""
        from app.services.prediction import SkillPredictor

        sp = SkillPredictor()
        reqs = sp.predict_requirements("ML Engineer")

        assert reqs.role_title == "ML Engineer"
        assert len(reqs.required_skills) > 0
        assert "Python" in reqs.required_skills
        assert reqs.years_experience >= 0

    def test_skill_predictor_suggestions(self):
        """Test skill suggestion functionality."""
        from app.services.prediction import SkillPredictor

        sp = SkillPredictor()
        suggestions = sp.suggest_skills("py", category="languages")

        assert len(suggestions) > 0
        assert "Python" in suggestions

    def test_master_orchestrator_prediction_methods(self):
        """Test master orchestrator has prediction methods."""
        from app.services.master_orchestrator import master_orchestrator

        # Check prediction methods exist
        assert hasattr(master_orchestrator, 'get_predictions')
        assert hasattr(master_orchestrator, 'get_dashboard_predictions')
        assert hasattr(master_orchestrator, 'autocomplete_query')
        assert hasattr(master_orchestrator, 'predict_interviews')
        assert hasattr(master_orchestrator, 'get_timing_digest')
        assert hasattr(master_orchestrator, 'get_hiring_plan')
        assert hasattr(master_orchestrator, 'suggest_role_requirements')

    def test_suggest_role_requirements(self):
        """Test synchronous role requirements suggestion."""
        from app.services.master_orchestrator import master_orchestrator

        reqs = master_orchestrator.suggest_role_requirements("Backend Engineer")

        assert "required_skills" in reqs
        assert "years_experience" in reqs
        assert len(reqs["required_skills"]) > 0


# =============================================================================
# ASYNC INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_unified_search_execution():
    """Test executing a unified search."""
    from app.services.unified_search import unified_search

    result = await unified_search.search(
        company_id=TEST_COMPANY_ID,
        role_title="ML Engineer",
        required_skills=["Python", "Machine Learning"],
        include_external=False,  # Network only for speed
        include_timing=True,
        deep_research=False,  # Skip for speed
        limit=5
    )

    assert result is not None
    assert result.role_title == "ML Engineer"
    assert isinstance(result.candidates, list)


@pytest.mark.asyncio
async def test_network_index_build():
    """Test building network index."""
    from app.services.network_index import network_index_service

    index = await network_index_service.build_index(TEST_COMPANY_ID)

    assert index is not None

    stats = network_index_service.get_network_stats(index)
    assert stats["total_contacts"] >= 0


@pytest.mark.asyncio
async def test_master_orchestrator_quick_search():
    """Test master orchestrator quick search."""
    from app.services.master_orchestrator import master_orchestrator

    result = await master_orchestrator.quick_search(
        company_id=TEST_COMPANY_ID,
        role_title="Software Engineer",
        required_skills=["Python"],
        limit=5
    )

    assert result is not None
    assert result.mode == "quick"
    assert "unified_search" in result.features_used


# =============================================================================
# RUN TESTS DIRECTLY
# =============================================================================

def run_all_tests():
    """Run all tests and print results."""
    print("="*60)
    print("PROOFHIRE INTEGRATION TESTS")
    print("="*60)

    tests_passed = 0
    tests_failed = 0
    errors = []

    # Collect all test classes
    test_classes = [
        TestV1SearchEngine,
        TestV2SearchEngine,
        TestV3Intelligence,
        TestV4CurationEngine,
        TestV5UnifiedSearch,
        TestReasoningEngine,
        TestFeedbackCollector,
        TestRewardModel,
        TestMasterOrchestrator,
        TestExternalSearch,
        TestNetworkIndex,
        TestWarmPathFinder,
        TestPredictionLayer,
    ]

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✅ {method_name}")
                    tests_passed += 1
                except Exception as e:
                    print(f"  ❌ {method_name}: {e}")
                    tests_failed += 1
                    errors.append((test_class.__name__, method_name, str(e)))

    # Run async tests
    print("\nAsync Tests:")

    async def run_async_tests():
        nonlocal tests_passed, tests_failed, errors

        async_tests = [
            ("test_unified_search_execution", test_unified_search_execution),
            ("test_network_index_build", test_network_index_build),
            ("test_master_orchestrator_quick_search", test_master_orchestrator_quick_search),
        ]

        for name, test_fn in async_tests:
            try:
                await test_fn()
                print(f"  ✅ {name}")
                tests_passed += 1
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                tests_failed += 1
                errors.append(("AsyncTests", name, str(e)))

    asyncio.run(run_async_tests())

    # Summary
    print("\n" + "="*60)
    print(f"RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("="*60)

    if errors:
        print("\nErrors:")
        for class_name, method, error in errors:
            print(f"  {class_name}.{method}: {error}")

    return tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
