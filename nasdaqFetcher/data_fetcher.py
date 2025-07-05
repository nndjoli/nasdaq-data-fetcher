import datetime

import pandas
import requests

from .utils import (
    calculate_chain_greeks,
    calculate_chain_implied_volatility,
    clean_numeric_value,
    fetch_nasdaq_chain,
    fetch_nasdaq_quote,
    fetch_nasdaq_realtime_trades,
)


class Data:
    """A class to interact with the NASDAQ API and retrieve asset data.

    This class provides methods to fetch various types of financial data for a
    given asset, including quotes, historical data, and option chains.

    Parameters
    ----------
    asset_symbol : str
        The ticker symbol of the asset (e.g., "AAPL").
    asset_category : str
        The category of the asset, such as "stocks", "etf", or "index".
    """

    def __init__(self, asset_symbol: str, asset_category: str):
        self.asset_symbol = asset_symbol
        self.asset_category = asset_category

    def get_quote(self) -> dict:
        """Retrieves the quote data for the asset.

        Returns
        -------
        dict
            A dictionary containing the quote data.
        """
        return fetch_nasdaq_quote(self.asset_symbol, self.asset_category)

    def get_raw_option_chain(
        self,
        exchange: str,
        option_strategy: str = "callput",
        start_date: str = None,
        end_date: str = None,
    ) -> list:
        """Retrieves the raw option chain data for the asset.

        Parameters
        ----------
        exchange : str
            The exchange code for the API call.
        option_strategy : str, optional
            The option strategy, by default "callput".
        start_date : str, optional
            The start date for the option chain, by default None.
        end_date : str, optional
            The end date for the option chain, by default None.

        Returns
        -------
        list
            A list of dictionaries representing the raw option chain data.
        """
        return fetch_nasdaq_chain(
            self.asset_symbol,
            self.asset_category,
            exchange,
            option_strategy=option_strategy,
            start_date=start_date,
            end_date=end_date,
        )

    def get_real_time_trades(self, number_of_trades: int = 1) -> list:
        """Retrieves real-time trade data for the asset.

        Parameters
        ----------
        number_of_trades : int, optional
            The number of trades to retrieve, by default 1.

        Returns
        -------
        list
            A list of dictionaries representing real-time trades.
        """
        return fetch_nasdaq_realtime_trades(
            self.asset_symbol, number_of_trades
        )

    def get_processed_option_chain(
        self,
        exchange: str,
        option_strategy: str,
        risk_free_rate: float,
        pricing_model: str = "black_scholes_merton",
    ) -> pandas.DataFrame:
        """Retrieves and processes the option chain data.

        This method fetches the raw option chain, calculates implied volatility
        and Greeks, and returns a processed DataFrame.

        Parameters
        ----------
        exchange : str
            The exchange code for the API call.
        option_strategy : str
            The option strategy.
        risk_free_rate : float
            The risk-free interest rate.
        pricing_model : str, optional
            The pricing model to use, by default "black_scholes_merton".

        Returns
        -------
        pandas.DataFrame
            A DataFrame with the processed option chain data.
        """
        options_data = self.get_raw_option_chain(exchange, option_strategy)
        quote_summary = self.get_quote()

        dataframe = pandas.DataFrame(options_data)

        try:
            dataframe["underlying_price"] = self.get_real_time_trades(1)[0][
                "nasdaq_last_sale_price"
            ]
        except Exception:
            dataframe["underlying_price"] = quote_summary["previous_close"]

        dataframe["risk_free_rate"] = risk_free_rate
        dataframe["years_until_expiry"] = dataframe.apply(
            lambda row: (row["contract_expiry"] - datetime.date.today()).days
            / 365,
            axis=1,
        )
        dataframe = dataframe[dataframe["years_until_expiry"] > 0]

        if self.asset_category in ["stocks", "etf", "index"]:
            dataframe["underlying_dividend_yield"] = quote_summary.get(
                "current_yield", 0
            )
        else:
            dataframe["underlying_dividend_yield"] = 0
        option_chain = calculate_chain_implied_volatility(
            dataframe, pricing_model
        )
        option_chain = calculate_chain_greeks(option_chain)
        option_chain["underlying_symbol"] = self.asset_symbol
        return option_chain

    def get_historical_data(self) -> pandas.DataFrame:
        """Retrieves historical data for the asset.

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the historical data.
        """
        today_date = str(datetime.date.today())

        request_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }
        query_params = {
            "assetclass": {self.asset_category},
            "limit": "10000",
            "fromdate": "1970-01-01",
            "todate": today_date,
        }
        api_response = requests.get(
            f"https://api.nasdaq.com/api/quote/{self.asset_symbol}/historical",
            params=query_params,
            headers=request_headers,
        )
        trades_data = api_response.json()["data"]["tradesTable"]["rows"]

        cleaned_trades_data = []

        for trade_info in trades_data:
            cleaned_trade_info = {}
            cleaned_trade_info["date"] = datetime.datetime.strptime(
                trade_info["date"], "%m/%d/%Y"
            ).date()
            cleaned_trade_info["close"] = clean_numeric_value(
                trade_info["close"].replace("$", "")
            )
            cleaned_trade_info["volume"] = clean_numeric_value(
                trade_info["volume"]
            )
            cleaned_trade_info["open"] = clean_numeric_value(
                trade_info["open"].replace("$", "")
            )
            cleaned_trade_info["high"] = clean_numeric_value(
                trade_info["high"].replace("$", "")
            )
            cleaned_trade_info["low"] = clean_numeric_value(
                trade_info["low"].replace("$", "")
            )
            cleaned_trades_data.append(cleaned_trade_info)

        historical_dataframe = pandas.DataFrame(
            cleaned_trades_data,
            index=[trade_info["date"] for trade_info in cleaned_trades_data],
        ).drop(columns=["date"])

        return historical_dataframe
