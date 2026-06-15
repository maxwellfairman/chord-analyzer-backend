import music21
from functools import lru_cache
import pandas as pd
import os
"""for the website, use midiAnalysis
midiAnalysis accepts a set of numbers as input
returns a nested list:

first entry has list of info about 2 best possible chords with roots [[quality, extensions, root, bass], [quality, extensions, root, bass]] 
then second entry has list of 2 best possible chords without roots [[quality, extensions, implied root, bass], [quality, extensions, root, bass]]
If there are not two possible options there will be just one entry. If no options then no entries.
"""
MIN_SCORE = 12
ROOT_BONUS = 2

#scoring matrix is based on how important each interval is for determining chord quality, as well as interactions between intervals
EXPECTED = [
    "1",
    "b3",
    "3",
    "4",
    "b5",
    "5",
    "#5",
    "d7",
    "b7",
    "7",
    "b9",
    "9",
    "#9",
    "11",
    "#11",
    "b13",
    "13"
]
def validate(df):
    if list(df.index) != EXPECTED:
        raise ValueError("Invalid row labels")
    if list(df.columns) != EXPECTED:
        raise ValueError("Invalid column labels")

MATRIX_PATH = os.path.join(os.path.dirname(__file__), "score_matrix.csv")

def load_matrix(path: str):
    df = pd.read_csv(path, index_col=0)
    validate(df)
    df = df.replace(r'^\s*$', 0, regex=True)
    df = df.fillna(0).astype(float).astype(int)
    return df.values.tolist()

scoreMatrix = load_matrix(MATRIX_PATH)





pcToName = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
pitchesToVector = {
        "root": 0,
        "m3": 1,
        "M3": 2,
        "P4": 3,
        "d5": 4,
        "P5": 5,
        "A5": 6,
        "d7": 7,
        "m7": 8,
        "M7": 9,
        "m9": 10,
        "M9": 11,
        "A9": 12,
        "P11": 13,
        "A11": 14,
        "m13": 15,
        "M13": 16
    }
#caching this function since it is expensive and has a specific list of vectors for each pitch class collection
#test all 12 possible roots
#for a possible root, make possible chords into a vector
@lru_cache (maxsize=None)
def vectorsFromPitchesAndRoot(pitches: frozenset[int], root: int) -> list[list[str]]:
    """Takes a set of pitch classes, and a root (input as a pitch class), and returns a list of lists of strings that have possible classifications for 
    intervals with the root of the chord.
    """
    #pitches will only give pitch classes, and no duplicates
    possibilities = {
        0: ["root"],
        1: ["m9"],
        2: ["M9"],
        3: ["m3", "A9"],
        4: ["M3"],
        5: ["P4", "P11"],
        6: ["d5", "A11"],
        7: ["P5"],
        8: ["m13", "A5"],
        9: ["M13", "d7"],
        10: ["m7"],
        11: ["M7"]
    }
    exclusivities = {
    #9ths
    "m9": {"M9"},
    "M9": {"m9", "A9"},
    "A9": {"M9", "P4"},

    # 3rds
    "m3": {"M3", "P4", "A5"},
    "M3": {"m3", "P4"},

    # 4ths/11ths
    "P4": {"m3", "M3", "A5", "d5", "P11", "A11", "A9", "d7"},
    "P11": {"P4", "A5", "d5", "A11"},
    "d5": {"P4", "P11", "A11"},
    "A11": {"P4", "P11", "d5"},

    # 5ths
    "P5": {"A5", "d5", "d7"},
    "A5": {"P5", "P4", "P11", "d5", "m13", "M13", "m3"},

    # 13ths
    "m13": {"M13", "A5"},
    "M13": {"m13", "A5"},
    # 7ths
    "M7": {"m7", "d7"},
    "m7": {"M7", "d7"},
    "d7": {"m13", "M13", "P5", "P4", "m7", "M7"},

    # root has no conflicts
    "root": set()
}
    if len(pitches) == 0:
        return []
    intervals = []
    for pitch in sorted(pitches):
        interval = (pitch - root) % 12
        intervals.append(interval)
    possibleIntervalNames = []
    for interval in intervals:
        if interval in possibilities:
            possibleIntervalNames.append(possibilities[interval])
    def allowed(chord, interval):
        return chord.isdisjoint(exclusivities[interval])
    """
    depth first search: 
    eg. if have  [["root"], ["m3", "M3"], ["P5"], ["b7", "m7"]]
    root -> m3 -> P5 -> b7
                     -> m7
    root -> M3 -> P5 -> b7
                    -> m7
    check for exclusivities in each step so that don't add unnecessary chords
    """
    def depthFirstSearch(index, chord, results):
        if index == len(possibleIntervalNames):
            if len(chord) == len(pitches):
                #only include interval lists that account for all pitches
                results.append(chord.copy())
            return
        for interval in possibleIntervalNames[index]:
            if allowed(chord, interval):
                chord.add(interval)
                depthFirstSearch(index + 1, chord, results)
                chord.remove(interval)
    chords = []
    depthFirstSearch(0, set(), chords)
    vectors = []
    for c in chords:
        vectors.append(chordToVector(c))
    return tuple(tuple(v) for v in vectors)

def chordToVector(intervals: list[str]):
    """Takes list of intervals and returns chord vector
    """
    vector = [0] * len(pitchesToVector.keys())
    for i in intervals:
        vector[pitchesToVector[i]] = 1
    return vector
def vectorToChord(vector: list[int]):
    "takes chord vector and returns list of intervals from the root"
    chord = []
    keys = list(pitchesToVector.keys())
    for i in range(len(vector)):
        if vector[i] == 1:
            chord.append(keys[i])
    return chord
def multMatrices(m1, m2):
    if len(m1[0]) != len(m2):
        raise ValueError("# of columns in m1 different than # of rows in m2")
    m = len(m1)
    p = len(m2[0])
    total = []
    for i in range(m):
        total.append([0]*p)
    for i in range(m):
        for j in range(p):
            #need to take dotproduct of ith row of m and jth column of p
            totalij = 0
            for k in range(len(m2)):
                totalij += m1[i][k] * m2[k][j]
            total[i][j] = totalij
    return total
def transpose(matrix):
    singleRow = not isinstance(matrix[0], list)
    if not singleRow:
        m = len(matrix)
        n = len(matrix[0])
    else:
        m = 1
        n = len(matrix)
    #create nxm matrix
    matrixT = []
    for i in range(n):
        matrixT.append([0] * m)
    for i in range(m):
        for j in range(n):
            if singleRow:
                matrixT[j][i] = matrix[i]
            else:
                matrixT[j][i] = matrix[i][j]
    return matrixT

def scoreChord(intervalVector: list[int]):
    v = vecToColMatrix(intervalVector)        # n x 1
    vT = transpose(v)                         # 1 x n

    Av = multMatrices(scoreMatrix, v)        # n x 1
    vTAv = multMatrices(vT, Av)              # 1 x 1
    return vTAv[0][0]

def vecToColMatrix(vec):
    return [[v] for v in vec]   # n x 1

def chordQuality(iset: set[str]):
    """
    Takes an interval set and returns the quality of the chord. Root not required
    pitchesToVector = {
        "root": 0,
        "m3": 1,
        "M3": 2,
        "P4": 3,
        "d5": 4,
        "P5": 5,
        "A5": 6,
        "d7": 7,
        "m7": 8,
        "M7": 9,
        "m9": 10,
        "M9": 11,
        "A9": 12,
        "P11": 13,
        "A11": 14,
        "m13": 15,
        "M13": 16
    }
    """
    #iset is intervalset

    quality = 'invalid'
    if 'm3' in iset:
        if 'd5' in iset:
            if 'd7' in iset:
                if not ({'P11', 'A11', 'm13', 'M13'} & iset):
                    quality = 'dim7'
            elif 'm7' in iset:
                quality = 'min7'
            elif 'M7' in iset:
                quality = 'minMaj7'
            else:
                if not ({'P11', 'A11', 'm13', 'M13'} & iset):
                    quality = 'dim'
        elif 'm7' in iset:
            quality = 'min7'
        elif 'M7' in iset:
            quality = 'minMaj7'
        elif 'M13' in iset:
            if 'M9' in iset:
                quality = 'min6/9'
            else:
                quality = 'min6'
        else:
            if 'd7' not in iset:
                quality = 'min'
    elif 'M3' in iset:
        if 'm7' in iset:
            quality = '7'
        elif 'M7' in iset:
            quality = 'maj7'
        elif 'd7' in iset:
            quality = 'invalid'
        elif 'A5' in iset:
            quality = 'aug'
        elif 'M13' in iset:
            if 'M9' in iset:
                quality = 'maj6/9'
            elif not ({'A5', 'd5'} & iset):
                quality = 'maj6'
        else: 
            quality = 'maj'
    elif 'P4' in iset:
        if 'm7' in iset:
            quality = '7sus4'
        elif 'M7' in iset:
            quality = 'Maj7sus4'
        else:
            quality = 'sus4'
    return quality
def chordExtensions(iset: set[str]):
    """Takes a set of intervals and returns list of extensions"""
    nameToExtension = {
        "d5": "b5",
        "A5": "#5",
        "m9": "b9",
        "M9": "9",
        "A9": "#9",
        "P11": "11",
        "A11": "#11",
        "m13": "b13",
        "M13": "13"
    }
    extensionOrder = {
        "b5": 0,
        "#5": 1,
        "b9": 2,
        "9": 3,
        "#9": 4,
        "11": 5,
        "#11": 6,
        "b13": 7,
        "13": 8
    }

    extensions = []
    for i in iset:
        if nameToExtension.get(i) != None:
            extensions.append(nameToExtension[i])
    return sorted(extensions, key=lambda x: extensionOrder.get(x,999))
def analyzeChord(testChord: music21.chord.Chord):
    """Analyzes best explanations for a chord and returns the most likely analysis assuming the root is in the chord and the most likely analysis assuming the chord has a rootless voicing.
    Analysis contains lists of [chord vector, quality, extensions, root, bass, score] for the 2 most likely chords with roots and the 2 most likely chords without roots as a 2-item list
    """
    pitchClasses = testChord.pitchClasses
    possibleRootChords = []
    possibleRootlessChords = []
    bass = testChord.bass()
    bassPitchClass = bass.pitchClass
    bassName = pcToName[bassPitchClass]
    for root in range(12):
        vectors = [list(v) for v in vectorsFromPitchesAndRoot(frozenset(pitchClasses), root)]
        for v in vectors:
            chordInts = vectorToChord(v)
            quality = chordQuality(set(chordInts))
            extensions = chordExtensions(set(chordInts))
            base_score = scoreChord(v)
           
            root_bonus = 0
            if(root == bassPitchClass):
                root_bonus = ROOT_BONUS
            score = base_score + root_bonus
            if quality != "invalid" and score > MIN_SCORE:
                if root in pitchClasses:
                    possibleRootChords.append([v, quality, extensions, root, bassName, score])
                else:
                    possibleRootlessChords.append([v, quality, extensions, root, bassName, score])
    possibleRootChords.sort(key = lambda x: x[5], reverse = True)
    possibleRootlessChords.sort(key = lambda x: x[5], reverse = True)
    return [possibleRootChords[:2], possibleRootlessChords[:2]]
        #eventually would be good to decide which root leads to most readable chord (eg. G# vs Ab)
        #will leave out invalid chords as well
def midiToChord(pitches: set[int]) -> music21.chord.Chord:
    "takes set of midi numbers and returns a music21.chord.Chord"
    return music21.chord.Chord(pitches)     
def _clean_extensions(quality: str, extensions: list[str]) -> list[str]:
    exts = extensions.copy()
    remove13 = False
    if quality.endswith("maj6/9") or quality.endswith("min6/9"):
        remove13 = True
        exts.remove("9")
    if quality.endswith("maj6") or quality.endswith("min6"):
        remove13 = True
    if "dim" in quality:
        exts.remove("b5")
        if "13" in exts:
            exts.remove("13")
    if "aug" in quality:
        exts.remove("#5")
    if remove13 and "13" in exts:
        exts.remove("13")
    return exts
def midiAnalysis(pitches: set[int]):
    """Accepts set of midi numbers for the pitches. Returns nested list with first entry describing chords with roots [quality, extensions, root, bass] then same with rootless chords."""
    chord = midiToChord(pitches)
    analysis = analyzeChord(chord)
    webInfo = [[], []]
    
    for idx in range(2):
        for i in analysis[idx]:
            quality, extensions, root, bass = i[1], i[2], pcToName[i[3]], i[4]
            webInfo[idx].append({
                "quality": quality,
                "extensions": _clean_extensions(quality, extensions),
                "root": root,
                "bass": bass
            })
    return webInfo

if __name__ == "__main__":
    #example usage with midi input, returns chord analysis with lists of dictionaries to send to website
    chordMidi = {60, 63, 69}
    analysis = midiAnalysis(chordMidi)
    chord = music21.chord.Chord(chordMidi)
    print(f"Chord {chord.pitchNames}")
    print(f"Possible chords with roots: {analysis[0]}\nPossible rootless chords: {analysis[1]}")
    #stream.show()
