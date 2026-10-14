"""Use the packaged skill's canonical Windows process ownership helper."""
from importlib.util import module_from_spec, spec_from_file_location

from runner.filesystem import SKILL_ROOT

_spec = spec_from_file_location("book_genesis_windows_job", SKILL_ROOT / "scripts/windows_job.py")
if _spec is None or _spec.loader is None:
    raise ImportError("The packaged Windows process ownership helper is missing")
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

CREATE_SUSPENDED = _module.CREATE_SUSPENDED
WindowsJob = _module.WindowsJob
