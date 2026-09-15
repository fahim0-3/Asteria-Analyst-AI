import json
from pathlib import Path


def main() -> None:
    questions = json.loads(Path("evaluation/questions.json").read_text())
    covered = {item["type"] for item in questions}
    unsafe = sum(item.get("expected_safe") is False for item in questions)
    print(json.dumps({"suite": "local deterministic contract evaluation", "questions": len(questions), "categories": len(covered), "explicit_adversarial_cases": unsafe, "note": "This reports suite coverage, not fabricated model accuracy."}, indent=2))


if __name__ == "__main__":
    main()

