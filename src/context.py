import pathlib
import glob
import logging

logger = logging.getLogger(__name__)

ALLOW_EXT = {".svelte",".ts",".tsx",".js",".jsx",".md",".css",".scss",".py"}

def read_small_file(path: pathlib.Path, max_bytes: int = 200000) -> str:
    data = path.read_bytes()
    if len(data) > max_bytes:
        return data[:max_bytes].decode('utf-8', errors='ignore') + "\n/* ...truncated... */\n"
    return data.decode('utf-8', errors='ignore')

def expand_context_specs(repo_path: str, specs: list[str], limit: int = 12) -> list[str]:
    """Expand file/directory/glob specifications to actual file paths."""
    root = pathlib.Path(repo_path)
    files = set()
    
    for spec in specs:
        abs_spec = root / spec
        
        # Direct file
        if abs_spec.is_file():
            files.add(spec)
        # Directory - get all allowed files
        elif abs_spec.is_dir():
            for ext in ALLOW_EXT:
                files.update(str(p.relative_to(root)) for p in abs_spec.rglob(f"*{ext}"))
        # Glob pattern
        else:
            pattern_files = glob.glob(str(abs_spec), recursive=True)
            files.update(str(pathlib.Path(f).relative_to(root)) for f in pattern_files if pathlib.Path(f).is_file())
    
    return list(files)[:limit]

def collect_context(repo_path: str, file_list: list[str], goal: str = "", use_cache: bool = True) -> str:
    """Collect context with intelligent caching support."""
    if not use_cache or not goal:
        # Fallback to direct collection
        return _collect_context_direct(repo_path, file_list)
    
    # Try to get from cache first
    from .context_cache import ContextCache
    cache = ContextCache()
    
    cached_context = cache.get_cached_context(repo_path, file_list, goal)
    if cached_context:
        return cached_context
    
    # Cache miss - collect context and cache it
    context = _collect_context_direct(repo_path, file_list)
    if context:  # Only cache if we got content
        cache.cache_context(repo_path, file_list, goal, context)
    
    return context

def _collect_context_direct(repo_path: str, file_list: list[str]) -> str:
    """Direct context collection without caching."""
    root = pathlib.Path(repo_path)
    expanded_files = expand_context_specs(repo_path, file_list)
    buf = []
    
    logger.info(f"Collecting context from {len(expanded_files)} files")
    
    for rel in expanded_files:
        p = (root / rel).resolve()
        if not p.exists() or not p.is_file():
            continue
        if p.suffix.lower() not in ALLOW_EXT:
            continue
        content = read_small_file(p)
        buf.append(f"=== FILE: {rel} ===\n{content}\n")
    
    return "\n".join(buf)
