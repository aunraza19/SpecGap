"""
Queue Manager for SpecGap
Manages analysis queue to stay within free tier rate limits.

Features:
- Global lock: Only one analysis runs at a time
- Session-based tracking: One analysis per user
- Queue position & ETA calculation
- Daily quota counter
- Timeout for abandoned analyses
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import threading

from app.core.logging import get_logger

logger = get_logger("queue_manager")


class QueueStatus(str, Enum):
    """Status of a queue entry"""
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class QueueEntry:
    """Represents a single queue entry"""
    id: str
    session_id: str
    created_at: datetime
    status: QueueStatus = QueueStatus.WAITING
    position: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "status": self.status.value,
            "position": self.position,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


@dataclass
class DailyQuota:
    """Tracks daily API usage"""
    date: str  # YYYY-MM-DD
    used: int = 0
    limit: int = 6  # ~6-7 full analyses per day (60 API calls / 9 per analysis)

    def is_exhausted(self) -> bool:
        return self.used >= self.limit

    def remaining(self) -> int:
        return max(0, self.limit - self.used)


class QueueManager:
    """
    Singleton queue manager for analysis requests.

    Ensures:
    - Only one analysis runs at a time (global lock)
    - Each user can only have one pending/active analysis
    - Tracks daily quota
    - Provides queue position and ETA
    """

    _instance = None
    _lock = threading.Lock()

    # Configuration
    ANALYSIS_TIMEOUT_SECONDS = 180  # 3 minutes max per analysis
    ESTIMATED_ANALYSIS_TIME = 90  # ~90 seconds average
    DAILY_QUOTA_LIMIT = 6  # Conservative limit for free tier

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._queue: List[QueueEntry] = []
        self._active_entry: Optional[QueueEntry] = None
        self._completed: Dict[str, QueueEntry] = {}  # entry_id -> entry
        self._session_entries: Dict[str, str] = {}  # session_id -> entry_id
        self._queue_lock = asyncio.Lock()
        self._daily_quota = self._get_or_create_daily_quota()

        logger.info("QueueManager initialized")

    def _get_or_create_daily_quota(self) -> DailyQuota:
        """Get or create daily quota for today"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return DailyQuota(date=today, limit=self.DAILY_QUOTA_LIMIT)

    def _check_reset_daily_quota(self):
        """Reset daily quota if it's a new day"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._daily_quota.date != today:
            logger.info(f"New day detected, resetting quota. Old: {self._daily_quota.date}, New: {today}")
            self._daily_quota = DailyQuota(date=today, limit=self.DAILY_QUOTA_LIMIT)

    def _update_positions(self):
        """Update queue positions for all waiting entries"""
        for i, entry in enumerate(self._queue):
            entry.position = i + 1

    def _cleanup_stale_entries(self):
        """Remove timed-out or stale entries"""
        now = datetime.now(timezone.utc)

        # Check if active entry has timed out
        if self._active_entry:
            if self._active_entry.started_at:
                elapsed = (now - self._active_entry.started_at).total_seconds()
                if elapsed > self.ANALYSIS_TIMEOUT_SECONDS:
                    logger.warning(f"Active entry {self._active_entry.id} timed out after {elapsed:.0f}s")
                    self._active_entry.status = QueueStatus.TIMEOUT
                    self._active_entry.completed_at = now
                    self._active_entry.error_message = "Analysis timed out"
                    self._completed[self._active_entry.id] = self._active_entry

                    # Clean up session mapping
                    if self._active_entry.session_id in self._session_entries:
                        del self._session_entries[self._active_entry.session_id]

                    self._active_entry = None

        # Clean up old completed entries (keep for 5 minutes)
        stale_threshold = now - timedelta(minutes=5)
        stale_ids = [
            eid for eid, entry in self._completed.items()
            if entry.completed_at and entry.completed_at < stale_threshold
        ]
        for eid in stale_ids:
            del self._completed[eid]

    async def enqueue(self, session_id: str) -> QueueEntry:
        """
        Add a new analysis request to the queue.

        Args:
            session_id: Unique session identifier for the user

        Returns:
            QueueEntry with position and status

        Raises:
            ValueError: If session already has a pending/active analysis
            RuntimeError: If daily quota is exhausted
        """
        async with self._queue_lock:
            self._check_reset_daily_quota()
            self._cleanup_stale_entries()

            # Check daily quota
            if self._daily_quota.is_exhausted():
                raise RuntimeError(
                    f"Daily quota exhausted ({self._daily_quota.used}/{self._daily_quota.limit}). "
                    f"Resets at midnight UTC."
                )

            # Check if session already has an active/pending entry
            if session_id in self._session_entries:
                existing_id = self._session_entries[session_id]

                # Check if it's the active entry
                if self._active_entry and self._active_entry.id == existing_id:
                    raise ValueError("You already have an analysis in progress")

                # Check if it's in the queue
                for entry in self._queue:
                    if entry.id == existing_id:
                        raise ValueError(f"You already have an analysis queued at position {entry.position}")

                # Entry was completed/failed, allow new one
                del self._session_entries[session_id]

            # Create new entry
            entry = QueueEntry(
                id=str(uuid.uuid4()),
                session_id=session_id,
                created_at=datetime.now(timezone.utc),
                status=QueueStatus.WAITING,
            )

            self._queue.append(entry)
            self._session_entries[session_id] = entry.id
            self._update_positions()

            logger.info(f"Enqueued {entry.id} for session {session_id}, position {entry.position}")

            return entry

    async def get_next(self) -> Optional[QueueEntry]:
        """
        Get the next entry to process (if no active entry).

        Returns:
            Next QueueEntry or None if queue is empty or busy
        """
        async with self._queue_lock:
            self._cleanup_stale_entries()

            # If there's an active entry, don't start another
            if self._active_entry:
                return None

            # If queue is empty, nothing to do
            if not self._queue:
                return None

            # Get next entry
            entry = self._queue.pop(0)
            entry.status = QueueStatus.PROCESSING
            entry.started_at = datetime.now(timezone.utc)
            entry.position = 0

            self._active_entry = entry
            self._update_positions()

            logger.info(f"Starting processing {entry.id}")

            return entry

    async def complete(self, entry_id: str, success: bool = True, error: Optional[str] = None):
        """
        Mark an entry as completed.

        Args:
            entry_id: ID of the entry to complete
            success: Whether the analysis succeeded
            error: Error message if failed
        """
        async with self._queue_lock:
            if self._active_entry and self._active_entry.id == entry_id:
                self._active_entry.status = QueueStatus.COMPLETED if success else QueueStatus.FAILED
                self._active_entry.completed_at = datetime.now(timezone.utc)
                self._active_entry.error_message = error

                # Increment quota on completion (successful or not, API was called)
                self._daily_quota.used += 1

                self._completed[entry_id] = self._active_entry

                # Clean up session mapping
                if self._active_entry.session_id in self._session_entries:
                    del self._session_entries[self._active_entry.session_id]

                logger.info(
                    f"Completed {entry_id}, success={success}, "
                    f"quota={self._daily_quota.used}/{self._daily_quota.limit}"
                )

                self._active_entry = None

    async def cancel(self, entry_id: str, session_id: str) -> bool:
        """
        Cancel a queued entry.

        Args:
            entry_id: ID of the entry to cancel
            session_id: Session ID (must match)

        Returns:
            True if cancelled, False if not found or not cancellable
        """
        async with self._queue_lock:
            # Can't cancel active entry
            if self._active_entry and self._active_entry.id == entry_id:
                return False

            # Find and remove from queue
            for i, entry in enumerate(self._queue):
                if entry.id == entry_id and entry.session_id == session_id:
                    entry.status = QueueStatus.CANCELLED
                    entry.completed_at = datetime.now(timezone.utc)
                    self._queue.pop(i)
                    self._completed[entry_id] = entry

                    if session_id in self._session_entries:
                        del self._session_entries[session_id]

                    self._update_positions()
                    logger.info(f"Cancelled {entry_id}")
                    return True

            return False

    async def get_status(self, entry_id: str) -> Optional[QueueEntry]:
        """Get status of a specific entry"""
        async with self._queue_lock:
            self._cleanup_stale_entries()

            # Check active
            if self._active_entry and self._active_entry.id == entry_id:
                return self._active_entry

            # Check queue
            for entry in self._queue:
                if entry.id == entry_id:
                    return entry

            # Check completed
            return self._completed.get(entry_id)

    async def get_session_status(self, session_id: str) -> Optional[QueueEntry]:
        """Get status of entry for a specific session"""
        async with self._queue_lock:
            self._cleanup_stale_entries()

            if session_id not in self._session_entries:
                return None

            entry_id = self._session_entries[session_id]
            return await self.get_status(entry_id)

    def get_queue_info(self) -> dict:
        """Get current queue information"""
        self._check_reset_daily_quota()

        return {
            "queue_length": len(self._queue),
            "is_processing": self._active_entry is not None,
            "estimated_wait_seconds": len(self._queue) * self.ESTIMATED_ANALYSIS_TIME,
            "daily_quota": {
                "used": self._daily_quota.used,
                "limit": self._daily_quota.limit,
                "remaining": self._daily_quota.remaining(),
                "is_exhausted": self._daily_quota.is_exhausted(),
                "resets_at": f"{self._daily_quota.date}T24:00:00Z"
            }
        }

    def get_position_eta(self, position: int) -> dict:
        """Calculate estimated wait time for a queue position"""
        if position <= 0:
            return {"wait_seconds": 0, "wait_formatted": "Now"}

        # If something is processing, add remaining time estimate
        base_wait = 0
        if self._active_entry and self._active_entry.started_at:
            elapsed = (datetime.now(timezone.utc) - self._active_entry.started_at).total_seconds()
            remaining = max(0, self.ESTIMATED_ANALYSIS_TIME - elapsed)
            base_wait = remaining

        total_wait = base_wait + (position - 1) * self.ESTIMATED_ANALYSIS_TIME

        minutes = int(total_wait // 60)
        seconds = int(total_wait % 60)

        if minutes > 0:
            formatted = f"{minutes}m {seconds}s"
        else:
            formatted = f"{seconds}s"

        return {
            "wait_seconds": int(total_wait),
            "wait_formatted": formatted
        }


# Global singleton instance
queue_manager = QueueManager()

