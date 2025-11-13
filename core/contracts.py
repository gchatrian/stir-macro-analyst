# core/contracts.py

def normalize_ticker(ticker: str) -> str:
    ticker = ticker.upper().strip()
    if " COMDTY" not in ticker and " COMB " not in ticker:
        if not any(x in ticker for x in ["COMDTY", "COMB"]):
            ticker = f"{ticker} Comdty"
    return ticker


def infer_currency(ticker: str) -> str:
    ticker = ticker.upper().strip()
    prefix = ticker[:3]
    
    if prefix.startswith("SFR"):
        return "USD"
    elif prefix.startswith("ER"):
        return "EUR"
    elif prefix.startswith("SFI"):
        return "GBP"
    else:
        raise ValueError(f"Cannot infer currency from ticker {ticker}")


def parse_contract_code(ticker: str) -> tuple:
    ticker = ticker.upper().strip()
    
    month_map = {
        'F': 'January', 'G': 'February', 'H': 'March',
        'J': 'April', 'K': 'May', 'M': 'June',
        'N': 'July', 'Q': 'August', 'U': 'September',
        'V': 'October', 'X': 'November', 'Z': 'December'
    }
    
    if len(ticker) >= 5:
        month_code = ticker[3]
        year_digit = ticker[4]
        
        month_name = month_map.get(month_code, 'Unknown')
        year = f"202{year_digit}"
        
        return (month_name, year)
    
    return ('Unknown', 'Unknown')