"""Curriculum model and repository."""
import json
from typing import List
from pathlib import Path

class CurriculumDay:
    """Represents a curriculum day."""
    def __init__(self, day: int, title: str, topics: List[str]):
        self.day = day
        self.title = title
        self.topics = topics

class CurriculumRepository:
    """Repository for managing curriculum."""
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.days = []
        self._load()
    
    def _load(self):
        """Load curriculum from file."""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.days = [CurriculumDay(**d) for d in data]
        except Exception:
            self.days = []
    
    def list_all(self) -> List[CurriculumDay]:
        """List all curriculum days."""
        return self.days
    
    def total_days(self) -> int:
        """Get total number of curriculum days."""
        return len(self.days)
