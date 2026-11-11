import json
from collections import defaultdict
from src.ambiguity import detect

CASES = json.load(open("data/ambiguity_cases.json"))

def ratio(a, b):
    return f"{a}/{b}" + (f" = {a / b:.0%}" if b else "")

tp = fp = fn = tn = 0
per_slice = defaultdict(lambda: [0, 0])      # slice -> [flagged, total]
wrong = []
for c in CASES:
    flagged = detect(c["question"])["status"] == "ambiguous"
    truth = c["is_ambiguous"]
    per_slice[c["slice"]][0] += flagged
    per_slice[c["slice"]][1] += 1
    tp += flagged and truth
    fp += flagged and not truth
    fn += (not flagged) and truth
    tn += (not flagged) and not truth
    if flagged != truth:
        wrong.append((c["id"], c["slice"], "FALSE CLARIFY" if flagged else "MISSED", c["question"]))

print(f"Cases: {len(CASES)}")
print(f"Clarification precision : {ratio(tp, tp + fp)}")
print(f"Clarification recall    : {ratio(tp, tp + fn)}")
print(f"False-clarify rate      : {ratio(fp, fp + tn)}")
print("\nFlagged per slice (A,D should be high; B,C should be 0):")
for s in sorted(per_slice):
    print(f"  Slice {s}: {ratio(*per_slice[s])}")
print("\nErrors:")
for e in wrong:
    print(f"  [{e[0]}] slice {e[1]} {e[2]}: {e[3]}")