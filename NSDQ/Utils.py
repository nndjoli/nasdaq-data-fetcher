import py_vollib_vectorized as vollib
import numpy as np
import datetime
import requests
import pandas
import re


def CleanExpiryDate(x: str) -> datetime.date:
    try:
        match = re.search(r"--(\d{6})", x or "")
        return datetime.datetime.strptime(match.group(1), "%y%m%d").date() if match else np.nan
    except Exception:
        return np.nan


def CleanFloat(x: str) -> float:
    if x is None:
        return np.nan
    elif x in ["-", "--", "N/A"]:
        return np.nan
    elif "," in x:
        try:
            return float(x.replace(",", ""))
        except Exception:
            return np.nan
    else:
        try:
            return float(x)
        except Exception:
            return np.nan


def ChainNASDAQ(
    Asset: str, AssetClass: str, ExchangeCode: str, Strategy: str = "callput", ExpiryStartDate: str = None, ExpiryEndDate: str = None
) -> list:
    if ExpiryStartDate is None:
        ExpiryStartDate = datetime.date.today()
    if ExpiryEndDate is None:
        ExpiryEndDate = ExpiryStartDate + datetime.timedelta(days=3650)

    Headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    URL = (
        f"https://api.nasdaq.com/api/quote/{Asset}/option-chain?"
        f"assetclass={AssetClass}&limit=10000&fromdate={str(ExpiryStartDate)}&todate={str(ExpiryEndDate)}"
        f"&excode={ExchangeCode}&callput={Strategy}&money=all&type=all"
    )

    Response = requests.get(URL, headers=Headers)
    ResponseJSON = Response.json()

    Chain = ResponseJSON["data"]["table"]["rows"]

    CleanedOptionChain = []

    for Contract in Chain:
        ExpiryDate = CleanExpiryDate(Contract["drillDownURL"])
        if ExpiryDate is np.nan:
            continue

        ID = Contract["drillDownURL"].split("/")[-1].upper().replace("-", "")

        CleanedOptionCallDictionary = {}
        CleanedOptionCallDictionary["Contract Identifier"] = ID
        CleanedOptionCallDictionary["Contract Type"] = "Call"
        CleanedOptionCallDictionary["Contract Strike"] = CleanFloat(Contract["strike"])
        CleanedOptionCallDictionary["Contract Expiry"] = ExpiryDate
        CleanedOptionCallDictionary["Contract Last"] = CleanFloat(Contract["c_Last"])
        CleanedOptionCallDictionary["Contract Change"] = CleanFloat(Contract["c_Change"])
        CleanedOptionCallDictionary["Contract Bid"] = CleanFloat(Contract["c_Bid"])
        CleanedOptionCallDictionary["Contract Ask"] = CleanFloat(Contract["c_Ask"])
        CleanedOptionCallDictionary["Contract Volume"] = CleanFloat(Contract["c_Volume"])
        CleanedOptionCallDictionary["Contract Open Interest"] = CleanFloat(Contract["c_Openinterest"])
        CleanedOptionChain.append(CleanedOptionCallDictionary)

        CleanedOptionPutDictionary = {}
        CleanedOptionPutDictionary["Contract Identifier"] = Asset + ID.split(Asset)[1].replace("C", "P")
        CleanedOptionPutDictionary["Contract Type"] = "Put"
        CleanedOptionPutDictionary["Contract Strike"] = CleanFloat(Contract["strike"])
        CleanedOptionPutDictionary["Contract Expiry"] = ExpiryDate
        CleanedOptionPutDictionary["Contract Last"] = CleanFloat(Contract["p_Last"])
        CleanedOptionPutDictionary["Contract Change"] = CleanFloat(Contract["p_Change"])
        CleanedOptionPutDictionary["Contract Bid"] = CleanFloat(Contract["p_Bid"])
        CleanedOptionPutDictionary["Contract Ask"] = CleanFloat(Contract["p_Ask"])
        CleanedOptionPutDictionary["Contract Volume"] = CleanFloat(Contract["p_Volume"])
        CleanedOptionPutDictionary["Contract Open Interest"] = CleanFloat(Contract["p_Openinterest"])
        CleanedOptionChain.append(CleanedOptionPutDictionary)

    return CleanedOptionChain


def RealtimeNASDAQ(Asset: str, NumberOfTrades: int = 1) -> list:
    Headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    URL = f"https://api.nasdaq.com/api/quote/{Asset}/realtime-trades?&limit={NumberOfTrades}"
    Response = requests.get(URL, headers=Headers)
    ResponseJSON = Response.json()

    Trades = ResponseJSON["data"]["rows"]
    TopTable = ResponseJSON["data"]["topTable"]
    Description = ResponseJSON["data"]["description"]
    Message = ResponseJSON["data"]["message"]
    Message2 = ResponseJSON["message"]

    if len(Trades) == 0:
        CurrentlyUnavailable = {}
        CurrentlyUnavailable["Previous Close"] = (
            CleanFloat(TopTable.get("rows", [{}])[0].get("previousClose", "N/A").replace("$", ""))
            if TopTable.get("rows", [{}])[0].get("previousClose", "N/A") != "N/A"
            else np.nan
        )
        CurrentlyUnavailable["Today High"] = (
            CleanFloat(TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A").split("/")[0].replace("$", ""))
            if TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A") != "N/A"
            else np.nan
        )
        CurrentlyUnavailable["Today Low"] = (
            CleanFloat(TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A").split("/")[1].replace("$", ""))
            if TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A") != "N/A"
            else np.nan
        )
        CurrentlyUnavailable["52 Week High"] = (
            CleanFloat(TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A").split("/")[0].replace("$", ""))
            if TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A") != "N/A"
            else np.nan
        )
        CurrentlyUnavailable["52 Week Low"] = (
            CleanFloat(TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A").split("/")[1].replace("$", ""))
            if TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A") != "N/A"
            else np.nan
        )
        CurrentlyUnavailable["Description"] = Description if Description != "N/A" else np.nan
        CurrentlyUnavailable["Message"] = Message if Message != "N/A" else np.nan
        CurrentlyUnavailable["Message2"] = Message2 if Message2 != "N/A" else np.nan
        return CurrentlyUnavailable
    else:
        CleanedTrades = []
        for Trade in Trades:
            CleanedTrade = {}
            CleanedTrade["NASDAQ Last Sale Time (ET)"] = Trade.get("nlsTime", np.nan) if Trade.get("nlsTime", np.nan) != "N/A" else np.nan
            CleanedTrade["NASDAQ Last Sale Price"] = (
                CleanFloat(Trade.get("nlsPrice", "N/A").replace("$", "")) if Trade.get("nlsPrice", "N/A") != "N/A" else np.nan
            )
            CleanedTrade["NASDAQ Last Sale Share Volume"] = (
                Trade.get("nlsShareVolume", np.nan) if Trade.get("nlsShareVolume", np.nan) != "N/A" else np.nan
            )
            CleanedTrade["Previous Close"] = (
                CleanFloat(TopTable.get("rows", [{}])[0].get("previousClose", "N/A").replace("$", ""))
                if TopTable.get("rows", [{}])[0].get("previousClose", "N/A") != "N/A"
                else np.nan
            )
            CleanedTrade["Today High"] = (
                CleanFloat(TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A").split("/")[0].replace("$", ""))
                if TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A") != "N/A"
                else np.nan
            )
            CleanedTrade["Today Low"] = (
                CleanFloat(TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A").split("/")[1].replace("$", ""))
                if TopTable.get("rows", [{}])[0].get("todayHighLow", "N/A") != "N/A"
                else np.nan
            )
            CleanedTrade["52 Week High"] = (
                CleanFloat(TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A").split("/")[0].replace("$", ""))
                if TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A") != "N/A"
                else np.nan
            )
            CleanedTrade["52 Week Low"] = (
                CleanFloat(TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A").split("/")[1].replace("$", ""))
                if TopTable.get("rows", [{}])[0].get("fiftyTwoWeekHighLow", "N/A") != "N/A"
                else np.nan
            )
            CleanedTrade["Description"] = Description if Description != "N/A" else np.nan
            CleanedTrade["Message"] = Message if Message != "N/A" else np.nan
            CleanedTrades.append(CleanedTrade)
    return CleanedTrades


def QuoteNASDAQ(Asset: str, AssetClass: str) -> dict:
    Headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    URL = f"https://api.nasdaq.com/api/quote/{Asset}/summary?assetclass={AssetClass}"
    Response = requests.get(URL, headers=Headers)
    ResponseJSON = Response.json()
    Quote = ResponseJSON.get("data", {}).get("summaryData", {})

    if AssetClass == "stocks":
        CleanedQuote = {}
        CleanedQuote["Symbol"] = Asset
        CleanedQuote["Exchange"] = Quote.get("Exchange", {}).get("value", np.nan)
        CleanedQuote["Sector"] = Quote.get("Sector", {}).get("value", np.nan)
        CleanedQuote["Industry"] = Quote.get("Industry", {}).get("value", np.nan)
        CleanedQuote["One Year Target"] = (
            CleanFloat(Quote.get("OneYrTarget", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("OneYrTarget", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Today's High"] = (
            CleanFloat(Quote.get("TodayHighLow", {}).get("value", "N/A").split("/")[0].replace("$", ""))
            if "N/A" not in Quote.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Today's Low"] = (
            CleanFloat(Quote.get("TodayHighLow", {}).get("value", "N/A").split("/")[1].replace("$", ""))
            if "N/A" not in Quote.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Share Volume"] = (
            CleanFloat(Quote.get("ShareVolume", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("ShareVolume", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Average Volume"] = (
            CleanFloat(Quote.get("AverageVolume", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("AverageVolume", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Previous Close"] = (
            CleanFloat(Quote.get("PreviousClose", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("PreviousClose", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["52 Week High"] = (
            CleanFloat(Quote.get("FiftyTwoWeekHighLow", {}).get("value", "N/A").split("/")[0].replace("$", ""))
            if "N/A" not in Quote.get("FiftyTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["52 Week Low"] = (
            CleanFloat(Quote.get("FiftyTwoWeekHighLow", {}).get("value", "N/A").split("/")[1].replace("$", ""))
            if "N/A" not in Quote.get("FiftyTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Market Cap"] = (
            CleanFloat(Quote.get("MarketCap", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("MarketCap", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["P/E Ratio"] = Quote.get("PERatio", {}).get("value", np.nan)
        CleanedQuote["Forward P/E 1 Yr."] = (
            CleanFloat(Quote.get("ForwardPE1Yr", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("ForwardPE1Yr", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Earnings Per Share(EPS)"] = (
            CleanFloat(Quote.get("EarningsPerShare", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("EarningsPerShare", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Annualized Dividend"] = (
            CleanFloat(Quote.get("AnnualizedDividend", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("AnnualizedDividend", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Ex Dividend Date"] = (
            Quote.get("ExDividendDate", {}).get("value", np.nan)
            if "N/A" not in Quote.get("ExDividendDate", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Dividend Pay Date"] = (
            Quote.get("DividendPaymentDate", {}).get("value", np.nan)
            if "N/A" not in Quote.get("DividendPaymentDate", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Current Yield"] = (
            CleanFloat(Quote.get("Yield", {}).get("value", "N/A").replace("%", "")) / 100
            if "N/A" not in Quote.get("Yield", {}).get("value", "N/A")
            else 0
        )
        return CleanedQuote

    elif AssetClass == "index":
        CleanedQuote = {}
        CleanedQuote["Symbol"] = Asset
        CleanedQuote["Current Price"] = CleanFloat(Quote.get("CurrentPrice", {}).get("value", "N/A"))
        CleanedQuote["Net Change"] = CleanFloat(Quote.get("NetChangePercentageChange", {}).get("value", "N/A").split("/")[0])
        CleanedQuote["Net Change %"] = (
            CleanFloat(Quote.get("NetChangePercentageChange", {}).get("value", "N/A").split("/")[1].replace("%", "")) / 100
        )
        CleanedQuote["Previous Close"] = CleanFloat(Quote.get("PreviousClose", {}).get("value", "N/A"))
        CleanedQuote["Today's High"] = CleanFloat(Quote.get("TodaysHigh", {}).get("value", "N/A"))
        CleanedQuote["Today's Low"] = CleanFloat(Quote.get("TodaysLow", {}).get("value", "N/A"))
        CleanedQuote["Current Yield"] = (
            CleanFloat(Quote.get("Yield", {}).get("value", "N/A").replace("%", "")) / 100
            if "N/A" not in Quote.get("Yield", {}).get("value", "N/A")
            else 0
        )
        return CleanedQuote

    elif AssetClass == "etf":
        CleanedQuote = {}
        CleanedQuote["Symbol"] = Asset
        CleanedQuote["Today's High"] = (
            CleanFloat(Quote.get("TodayHighLow", {}).get("value", "N/A").split("/")[0].replace("$", ""))
            if "N/A" not in Quote.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Today's Low"] = (
            CleanFloat(Quote.get("TodayHighLow", {}).get("value", "N/A").split("/")[1].replace("$", ""))
            if "N/A" not in Quote.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Share Volume"] = (
            CleanFloat(Quote.get("ShareVolume", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("ShareVolume", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["50 Day Avg. Daily Volume"] = (
            CleanFloat(Quote.get("FiftyDayAvgDailyVol", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("FiftyDayAvgDailyVol", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Previous Close"] = (
            CleanFloat(Quote.get("PreviousClose", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("PreviousClose", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["52 Week High"] = (
            CleanFloat(Quote.get("FiftTwoWeekHighLow", {}).get("value", "N/A").split("/")[0].replace("$", ""))
            if "N/A" not in Quote.get("FiftTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["52 Week Low"] = (
            CleanFloat(Quote.get("FiftTwoWeekHighLow", {}).get("value", "N/A").split("/")[1].replace("$", ""))
            if "N/A" not in Quote.get("FiftTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Market Cap"] = (
            CleanFloat(Quote.get("MarketCap", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("MarketCap", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Annualized Dividend"] = (
            CleanFloat(Quote.get("AnnualizedDividend", {}).get("value", "N/A").replace("$", ""))
            if "N/A" not in Quote.get("AnnualizedDividend", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Ex Dividend Date"] = (
            Quote.get("ExDividendDate", {}).get("value", "N/A")
            if "N/A" not in Quote.get("ExDividendDate", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Dividend Payment Date"] = (
            Quote.get("DividendPaymentDate", {}).get("value", "N/A")
            if "N/A" not in Quote.get("DividendPaymentDate", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Current Yield"] = (
            CleanFloat(Quote.get("Yield", {}).get("value", "N/A").replace("%", "")) / 100
            if "N/A" not in Quote.get("Yield", {}).get("value", "N/A")
            else 0
        )
        CleanedQuote["Alpha"] = (
            CleanFloat(Quote.get("Alpha", {}).get("value", "N/A")) if "N/A" not in Quote.get("Alpha", {}).get("value", "N/A") else np.nan
        )
        CleanedQuote["Weighted Alpha"] = (
            CleanFloat(Quote.get("WeightedAlpha", {}).get("value", "N/A"))
            if "N/A" not in Quote.get("WeightedAlpha", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Beta"] = (
            CleanFloat(Quote.get("Beta", {}).get("value", "N/A"))
            if isinstance(Quote.get("Beta", {}).get("value", "N/A"), str) and "N/A" not in Quote.get("Beta", {}).get("value", "N/A")
            else np.nan
        )
        CleanedQuote["Standard Deviation"] = (
            CleanFloat(Quote.get("StandardDeviation", {}).get("value", "N/A"))
            if isinstance(Quote.get("StandardDeviation", {}).get("value", "N/A"), str)
            and "N/A" not in Quote.get("StandardDeviation", {}).get("value", "N/A")
            else np.nan
        )
        return CleanedQuote


def ChainImpliedVolatility(Chain, Model):
    import numpy as np

    S = Chain["Underlying Price"].to_numpy()
    K = Chain["Contract Strike"].to_numpy()
    T = Chain["Years Until Expiry"].to_numpy()
    r = Chain["Risk Free Rate"].iloc[0] if isinstance(Chain["Risk Free Rate"], pandas.Series) else Chain["Risk Free Rate"]

    Flag = np.where(Chain["Contract Type"].str.lower() == "call", "c", "p")

    if "Underlying Dividend Yield" in Chain.columns:
        q = Chain["Underlying Dividend Yield"].to_numpy()
    else:
        q = 0

    Price = Chain["Contract Last"].to_numpy()

    Intrinsic = np.where(Flag == "c", np.maximum(0, S - K), np.maximum(0, K - S))
    ValidMask = (Price > Intrinsic) & (T > 0)

    IV = np.full_like(Price, np.nan, dtype=np.float64)

    if ValidMask.any():
        IV_calculated = vollib.vectorized_implied_volatility(
            Price[ValidMask],
            S[ValidMask],
            K[ValidMask],
            T[ValidMask],
            r,
            Flag[ValidMask],
            q[ValidMask] if isinstance(q, np.ndarray) else q,
            model=Model,
            on_error="ignore",
        )
        IV[ValidMask] = np.array(IV_calculated).flatten()

    Chain["Implied Volatility"] = IV
    return Chain


def ChainGreeks(Chain, Model):
    import numpy as np

    S = Chain["Underlying Price"].to_numpy()
    K = Chain["Contract Strike"].to_numpy()
    T = Chain["Years Until Expiry"].to_numpy()
    r = Chain["Risk Free Rate"].iloc[0] if isinstance(Chain["Risk Free Rate"], pandas.Series) else Chain["Risk Free Rate"]
    sigma = Chain["Implied Volatility"].to_numpy()

    Flag = np.where(Chain["Contract Type"].str.lower() == "call", "c", "p")

    if "Underlying Dividend Yield" in Chain.columns:
        q = Chain["Underlying Dividend Yield"].to_numpy()
    else:
        q = 0

    Greeks = vollib.get_all_greeks(Flag, S, K, T, r, sigma, q, model=Model)

    Chain["Delta"] = Greeks["delta"]
    Chain["Gamma"] = Greeks["gamma"]
    Chain["Theta"] = Greeks["theta"]
    Chain["Vega"] = Greeks["vega"]
    Chain["Rho"] = Greeks["rho"]

    return Chain
