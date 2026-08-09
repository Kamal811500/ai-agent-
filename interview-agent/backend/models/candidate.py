"""Candidate model and repository."""
import json
from typing import List, Optional
from pathlib import Path

class Candidate:
    """Represents a candidate."""
    def __init__(self, id: str, name: str, level: str):
        self.id = id
        self.name = name
        self.level = level

class CandidateRepository:
    """Repository for managing candidates."""
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.candidates = []
        self._load()
    
    def _load(self):
        """Load candidates from file."""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.candidates = [Candidate(**c) for c in data]
        except Exception:
            self.candidates = []
    
    def list_all(self) -> List[Candidate]:
        """List all candidates."""
        return self.candidates
    
    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID."""
        return next((c for c in self.candidates if c.id == candidate_id), None)
