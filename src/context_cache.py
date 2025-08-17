"""
Intelligent File-based Context Caching System
Optimizes token usage through smart caching and context chaining.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class FileEntry:
    """Represents a cached file with metadata."""
    path: str
    content: str
    mtime: float
    size: int
    content_hash: str
    cached_at: str


@dataclass
class CacheSession:
    """Represents a context session for chaining related prompts."""
    session_id: str
    created_at: str
    last_used: str
    goal_context: str  # Original goal for context matching
    file_count: int
    files: Dict[str, FileEntry]


class ContextCache:
    """Smart caching system for context files with change detection."""
    
    def __init__(self, cache_dir: str = ".ai_agents_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.cache_file = self.cache_dir / "context_cache.json"
        self.sessions_file = self.cache_dir / "sessions.json"
        
        # Configuration
        self.max_files_per_session = 40
        self.max_sessions = 10
        self.session_timeout_hours = 24
        
        # Load existing cache
        self.sessions: Dict[str, CacheSession] = self._load_sessions()
        self.current_session_id: Optional[str] = None
        
    def _load_sessions(self) -> Dict[str, CacheSession]:
        """Load existing cache sessions from disk."""
        if not self.sessions_file.exists():
            return {}
            
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    sid: CacheSession(**session_data) 
                    for sid, session_data in data.items()
                }
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to load cache sessions: {e}")
            return {}
    
    def _save_sessions(self):
        """Save cache sessions to disk."""
        try:
            data = {
                sid: asdict(session) 
                for sid, session in self.sessions.items()
            }
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save cache sessions: {e}")
    
    def _cleanup_old_sessions(self):
        """Remove old or expired sessions."""
        current_time = time.time()
        timeout_seconds = self.session_timeout_hours * 3600
        
        expired_sessions = []
        for sid, session in self.sessions.items():
            last_used_time = datetime.fromisoformat(session.last_used).timestamp()
            if current_time - last_used_time > timeout_seconds:
                expired_sessions.append(sid)
        
        for sid in expired_sessions:
            del self.sessions[sid]
            logger.info(f"Removed expired session: {sid}")
        
        # Keep only the most recent sessions
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_used,
                reverse=True
            )
            self.sessions = dict(sorted_sessions[:self.max_sessions])
            logger.info(f"Kept {self.max_sessions} most recent sessions")
    
    def _generate_session_id(self, goal: str, file_specs: List[str]) -> str:
        """Generate a session ID based on goal and file specifications."""
        # Create a deterministic ID based on goal context and file patterns
        context_key = f"{goal}|{'|'.join(sorted(file_specs))}"
        return hashlib.md5(context_key.encode()).hexdigest()[:12]
    
    def _get_file_metadata(self, file_path: Path) -> Tuple[float, int, str]:
        """Get file modification time, size, and content hash."""
        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            
            # Generate content hash for change detection
            with open(file_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()[:16]
                
            return mtime, size, content_hash
        except Exception:
            return 0.0, 0, ""
    
    def _has_file_changed(self, file_path: Path, cached_entry: FileEntry) -> bool:
        """Check if a file has changed since it was cached."""
        if not file_path.exists():
            return True
            
        mtime, size, content_hash = self._get_file_metadata(file_path)
        
        return (
            mtime != cached_entry.mtime or
            size != cached_entry.size or
            content_hash != cached_entry.content_hash
        )
    
    def find_or_create_session(self, goal: str, file_specs: List[str]) -> str:
        """Find existing session or create new one for context chaining."""
        session_id = self._generate_session_id(goal, file_specs)
        
        # Check if session exists and is still valid
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_used = datetime.now().isoformat()
            logger.info(f"Reusing existing session: {session_id}")
        else:
            # Create new session
            session = CacheSession(
                session_id=session_id,
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                goal_context=goal[:100],  # Store truncated goal for reference
                file_count=0,
                files={}
            )
            self.sessions[session_id] = session
            logger.info(f"Created new session: {session_id}")
        
        self.current_session_id = session_id
        self._cleanup_old_sessions()
        return session_id
    
    def get_cached_context(self, repo_path: str, file_specs: List[str], goal: str) -> Optional[str]:
        """Get cached context if available and files haven't changed."""
        session_id = self.find_or_create_session(goal, file_specs)
        session = self.sessions[session_id]
        
        # Expand file specifications to actual files
        from .context import expand_context_specs
        actual_files = expand_context_specs(repo_path, file_specs, limit=self.max_files_per_session)
        
        # Check if we have all files cached and they haven't changed
        root = Path(repo_path)
        cache_valid = True
        missing_files = []
        changed_files = []
        
        for file_path in actual_files:
            abs_path = root / file_path
            
            if file_path not in session.files:
                missing_files.append(file_path)
                cache_valid = False
            elif self._has_file_changed(abs_path, session.files[file_path]):
                changed_files.append(file_path)
                cache_valid = False
        
        if cache_valid and session.files:
            logger.info(f"Cache hit: {len(session.files)} files, session {session_id}")
            console.print(f"[green]📦 Cache hit: {len(session.files)} files loaded from cache[/green]")
            
            # Reconstruct context from cache
            context_parts = []
            for file_path in actual_files:
                if file_path in session.files:
                    entry = session.files[file_path]
                    context_parts.append(f"=== FILE: {entry.path} ===\n{entry.content}\n")
            
            return "\n".join(context_parts)
        
        # Cache miss or invalid
        if missing_files:
            logger.info(f"Cache miss: {len(missing_files)} new files")
        if changed_files:
            logger.info(f"Cache invalidated: {len(changed_files)} changed files")
            
        return None
    
    def cache_context(self, repo_path: str, file_specs: List[str], goal: str, context_content: str):
        """Cache the context content with file metadata."""
        if not self.current_session_id:
            session_id = self.find_or_create_session(goal, file_specs)
        else:
            session_id = self.current_session_id
            
        session = self.sessions[session_id]
        
        # Expand file specifications
        from .context import expand_context_specs
        actual_files = expand_context_specs(repo_path, file_specs, limit=self.max_files_per_session)
        
        # Check file count limit
        if len(actual_files) > self.max_files_per_session:
            console.print(f"[yellow]⚠️ Warning: {len(actual_files)} files exceed cache limit of {self.max_files_per_session}[/yellow]")
            console.print(f"[yellow]Consider using more specific file patterns to reduce token usage[/yellow]")
            actual_files = actual_files[:self.max_files_per_session]
        
        # Cache each file with metadata
        root = Path(repo_path)
        cached_files = {}
        
        for file_path in actual_files:
            abs_path = root / file_path
            
            if abs_path.exists() and abs_path.is_file():
                try:
                    mtime, size, content_hash = self._get_file_metadata(abs_path)
                    
                    # Extract content from context_content
                    file_marker = f"=== FILE: {file_path} ==="
                    if file_marker in context_content:
                        start_idx = context_content.find(file_marker)
                        end_idx = context_content.find("=== FILE:", start_idx + 1)
                        if end_idx == -1:
                            file_content = context_content[start_idx + len(file_marker):].strip()
                        else:
                            file_content = context_content[start_idx + len(file_marker):end_idx].strip()
                        
                        cached_files[file_path] = FileEntry(
                            path=file_path,
                            content=file_content,
                            mtime=mtime,
                            size=size,
                            content_hash=content_hash,
                            cached_at=datetime.now().isoformat()
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to cache file {file_path}: {e}")
        
        # Update session
        session.files = cached_files
        session.file_count = len(cached_files)
        session.last_used = datetime.now().isoformat()
        
        self._save_sessions()
        
        logger.info(f"Cached {len(cached_files)} files in session {session_id}")
        console.print(f"[blue]💾 Cached {len(cached_files)} files for future use[/blue]")
    
    def reset_cache(self, session_id: Optional[str] = None):
        """Reset cache for specific session or all sessions."""
        if session_id:
            if session_id in self.sessions:
                del self.sessions[session_id]
                console.print(f"[yellow]🗑️ Reset cache for session {session_id}[/yellow]")
            else:
                console.print(f"[red]Session {session_id} not found[/red]")
        else:
            self.sessions.clear()
            self.current_session_id = None
            console.print("[yellow]🗑️ Reset all cache sessions[/yellow]")
        
        self._save_sessions()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_files = sum(session.file_count for session in self.sessions.values())
        
        return {
            "sessions": len(self.sessions),
            "total_files": total_files,
            "current_session": self.current_session_id,
            "max_files_per_session": self.max_files_per_session,
            "session_timeout_hours": self.session_timeout_hours
        }
    
    def list_sessions(self):
        """List all cache sessions with details."""
        if not self.sessions:
            console.print("[yellow]No cache sessions found[/yellow]")
            return
        
        console.print("\n[bold cyan]📦 Cache Sessions:[/bold cyan]")
        for sid, session in self.sessions.items():
            age_hours = (datetime.now() - datetime.fromisoformat(session.created_at)).total_seconds() / 3600
            status = "🟢 Active" if sid == self.current_session_id else "⚪ Inactive"
            
            console.print(f"  {status} [bold]{sid}[/bold] ({session.file_count} files, {age_hours:.1f}h old)")
            console.print(f"    Goal: {session.goal_context}")
            console.print(f"    Last used: {session.last_used}")
            console.print()
