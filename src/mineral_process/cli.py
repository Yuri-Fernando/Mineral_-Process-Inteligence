"""Command-line source of truth."""

from __future__ import annotations

import argparse
import json

from mineral_process.case_studies import run_geomet_case, run_polymetallic_case
from mineral_process.control.benchmark import benchmark_controllers
from mineral_process.data.datasets import download_all
from mineral_process.optimization.advanced import run_advanced_optimization
from mineral_process.pipeline import run_end_to_end


def main() -> None:
    parser = argparse.ArgumentParser(prog="mpi", description="Mineral Process Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("download-data", help="download public datasets and write checksums")
    demo = subparsers.add_parser("run-demo", help="run the free synthetic end-to-end flow")
    demo.add_argument("--seed", type=int, default=42)
    real = subparsers.add_parser("run-real-cases", help="run GeoMet and polymetallic case studies")
    real.add_argument("--seed", type=int, default=42)
    benchmark = subparsers.add_parser("benchmark-control", help="compare controllers in the twin")
    benchmark.add_argument("--seed", type=int, default=42)
    advanced = subparsers.add_parser(
        "advanced-optimize", help="run Gaussian-Process Bayesian optimization and NSGA-II"
    )
    advanced.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.command == "download-data":
        records, failures = download_all()
        print(json.dumps({"downloaded": len(records), "failures": failures}, indent=2))
    elif args.command == "run-demo":
        print(json.dumps(run_end_to_end(seed=args.seed), indent=2, default=str))
    elif args.command == "run-real-cases":
        summaries = {
            "geomet": run_geomet_case(seed=args.seed),
            "polymetallic": run_polymetallic_case(seed=args.seed),
        }
        print(json.dumps(summaries, indent=2, default=str))
    elif args.command == "benchmark-control":
        _, metrics = benchmark_controllers(seed=args.seed)
        print(metrics.to_json(orient="records", indent=2))
    else:
        print(json.dumps(run_advanced_optimization(seed=args.seed), indent=2, default=str))


if __name__ == "__main__":
    main()
