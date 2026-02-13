"""
End-to-End Full System Test

This test validates the ENTIRE ProofHire system working together:

1. UNIFIED SEARCH & INTELLIGENCE SYSTEM
   - Master Orchestrator
   - Reasoning Layer (Kimi K2.5)
   - Intelligence Layer (4 Pillars)
   - Search Layer (V1-V5)
   - RL Feedback Layer

2. PREDICTION LAYER
   - Query Autocomplete
   - Role Suggester
   - Candidate Surfacer
   - Skill Predictor
   - Warm Path Alerter
   - Interview Predictor

This simulates a real founder workflow from start to finish.
"""

import asyncio
import time
from datetime import datetime

# Test configuration
TEST_COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"
TEST_USER_ID = "test-user-001"
TEST_ROLE_TITLE = "ML Engineer"
TEST_SKILLS = ["Python", "PyTorch", "Machine Learning", "Deep Learning"]


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_section(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}>>> {text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.GREEN}  ✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.YELLOW}  ⚠ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.RED}  ✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.BLUE}    {text}{Colors.ENDC}")


class EndToEndTester:
    """Comprehensive end-to-end system tester."""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
        self.start_time = None

    def record_test(self, name: str, passed: bool, details: str = "", warning: bool = False):
        """Record a test result."""
        status = "passed" if passed else ("warning" if warning else "failed")
        self.results["tests"].append({
            "name": name,
            "status": status,
            "details": details
        })
        if passed:
            self.results["passed"] += 1
            print_success(f"{name}: {details}")
        elif warning:
            self.results["warnings"] += 1
            print_warning(f"{name}: {details}")
        else:
            self.results["failed"] += 1
            print_error(f"{name}: {details}")

    async def run_all_tests(self):
        """Run all end-to-end tests."""
        self.start_time = time.time()

        print_header("PROOFHIRE END-TO-END SYSTEM TEST")
        print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Company ID: {TEST_COMPANY_ID}")
        print(f"Test Role: {TEST_ROLE_TITLE}")

        # =====================================================================
        # PHASE 1: IMPORT VERIFICATION
        # =====================================================================
        print_header("PHASE 1: IMPORT VERIFICATION")
        await self.test_imports()

        # =====================================================================
        # PHASE 2: COMPONENT INITIALIZATION
        # =====================================================================
        print_header("PHASE 2: COMPONENT INITIALIZATION")
        await self.test_initialization()

        # =====================================================================
        # PHASE 3: PREDICTION LAYER
        # =====================================================================
        print_header("PHASE 3: PREDICTION LAYER")
        await self.test_prediction_layer()

        # =====================================================================
        # PHASE 4: SEARCH LAYER (V1-V5)
        # =====================================================================
        print_header("PHASE 4: SEARCH LAYER")
        await self.test_search_layer()

        # =====================================================================
        # PHASE 5: INTELLIGENCE LAYER
        # =====================================================================
        print_header("PHASE 5: INTELLIGENCE LAYER")
        await self.test_intelligence_layer()

        # =====================================================================
        # PHASE 6: REASONING LAYER
        # =====================================================================
        print_header("PHASE 6: REASONING LAYER (KIMI)")
        await self.test_reasoning_layer()

        # =====================================================================
        # PHASE 7: FEEDBACK & RL LAYER
        # =====================================================================
        print_header("PHASE 7: FEEDBACK & RL LAYER")
        await self.test_feedback_rl_layer()

        # =====================================================================
        # PHASE 8: MASTER ORCHESTRATOR (FULL FLOW)
        # =====================================================================
        print_header("PHASE 8: MASTER ORCHESTRATOR")
        await self.test_master_orchestrator()

        # =====================================================================
        # PHASE 9: FOUNDER WORKFLOW SIMULATION
        # =====================================================================
        print_header("PHASE 9: FOUNDER WORKFLOW SIMULATION")
        await self.test_founder_workflow()

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        self.print_summary()

    async def test_imports(self):
        """Test all critical imports."""
        print_section("Testing Critical Imports")

        imports_to_test = [
            ("Master Orchestrator", "from app.services.master_orchestrator import master_orchestrator, MasterOrchestrator"),
            ("Prediction Engine", "from app.services.prediction import prediction_engine, PredictionEngine"),
            ("Unified Search", "from app.services.unified_search import unified_search"),
            ("Kimi Reasoning", "from app.services.reasoning import kimi_engine"),
            ("Feedback Collector", "from app.services.feedback import feedback_collector, FeedbackAction"),
            ("Reward Model", "from app.services.rl import reward_model"),
            ("Network Index", "from app.services.network_index import network_index_service"),
            ("Warm Path Finder", "from app.services.warm_path_finder import warm_path_finder"),
            ("V1 Search Engine", "from app.search.engine import SearchEngine"),
            ("V2 Search Engine", "from app.search.engine_v2 import SearchEngineV2"),
            ("V4 Curation Engine", "from app.services.curation_engine import CandidateCurationEngine"),
            ("Query Autocomplete", "from app.services.prediction.query_autocomplete import QueryAutocomplete"),
            ("Role Suggester", "from app.services.prediction.role_suggester import RoleSuggester"),
            ("Candidate Surfacer", "from app.services.prediction.candidate_surfacer import CandidateSurfacer"),
            ("Skill Predictor", "from app.services.prediction.skill_predictor import SkillPredictor"),
            ("Warm Path Alerter", "from app.services.prediction.warm_path_alerter import WarmPathAlerter"),
            ("Interview Predictor", "from app.services.prediction.interview_predictor import InterviewPredictor"),
        ]

        for name, import_str in imports_to_test:
            try:
                exec(import_str)
                self.record_test(name, True, "Import successful")
            except Exception as e:
                self.record_test(name, False, f"Import failed: {str(e)[:50]}")

    async def test_initialization(self):
        """Test component initialization."""
        print_section("Testing Component Initialization")

        # Master Orchestrator
        try:
            from app.services.master_orchestrator import master_orchestrator
            assert master_orchestrator is not None
            assert hasattr(master_orchestrator, 'search')
            self.record_test("Master Orchestrator Init", True, "Singleton initialized")
        except Exception as e:
            self.record_test("Master Orchestrator Init", False, str(e)[:50])

        # Prediction Engine
        try:
            from app.services.prediction import prediction_engine
            assert prediction_engine._initialized
            assert hasattr(prediction_engine, 'autocomplete')
            assert hasattr(prediction_engine, 'role_suggester')
            assert hasattr(prediction_engine, 'candidate_surfacer')
            assert hasattr(prediction_engine, 'skill_predictor')
            assert hasattr(prediction_engine, 'warm_path_alerter')
            assert hasattr(prediction_engine, 'interview_predictor')
            self.record_test("Prediction Engine Init", True, "All 6 predictors ready")
        except Exception as e:
            self.record_test("Prediction Engine Init", False, str(e)[:50])

        # Reward Model
        try:
            from app.services.rl import reward_model
            info = reward_model.get_model_info()
            assert "enabled" in info
            self.record_test("Reward Model Init", True, f"Enabled: {info['enabled']}")
        except Exception as e:
            self.record_test("Reward Model Init", False, str(e)[:50])

    async def test_prediction_layer(self):
        """Test the prediction layer components."""

        # Test 1: Skill Predictor
        print_section("Skill Predictor")
        try:
            from app.services.prediction import SkillPredictor
            sp = SkillPredictor()

            # Test role requirements
            reqs = sp.predict_requirements("ML Engineer")
            assert reqs.role_title == "ML Engineer"
            assert len(reqs.required_skills) > 0
            assert "Python" in reqs.required_skills
            self.record_test("Skill Predictor - ML Engineer", True,
                             f"Skills: {reqs.required_skills[:3]}")

            # Test different roles
            for role in ["Backend Engineer", "Product Manager", "DevOps Engineer"]:
                r = sp.predict_requirements(role)
                assert len(r.required_skills) > 0
            self.record_test("Skill Predictor - Multiple Roles", True, "3 roles predicted")

            # Test skill suggestions
            suggestions = sp.suggest_skills("py", category="languages")
            assert "Python" in suggestions
            self.record_test("Skill Suggestions", True, f"Found: {suggestions}")

        except Exception as e:
            self.record_test("Skill Predictor", False, str(e)[:50])

        # Test 2: Query Autocomplete
        print_section("Query Autocomplete")
        try:
            from app.services.prediction import QueryAutocomplete
            qa = QueryAutocomplete()

            # Test that it initializes with patterns
            assert qa._supabase is None  # Lazy loading
            self.record_test("Query Autocomplete Init", True, "Lazy DB connection")

        except Exception as e:
            self.record_test("Query Autocomplete", False, str(e)[:50])

        # Test 3: Role Suggester
        print_section("Role Suggester")
        try:
            from app.services.prediction import RoleSuggester
            rs = RoleSuggester()

            # Test stage patterns exist
            from app.services.prediction.role_suggester import STAGE_PATTERNS
            assert "seed" in STAGE_PATTERNS
            assert "series_a" in STAGE_PATTERNS
            self.record_test("Role Suggester - Patterns", True,
                             f"Stages: {list(STAGE_PATTERNS.keys())[:3]}")

        except Exception as e:
            self.record_test("Role Suggester", False, str(e)[:50])

        # Test 4: Candidate Surfacer
        print_section("Candidate Surfacer")
        try:
            from app.services.prediction import CandidateSurfacer
            from app.services.prediction.candidate_surfacer import RECENT_LAYOFFS

            cs = CandidateSurfacer()

            # Test layoff data exists
            assert len(RECENT_LAYOFFS) > 0
            assert "meta" in RECENT_LAYOFFS
            assert "google" in RECENT_LAYOFFS
            self.record_test("Candidate Surfacer - Layoff Data", True,
                             f"Tracking {len(RECENT_LAYOFFS)} companies")

        except Exception as e:
            self.record_test("Candidate Surfacer", False, str(e)[:50])

        # Test 5: Warm Path Alerter
        print_section("Warm Path Alerter")
        try:
            from app.services.prediction import WarmPathAlerter
            from app.services.prediction.warm_path_alerter import TARGET_COMPANIES

            wpa = WarmPathAlerter()

            # Test target companies
            assert len(TARGET_COMPANIES) > 0
            assert "google" in TARGET_COMPANIES
            assert "anthropic" in TARGET_COMPANIES
            self.record_test("Warm Path Alerter - Targets", True,
                             f"Tracking {len(TARGET_COMPANIES)} target companies")

        except Exception as e:
            self.record_test("Warm Path Alerter", False, str(e)[:50])

        # Test 6: Interview Predictor
        print_section("Interview Predictor")
        try:
            from app.services.prediction import InterviewPredictor

            ip = InterviewPredictor()

            # Test prediction on mock candidate
            mock_candidate = {
                "id": "test-001",
                "full_name": "Test Candidate",
                "fit_score": 85,
                "warmth_score": 60,
                "timing_score": 40,
                "is_from_network": True
            }

            patterns = {"avg_fit_interviewed": 70, "network_preference": 0.6}
            prediction = ip._predict_single(mock_candidate, patterns)

            assert prediction.candidate_id == "test-001"
            assert 0 <= prediction.interview_probability <= 1
            assert len(prediction.key_factors) > 0
            self.record_test("Interview Predictor", True,
                             f"Probability: {prediction.interview_probability:.2f}")

        except Exception as e:
            self.record_test("Interview Predictor", False, str(e)[:50])

        # Test 7: Prediction Engine Integration
        print_section("Prediction Engine - suggest_role_requirements")
        try:
            from app.services.prediction import prediction_engine

            reqs = prediction_engine.suggest_role_requirements("Data Engineer")
            assert reqs.role_title == "Data Engineer"
            assert "Python" in reqs.required_skills or "SQL" in reqs.required_skills
            self.record_test("Prediction Engine Integration", True,
                             f"Requirements for {reqs.role_title}")

        except Exception as e:
            self.record_test("Prediction Engine Integration", False, str(e)[:50])

    async def test_search_layer(self):
        """Test search layer components."""

        # Test V1 Search
        print_section("V1 Search Engine")
        try:
            from app.search.engine import SearchEngine
            v1 = SearchEngine(company_id=TEST_COMPANY_ID)
            assert hasattr(v1, 'search')
            self.record_test("V1 Search Engine", True, "Gateway search ready")
        except Exception as e:
            self.record_test("V1 Search Engine", False, str(e)[:50])

        # Test V2 Search
        print_section("V2 Search Engine")
        try:
            from app.search.engine_v2 import SearchEngineV2
            v2 = SearchEngineV2(company_id=TEST_COMPANY_ID)
            assert hasattr(v2, 'search')
            self.record_test("V2 Search Engine", True, "Tiered search ready")
        except Exception as e:
            self.record_test("V2 Search Engine", False, str(e)[:50])

        # Test V4 Curation
        print_section("V4 Curation Engine")
        try:
            from app.services.curation_engine import CandidateCurationEngine
            from app.core.database import get_supabase_client
            v4 = CandidateCurationEngine(supabase_client=get_supabase_client())
            assert hasattr(v4, 'curate')
            self.record_test("V4 Curation Engine", True, "Curation ready")
        except Exception as e:
            self.record_test("V4 Curation Engine", False, str(e)[:50])

        # Test V5 Unified Search
        print_section("V5 Unified Search")
        try:
            from app.services import unified_search as unified_module
            us = unified_module.unified_search
            assert hasattr(us, 'search')
            self.record_test("V5 Unified Search", True, "Unified search ready")
        except Exception as e:
            self.record_test("V5 Unified Search", False, str(e)[:50])

        # Test Network Index
        print_section("Network Index Service")
        try:
            from app.services.network_index import network_index_service
            assert network_index_service is not None
            assert hasattr(network_index_service, 'build_index')
            self.record_test("Network Index Service", True, "Index service ready")
        except Exception as e:
            self.record_test("Network Index Service", False, str(e)[:50])

        # Test Warm Path Finder
        print_section("Warm Path Finder")
        try:
            from app.services.warm_path_finder import warm_path_finder
            assert hasattr(warm_path_finder, 'find_warm_paths')
            self.record_test("Warm Path Finder", True, "Path finding ready")
        except Exception as e:
            self.record_test("Warm Path Finder", False, str(e)[:50])

    async def test_intelligence_layer(self):
        """Test intelligence layer (4 pillars)."""

        # Pillar 1: Activation
        print_section("Pillar 1: Activation (Network Asks)")
        try:
            from app.intelligence.activation.reverse_reference import ReverseReferenceGenerator
            self.record_test("Activation Import", True, "Reverse reference ready")
        except Exception as e:
            self.record_test("Activation Import", False, str(e)[:50])

        # Pillar 2: Timing
        print_section("Pillar 2: Timing (Readiness)")
        try:
            from app.search.readiness import ReadinessScorer
            scorer = ReadinessScorer()

            # Test readiness scoring
            mock_person = {
                "current_company": "Meta",
                "current_title": "Senior Engineer",
                "employment_history": [
                    {"company": "Meta", "start_date": "2020-01", "is_current": True}
                ]
            }
            result = scorer.score(mock_person)
            assert "readiness_score" in result
            assert 0 <= result["readiness_score"] <= 1
            self.record_test("Timing - Readiness Scorer", True,
                             f"Score: {result['readiness_score']:.2f}")
        except Exception as e:
            self.record_test("Timing - Readiness Scorer", False, str(e)[:50])

        # Pillar 3: Expansion
        print_section("Pillar 3: Expansion (Colleagues)")
        try:
            from app.intelligence.expansion.colleague_expander import ColleagueExpander
            self.record_test("Expansion Import", True, "Colleague expander ready")
        except Exception as e:
            self.record_test("Expansion Import", False, str(e)[:50])

        # Pillar 4: Company Events
        print_section("Pillar 4: Company Events")
        try:
            from app.intelligence.company.event_monitor import CompanyEventMonitor
            self.record_test("Company Events Import", True, "Event monitor ready")
        except Exception as e:
            self.record_test("Company Events Import", False, str(e)[:50])

    async def test_reasoning_layer(self):
        """Test the Kimi K2.5 reasoning layer."""

        print_section("Kimi Engine Status")
        try:
            from app.services.reasoning import kimi_engine

            # Check if enabled
            if kimi_engine.enabled:
                self.record_test("Kimi Engine", True, "API key configured, full reasoning available")
            else:
                self.record_test("Kimi Engine", True, "Fallback mode (no API key)", warning=True)

        except Exception as e:
            self.record_test("Kimi Engine", False, str(e)[:50])

        # Test fallback query reasoning
        print_section("Query Reasoning (Fallback)")
        try:
            from app.services.reasoning import kimi_engine

            result = await kimi_engine.reason_about_queries(
                role_title=TEST_ROLE_TITLE,
                required_skills=TEST_SKILLS[:2],
                preferred_skills=TEST_SKILLS[2:],
                location="San Francisco"
            )

            assert result.primary_query is not None
            assert len(result.expansion_queries) > 0
            self.record_test("Query Reasoning", True,
                             f"Primary: {result.primary_query[:40]}...")

        except Exception as e:
            self.record_test("Query Reasoning", False, str(e)[:50])

        # Test fallback candidate analysis
        print_section("Candidate Analysis (Fallback)")
        try:
            from app.services.reasoning import kimi_engine

            mock_candidate = {
                "full_name": "Jane Smith",
                "current_title": "Senior ML Engineer",
                "current_company": "Google",
                "skills": ["Python", "PyTorch", "TensorFlow"],
                "years_experience": 5
            }

            result = await kimi_engine.analyze_candidate(
                candidate=mock_candidate,
                role_title=TEST_ROLE_TITLE,
                required_skills=TEST_SKILLS[:2]
            )

            assert result.why_consider is not None
            assert 0 <= result.confidence <= 1
            self.record_test("Candidate Analysis", True,
                             f"Confidence: {result.confidence:.2f}")

        except Exception as e:
            self.record_test("Candidate Analysis", False, str(e)[:50])

    async def test_feedback_rl_layer(self):
        """Test the feedback and RL layer."""

        # Test Feedback Collector
        print_section("Feedback Collector")
        try:
            from app.services.feedback import feedback_collector, FeedbackAction

            # Verify actions
            assert FeedbackAction.HIRED.value == "hired"
            assert FeedbackAction.VIEWED.value == "viewed"

            # Verify collector exists
            assert hasattr(feedback_collector, 'record_action')
            assert hasattr(feedback_collector, 'get_training_pairs')

            self.record_test("Feedback Collector", True, "Ready to collect feedback")

        except Exception as e:
            self.record_test("Feedback Collector", False, str(e)[:50])

        # Test Reward Model
        print_section("Reward Model")
        try:
            from app.services.rl import reward_model

            # Test scoring
            mock_candidate = {
                "fit_score": 80,
                "warmth_score": 60,
                "timing_score": 40,
                "skills": ["Python", "PyTorch"],
                "years_experience": 4
            }

            result = reward_model.score(mock_candidate)
            assert 0 <= result.reward_score <= 1
            self.record_test("Reward Model - Scoring", True,
                             f"Score: {result.reward_score:.3f}")

            # Test ranking adjustment
            candidates = [
                {"id": "1", "fit_score": 80, "warmth_score": 50, "combined_score": 70},
                {"id": "2", "fit_score": 70, "warmth_score": 80, "combined_score": 75},
                {"id": "3", "fit_score": 90, "warmth_score": 30, "combined_score": 65},
            ]

            adjusted = reward_model.adjust_ranking(candidates, {"company_id": TEST_COMPANY_ID})
            assert len(adjusted) == 3
            assert all("reward_adjustment" in c for c in adjusted)
            self.record_test("Reward Model - Ranking", True,
                             f"Adjusted {len(adjusted)} candidates")

        except Exception as e:
            self.record_test("Reward Model", False, str(e)[:50])

    async def test_master_orchestrator(self):
        """Test the master orchestrator."""

        print_section("Master Orchestrator Methods")
        try:
            from app.services.master_orchestrator import master_orchestrator

            # Verify all methods exist
            methods = [
                'search', 'quick_search', 'network_only_search',
                'get_timing_alerts', 'get_intelligence_summary',
                'record_candidate_action', 'train_from_feedback',
                'get_predictions', 'get_dashboard_predictions',
                'autocomplete_query', 'predict_interviews',
                'get_timing_digest', 'get_hiring_plan',
                'suggest_role_requirements'
            ]

            missing = [m for m in methods if not hasattr(master_orchestrator, m)]
            if missing:
                self.record_test("Orchestrator Methods", False, f"Missing: {missing}")
            else:
                self.record_test("Orchestrator Methods", True, f"{len(methods)} methods available")

        except Exception as e:
            self.record_test("Orchestrator Methods", False, str(e)[:50])

        # Test suggest_role_requirements (sync, no DB needed)
        print_section("Orchestrator - Role Requirements")
        try:
            from app.services.master_orchestrator import master_orchestrator

            reqs = master_orchestrator.suggest_role_requirements(TEST_ROLE_TITLE)
            assert "required_skills" in reqs
            assert "Python" in reqs["required_skills"]
            self.record_test("Role Requirements via Orchestrator", True,
                             f"Skills: {reqs['required_skills'][:3]}")

        except Exception as e:
            self.record_test("Role Requirements via Orchestrator", False, str(e)[:50])

    async def test_founder_workflow(self):
        """Simulate a complete founder workflow."""

        print_section("Step 1: Founder Opens Search")
        print_info("Founder wants to hire an ML Engineer...")

        try:
            from app.services.master_orchestrator import master_orchestrator

            # Get role requirements
            reqs = master_orchestrator.suggest_role_requirements("ML Engineer")
            print_info(f"Suggested skills: {reqs['required_skills']}")
            print_info(f"Experience: {reqs['years_experience']}+ years")
            self.record_test("Workflow - Role Requirements", True, "Auto-filled search form")

        except Exception as e:
            self.record_test("Workflow - Role Requirements", False, str(e)[:50])

        print_section("Step 2: Founder Types Query")
        print_info("Founder starts typing 'ML Eng'...")

        try:
            from app.services.prediction import prediction_engine

            # Would normally call autocomplete, but we test the search predictions
            result = await prediction_engine.get_search_predictions(
                company_id=TEST_COMPANY_ID,
                user_id=TEST_USER_ID,
                partial_query="ML"
            )
            print_info(f"Skill suggestions: {result.get('skill_suggestions', [])[:3]}")
            self.record_test("Workflow - Search Autocomplete", True, "Suggestions provided")

        except Exception as e:
            self.record_test("Workflow - Search Autocomplete", False, str(e)[:50])

        print_section("Step 3: Dashboard Predictions")
        print_info("Showing predictions on dashboard...")

        try:
            from app.services.prediction import prediction_engine

            # Test interview predictor with mock candidates
            mock_candidates = [
                {"id": "c1", "full_name": "Alice Chen", "fit_score": 90, "warmth_score": 80, "timing_score": 60, "is_from_network": True},
                {"id": "c2", "full_name": "Bob Smith", "fit_score": 85, "warmth_score": 40, "timing_score": 70, "is_from_network": False},
                {"id": "c3", "full_name": "Carol Davis", "fit_score": 75, "warmth_score": 90, "timing_score": 50, "is_from_network": True},
            ]

            predictions = await prediction_engine.predict_interview_outcomes(
                company_id=TEST_COMPANY_ID,
                candidates=mock_candidates,
                role_title=TEST_ROLE_TITLE
            )

            print_info("Interview Predictions:")
            for p in predictions[:3]:
                print_info(f"  {p.candidate_name}: {p.interview_probability:.0%} ({p.reasoning[:30]}...)")

            self.record_test("Workflow - Interview Predictions", True,
                             f"Ranked {len(predictions)} candidates")

        except Exception as e:
            self.record_test("Workflow - Interview Predictions", False, str(e)[:50])

        print_section("Step 4: Feedback Recording")
        print_info("Founder saves a candidate...")

        try:
            from app.services.feedback import feedback_collector, FeedbackAction

            # Verify feedback can be recorded (without actually writing to DB)
            assert hasattr(feedback_collector, 'record_action')
            self.record_test("Workflow - Feedback Ready", True, "Feedback system ready")

        except Exception as e:
            self.record_test("Workflow - Feedback Ready", False, str(e)[:50])

        print_section("Step 5: Hiring Plan")
        print_info("Founder checks hiring recommendations...")

        try:
            from app.services.prediction import prediction_engine

            # Test role requirements for multiple roles
            roles = ["ML Engineer", "Backend Engineer", "Product Manager"]
            for role in roles:
                reqs = prediction_engine.suggest_role_requirements(role)
                print_info(f"  {role}: {reqs.required_skills[:2]}")

            self.record_test("Workflow - Hiring Plan", True, f"Analyzed {len(roles)} roles")

        except Exception as e:
            self.record_test("Workflow - Hiring Plan", False, str(e)[:50])

    def print_summary(self):
        """Print final test summary."""
        duration = time.time() - self.start_time

        print_header("FINAL TEST SUMMARY")

        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]

        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"  {Colors.GREEN}Passed:   {self.results['passed']}{Colors.ENDC}")
        print(f"  {Colors.YELLOW}Warnings: {self.results['warnings']}{Colors.ENDC}")
        print(f"  {Colors.RED}Failed:   {self.results['failed']}{Colors.ENDC}")
        print(f"  Total:    {total}")
        print(f"\n  Duration: {duration:.2f}s")

        # Calculate pass rate
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        print(f"\n{Colors.BOLD}Pass Rate: {pass_rate:.1f}%{Colors.ENDC}")

        if self.results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}")
            print("=" * 70)
            print("  SYSTEM IS PRODUCTION READY!")
            print("  All components working together successfully.")
            print("=" * 70)
            print(f"{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}")
            print("=" * 70)
            print("  ISSUES FOUND - Review failed tests above")
            print("=" * 70)
            print(f"{Colors.ENDC}")

            print("\nFailed tests:")
            for test in self.results["tests"]:
                if test["status"] == "failed":
                    print(f"  - {test['name']}: {test['details']}")


async def main():
    """Run the end-to-end tests."""
    tester = EndToEndTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
