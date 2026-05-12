from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "topic_detect",
    ROOT / "__init__.py",
    submodule_search_locations=[str(ROOT)],
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["topic_detect"] = mod
spec.loader.exec_module(mod)

suffix = mod._transform_llm_output(
    "",
    model="gpt-5.5",
    provider="openai-codex",
    _arc_finalize={
        "topic": "general",
        "routed_model": "gpt-5.5",
        "routed_provider": "openai-codex",
    },
)
assert suffix == "- gpt-5.5 [general]", suffix

fallback_suffix = mod._transform_llm_output(
    "",
    model="google/gemini-3-flash",
    provider="openrouter",
    _arc_finalize={
        "topic": "software_it",
        "routed_model": "nvidia/nemotron-3-super-120b-a12b:free",
        "routed_provider": "openrouter",
    },
)
assert fallback_suffix == "- gemini-3-flash [software_it | routed: nemotron-3-super-120b-a12b]", fallback_suffix

print("PASS | _arc_finalize renders final ARC signature")
