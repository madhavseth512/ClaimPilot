"""
Eval accuracy measurement for intent classifier and query router.

Runs all 50 labelled inputs from eval_set.json through the real models
and reports accuracy, per-class breakdown, and each wrong prediction.

Requires: GROQ_API_KEY set in .env

Run:  python tests/run_eval.py
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.intent_classifier import IntentClassifier
from core.query_router import QueryRouter

EVAL_PATH = os.path.join(os.path.dirname(__file__), "eval_set.json")

# ─── Helpers ─────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# Windows CP1252-safe symbols
OK  = "PASS"
FAIL = "FAIL"
ARROW = "->"

def pct(n, total):
    return f"{100 * n / total:.1f}%" if total else "N/A"

def print_header(title):
    print(f"\n{BOLD}{'-' * 60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'-' * 60}{RESET}")


# ─── Intent Classifier Eval ───────────────────────────────────────────────────

def eval_intent_classifier(cases):
    print_header("Intent Classifier Accuracy")
    classifier = IntentClassifier()

    correct = 0
    wrong = []
    per_class = {}

    for case in cases:
        inp      = case["input"]
        expected = case["expected"]

        result     = classifier.classify(inp)
        predicted  = result.get("intent", "unknown")
        confidence = result.get("confidence", 0.0)

        # Track per-class
        per_class.setdefault(expected, {"total": 0, "correct": 0})
        per_class[expected]["total"] += 1

        if predicted == expected:
            correct += 1
            per_class[expected]["correct"] += 1
            status = f"{GREEN}{OK}{RESET}"
        else:
            wrong.append({
                "input": inp, "expected": expected,
                "predicted": predicted, "confidence": confidence,
            })
            status = f"{RED}{FAIL}{RESET}"

        print(f"  {status}  [{confidence:.2f}]  {inp[:55]:<55}  {ARROW} {predicted}")
        time.sleep(0.3)   # avoid Groq rate limit

    total = len(cases)
    print(f"\n{BOLD}Overall: {correct}/{total}  ({pct(correct, total)}){RESET}")

    print(f"\n{BOLD}Per-class breakdown:{RESET}")
    for cls, counts in sorted(per_class.items()):
        c, t = counts["correct"], counts["total"]
        colour = GREEN if c == t else (YELLOW if c / t >= 0.5 else RED)
        print(f"  {colour}{cls:<22}{RESET}  {c}/{t}  ({pct(c, t)})")

    if wrong:
        print(f"\n{BOLD}{RED}Wrong predictions:{RESET}")
        for w in wrong:
            print(f"  Input     : {w['input']}")
            print(f"  Expected  : {w['expected']}")
            print(f"  Predicted : {w['predicted']}  (confidence {w['confidence']:.2f})")
            print()

    return correct, total


# ─── Query Router Eval ────────────────────────────────────────────────────────

def eval_query_router(cases):
    print_header("Query Router Accuracy")
    router = QueryRouter()

    correct = 0
    wrong = []
    per_class = {}

    for case in cases:
        inp      = case["input"]
        expected = case["expected"]

        result     = router.route(inp)
        predicted  = result.get("category", "unknown")
        confidence = result.get("confidence", 0.0)

        per_class.setdefault(expected, {"total": 0, "correct": 0})
        per_class[expected]["total"] += 1

        if predicted == expected:
            correct += 1
            per_class[expected]["correct"] += 1
            status = f"{GREEN}{OK}{RESET}"
        else:
            wrong.append({
                "input": inp, "expected": expected,
                "predicted": predicted, "confidence": confidence,
            })
            status = f"{RED}{FAIL}{RESET}"

        print(f"  {status}  [{confidence:.2f}]  {inp[:55]:<55}  {ARROW} {predicted}")
        time.sleep(0.3)

    total = len(cases)
    print(f"\n{BOLD}Overall: {correct}/{total}  ({pct(correct, total)}){RESET}")

    print(f"\n{BOLD}Per-class breakdown:{RESET}")
    for cls, counts in sorted(per_class.items()):
        c, t = counts["correct"], counts["total"]
        colour = GREEN if c == t else (YELLOW if c / t >= 0.5 else RED)
        print(f"  {colour}{cls:<22}{RESET}  {c}/{t}  ({pct(c, t)})")

    if wrong:
        print(f"\n{BOLD}{RED}Wrong predictions:{RESET}")
        for w in wrong:
            print(f"  Input     : {w['input']}")
            print(f"  Expected  : {w['expected']}")
            print(f"  Predicted : {w['predicted']}  (confidence {w['confidence']:.2f})")
            print()

    return correct, total


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open(EVAL_PATH) as f:
        data = json.load(f)

    ic = eval_intent_classifier(data["intent_classifier"])
    qr = eval_query_router(data["query_router"])

    total_correct = ic[0] + qr[0]
    total_cases   = ic[1] + qr[1]

    print_header("Final Score")
    overall_pct = 100 * total_correct / total_cases
    colour = GREEN if overall_pct >= 85 else (YELLOW if overall_pct >= 70 else RED)
    print(f"  Intent Classifier : {ic[0]}/{ic[1]}  ({pct(*ic)})")
    print(f"  Query Router      : {qr[0]}/{qr[1]}  ({pct(*qr)})")
    print(f"  {colour}{BOLD}Total             : {total_correct}/{total_cases}  ({pct(total_correct, total_cases)}){RESET}")
