"""
ZeroNoiseBench Evaluator
Usage:
    python evaluate.py --responses results/model_responses.json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_tasks(tasks_dir: Path) -> dict:
    """Load all task JSONs from the tasks directory and return a lookup dict {id: task}."""
    tasks = {}
    if not tasks_dir.exists():
        print(f"[WARNING] Tasks directory not found: {tasks_dir}", file=sys.stderr)
        return tasks

    for task_file in tasks_dir.glob("*.json"):
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Support both a single task dict and a list of tasks in one file
            if isinstance(data, list):
                for task in data:
                    if "id" in task:
                        tasks[task["id"]] = task
            elif isinstance(data, dict) and "id" in data:
                tasks[data["id"]] = data
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARNING] Could not load {task_file}: {e}", file=sys.stderr)

    return tasks


def score_response(task: dict, model_response: str) -> bool:
    """Return True if the model_response passes for the given task."""
    eval_type = task.get("eval_type", "exact")
    expected = task.get("expected_output", "")

    if eval_type == "exact":
        return model_response.strip() == expected
    elif eval_type == "extract":
        return expected.lower() in model_response.lower()
    else:
        # Unknown eval_type: fall back to exact
        return model_response.strip() == expected


def evaluate(responses_path: Path) -> None:
    # Resolve paths relative to the responses file
    responses_path = responses_path.resolve()
    tasks_dir = responses_path.parent.parent / "tasks"

    # Load tasks
    tasks = load_tasks(tasks_dir)
    if not tasks:
        print("[ERROR] No tasks loaded. Check that ../tasks/*.json files exist.", file=sys.stderr)
        sys.exit(1)

    # Load model responses
    try:
        with open(responses_path, "r", encoding="utf-8") as f:
            responses = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR] Could not load responses file: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(responses, list):
        print("[ERROR] Responses file must be a JSON array.", file=sys.stderr)
        sys.exit(1)

    # Score each response
    results = []
    category_stats: dict[str, dict] = {}  # category -> {total, correct}

    for entry in responses:
        task_id = entry.get("id", "")
        model_response = entry.get("model_response", "")

        if task_id not in tasks:
            result = {
                "id": task_id,
                "category": "unknown",
                "difficulty": "unknown",
                "pass": False,
                "reason": "Task ID not found in task definitions",
                "expected": None,
                "model_response": model_response,
            }
        else:
            task = tasks[task_id]
            passed = score_response(task, model_response)
            category = task.get("category", "unknown")
            difficulty = task.get("difficulty", "unknown")

            result = {
                "id": task_id,
                "category": category,
                "difficulty": difficulty,
                "pass": passed,
                "reason": "ok" if passed else "mismatch",
                "expected": task.get("expected_output"),
                "model_response": model_response,
            }

        results.append(result)

        cat = result["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0}
        category_stats[cat]["total"] += 1
        if result["pass"]:
            category_stats[cat]["correct"] += 1

    # ------------------------------------------------------------------ #
    # Print results table
    # ------------------------------------------------------------------ #
    col_id = max(len("Task ID"), max((len(r["id"]) for r in results), default=0))
    col_cat = max(len("Category"), max((len(r["category"]) for r in results), default=0))
    col_diff = max(len("Diff"), max((len(r["difficulty"]) for r in results), default=0))

    header = (
        f"{'Task ID':<{col_id}}  "
        f"{'Category':<{col_cat}}  "
        f"{'Diff':<{col_diff}}  "
        f"{'Pass':<5}  "
        f"Notes"
    )
    separator = "-" * len(header)

    print()
    print("=" * len(header))
    print("ZeroNoiseBench Evaluation Results")
    print("=" * len(header))
    print(header)
    print(separator)

    for r in results:
        pass_str = "PASS" if r["pass"] else "FAIL"
        notes = r["reason"] if r["pass"] else f"expected: {r['expected']!r}"
        print(
            f"{r['id']:<{col_id}}  "
            f"{r['category']:<{col_cat}}  "
            f"{r['difficulty']:<{col_diff}}  "
            f"{pass_str:<5}  "
            f"{notes}"
        )

    print(separator)

    # ------------------------------------------------------------------ #
    # Per-category summary
    # ------------------------------------------------------------------ #
    print()
    print("Per-Category Accuracy:")
    print("-" * 40)
    col_cat2 = max(len("Category"), max((len(c) for c in category_stats), default=0))
    for cat in sorted(category_stats):
        stats = category_stats[cat]
        pct = 100.0 * stats["correct"] / stats["total"] if stats["total"] else 0.0
        print(f"  {cat:<{col_cat2}}  {stats['correct']:>3}/{stats['total']:<3}  ({pct:5.1f}%)")

    # ------------------------------------------------------------------ #
    # Overall summary
    # ------------------------------------------------------------------ #
    total = len(results)
    correct = sum(1 for r in results if r["pass"])
    overall_pct = 100.0 * correct / total if total else 0.0

    print()
    print(f"Overall Accuracy: {correct}/{total}  ({overall_pct:.1f}%)")
    print()

    # ------------------------------------------------------------------ #
    # Save scored results JSON
    # ------------------------------------------------------------------ #
    stem = responses_path.stem
    scored_path = responses_path.parent / f"{stem}_scored.json"
    output = {
        "responses_file": str(responses_path),
        "total": total,
        "correct": correct,
        "overall_accuracy_pct": round(overall_pct, 2),
        "per_category": {
            cat: {
                "correct": s["correct"],
                "total": s["total"],
                "accuracy_pct": round(100.0 * s["correct"] / s["total"], 2) if s["total"] else 0.0,
            }
            for cat, s in sorted(category_stats.items())
        },
        "results": results,
    }

    with open(scored_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Scored results saved to: {scored_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ZeroNoiseBench evaluator — scores model responses against expected outputs."
    )
    parser.add_argument(
        "--responses",
        required=True,
        type=Path,
        help="Path to the model responses JSON file (list of {id, model_response}).",
    )
    args = parser.parse_args()
    evaluate(args.responses)


if __name__ == "__main__":
    main()
