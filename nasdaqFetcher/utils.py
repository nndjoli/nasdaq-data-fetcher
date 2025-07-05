import datetime
import re

import numpy as np
import pandas as pd
import requests
from scipy.optimize import brentq
from scipy.stats import norm


def parse_expiry_date(expiry_string: str) -> datetime.date:
    """Parses the expiry date from a string.

    Parameters
    ----------
    expiry_string : str
        The string containing the expiry date.

    Returns
    -------
    datetime.date
        The parsed expiry date.
    """
    try:
        match = re.search(r"--(\d{6})", expiry_string or "")

        return (
            datetime.datetime.strptime(match.group(1), "%y%m%d").date()
            if match
            else np.nan
        )

    except Exception:
        return np.nan


def clean_numeric_value(numeric_string: str) -> float:
    """Cleans a string to a float.

    Parameters
    ----------
    numeric_string : str
        The string to clean.

    Returns
    -------
    float
        The cleaned float value.
    """
    if numeric_string is None:
        return np.nan

    elif numeric_string in ["-", "--", "N/A"]:
        return np.nan

    elif "," in numeric_string:
        try:
            return float(numeric_string.replace(",", ""))

        except Exception:
            return np.nan

    else:
        try:
            return float(numeric_string)

        except Exception:
            return np.nan


def fetch_nasdaq_chain(
    asset_symbol: str,
    asset_category: str,
    exchange: str,
    option_strategy: str = "callput",
    start_date: str = None,
    end_date: str = None,
) -> list:
    """Fetches the option chain from NASDAQ.

    Parameters
    ----------
    asset_symbol : str
        The asset symbol.
    asset_category : str
        The asset category.
    exchange : str
        The exchange code.
    option_strategy : str, optional
        The option strategy, by default "callput".
    start_date : str, optional
        The start date, by default None.
    end_date : str, optional
        The end date, by default None.

    Returns
    -------
    list
        A list of dictionaries representing the option chain.
    """
    if start_date is None:
        start_date = datetime.date.today()

    if end_date is None:
        end_date = start_date + datetime.timedelta(days=3650)

    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    api_url = (
        f"https://api.nasdaq.com/api/quote/{asset_symbol}/option-chain?"
        f"assetclass={asset_category}&limit=10000&fromdate={str(start_date)}&todate={str(end_date)}"
        f"&excode={exchange}&callput={option_strategy}&money=all&type=all"
    )

    api_response = requests.get(api_url, headers=request_headers)

    response_json = api_response.json()

    option_chain = response_json["data"]["table"]["rows"]

    cleaned_chain = []

    for contract_data in option_chain:
        expiry_date = parse_expiry_date(contract_data["drillDownURL"])
        if expiry_date is np.nan:
            continue

        contract_id = (
            contract_data["drillDownURL"]
            .split("/")[-1]
            .upper()
            .replace("-", "")
        )

        cleaned_call_data = {}
        cleaned_call_data["contract_identifier"] = contract_id
        cleaned_call_data["contract_type"] = "Call"
        cleaned_call_data["contract_strike"] = clean_numeric_value(
            contract_data["strike"]
        )
        cleaned_call_data["contract_expiry"] = expiry_date
        cleaned_call_data["contract_last_price"] = clean_numeric_value(
            contract_data["c_Last"]
        )
        cleaned_call_data["contract_change"] = clean_numeric_value(
            contract_data["c_Change"]
        )
        cleaned_call_data["contract_bid"] = clean_numeric_value(
            contract_data["c_Bid"]
        )
        cleaned_call_data["contract_ask"] = clean_numeric_value(
            contract_data["c_Ask"]
        )
        cleaned_call_data["contract_volume"] = clean_numeric_value(
            contract_data["c_Volume"]
        )
        cleaned_call_data["contract_open_interest"] = clean_numeric_value(
            contract_data["c_Openinterest"]
        )
        cleaned_chain.append(cleaned_call_data)

        cleaned_put_data = {}
        cleaned_put_data["contract_identifier"] = (
            asset_symbol + contract_id.split(asset_symbol)[1].replace("C", "P")
        )
        cleaned_put_data["contract_type"] = "Put"
        cleaned_put_data["contract_strike"] = clean_numeric_value(
            contract_data["strike"]
        )
        cleaned_put_data["contract_expiry"] = expiry_date
        cleaned_put_data["contract_last_price"] = clean_numeric_value(
            contract_data["p_Last"]
        )
        cleaned_put_data["contract_change"] = clean_numeric_value(
            contract_data["p_Change"]
        )
        cleaned_put_data["contract_bid"] = clean_numeric_value(
            contract_data["p_Bid"]
        )
        cleaned_put_data["contract_ask"] = clean_numeric_value(
            contract_data["p_Ask"]
        )
        cleaned_put_data["contract_volume"] = clean_numeric_value(
            contract_data["p_Volume"]
        )
        cleaned_put_data["contract_open_interest"] = clean_numeric_value(
            contract_data["p_Openinterest"]
        )
        cleaned_chain.append(cleaned_put_data)

    return cleaned_chain


def fetch_nasdaq_realtime_trades(
    asset_symbol: str, number_of_trades: int = 1
) -> list:
    """Fetches real-time trades from NASDAQ.

    Parameters
    ----------
    asset_symbol : str
        The asset symbol.
    number_of_trades : int, optional
        The number of trades to fetch, by default 1.

    Returns
    -------
    list
        A list of dictionaries representing the real-time trades.
    """
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    api_url = f"https://api.nasdaq.com/api/quote/{asset_symbol}/realtime-trades?&limit={number_of_trades}"
    api_response = requests.get(api_url, headers=request_headers)

    response_json = api_response.json()

    trades_data = response_json["data"]["rows"]

    top_table_data = response_json["data"]["topTable"]

    description_text = response_json["data"]["description"]

    message_text = response_json["data"]["message"]

    message_text_2 = response_json["message"]

    if len(trades_data) == 0:
        unavailable_data = {}

        unavailable_data["previous_close"] = (
            clean_numeric_value(
                top_table_data.get("rows", [{}])[0]
                .get("previousClose", "N/A")
                .replace("$", "")
            )
            if top_table_data.get("rows", [{}])[0].get("previousClose", "N/A")
            != "N/A"
            else np.nan
        )

        unavailable_data["today_high"] = (
            clean_numeric_value(
                top_table_data.get("rows", [{}])[0]
                .get("todayHighLow", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if top_table_data.get("rows", [{}])[0].get("todayHighLow", "N/A")
            != "N/A"
            else np.nan
        )

        unavailable_data["today_low"] = (
            clean_numeric_value(
                top_table_data.get("rows", [{}])[0]
                .get("todayHighLow", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if top_table_data.get("rows", [{}])[0].get("todayHighLow", "N/A")
            != "N/A"
            else np.nan
        )

        unavailable_data["fifty_two_week_high"] = (
            clean_numeric_value(
                top_table_data.get("rows", [{}])[0]
                .get("fiftyTwoWeekHighLow", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if top_table_data.get("rows", [{}])[0].get(
                "fiftyTwoWeekHighLow", "N/A"
            )
            != "N/A"
            else np.nan
        )

        unavailable_data["fifty_two_week_low"] = (
            clean_numeric_value(
                top_table_data.get("rows", [{}])[0]
                .get("fiftyTwoWeekHighLow", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if top_table_data.get("rows", [{}])[0].get(
                "fiftyTwoWeekHighLow", "N/A"
            )
            != "N/A"
            else np.nan
        )

        unavailable_data["description"] = (
            description_text if description_text != "N/A" else np.nan
        )

        unavailable_data["message"] = (
            message_text if message_text != "N/A" else np.nan
        )

        unavailable_data["message2"] = (
            message_text_2 if message_text_2 != "N/A" else np.nan
        )

        return unavailable_data

    else:
        cleaned_trades_data = []

        for trade_data in trades_data:
            cleaned_trade_data = {}

            cleaned_trade_data["nasdaq_last_sale_time_et"] = (
                trade_data.get("nlsTime", np.nan)
                if trade_data.get("nlsTime", np.nan) != "N/A"
                else np.nan
            )

            cleaned_trade_data["nasdaq_last_sale_price"] = (
                clean_numeric_value(
                    trade_data.get("nlsPrice", "N/A").replace("$", "")
                )
                if trade_data.get("nlsPrice", "N/A") != "N/A"
                else np.nan
            )

            cleaned_trade_data["nasdaq_last_sale_share_volume"] = (
                trade_data.get("nlsShareVolume", np.nan)
                if trade_data.get("nlsShareVolume", np.nan) != "N/A"
                else np.nan
            )

            cleaned_trade_data["previous_close"] = (
                clean_numeric_value(
                    top_table_data.get("rows", [{}])[0]
                    .get("previousClose", "N/A")
                    .replace("$", "")
                )
                if top_table_data.get("rows", [{}])[0].get(
                    "previousClose", "N/A"
                )
                != "N/A"
                else np.nan
            )

            cleaned_trade_data["today_high"] = (
                clean_numeric_value(
                    top_table_data.get("rows", [{}])[0]
                    .get("todayHighLow", "N/A")
                    .split("/")[0]
                    .replace("$", "")
                )
                if top_table_data.get("rows", [{}])[0].get(
                    "todayHighLow", "N/A"
                )
                != "N/A"
                else np.nan
            )

            cleaned_trade_data["today_low"] = (
                clean_numeric_value(
                    top_table_data.get("rows", [{}])[0]
                    .get("todayHighLow", "N/A")
                    .split("/")[1]
                    .replace("$", "")
                )
                if top_table_data.get("rows", [{}])[0].get(
                    "todayHighLow", "N/A"
                )
                != "N/A"
                else np.nan
            )

            cleaned_trade_data["fifty_two_week_high"] = (
                clean_numeric_value(
                    top_table_data.get("rows", [{}])[0]
                    .get("fiftyTwoWeekHighLow", "N/A")
                    .split("/")[0]
                    .replace("$", "")
                )
                if top_table_data.get("rows", [{}])[0].get(
                    "fiftyTwoWeekHighLow", "N/A"
                )
                != "N/A"
                else np.nan
            )

            cleaned_trade_data["fifty_two_week_low"] = (
                clean_numeric_value(
                    top_table_data.get("rows", [{}])[0]
                    .get("fiftyTwoWeekHighLow", "N/A")
                    .split("/")[1]
                    .replace("$", "")
                )
                if top_table_data.get("rows", [{}])[0].get(
                    "fiftyTwoWeekHighLow", "N/A"
                )
                != "N/A"
                else np.nan
            )

            cleaned_trade_data["description"] = (
                description_text if description_text != "N/A" else np.nan
            )

            cleaned_trade_data["message"] = (
                message_text if message_text != "N/A" else np.nan
            )

            cleaned_trades_data.append(cleaned_trade_data)

    return cleaned_trades_data


def fetch_nasdaq_quote(asset_symbol: str, asset_category: str) -> dict:
    """Fetches a quote from NASDAQ.

    Parameters
    ----------
    asset_symbol : str
        The asset symbol.
    asset_category : str
        The asset category.

    Returns
    -------
    dict
        A dictionary representing the quote.
    """
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    api_url = f"https://api.nasdaq.com/api/quote/{asset_symbol}/summary?assetclass={asset_category}"
    api_response = requests.get(api_url, headers=request_headers)

    response_json = api_response.json()

    quote_data = response_json.get("data", {}).get("summaryData", {})

    if asset_category == "stocks":
        cleaned_quote_data = {}
        cleaned_quote_data["symbol"] = asset_symbol
        cleaned_quote_data["exchange"] = quote_data.get("Exchange", {}).get(
            "value", np.nan
        )
        cleaned_quote_data["sector"] = quote_data.get("Sector", {}).get(
            "value", np.nan
        )
        cleaned_quote_data["industry"] = quote_data.get("Industry", {}).get(
            "value", np.nan
        )
        cleaned_quote_data["one_year_target"] = (
            clean_numeric_value(
                quote_data.get("OneYrTarget", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("OneYrTarget", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["today_high"] = (
            clean_numeric_value(
                quote_data.get("TodayHighLow", {})
                .get("value", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["today_low"] = (
            clean_numeric_value(
                quote_data.get("TodayHighLow", {})
                .get("value", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["share_volume"] = (
            clean_numeric_value(
                quote_data.get("ShareVolume", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("ShareVolume", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["average_volume"] = (
            clean_numeric_value(
                quote_data.get("AverageVolume", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("AverageVolume", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["previous_close"] = (
            clean_numeric_value(
                quote_data.get("PreviousClose", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("PreviousClose", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["fifty_two_week_high"] = (
            clean_numeric_value(
                quote_data.get("FiftyTwoWeekHighLow", {})
                .get("value", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("FiftyTwoWeekHighLow", {}).get(
                "value", "N/A"
            )
            else np.nan
        )
        cleaned_quote_data["fifty_two_week_low"] = (
            clean_numeric_value(
                quote_data.get("FiftyTwoWeekHighLow", {})
                .get("value", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("FiftyTwoWeekHighLow", {}).get(
                "value", "N/A"
            )
            else np.nan
        )
        cleaned_quote_data["market_cap"] = (
            clean_numeric_value(
                quote_data.get("MarketCap", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A" not in quote_data.get("MarketCap", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["pe_ratio"] = quote_data.get("PERatio", {}).get(
            "value", np.nan
        )
        cleaned_quote_data["forward_pe_1yr"] = (
            clean_numeric_value(
                quote_data.get("ForwardPE1Yr", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("ForwardPE1Yr", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["eps"] = (
            clean_numeric_value(
                quote_data.get("EarningsPerShare", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("EarningsPerShare", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["annualized_dividend"] = (
            clean_numeric_value(
                quote_data.get("AnnualizedDividend", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("AnnualizedDividend", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["ex_dividend_date"] = (
            quote_data.get("ExDividendDate", {}).get("value", np.nan)
            if "N/A"
            not in quote_data.get("ExDividendDate", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["dividend_payment_date"] = (
            quote_data.get("DividendPaymentDate", {}).get("value", np.nan)
            if "N/A"
            not in quote_data.get("DividendPaymentDate", {}).get(
                "value", "N/A"
            )
            else np.nan
        )
        cleaned_quote_data["current_yield"] = (
            clean_numeric_value(
                quote_data.get("Yield", {})
                .get("value", "N/A")
                .replace("%", "")
            )
            / 100
            if "N/A" not in quote_data.get("Yield", {}).get("value", "N/A")
            else 0
        )
        return cleaned_quote_data

    elif asset_category == "index":
        cleaned_quote_data = {}
        cleaned_quote_data["symbol"] = asset_symbol
        cleaned_quote_data["current_price"] = clean_numeric_value(
            quote_data.get("CurrentPrice", {}).get("value", "N/A")
        )
        cleaned_quote_data["net_change"] = clean_numeric_value(
            quote_data.get("NetChangePercentageChange", {})
            .get("value", "N/A")
            .split("/")[0]
        )
        cleaned_quote_data["net_change_pct"] = (
            clean_numeric_value(
                quote_data.get("NetChangePercentageChange", {})
                .get("value", "N/A")
                .split("/")[1]
                .replace("%", "")
            )
            / 100
        )
        cleaned_quote_data["previous_close"] = clean_numeric_value(
            quote_data.get("PreviousClose", {}).get("value", "N/A")
        )
        cleaned_quote_data["today_high"] = clean_numeric_value(
            quote_data.get("TodaysHigh", {}).get("value", "N/A")
        )
        cleaned_quote_data["today_low"] = clean_numeric_value(
            quote_data.get("TodaysLow", {}).get("value", "N/A")
        )
        cleaned_quote_data["current_yield"] = (
            clean_numeric_value(
                quote_data.get("Yield", {})
                .get("value", "N/A")
                .replace("%", "")
            )
            / 100
            if "N/A" not in quote_data.get("Yield", {}).get("value", "N/A")
            else 0
        )
        return cleaned_quote_data

    elif asset_category == "etf":
        cleaned_quote_data = {}
        cleaned_quote_data["symbol"] = asset_symbol
        cleaned_quote_data["today_high"] = (
            clean_numeric_value(
                quote_data.get("TodayHighLow", {})
                .get("value", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["today_low"] = (
            clean_numeric_value(
                quote_data.get("TodayHighLow", {})
                .get("value", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("TodayHighLow", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["share_volume"] = (
            clean_numeric_value(
                quote_data.get("ShareVolume", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("ShareVolume", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["fifty_day_avg_daily_volume"] = (
            clean_numeric_value(
                quote_data.get("FiftyDayAvgDailyVol", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("FiftyDayAvgDailyVol", {}).get(
                "value", "N/A"
            )
            else np.nan
        )
        cleaned_quote_data["previous_close"] = (
            clean_numeric_value(
                quote_data.get("PreviousClose", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("PreviousClose", {}).get("value", "N/A")
            else np.nan
        )
        cleaned_quote_data["fifty_two_week_high"] = (
            clean_numeric_value(
                quote_data.get("FiftTwoWeekHighLow", {})
                .get("value", "N/A")
                .split("/")[0]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("FiftTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["fifty_two_week_low"] = (
            clean_numeric_value(
                quote_data.get("FiftTwoWeekHighLow", {})
                .get("value", "N/A")
                .split("/")[1]
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("FiftTwoWeekHighLow", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["market_cap"] = (
            clean_numeric_value(
                quote_data.get("MarketCap", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A" not in quote_data.get("MarketCap", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["annualized_dividend"] = (
            clean_numeric_value(
                quote_data.get("AnnualizedDividend", {})
                .get("value", "N/A")
                .replace("$", "")
            )
            if "N/A"
            not in quote_data.get("AnnualizedDividend", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["ex_dividend_date"] = (
            quote_data.get("ExDividendDate", {}).get("value", "N/A")
            if "N/A"
            not in quote_data.get("ExDividendDate", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["dividend_payment_date"] = (
            quote_data.get("DividendPaymentDate", {}).get("value", "N/A")
            if "N/A"
            not in quote_data.get("DividendPaymentDate", {}).get(
                "value", "N/A"
            )
            else np.nan
        )

        cleaned_quote_data["current_yield"] = (
            clean_numeric_value(
                quote_data.get("Yield", {})
                .get("value", "N/A")
                .replace("%", "")
            )
            / 100
            if "N/A" not in quote_data.get("Yield", {}).get("value", "N/A")
            else 0
        )

        cleaned_quote_data["alpha"] = (
            clean_numeric_value(
                quote_data.get("Alpha", {}).get("value", "N/A")
            )
            if "N/A" not in quote_data.get("Alpha", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["weighted_alpha"] = (
            clean_numeric_value(
                quote_data.get("WeightedAlpha", {}).get("value", "N/A")
            )
            if "N/A"
            not in quote_data.get("WeightedAlpha", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["beta"] = (
            clean_numeric_value(quote_data.get("Beta", {}).get("value", "N/A"))
            if isinstance(quote_data.get("Beta", {}).get("value", "N/A"), str)
            and "N/A" not in quote_data.get("Beta", {}).get("value", "N/A")
            else np.nan
        )

        cleaned_quote_data["standard_deviation"] = (
            clean_numeric_value(
                quote_data.get("StandardDeviation", {}).get("value", "N/A")
            )
            if isinstance(
                quote_data.get("StandardDeviation", {}).get("value", "N/A"),
                str,
            )
            and "N/A"
            not in quote_data.get("StandardDeviation", {}).get("value", "N/A")
            else np.nan
        )

        return cleaned_quote_data


def black_scholes_price(
    underlying_price,
    strike_price,
    time_to_expiry,
    risk_free_rate,
    volatility,
    option_type_flag,
    dividend_yield=0,
):
    """Calculates the Black-Scholes price of an option.

    Parameters
    ----------
    underlying_price : float
        The price of the underlying asset.
    strike_price : float
        The strike price of the option.
    time_to_expiry : float
        The time to expiry of the option in years.
    risk_free_rate : float
        The risk-free interest rate.
    volatility : float
        The volatility of the underlying asset.
    option_type_flag : str
        The type of option, 'c' for call or 'p' for put.
    dividend_yield : float, optional
        The dividend yield of the underlying asset, by default 0.

    Returns
    -------
    float
        The Black-Scholes price of the option.
    """
    if time_to_expiry <= 0:
        return max(
            0.0,
            (underlying_price - strike_price)
            if option_type_flag == "c"
            else (strike_price - underlying_price),
        )

    d1 = (
        np.log(underlying_price / strike_price)
        + (risk_free_rate - dividend_yield + 0.5 * volatility**2)
        * time_to_expiry
    ) / (volatility * np.sqrt(time_to_expiry))
    d2 = d1 - volatility * np.sqrt(time_to_expiry)

    if option_type_flag == "c":
        price = underlying_price * np.exp(
            -dividend_yield * time_to_expiry
        ) * norm.cdf(d1) - strike_price * np.exp(
            -risk_free_rate * time_to_expiry
        ) * norm.cdf(d2)
    else:
        price = strike_price * np.exp(
            -risk_free_rate * time_to_expiry
        ) * norm.cdf(-d2) - underlying_price * np.exp(
            -dividend_yield * time_to_expiry
        ) * norm.cdf(-d1)

    return price


def implied_volatility_brent(
    option_price,
    underlying_price,
    strike_price,
    time_to_expiry,
    risk_free_rate,
    option_type_flag,
    dividend_yield=0,
    tol=1e-6,
    maxiter=100,
):
    """Calculates the implied volatility of an option using the Brent method.

    Parameters
    ----------
    option_price : float
        The price of the option.
    underlying_price : float
        The price of the underlying asset.
    strike_price : float
        The strike price of the option.
    time_to_expiry : float
        The time to expiry of the option in years.
    risk_free_rate : float
        The risk-free interest rate.
    option_type_flag : str
        The type of option, 'c' for call or 'p' for put.
    dividend_yield : float, optional
        The dividend yield of the underlying asset, by default 0.
    tol : float, optional
        The tolerance for the Brent method, by default 1e-6.
    maxiter : int, optional
        The maximum number of iterations for the Brent method, by default 100.

    Returns
    -------
    float
        The implied volatility of the option.
    """
    vol_lower, vol_upper = 1e-4, 5.0

    f = lambda vol: (
        black_scholes_price(
            underlying_price,
            strike_price,
            time_to_expiry,
            risk_free_rate,
            vol,
            option_type_flag,
            dividend_yield,
        )
        - option_price
    )

    try:
        return brentq(f, vol_lower, vol_upper, xtol=tol, maxiter=maxiter)
    except ValueError:
        return np.nan


def calculate_chain_implied_volatility(option_chain, pricing_model=None):
    """Calculates the implied volatility for an entire option chain.

    Parameters
    ----------
    option_chain : pandas.DataFrame
        The option chain.
    pricing_model : str, optional
        The pricing model to use, by default None.

    Returns
    -------
    pandas.DataFrame
        The option chain with an added 'implied_volatility' column.
    """
    S = option_chain["underlying_price"].to_numpy()
    K = option_chain["contract_strike"].to_numpy()
    T = option_chain["years_until_expiry"].to_numpy()
    r = (
        option_chain["risk_free_rate"].iloc[0]
        if isinstance(option_chain["risk_free_rate"], pd.Series)
        else option_chain["risk_free_rate"]
    )
    div = (
        option_chain["underlying_dividend_yield"].to_numpy()
        if "underlying_dividend_yield" in option_chain.columns
        else 0.0
    )
    price = option_chain["contract_last_price"].to_numpy()
    flag = np.where(
        option_chain["contract_type"].str.lower() == "call", "c", "p"
    )

    intrinsic = np.where(
        flag == "c", np.maximum(0, S - K), np.maximum(0, K - S)
    )

    mask = (price > intrinsic) & (T > 0)
    iv = np.full_like(price, np.nan, dtype=float)

    for idx in np.where(mask)[0]:
        iv[idx] = implied_volatility_brent(
            option_price=price[idx],
            underlying_price=S[idx],
            strike_price=K[idx],
            time_to_expiry=T[idx],
            risk_free_rate=r,
            option_type_flag=flag[idx],
            dividend_yield=div[idx] if isinstance(div, np.ndarray) else div,
        )

    option_chain["implied_volatility"] = iv
    return option_chain


def calculate_chain_greeks(option_chain):
    """Calculates the Greeks for an entire option chain.

    Parameters
    ----------
    option_chain : pandas.DataFrame
        The option chain.

    Returns
    -------
    pandas.DataFrame
        The option chain with added columns for each of the Greeks.
    """
    S = option_chain["underlying_price"].to_numpy()
    K = option_chain["contract_strike"].to_numpy()
    T = option_chain["years_until_expiry"].to_numpy()
    r = (
        option_chain["risk_free_rate"].iloc[0]
        if isinstance(option_chain["risk_free_rate"], pd.Series)
        else option_chain["risk_free_rate"]
    )
    sigma = option_chain["implied_volatility"].to_numpy()
    flag = np.where(
        option_chain["contract_type"].str.lower() == "call", "c", "p"
    )
    q = (
        option_chain["underlying_dividend_yield"].to_numpy()
        if "underlying_dividend_yield" in option_chain.columns
        else np.zeros_like(S)
    )

    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    pdf_d1 = norm.pdf(d1)

    delta = np.where(
        flag == "c",
        np.exp(-q * T) * norm.cdf(d1),
        -np.exp(-q * T) * norm.cdf(-d1),
    )

    gamma = np.exp(-q * T) * pdf_d1 / (S * sigma * sqrt_T)

    vega = S * np.exp(-q * T) * pdf_d1 * sqrt_T

    theta = np.where(
        flag == "c",
        -(S * pdf_d1 * sigma * np.exp(-q * T)) / (2 * sqrt_T)
        - r * K * np.exp(-r * T) * norm.cdf(d2)
        + q * S * np.exp(-q * T) * norm.cdf(d1),
        -(S * pdf_d1 * sigma * np.exp(-q * T)) / (2 * sqrt_T)
        + r * K * np.exp(-r * T) * norm.cdf(-d2)
        - q * S * np.exp(-q * T) * norm.cdf(-d1),
    )

    rho = np.where(
        flag == "c",
        K * T * np.exp(-r * T) * norm.cdf(d2),
        -K * T * np.exp(-r * T) * norm.cdf(-d2),
    )

    option_chain["delta"] = delta
    option_chain["gamma"] = gamma
    option_chain["theta"] = theta
    option_chain["vega"] = vega
    option_chain["rho"] = rho

    return option_chain
