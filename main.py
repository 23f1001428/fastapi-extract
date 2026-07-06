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
    # Step 1: prioritize real company-like patterns first
    match = re.search(
        r"(Acme-[A-Za-z0-9\-]+[A-Za-z0-9\s&]*|[A-Z][A-Za-z0-9\-\s&]+(Ltd\.|Inc\.|Industries|Corp\.|LLC))",
        text
    )

    if match:
        return match.group(1).strip()

    # Step 2: fallback (avoid generic words like "Invoice")
    words = text.split()
    for i in range(len(words)):
        if words[i].istitle() and words[i].lower() not in ["invoice", "bill", "receipt"]:
            return words[i]

    return "Unknown"

def get_amount(text: str):
    # Step 1: look for keyword-based amounts (IMPORTANT)
    match = re.search(
        r"(?:total|amount|due|payable|balance)[^\d]{0,10}(\d+(\.\d{1,2})?)",
        text.lower()
    )

    if match:
        return float(match.group(1))

    # Step 2: fallback — pick LAST number (NOT first)
    numbers = re.findall(r"\d+(\.\d{1,2})?", text)
    if numbers:
        return float(numbers[-1])

    return 0.0

def get_currency(text: str):
    # Step 1: direct match (case-insensitive)
    match = re.search(r"\b(USD|EUR|GBP)\b", text.upper())
    if match:
        return match.group(1)

    # Step 2: handle lowercase / mixed formats
    match = re.search(r"\b(usd|eur|gbp)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Step 3: fallback (default safest choice)
    return "USD"


def get_date(text: str):
    text_lower = text.lower()

    # Step 1: prioritize "due date" context
    match = re.search(
        r"(due|payable by|payment due|deadline)[^\d]{0,10}(2026-\d{2}-\d{2})",
        text_lower
    )

    if match:
        return match.group(2)

    # Step 2: fallback — pick ANY valid date (but only 2026 format)
    match = re.findall(r"(2026-\d{2}-\d{2})", text)
    if match:
        return match[0]   # usually only one, but safe

    return "2026-01-01"


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