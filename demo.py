"""Run steps 3 to 6 on sample events, with no API keys. Good for showing how it works.

    python demo.py
"""
from config import OUTPUT_DIR
from pipeline import build_graph
from tests.sample_events import sample_state

if __name__ == "__main__":
    result = build_graph(skip_until="normalizer").invoke(sample_state(output_dir=OUTPUT_DIR / "demo"))
    print(result["report"])
    print(f"\nSheet rows saved to {result['csv_path']}")
