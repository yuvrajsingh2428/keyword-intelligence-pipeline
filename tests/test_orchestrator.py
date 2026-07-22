"""Unit tests for the Pipeline Orchestrator."""

from keyword_intelligence.core.constants import StageType
from keyword_intelligence.core.exceptions import SchemaValidationError
from keyword_intelligence.models import PipelineResult
from keyword_intelligence.pipeline.context import PipelineContext
from keyword_intelligence.pipeline.orchestrator import PipelineOrchestrator
from keyword_intelligence.pipeline.registry import StageRegistry
from keyword_intelligence.pipeline.stage import BaseStage


class MockSuccessStage(BaseStage):
    """A mock stage that always succeeds."""

    @property
    def stage_type(self) -> StageType:
        return StageType.LOADER  # Using LOADER as dummy

    @property
    def stage_version(self) -> str:
        return "1.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        context.add_warning(self.stage_type.value, "TEST_WARNING", "This is a test")
        return context


class MockFailingStage(BaseStage):
    """A mock stage that raises an error."""

    @property
    def stage_type(self) -> StageType:
        return StageType.VALIDATOR  # Using VALIDATOR as dummy

    @property
    def stage_version(self) -> str:
        return "1.0"

    def execute(self, context: PipelineContext) -> PipelineContext:
        raise SchemaValidationError("Simulated failure")


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    def test_orchestrator_success(self, settings):
        """Test that stages execute successfully and metrics are recorded."""
        context = PipelineContext(settings)
        registry = StageRegistry()
        registry.register(MockSuccessStage())

        orchestrator = PipelineOrchestrator(settings, registry)

        result = orchestrator.run(context)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert len(result.stage_metrics) == 1
        assert result.stage_metrics[0].stage_name == StageType.LOADER.value
        assert result.stage_metrics[0].warnings_count == 1
        assert result.metrics.total_warnings == 1
        assert result.metrics.total_errors == 0
        assert result.execution_id == context.execution_id

    def test_orchestrator_failure_stops_execution(self, settings):
        """Test that STOP_ON_ERROR halts pipeline execution."""
        settings.stop_on_error = True
        # Set max retries to 0 for this test to avoid waiting
        settings.max_stage_retries = 0
        context = PipelineContext(settings)

        registry = StageRegistry()
        registry.register(MockSuccessStage())
        registry.register(MockFailingStage())
        registry.register(MockSuccessStage())

        orchestrator = PipelineOrchestrator(settings, registry)

        result = orchestrator.run(context)

        assert result.success is False
        # Only the first stage should have metrics (success)
        # The failing stage exception is caught before metrics are appended
        assert len(result.stage_metrics) == 1
        assert len(result.errors) == 1
        assert result.errors[0].stage == StageType.VALIDATOR.value

    def test_orchestrator_failure_continues_execution(self, settings):
        """Test that pipeline continues if STOP_ON_ERROR is False."""
        settings.stop_on_error = False
        settings.max_stage_retries = 0
        context = PipelineContext(settings)

        registry = StageRegistry()
        registry.register(MockSuccessStage())
        registry.register(MockFailingStage())
        registry.register(MockSuccessStage())

        orchestrator = PipelineOrchestrator(settings, registry)

        result = orchestrator.run(context)

        assert result.success is False
        # First stage and third stage should be recorded, second stage threw error
        assert len(result.stage_metrics) == 2
        assert result.stage_metrics[0].stage_name == StageType.LOADER.value
        assert result.stage_metrics[1].stage_name == StageType.LOADER.value
        assert len(result.errors) == 1
        assert result.errors[0].stage == StageType.VALIDATOR.value
