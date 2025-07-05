import datetime
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas
import seaborn as sns


def remove_outliers(data, column, threshold=3):
    """Removes outliers from a DataFrame based on the Median Absolute Deviation (MAD).

    Parameters
    ----------
    data : pandas.DataFrame
        The input DataFrame.
    column : str
        The name of the column from which to remove outliers.
    threshold : int, optional
        The Z-score threshold to use for outlier detection, by default 3.

    Returns
    -------
    pandas.DataFrame
        The DataFrame with outliers removed.
    """
    cleaned_data = data.copy()
    median = cleaned_data[column].median()
    mad = np.median(np.abs(cleaned_data[column] - median))
    mask = np.abs(cleaned_data[column] - median) / mad <= threshold
    cleaned_data = cleaned_data[mask]
    return cleaned_data


class OptionsChain:
    """A class to represent and visualize an options chain.

    Parameters
    ----------
    data : pandas.DataFrame
        A DataFrame containing the options chain data.

    Attributes
    ----------
    data : pandas.DataFrame
        The options chain data.
    asset_symbol : str
        The ticker symbol of the underlying asset.
    """

    def __init__(self, data: "pandas.DataFrame"):
        self.data = data
        self.asset_symbol = (
            data.get("underlying_symbol").iloc[0]
            if "underlying_symbol" in data.columns
            else None
        )

    def plot_2d(
        self,
        z_variable: str = None,
        option_type: str = None,
        strike_range: list = None,
        years_to_expiry_range: list = None,
    ):
        """Plots a 2D representation of a specified variable.

        This method plots the specified variable as a function of strike price
        and time to expiry. If no variable is specified, it plots a series of
        subplots for common option Greeks and metrics.

        Parameters
        ----------
        z_variable : str, optional
            The variable to plot (e.g., 'delta', 'gamma'). If None, plots all
            supported variables. By default None.
        option_type : str, optional
            The type of option to plot ('Call' or 'Put'). If None, plots both.
            By default None.
        strike_range : list, optional
            A list containing the minimum and maximum strike prices to include.
            By default None.
        years_to_expiry_range : list, optional
            A list containing the minimum and maximum years to expiry.
            By default None.

        Returns
        -------
        self
            The OptionsChain object.
        """
        if "years_until_expiry" not in self.data.columns:
            raise Exception(
                "Plotting functions are only available for Processed DataFrames."
            )

        sns.set_style("darkgrid")
        plot_data = self.data.copy()
        if option_type:
            plot_data = plot_data[
                plot_data["contract_type"] == option_type.capitalize()
            ]
        if strike_range:
            plot_data = plot_data[
                plot_data["contract_strike"].between(
                    strike_range[0], strike_range[1]
                )
            ]
        if years_to_expiry_range:
            plot_data = plot_data[
                plot_data["years_until_expiry"].between(
                    years_to_expiry_range[0], years_to_expiry_range[1]
                )
            ]

        plot_data["expiry_months"] = (
            plot_data["years_until_expiry"] * 12 / 3
        ).round(0) * 3
        plot_data["strike_rounded"] = (plot_data["contract_strike"] // 10) * 10

        variable_mapping = {
            "option_price": "contract_last_price",
            "price": "contract_last_price",
            "implied_volatility": "implied_volatility",
            "iv": "implied_volatility",
            "delta": "delta",
            "gamma": "gamma",
            "theta": "theta",
            "vega": "vega",
            "rho": "rho",
        }

        if z_variable:
            variable_key = z_variable.lower().strip()
            if variable_key not in variable_mapping:
                raise ValueError(
                    "z_variable must be one of: 'option_price', 'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'"
                )
            column_name = variable_mapping[variable_key]
            grouped_data = (
                plot_data.groupby(["expiry_months", "strike_rounded"])[
                    column_name
                ]
                .mean()
                .reset_index()
                .dropna()
            )

            figure, axis = plt.subplots(figsize=(10, 6))

            for expiry in np.sort(grouped_data["expiry_months"].unique()):
                expiry_group = grouped_data[
                    grouped_data["expiry_months"] == expiry
                ]
                axis.plot(
                    expiry_group["strike_rounded"],
                    expiry_group[column_name],
                    label=f"{expiry} Months",
                )
            axis.set_xlabel("Strike Price")

            axis.set_ylabel(column_name)

            axis.legend()

            axis.set_title(f"{column_name} vs Strike Price and Time to Expiry")

            plt.show()

        else:
            variables = list(dict.fromkeys(variable_mapping.values()))
            num_variables = len(variables)
            num_columns = 2
            num_rows = int(np.ceil(num_variables / num_columns))
            figure, axes = plt.subplots(
                num_rows, num_columns, figsize=(12, num_rows * 4)
            )
            axes = axes.flatten()

            for i, var in enumerate(variables):
                grouped_data = (
                    plot_data.groupby(["expiry_months", "strike_rounded"])[var]
                    .mean()
                    .reset_index()
                    .dropna()
                )
                axis = axes[i]
                for expiry in np.sort(grouped_data["expiry_months"].unique()):
                    expiry_group = grouped_data[
                        grouped_data["expiry_months"] == expiry
                    ]
                    axis.plot(
                        expiry_group["strike_rounded"],
                        expiry_group[var],
                        label=f"{expiry} Months",
                    )
                axis.set_xlabel("Strike Price")

                axis.set_ylabel(var)

                axis.set_title(f"{var} vs Strike Price and Time to Expiry")

                axis.legend()

            for j in range(i + 1, len(axes)):
                figure.delaxes(axes[j])

            plt.tight_layout()

            plt.show()

        return self

    def plot_3d(
        self,
        z_variable: str = None,
        option_type: str = "Call",
        strike_range: tuple = None,
        years_to_expiry_range: tuple = None,
        figure_size: tuple = (12, 12),
        color_map: str = "viridis",
        edge_color: str = "none",
        alpha_value: float = 0.9,
        viewing_angle: tuple = (15, 315),
        box_aspect_ratio: tuple = (36, 36, 18),
        show_scatter_plot: bool = True,
    ):
        """Plots a 3D representation of a specified variable.

        This method creates a 3D surface plot of the specified variable as a
        function of strike price and time to maturity. If no variable is
        specified, it plots all supported variables in subplots.

        Parameters
        ----------
        z_variable : str, optional
            The variable to plot (e.g., 'delta'). If None, plots all supported
            variables. By default None.
        option_type : str, optional
            The type of option to plot ('Call' or 'Put'). By default "Call".
        strike_range : tuple, optional
            A tuple containing the min and max strike prices. By default None.
        years_to_expiry_range : tuple, optional
            A tuple containing the min and max years to expiry. By default None.
        figure_size : tuple, optional
            The size of the figure. By default (12, 12).
        color_map : str, optional
            The colormap to use for the plot. By default "viridis".
        edge_color : str, optional
            The color of the edges of the surface plot. By default "none".
        alpha_value : float, optional
            The opacity of the surface plot. By default 0.9.
        viewing_angle : tuple, optional
            The viewing angle (elevation, azimuth). By default (15, 315).
        box_aspect_ratio : tuple, optional
            The aspect ratio of the 3D plot box. By default (36, 36, 18).
        show_scatter_plot : bool, optional
            Whether to show the original data points as a scatter plot.
            By default True.

        Returns
        -------
        self
            The OptionsChain object.
        """
        if "years_until_expiry" not in self.data.columns:
            raise Exception(
                "Plotting functions are only available for Processed DataFrames."
            )

        sns.set_style("whitegrid")

        plot_data = self.data.copy()
        if option_type:
            plot_data = plot_data[
                plot_data["contract_type"] == option_type.capitalize()
            ]
        if strike_range:
            plot_data = plot_data[
                plot_data["contract_strike"].between(
                    strike_range[0], strike_range[1]
                )
            ]
        if years_to_expiry_range:
            plot_data = plot_data[
                plot_data["years_until_expiry"].between(
                    years_to_expiry_range[0], years_to_expiry_range[1]
                )
            ]

        plot_data["implied_volatility"] = plot_data[
            "implied_volatility"
        ].replace([np.inf, -np.inf], np.nan)

        plot_data = plot_data.dropna(subset=["implied_volatility"])

        plot_data = remove_outliers(
            plot_data, "implied_volatility", threshold=3
        )

        variable_mapping = {
            "option_price": "contract_last_price",
            "price": "contract_last_price",
            "implied_volatility": "implied_volatility",
            "iv": "implied_volatility",
            "delta": "delta",
            "gamma": "gamma",
            "theta": "theta",
            "vega": "vega",
            "rho": "rho",
        }

        def plot_3d_column(column_name, axis):
            plot_data["expiry_months"] = (
                plot_data["years_until_expiry"] * 12 / 3
            ).round(0) * 3
            plot_data["strike_rounded"] = (
                plot_data["contract_strike"] // 10
            ) * 10
            grouped_data = (
                plot_data.groupby(["expiry_months", "strike_rounded"])[
                    column_name
                ]
                .mean()
                .reset_index()
                .dropna()
            )
            pivot_table = grouped_data.pivot(
                index="strike_rounded",
                columns="expiry_months",
                values=column_name,
            )
            strike_values = pivot_table.index.values

            expiration_values = pivot_table.columns.values

            expiration_grid, strike_grid = np.meshgrid(
                expiration_values, strike_values
            )

            z_values = pivot_table.values

            surface = axis.plot_surface(
                expiration_grid,
                strike_grid,
                z_values,
                cmap=color_map,
                edgecolor=edge_color,
                alpha=alpha_value,
            )

            axis.set_xlabel("Months until Expiry")

            axis.set_ylabel("Contract Strike price")

            axis.set_zlabel(column_name)

            axis.view_init(viewing_angle[0], viewing_angle[1])

            axis.set_box_aspect(box_aspect_ratio)

            if show_scatter_plot:
                axis.scatter(
                    expiration_grid,
                    strike_grid,
                    z_values,
                    color="black",
                    marker="+",
                    s=5,
                )

            asset_symbol = (
                plot_data["underlying_symbol"].iloc[0]
                if "underlying_symbol" in plot_data.columns
                else None
            )
            if column_name == "contract_last_price":
                column_name = "Option Price"

            if plot_data["contract_type"].unique().size == 1:
                option_type = plot_data["contract_type"].unique()[0]

                if asset_symbol:
                    axis.set_title(
                        f"{asset_symbol} {option_type} {column_name} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')})"
                    )

                else:
                    axis.set_title(
                        f"{column_name} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')})"
                    )

            else:
                if asset_symbol:
                    axis.set_title(
                        f"{asset_symbol} {column_name} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')})"
                    )

                else:
                    axis.set_title(
                        f"{column_name} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')})"
                    )

            return surface

        if z_variable:
            variable_key = z_variable.lower().strip()
            if variable_key not in variable_mapping:
                raise ValueError(
                    "z_variable must be one of: 'option_price', 'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'"
                )
            column_name = variable_mapping[variable_key]
            figure = plt.figure(figsize=figure_size)
            axis = figure.add_subplot(111, projection="3d")
            surface = plot_3d_column(column_name, axis)
            figure.colorbar(surface, shrink=0.5, aspect=12, label=column_name)
            plt.show()
        else:
            variables = list(dict.fromkeys(variable_mapping.values()))
            num_variables = len(variables)
            num_columns = 4
            num_rows = math.ceil(num_variables / num_columns)
            figure = plt.figure(
                figsize=(
                    figure_size[0] * num_columns,
                    figure_size[1] * num_rows,
                )
            )
            for i, var in enumerate(variables):
                axis = figure.add_subplot(
                    num_rows, num_columns, i + 1, projection="3d"
                )
                surface = plot_3d_column(var, axis)
                figure.colorbar(
                    surface, ax=axis, shrink=0.5, aspect=12, label=var
                )
            plt.tight_layout()
            plt.show()
        return self
