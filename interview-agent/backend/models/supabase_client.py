"""
Supabase Database Persistence Client.
Optional cloud persistence layer for storing interview transcripts, candidates, and reports.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    Client = Any


class SupabaseStore:
    """
    Supabase DB Persistence Client.
    Synchronizes candidate profiles, interview turns, and evaluation reports to Supabase SQL Database.
    """

    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        self.enabled = bool(HAS_SUPABASE and self.url and self.key)
        self._client: Optional[Client] = None

        if self.enabled:
            try:
                self._client = create_client(self.url, self.key)
                logger.info("Supabase DB persistence client initialized successfully")
            except Exception as e:
                logger.warning(f"Supabase connection warning: {e}")
                self.enabled = False
        else:
            logger.info("Supabase client initialized in local mode (SUPABASE_URL not configured)")

    async def save_candidate(self, candidate_data: Dict[str, Any]) -> bool:
        """Persist candidate profile to Supabase 'candidates' table."""
        if not self.enabled or not self._client:
            return False
        try:
            self._client.table("candidates").upsert(candidate_data).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase save_candidate error: {e}")
            return False

    async def save_interview_turn(self, interview_id: str, turn_data: Dict[str, Any]) -> bool:
        """Persist interview turn transcript to Supabase 'interview_turns' table."""
        if not self.enabled or not self._client:
            return False
        try:
            payload = {"interview_id": interview_id, **turn_data}
            self._client.table("interview_turns").insert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase save_interview_turn error: {e}")
            return False

    async def save_report(self, interview_id: str, report_data: Dict[str, Any]) -> bool:
        """Persist final evaluation report to Supabase 'evaluation_reports' table."""
        if not self.enabled or not self._client:
            return False
        try:
            payload = {"interview_id": interview_id, **report_data}
            self._client.table("evaluation_reports").upsert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"Supabase save_report error: {e}")
            return False
