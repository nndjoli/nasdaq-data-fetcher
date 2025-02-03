from .Utils import CleanFloat
from .Utils import QuoteNASDAQ
from .Utils import ChainNASDAQ
from .Utils import RealtimeNASDAQ
from .Utils import ChainImpliedVolatility
from .Utils import ChainGreeks

import requests
import pandas
import datetime


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
        Chain["Underlying Symbol"] = self.Asset
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
