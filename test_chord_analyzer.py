#this code for testing was written by Claude
import sys
sys.path.insert(0, '.')
from chord_analyzer import midiAnalysis

pcToName = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
enharmonic = {"G#":"Ab","Ab":"G#","D#":"Eb","Eb":"D#","A#":"Bb","Bb":"A#","C#":"Db","Db":"C#","F#":"Gb","Gb":"F#"}
def names_match(a,b):
    return a == b or enharmonic.get(a) == b

# chord templates: name -> (intervals from root in semitones, expected quality, expected extensions set)
templates = {
    "maj":       ([0,4,7],        "maj",     set()),
    "min":       ([0,3,7],        "min",     set()),
    "dim":       ([0,3,6],        "dim",     set()),
    "aug":       ([0,4,8],        "aug",     set()),
    "sus4":      ([0,5,7],        "sus4",    set()),
    "maj7":      ([0,4,7,11],     "maj7",    set()),
    "dom7":      ([0,4,7,10],     "7",       set()),
    "min7":      ([0,3,7,10],     "min7",    set()),
    "m7b5":      ([0,3,6,10],     "min7",    {"b5"}),
    "dim7":      ([0,3,6,9],      "dim7",    set()),
    "minMaj7":   ([0,3,7,11],     "minMaj7", set()),
    "7sus4":     ([0,5,7,10],     "7sus4",   set()),
    "maj6":      ([0,4,7,9],      "maj6",    set()),
    "min6":      ([0,3,7,9],      "min6",    set()),
    "maj6/9":    ([0,4,7,9,2],    "maj6/9",  set()),
    "min6/9":    ([0,3,7,9,2],    "min6/9",  set()),
    "dom9":      ([0,4,7,10,2],   "7",       {"9"}),
    "maj9":      ([0,4,7,11,2],   "maj7",    {"9"}),
    "min9":      ([0,3,7,10,2],   "min7",    {"9"}),
    "add9":      ([0,4,7,2],      "maj",     {"9"}),
    "7b9":       ([0,4,7,10,1],   "7",       {"b9"}),
    "7#9":       ([0,4,7,10,3],   "7",       {"#9"}),
    "7#11":      ([0,4,7,10,6],   "7",       {"#11"}),
    "maj7#11":   ([0,4,7,11,6],   "maj7",    {"#11"}),
    "13(1,3,b7,13)": ([0,4,10,9], "7",       {"13"}),
    "min7b9":    ([0,3,7,10,1],   "min7",    {"b9"}),
}

def is_match(c, exp_q, exp_ext, exp_root, exp_bass):
    return (c["quality"] == exp_q and set(c["extensions"]) == exp_ext
            and names_match(c["root"], exp_root) and names_match(c["bass"], exp_bass))

results = []
for root_pc in range(12):
    root_name = pcToName[root_pc]
    for tname, (intervals, exp_q, exp_ext) in templates.items():
        pitches = {60 + root_pc + iv for iv in intervals}
        name = f"{root_name} {tname}"
        result = midiAnalysis(pitches)
        candidates = result[0] + result[1]
        top1 = candidates and is_match(candidates[0], exp_q, exp_ext, root_name, root_name)
        top2 = top1 or any(is_match(c, exp_q, exp_ext, root_name, root_name) for c in candidates[:2])
        results.append((name, top1, top2, candidates[0] if candidates else None, exp_q, exp_ext, root_name))

total = len(results)
top1_pass = sum(1 for r in results if r[1])
top2_pass = sum(1 for r in results if r[2])

print(f"Total test chords: {total}")
print(f"Top-1 accuracy: {top1_pass}/{total} ({100*top1_pass/total:.1f}%)")
print(f"Top-2 accuracy: {top2_pass}/{total} ({100*top2_pass/total:.1f}%)")
print()

# breakdown by chord type
print("Accuracy by chord type (top-1):")
from collections import defaultdict
by_type = defaultdict(lambda: [0,0])
for name, top1, top2, top, exp_q, exp_ext, root in results:
    tname = name.split(" ", 1)[1]
    by_type[tname][1] += 1
    if top1:
        by_type[tname][0] += 1
for tname, (p, t) in by_type.items():
    marker = "  <-- issues" if p < t else ""
    print(f"  {tname:20s}: {p}/{t}{marker}")

print()
print("Failures (top-1 miss):")
for name, top1, top2, top, exp_q, exp_ext, root in results:
    if not top1:
        print(f"  {name}: expected quality={exp_q} ext={exp_ext} root={root} | got {top}")
