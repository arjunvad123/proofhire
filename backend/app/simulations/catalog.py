"""Simulation catalog - load and manage simulation definitions."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.logging_config import get_logger

logger = get_logger(__name__)


class SimulationDefinition(BaseModel):
    """Definition of a simulation."""

    id: str
    name: str
    description: str
    type: str  # "bugfix", "feature", "refactor"
    difficulty: str  # "easy", "medium", "hard"
    time_limit_minutes: int = 60
    languages: list[str] = Field(default_factory=lambda: ["python"])
    dimensions: list[str]  # Which dimensions this simulation evaluates
    claims: list[str]  # Which claims can be proven
    setup_instructions: str = ""
    candidate_instructions: str = ""
    writeup_prompts: list[str] = Field(default_factory=list)


class SimulationCatalog:
    """Catalog of available simulations."""

    def __init__(self):
        self._simulations: dict[str, SimulationDefinition] = {}
        self._loaded = False

    def load(self, definitions_dir: Path | None = None) -> None:
        """Load simulation definitions from YAML files."""
        if definitions_dir is None:
            definitions_dir = Path(__file__).parent / "definitions"

        if not definitions_dir.exists():
            logger.warning("Definitions directory not found", path=str(definitions_dir))
            return

        for yaml_file in definitions_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                sim = SimulationDefinition(**data)
                self._simulations[sim.id] = sim
                logger.info("Loaded simulation", id=sim.id, name=sim.name)

            except Exception as e:
                logger.error("Failed to load simulation", file=str(yaml_file), error=str(e))

        self._loaded = True
        logger.info("Simulation catalog loaded", count=len(self._simulations))

    def get(self, simulation_id: str) -> SimulationDefinition | None:
        """Get a simulation by ID."""
        if not self._loaded:
            self.load()
        return self._simulations.get(simulation_id)

    def list_all(self) -> list[SimulationDefinition]:
        """List all available simulations."""
        if not self._loaded:
            self.load()
        return list(self._simulations.values())

    def list_by_type(self, sim_type: str) -> list[SimulationDefinition]:
        """List simulations by type."""
        return [s for s in self.list_all() if s.type == sim_type]

    def list_by_difficulty(self, difficulty: str) -> list[SimulationDefinition]:
        """List simulations by difficulty."""
        return [s for s in self.list_all() if s.difficulty == difficulty]

    def get_for_role(self, dimensions: list[str]) -> list[SimulationDefinition]:
        """Get simulations that cover the given dimensions."""
        result = []
        for sim in self.list_all():
            if any(d in sim.dimensions for d in dimensions):
                result.append(sim)
        return result


# Global catalog instance
_catalog: SimulationCatalog | None = None


def get_simulation_catalog() -> SimulationCatalog:
    """Get the global simulation catalog."""
    global _catalog
    if _catalog is None:
        _catalog = SimulationCatalog()
        _catalog.load()
    return _catalog
