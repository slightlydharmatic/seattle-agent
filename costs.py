"""Rough cost per weekly run, from token assumptions and list prices in config.MODEL_PRICES.

An estimate, not a bill: the assumptions are written out so anyone can check them.
"""
import math

from config import MODEL_PRICES

# Per listing page: about 1.5 chunks, each ~5,000 tokens in and ~1,200 out.
PAGE_IN, PAGE_OUT = 7_500, 1_800
# Per curator call (20 events): instructions + examples + events in, a short verdict per event out.
BATCH, CALL_IN_FIXED, EVENT_IN, EVENT_OUT = 20, 2_800, 150, 45


def price(model: str, tok_in: int, tok_out: int) -> float | None:
    p = MODEL_PRICES.get(model)
    return None if p is None else (tok_in * p[0] + tok_out * p[1]) / 1_000_000


def estimate(pages: int, events: int, extract_model: str, curator_model: str) -> dict:
    calls = math.ceil(events / BATCH) if events else 0
    ex_in, ex_out = pages * PAGE_IN, pages * PAGE_OUT
    cu_in, cu_out = calls * CALL_IN_FIXED + events * EVENT_IN, events * EVENT_OUT
    ex, cu = price(extract_model, ex_in, ex_out), price(curator_model, cu_in, cu_out)
    total = None if ex is None or cu is None else ex + cu
    return {"pages": pages, "events": events, "calls": calls,
            "extract": {"model": extract_model, "in": ex_in, "out": ex_out, "usd": ex},
            "curate": {"model": curator_model, "in": cu_in, "out": cu_out, "usd": cu},
            "total": total, "month": None if total is None else total * 4.33,
            "per_event": None if total is None or not events else total / events}
