from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Kalkulator API")

class Operacja(BaseModel):
    a: float
    b: float

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/dodaj")
def dodaj(op: Operacja):
    return {"wynik": op.a + op.b}

@app.post("/odejmij")
def odejmij(op: Operacja):
    return {"wynik": op.a - op.b}

@app.post("/mnoz")
def mnoz(op: Operacja):
    return {"wynik": op.a * op.b}

@app.post("/dziel")
def dziel(op: Operacja):
    if op.b == 0:
        raise HTTPException(status_code=400, detail="Dzielenie przez zero")
    return {"wynik": op.a / op.b}