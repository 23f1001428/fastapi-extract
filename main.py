from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()

# ---------- Request ----------
class ExtractRequest(BaseModel):
    text: str

# ---------- Response ----------
class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


# ---------- Extract helpers ----------
def get_vendor(text: str):
    match = re.search(r"([A-Z][A-Za-z0-9\-\s&]+(Ltd\.|Inc\.|Industries|Corp\.|LLC)?)", text)
    return match.group(1).strip() if match else "Unknown"


def get_amount(text: str):
    match = re.search(r"(\d+(\.\d{1,2})?)", text)
    return float(match.group(1)) if match else 0.0


def get_currency(text: str):
    match = re.search(r"\b(USD|EUR|GBP)\b", text.upper())
    return match.group(1) if match else "USD"


def get_date(text: str):
    match = re.search(r"(2026-\d{2}-\d{2})", text)
    return match.group(1) if match else "2026-01-01"


# ---------- API ----------
@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):

    if not req.text or not req.text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    text = req.text

    return ExtractResponse(
        vendor=get_vendor(text),
        amount=get_amount(text),
        currency=get_currency(text),
        date=get_date(text),
    )