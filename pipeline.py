"""The seven-step agent pipeline, wired together with LangGraph."""
from langgraph.graph import END, StateGraph

from agents.curator import curate
from agents.extractor import extract
from agents.normalizer import normalize
from agents.reasoner import reason
from agents.retriever import retrieve
from agents.synthesizer import synthesize
from agents.validator import validate

STEPS = [
    ("retriever", retrieve),
    ("extractor", extract),
    ("normalizer", normalize),
    ("validator", validate),
    ("curator", curate),
    ("reasoner", reason),
    ("synthesizer", synthesize),
]


def build_graph(skip_until: str | None = None, stop_after: str | None = None):
    """Build the graph. skip_until starts partway through; stop_after ends early.

    The app uses both: it fetches pages once (retriever to extractor), then reruns
    the cheap steps (normalizer to synthesizer) whenever settings or custom events change.
    """
    names = [n for n, _ in STEPS]
    start = names.index(skip_until) if skip_until else 0
    end = names.index(stop_after) + 1 if stop_after else len(STEPS)
    steps = STEPS[start:end]

    graph = StateGraph(dict)
    for name, fn in steps:
        graph.add_node(name, fn)
    for (a, _), (b, _) in zip(steps, steps[1:]):
        graph.add_edge(a, b)
    graph.add_edge(steps[-1][0], END)
    graph.set_entry_point(steps[0][0])
    return graph.compile()
