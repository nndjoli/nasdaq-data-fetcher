import pandas

from .DataCLS import Data
from .OptionsCLS import OC


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

        return OC(Data)
