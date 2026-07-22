import argparse, json
from pathlib import Path
from hospital_ai.evaluation.benchmark import generate_benchmark, validate_benchmark

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, default=20260722); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    cases = generate_benchmark(seed=args.seed); result = validate_benchmark(cases)
    if not result.valid: raise SystemExit("; ".join(result.errors))
    if args.write:
        root = Path(__file__).parents[1] / "data"; root.mkdir(exist_ok=True)
        (root / "rag_value_benchmark_v1.jsonl").write_text("".join(c.json() + "\n" for c in cases), encoding="utf-8")
        (root / "rag_value_sentinel_v1.jsonl").write_text("".join(c.json() + "\n" for c in cases[:50]), encoding="utf-8")
    print(f"{len(cases)} benchmark cases validated")
if __name__ == "__main__": main()
