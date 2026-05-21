import os, re
from datetime import date

def extract(file_path):
    text = _read_text(file_path)
    if not text:
        return _empty(error='Could not read file')

    amount_cents = _extract_amount(text)
    dt           = _extract_date(text)
    merchant     = _extract_merchant(text)
    confidence   = _confidence(amount_cents, dt, merchant)

    return {
        'raw_text':     text,
        'merchant':     merchant,
        'amount':       round(amount_cents/100, 2) if amount_cents else None,
        'amount_cents': amount_cents,
        'date':         dt.isoformat() if dt else None,
        'confidence':   confidence,
        'fields': {
            'amount_found':   amount_cents is not None,
            'date_found':     dt is not None,
            'merchant_found': merchant is not None,
        }
    }

def _read_text(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.pdf':
            return _pdf_text(path)
        else:
            return _image_text(path)
    except Exception as e:
        return ''

def _image_text(path):
    try:
        import pytesseract
        from PIL import Image
        cmd = os.getenv('TESSERACT_CMD')
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        return pytesseract.image_to_string(Image.open(path))
    except Exception:
        return ''

def _pdf_text(path):
    try:
        import fitz  # PyMuPDF optional
        doc  = fitz.open(path)
        return '\n'.join(p.get_text() for p in doc)
    except Exception:
        return _image_text(path)

AMOUNT_RE = [
    r'(?:total|amount|grand total)[^\d]*([\d,]+\.\d{2})',
    r'₹\s*([\d,]+\.\d{2})',
    r'([\d,]+\.\d{2})',
]

DATE_RE = [
    r'\d{4}-\d{2}-\d{2}',
    r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}',
]

def _extract_amount(text):
    for pattern in AMOUNT_RE:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = int(round(float(m.group(1).replace(',', '')) * 100))
            if val > 0:
                return val
    return None

def _extract_date(text):
    for pattern in DATE_RE:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                from dateutil import parser as dp
                return dp.parse(m.group(0)).date()
            except Exception:
                continue
    return None

def _extract_merchant(text):
    lines = [l.strip() for l in text.splitlines()
             if l.strip() and not l.strip()[0].isdigit() and len(l.strip()) >= 3]
    return lines[0][:60] if lines else None

def _confidence(amount, dt, merchant):
    score = 0.0
    if amount: score += 0.5
    if dt:     score += 0.3
    if merchant: score += 0.2
    return round(score, 2)

def _empty(error=None):
    return {'raw_text':'','merchant':None,'amount':None,'amount_cents':None,
            'date':None,'confidence':0.0,'error':error,
            'fields':{'amount_found':False,'date_found':False,'merchant_found':False}}
