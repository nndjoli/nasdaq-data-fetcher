from scipy.interpolate import SmoothBivariateSpline
import py_vollib_vectorized as vollib
import matplotlib.pyplot as plt
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


class Data:
    """
    Class to interact with the NASDAQ API and retrieve various asset-related data.

    Methods:
    - Quote(): returns the quote data.
    - RawOptionChain(): returns the raw option chain data.
    - Realtime(): returns the real-time data.
    - ProcessedOptionChain(): returns a processed DataFrame of options.
    """

    def __init__(self, Asset: str, AssetClass: str):
        self.Asset = Asset
        self.AssetClass = AssetClass

    def Quote(self) -> dict:
        return QuoteNASDAQ(self.Asset, self.AssetClass)

    def RawOptionChain(self, ExchangeCode: str, Strategy: str = "callput", ExpiryStartDate: str = None, ExpiryEndDate: str = None) -> list:
        return ChainNASDAQ(
            self.Asset, self.AssetClass, ExchangeCode, Strategy=Strategy, ExpiryStartDate=ExpiryStartDate, ExpiryEndDate=ExpiryEndDate
        )

    def Realtime(self, NumberOfTrades: int = 1) -> list:
        return RealtimeNASDAQ(self.Asset, NumberOfTrades)

    def ProcessedOptionChain(
        self, ExchangeCode: str, Strategy: str, RiskFreeRate: float, Model: str = "black_scholes_merton"
    ) -> pandas.DataFrame:
        Options = self.RawOptionChain(ExchangeCode, Strategy)
        QuoteSummary = self.Quote()

        DataFrame = pandas.DataFrame(Options)

        try:
            DataFrame["Underlying Price"] = self.Realtime(1)[0]["NASDAQ Last Sale Price"]
        except Exception:
            DataFrame["Underlying Price"] = QuoteSummary["Previous Close"]

        DataFrame["Risk Free Rate"] = RiskFreeRate
        DataFrame["Years Until Expiry"] = DataFrame.apply(lambda row: (row["Contract Expiry"] - datetime.date.today()).days / 365, axis=1)
        DataFrame = DataFrame[DataFrame["Years Until Expiry"] > 0]

        if self.AssetClass in ["stocks", "etf", "index"]:
            DataFrame["Underlying Dividend Yield"] = QuoteSummary.get("Current Yield", 0)
        else:
            DataFrame["Underlying Dividend Yield"] = 0
        Chain = ChainImpliedVolatility(DataFrame, Model)
        Chain = ChainGreeks(Chain, Model)
        return Chain

    def HistoricalData(self) -> pandas.DataFrame:

        Today = str(datetime.date.today())

        Headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }
        Parameters = {"assetclass": {self.AssetClass}, "limit": "10000", "fromdate": "1970-01-01", "todate": Today}
        Response = requests.get(f"https://api.nasdaq.com/api/quote/{self.Asset}/historical", params=Parameters, headers=Headers)
        Data = Response.json()["data"]["tradesTable"]["rows"]

        CleanedData = []
        for Trade in Data:
            CleanedTrade = {}
            CleanedTrade["Date"] = datetime.datetime.strptime(Trade["date"], "%m/%d/%Y").date()
            CleanedTrade["Close"] = CleanFloat(Trade["close"].replace("$", ""))
            CleanedTrade["Volume"] = CleanFloat(Trade["volume"])
            CleanedTrade["Open"] = CleanFloat(Trade["open"].replace("$", ""))
            CleanedTrade["High"] = CleanFloat(Trade["high"].replace("$", ""))
            CleanedTrade["Low"] = CleanFloat(Trade["low"].replace("$", ""))
            CleanedData.append(CleanedTrade)

        HistoricalData = pandas.DataFrame(CleanedData, index=[Trade["Date"] for Trade in CleanedData]).drop(columns=["Date"])

        return HistoricalData


class Asset:
    """
    Retrieve data related to an asset via the NASDAQ API.

    Attributes:
        Asset (str): The asset symbol (e.g., "AAPL").
        AssetClass (str): The asset class, such as "stocks", "etf", or "index".

    Methods:
        Informations() -> dict:
            Retrieves and returns the asset's current quote information.
        HistoricalData() -> pandas.DataFrame:
            Retrieves and returns the asset's historical trading data as a DataFrame.

        RealTime(NumberOfTrades: int = 1) -> list:
            Retrieves and returns the most recent real-time trade data for the asset.

        Options(DataType: str = "processed", ExchangeCode: str = "oprac",
                Strategy: str = "callput", RiskFreeRate: float = 0.045) -> pandas.DataFrame:
            Retrieves and returns the option chain data for the asset.
            The data can be returned either as raw data or as a processed DataFrame.
            Additionally, it can be filtered by call or put options.

        ImpliedVolatilitySurface(OptionsType: str, RiskFreeRate: float, **kwargs):
            Retrieves and returns an ImpliedVolatilitySurface object.
    """

    def __init__(self, Asset: str, AssetClass: str):
        self.Asset = Asset
        self.AssetClass = AssetClass
        self._Data = Data(Asset, AssetClass)

    def Informations(self) -> dict:
        """Returns the asset's quote information."""
        return self._Data.Quote()

    def HistoricalData(self) -> pandas.DataFrame:
        """Returns the asset's historical data."""
        return self._Data.HistoricalData()

    def RealTime(self, NumberOfTrades: int = 1) -> list:
        """Returns the asset's real-time data."""
        return self._Data.Realtime(NumberOfTrades)

    def Options(self, DataType: str = "processed", ExchangeCode: str = "oprac", Strategy: str = "callput", RiskFreeRate: float = 0.045):
        """
        Returns the asset's option chain data.

        Args:
            DataType (str): Type of option data to return; either "raw" or "processed". Default is "processed".
            ExchangeCode (str): Exchange code used in the API call. Accepted values are:
                - 'oprac' for Composite
                - 'cbo' for CBO
                - 'aoe' for AOE
                - 'nyo' for NYO
                - 'pho' for PHO
                - 'moe' for MOE
                - 'box' for BOX
                - 'ise' for ISE
                - 'bto' for BTO
                - 'nso' for NSO
                - 'c2o' for C2O
                - 'bxo' for BXO
                - 'mio' for MIAX
            Strategy (str): Option strategy. Can be "callput", "call", or "put". Default is "callput".
            RiskFreeRate (float): The risk-free rate used for processing options data. Default is 0.045.

        Returns:
            pandas.DataFrame: A DataFrame containing the option chain data,
            optionally filtered by option type.
        """

        if DataType.lower() == "raw":
            Data = self._Data.RawOptionChain(ExchangeCode, "callput")
            Data = pandas.DataFrame(Data)

        elif DataType.lower() == "processed":
            Data = self._Data.ProcessedOptionChain(ExchangeCode, "callput", RiskFreeRate)

        if Strategy.lower() in ["call", "put"]:
            Data = Data[Data["Contract Type"] == Strategy.capitalize()]

        return Data

    def ImpliedVolatilitySurface(self, OptionsType: str, RiskFreeRate: float, **kwargs):
        """
        Returns an ImpliedVolatilitySurface object for this asset.

        Args:
            OptionsType (str): The type of options to consider ("call" or "put").
            RiskFreeRate (float): The risk-free rate used in the implied volatility calculation.
            **kwargs: Additional keyword arguments to configure the surface (e.g., smoothing factors).

        Returns:
            ImpliedVolatilitySurface: An object representing the implied volatility surface.
        """
        return ImpliedVolatilitySurface(self.Asset, self.AssetClass, OptionsType, RiskFreeRate, **kwargs)


class ImpliedVolatilitySurface:
    """
    A class to create and analyze the implied volatility surface for a given asset.

    Parameters:
        Asset (str): The asset symbol (e.g., "AAPL").
        AssetClass (str): The asset class, such as "stocks", "etf", or "index".
        OptionsType (str): The type of options to analyze ("call" or "put").
        RiskFreeRate (float): The risk-free rate used for option pricing models.
        MoneynessRange (list, optional): A list specifying the lower and upper bounds for the moneyness filter.
            Default is [0.05, 1.95].
        IVRange (list, optional): A list specifying the minimum and maximum implied volatility values to consider.
            Default is [0, 2].
        MinDaysUntilExpiry (int, optional): The minimum number of days until expiry for options to be included.
            Default is 21.
        MinVolume (int, optional): The minimum contract volume required to include an option.
            Default is 5.
        MinOpenInt (int, optional): The minimum open interest required to include an option.
            Default is 100.
        MaxAbsDeviation (float, optional): The maximum absolute deviation (in multiples of the median absolute deviation)
            allowed for filtering out outlier options. Default is 3.

    Attributes:
        DataFrame (pandas.DataFrame): The filtered option chain data after applying the specified criteria.
        T (numpy.ndarray): Array of years until expiry for the options in the DataFrame.
        K (numpy.ndarray): Array of contract strikes for the options.
        Sigma (numpy.ndarray): Array of implied volatilities for the options.
        Title (str): Title for the volatility surface plot, including asset, option type, and current date.
    """

    def __init__(
        self,
        Asset,
        AssetClass,
        OptionsType,
        RiskFreeRate,
        MoneynessRange: list = [0.05, 1.95],
        IVRange: list = [0, 2],
        MinDaysUntilExpiry: int = 21,
        MinVolume: int = 5,
        MinOpenInt: int = 100,
        MaxAbsDeviation: float = 3,
    ):
        self.Asset = Asset
        self.AssetClass = AssetClass
        self.OptionsType = OptionsType
        self.k = MaxAbsDeviation
        MinIV = IVRange[0]
        MaxIV = IVRange[1]
        self.DataFrame = (
            Data(self.Asset, self.AssetClass).ProcessedOptionChain("oprac", "callput", RiskFreeRate, "black_scholes_merton").dropna()
        )
        self.DataFrame = self.DataFrame[self.DataFrame["Years Until Expiry"] * 365 > MinDaysUntilExpiry]
        self.DataFrame["Moneyness"] = (
            self.DataFrame["Underlying Price"] / self.DataFrame["Contract Strike"]
            if OptionsType.lower() == "call"
            else self.DataFrame["Contract Strike"] / self.DataFrame["Underlying Price"]
        )
        self.DataFrame = self.DataFrame[
            (self.DataFrame["Moneyness"] >= MoneynessRange[0]) & (self.DataFrame["Moneyness"] <= MoneynessRange[1])
        ]
        self.DataFrame = self.DataFrame[(self.DataFrame["Implied Volatility"] >= MinIV) & (self.DataFrame["Implied Volatility"] <= MaxIV)]
        self.DataFrame = self.DataFrame[
            (self.DataFrame["Contract Volume"] > MinVolume) & (self.DataFrame["Contract Open Interest"] > MinOpenInt)
        ]
        if self.OptionsType.lower() in ["call", "put"]:
            self.DataFrame = self.DataFrame[self.DataFrame["Contract Type"].str.lower() == self.OptionsType.lower()]
        Median = self.DataFrame["Implied Volatility"].median()
        self.DataFrame["Absolute Deviation"] = abs(self.DataFrame["Implied Volatility"] - Median)
        MAD = self.DataFrame["Absolute Deviation"].median()
        self.DataFrame["Outlier"] = (self.DataFrame["Absolute Deviation"] / MAD) > self.k
        self.DataFrame = self.DataFrame[self.DataFrame["Outlier"] == False]
        self.T = self.DataFrame["Years Until Expiry"].values
        self.K = self.DataFrame["Contract Strike"].values
        self.Sigma = self.DataFrame["Implied Volatility"].values
        self.Title = f"{self.Asset} Implied Volatility Surface -- {self.OptionsType} --  {datetime.date.today()}"

    def Plot(
        self,
        SmoothingFactor: float = 1,
        Granularity: int = 256,
        FigSize: tuple = (12, 12),
        CMap: str = "viridis",
        EdgeColor: str = "none",
        Alpha: float = 0.9,
        ViewAngle: tuple = (15, 315),
        BoxAspect: tuple = [36, 36, 18],
        ShowScatter: bool = False,
    ):
        """
        Displays a 3D plot of the smoothed implied volatility surface for the asset.

        Parameters:
            SmoothingFactor (float, optional): Smoothing factor for the bivariate spline. Default is 1.
            Granularity (int, optional): Number of grid points for evaluating the spline. Default is 256.
            FigSize (tuple, optional): Size of the matplotlib figure (width, height). Default is (12, 12).
            CMap (str, optional): Colormap used to color the surface. Default is "viridis".
            EdgeColor (str, optional): Color of the surface edges. Default is "none".
            Alpha (float, optional): Opacity of the displayed surface. Default is 0.9.
            ViewAngle (tuple, optional): Viewing angle for the 3D projection in the form (elevation, azimuth). Default is (15, 315).
            BoxAspect (tuple, optional): Aspect ratio of the 3D plot box. Default is [36, 36, 18].
            ShowScatter (bool, optional): If True, also displays the original data points on the surface. Default is False.

        Returns:
            None: This function directly displays the 3D plot of the implied volatility surface.
        """

        Spline = SmoothBivariateSpline(self.T, self.K, self.Sigma, s=SmoothingFactor)

        TGrid = np.linspace(self.T.min(), self.T.max(), Granularity)
        KGrid = np.linspace(self.K.min(), self.K.max(), Granularity)

        TMesh, KMesh = np.meshgrid(TGrid, KGrid)

        SigmaSmooth = Spline.ev(TMesh.ravel(), KMesh.ravel())
        SigmaSmooth = SigmaSmooth.reshape(TMesh.shape)

        Fig = plt.figure(figsize=FigSize)
        Ax = Fig.add_subplot(111, projection="3d")

        Surf = Ax.plot_surface(TMesh, KMesh, SigmaSmooth, cmap=CMap, edgecolor=EdgeColor, alpha=Alpha)

        Ax.set_xlabel("Years Until Expiry")
        Ax.set_ylabel("Contract Strike")
        Ax.set_zlabel("Implied Volatility")
        Ax.view_init(ViewAngle[0], ViewAngle[1])
        Ax.set_box_aspect(BoxAspect)

        Fig.colorbar(Surf, shrink=0.275, aspect=12, label="Implied Volatility")

        plt.title(self.Title)

        if ShowScatter:
            Ax.scatter(self.T, self.K, self.Sigma, color="black", marker="o", s=10)

        plt.show()
