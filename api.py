from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chord_analyzer import midiAnalysis
from pydantic import BaseModel

app = FastAPI()

class NotesRequest(BaseModel):
    notes: list[int]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chord-analyzer-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/api/analyze")
def analyze(req: NotesRequest):
    result = midiAnalysis(set(req.notes))
    return {"Chords with roots": result[0], "Chords without roots": result[1]}
