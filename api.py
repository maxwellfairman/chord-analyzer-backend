from fastapi import FastAPI
from chord_analyzer import midiAnalysis
from pydantic import BaseModel

app = FastAPI()

class NotesRequest(BaseModel):
    notes: list[int]

@app.post("/api/analyze")
def analyze(req: NotesRequest):
    result = midiAnalysis(set(req.notes))
    return {"Chords with roots": result[0], "Chords without roots": result[1]}
