import pandas

from .data_fetcher import Data
from .options_fetcher import OptionsChain


class Asset:
    """A class to retrieve data for a financial asset using the NASDAQ API.

    Parameters
    ----------
    asset_symbol : str
        The ticker symbol of the asset (e.g., "AAPL").
    asset_category : str
        The category of the asset, such as "stocks", "etf", or "index".

    Attributes
    ----------
    asset_symbol : str
        The ticker symbol of the asset.
    asset_category : str
        The category of the asset.
    _data_handler : Data
        An instance of the Data class to handle API requests.
    """

    def __init__(self, asset_symbol: str, asset_category: str):
        """Initializes the Asset object."""
        self.asset_symbol = asset_symbol
        self.asset_category = asset_category
        self._data_handler = Data(asset_symbol, asset_category)

    def get_informations(self) -> dict:
        """Retrieves the asset's current quote information.

        Returns
        -------
        dict
            A dictionary containing the asset's quote data.
        """
        return self._data_handler.get_quote()

    def get_historical_data(self) -> pandas.DataFrame:
        """Retrieves the asset's historical trading data.

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the historical trading data.
        """
        return self._data_handler.get_historical_data()

    def get_real_time_trades(self, number_of_trades: int = 1) -> list:
        """Retrieves the most recent real-time trade data for the asset.

        Parameters
        ----------
        number_of_trades : int, optional
            The number of recent trades to retrieve, by default 1.

        Returns
        -------
        list
            A list of dictionaries, where each dictionary represents a recent trade.
        """
        return self._data_handler.get_real_time_trades(number_of_trades)

    def get_options_chain(
        self,
        data_format: str = "processed",
        exchange: str = "oprac",
        option_strategy: str = "callput",
        risk_free_interest_rate: float = 0.045,
    ) -> OptionsChain:
        """Retrieves and returns the option chain data for the asset.

        The data can be returned as raw data or as a processed DataFrame,
        and can be filtered by call or put options.

        Parameters
        ----------
        data_format : str, optional
            The type of option data to return, either "raw" or "processed".
            Defaults to "processed".
        exchange : str, optional
            The exchange code for the API call. Defaults to "oprac" (Composite).
            Accepted values include 'cbo', 'aoe', 'nyo', 'pho', 'moe', 'box',
            'ise', 'bto', 'nso', 'c2o', 'bxo', 'mio'.
        option_strategy : str, optional
            The option strategy to apply, one of "callput", "call", or "put".
            Defaults to "callput".
        risk_free_interest_rate : float, optional
            The risk-free interest rate used for processing options data.
            Defaults to 0.045.

        Returns
        -------
        OptionsChain
            An OptionsChain object containing the option chain data.
        """
        if data_format.lower() == "raw":
            options_data = self._data_handler.get_raw_option_chain(
                exchange, "callput"
            )
            options_data = pandas.DataFrame(options_data)

        elif data_format.lower() == "processed":
            options_data = self._data_handler.get_processed_option_chain(
                exchange, "callput", risk_free_interest_rate
            )

        if option_strategy.lower() in ["call", "put"]:
            options_data = options_data[
                options_data["contract_type"]
                == option_strategy.lower().capitalize()
            ]

        return OptionsChain(options_data)
