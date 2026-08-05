"""CLI for the Crocoblock Smart Ticket Classifier.

Usage:
    python main.py "My JetEngine listing is empty after the update"   # classify one ticket
    python main.py --file ticket.txt                                  # classify a ticket from a file
    python main.py --examples                                         # run the 5 bundled examples
"""

import argparse
import json
import sys
from pathlib import Path

from classifier import classify_ticket, ClassificationResult

EXAMPLES_PATH = Path(__file__).parent / "examples" / "tickets.json"


def _print_one(ticket_id: str, subject: str, result: ClassificationResult) -> None:
    lb = result.label
    header = f"[{ticket_id}] {subject}" if ticket_id else "Result"
    print(f"\n{header}")
    print("-" * len(header))
    print(f"  category   : {lb.category.value}")
    print(f"  priority   : {lb.priority.value}")
    print(f"  plugin     : {lb.plugin.value}")
    print(f"  sentiment  : {lb.sentiment.value}")
    print(f"  confidence : {lb.confidence:.2f}")
    print(f"  reasoning  : {lb.reasoning}")
    print(f"  ({result.model}, {result.latency_ms} ms, "
          f"{result.input_tokens} in / {result.output_tokens} out tokens)")


def run_examples() -> None:
    tickets = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    rows = []
    for t in tickets:
        result = classify_ticket(t["body"])
        _print_one(t["id"], t["subject"], result)
        lb = result.label
        rows.append((t["id"], lb.category.value, lb.priority.value,
                     lb.plugin.value, lb.sentiment.value))

    # Compact summary table.
    print("\nSummary")
    print("=" * 74)
    print(f"{'ID':<9}{'category':<17}{'priority':<10}{'plugin':<20}{'sentiment':<12}")
    print("-" * 74)
    for tid, cat, prio, plug, sent in rows:
        print(f"{tid:<9}{cat:<17}{prio:<10}{plug:<20}{sent:<12}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Crocoblock support tickets.")
    parser.add_argument("text", nargs="?", help="Ticket text to classify")
    parser.add_argument("--file", help="Path to a text file containing the ticket")
    parser.add_argument("--examples", action="store_true",
                        help="Run the 5 bundled real-world examples")
    args = parser.parse_args()

    if args.examples:
        run_examples()
        return

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        parser.error("provide ticket text, --file PATH, or --examples")

    result = classify_ticket(text)
    _print_one("", "", result)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - top-level CLI guard
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
