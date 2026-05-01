import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)


# 🔥 SAFE FLOAT HANDLER
def safe_float(x):
    try:
        if x in ("", None):
            return None
        return float(x)
    except:
        return None


# 🔥 ETF-SPECIFIC CONFIG
ETF_CONFIG = {
    "MOM100": {"dip3": 6, "dip6": 12, "rsi_low": 45, "rsi_high": 60},
    "HDFCSML250": {"dip3": 8, "dip6": 15, "rsi_low": 40, "rsi_high": 55},
    "CPSEETF": {"dip3": 7, "dip6": 14, "rsi_low": 40, "rsi_high": 55},
    "JUNIORBEES": {"dip3": 5, "dip6": 10, "rsi_low": 40, "rsi_high": 55},
    "GOLDBEES": {"dip3": 4, "dip6": 8, "rsi_low": 35, "rsi_high": 50},
    "SILVERBEES": {"dip3": 6, "dip6": 12, "rsi_low": 40, "rsi_high": 55},
    "MON100": {"dip3": 5, "dip6": 10, "rsi_low": 40, "rsi_high": 55}
}


def run():
    client = get_client()
    ss = client.open("PortfolioAutomation")

    hist = ss.worksheet("ETF_Historical").get_all_values()
    sig = ss.worksheet("ETF_Signals")

    try:
        buy = ss.worksheet("ETF_BuyHistory")
    except:
        buy = ss.add_worksheet(title="ETF_BuyHistory", rows=1000, cols=10)
        buy.append_row(["Date","ETF","Price","Score","Reason"])

    sig.clear()
    sig.append_row(["Date","ETF","Action","Score","Price","RSI","EMA100","Dip%","Reason"])

    today = datetime.now().strftime("%Y-%m-%d")

    for c in range(1, len(hist[0]), 12):

        etf = hist[0][c]

        config = ETF_CONFIG.get(etf, {"dip3":5, "dip6":10, "rsi_low":40, "rsi_high":55})

        close = safe_float(hist[-1][c])
        rsi = safe_float(hist[-1][c+1])
        ema100 = safe_float(hist[-1][c+2])

								
        prev_rsi = safe_float(hist[-2][c+1]) if len(hist) > 2 else None

        if close is None or rsi is None or ema100 is None:
            continue

										 
        if rsi >= 65:
            continue

        # ===== DIP LOGIC =====
        highs_3m = [safe_float(r[c]) for r in hist[-60:] if safe_float(r[c]) is not None]
        highs_6m = [safe_float(r[c]) for r in hist[-120:] if safe_float(r[c]) is not None]
							
								  
							   
									

					 
							 
								  
							   
									

        if not highs_3m:
            continue

        high_3m = max(highs_3m)
        dip_3m = ((high_3m - close) / high_3m) * 100

        dip = dip_3m

        dip_6m = 0
        if highs_6m:
            high_6m = max(highs_6m)
            dip_6m = ((high_6m - close) / high_6m) * 100

        # ===== SCORING =====

        score = 0
        reason = []

			  
        if dip_3m > config["dip3"]:
            score += 20
            reason.append("3M Dip")

        if dip_6m > config["dip6"]:
            score += 20
            reason.append("6M Deep Dip")

        # 🔥 ETF-SPECIFIC RSI
        if config["rsi_low"] <= rsi <= config["rsi_high"]:
            if prev_rsi is not None and rsi > prev_rsi + 1:
                score += 25
                reason.append("RSI Rising")
            else:
                score += 15
                reason.append("RSI Neutral")

        if close > ema100:
            score += 20
            reason.append("Trend")

        action = "BUY" if score >= 60 else "HOLD"

        if action == "BUY":
            buy.append_row([today, etf, close, score, ",".join(reason)])

        sig.append_row([
            today, etf, action, score,
            close, rsi, ema100,
            round(dip, 2), ",".join(reason)
        ])


if __name__ == "__main__":
    run()