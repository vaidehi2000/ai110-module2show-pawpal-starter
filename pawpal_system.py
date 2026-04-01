from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)

    def get_profile(self) -> str:
        pass

    def requires_medication(self) -> bool:
        pass


@dataclass
class Task:
    title: str
    category: str          # walk | feed | medication | grooming | enrichment
    duration_minutes: int
    priority: str          # low | medium | high
    preferred_time: Optional[str] = None   # e.g. "morning", "evening"
    is_completed: bool = False

    def mark_complete(self) -> None:
        pass

    def to_dict(self) -> dict:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: dict = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_total_available_time(self) -> int:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[Task] = []
        self.scheduled_plan: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def generate_plan(self) -> list[Task]:
        pass

    def explain_plan(self) -> str:
        pass
