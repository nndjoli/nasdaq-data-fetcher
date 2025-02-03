import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import datetime
import pandas
import math


def RemoveOutliers(Data, Column, Threshold=3):

    CleanedData = Data.copy()
    Median = CleanedData[Column].median()
    MAD = np.median(np.abs(CleanedData[Column] - Median))
    Mask = np.abs(CleanedData[Column] - Median) / MAD <= Threshold
    CleanedData = CleanedData[Mask]
    return CleanedData


class OC:
    def __init__(self, Data: "pandas.DataFrame"):

        self.Data = Data
        self.Asset = Data["Underlying Symbol"].iloc[0]

    def Plot2D(self, x: str = None, Type: str = None, StrikeRange: list = None, YToExpiryRange: list = None):
        """
        Plots in 2D the specified variable 'x' as a function of strike and time until expiry.

        If 'x' is None, plots the following 7 variables in separate subplots:
            - Option Price ("Contract Last Price")
            - Implied Volatility ("Implied Volatility")
            - Delta
            - Gamma
            - Theta
            - Vega
            - Rho

        Parameters:
            x (str, optional): The variable to plot (e.g., 'Delta', 'Implied Volatility', etc.).
            Type (str, optional): Filter by option type (e.g., 'Call' or 'Put').
            StrikeRange (list, optional): [min, max] range to filter the 'Contract Strike' column.
            YToExpiryRange (list, optional): [min, max] range to filter the 'Years Until Expiry' column.
        """
        sns.set_style("darkgrid")
        Data = self.Data.copy()
        if Type:
            Data = Data[Data["Contract Type"] == Type.capitalize()]
        if StrikeRange:
            Data = Data[Data["Contract Strike"].between(StrikeRange[0], StrikeRange[1])]
        if YToExpiryRange:
            Data = Data[Data["Years Until Expiry"].between(YToExpiryRange[0], YToExpiryRange[1])]

        Data["Expiry (Months)"] = (Data["Years Until Expiry"] * 12 / 3).round(0) * 3
        Data["Strike (rounded10)"] = (Data["Contract Strike"] // 10) * 10

        Mapping = {
            "option price": "Contract Last",
            "price": "Contract Last",
            "implied volatility": "Implied Volatility",
            "iv": "Implied Volatility",
            "delta": "Delta",
            "gamma": "Gamma",
            "theta": "Theta",
            "vega": "Vega",
            "rho": "Rho",
        }

        if x:
            Key = x.lower().strip()
            if Key not in Mapping:
                raise ValueError("x must be one of: 'option price', 'implied volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'")
            Column = Mapping[Key]
            Grouped = Data.groupby(["Expiry (Months)", "Strike (rounded10)"])[Column].mean().reset_index().dropna()

            Figure, ax = plt.subplots(figsize=(10, 6))
            for Expiry in np.sort(Grouped["Expiry (Months)"].unique()):
                Group = Grouped[Grouped["Expiry (Months)"] == Expiry]
                ax.plot(Group["Strike (rounded10)"], Group[Column], label=f"{Expiry} Months")
            ax.set_xlabel("Strike Price")
            ax.set_ylabel(Column)
            ax.legend()
            ax.set_title(f"{Column} vs Strike Price and Time to Expiry")
            plt.show()
        else:

            Variables = list(dict.fromkeys(Mapping.values()))
            NVariables = len(Variables)
            NColumns = 2
            nrows = int(np.ceil(NVariables / NColumns))
            Figure, Axes = plt.subplots(nrows, NColumns, figsize=(12, nrows * 4))
            Axes = Axes.flatten()

            for i, Variable in enumerate(Variables):
                Grouped = Data.groupby(["Expiry (Months)", "Strike (rounded10)"])[Variable].mean().reset_index().dropna()
                ax = Axes[i]
                for Expiry in np.sort(Grouped["Expiry (Months)"].unique()):
                    Group = Grouped[Grouped["Expiry (Months)"] == Expiry]
                    ax.plot(Group["Strike (rounded10)"], Group[Variable], label=f"{Expiry} Months")
                ax.set_xlabel("Strike Price")
                ax.set_ylabel(Variable)
                ax.set_title(f"{Variable} vs Strike Price and Time to Expiry")
                ax.legend()

            for j in range(i + 1, len(Axes)):
                Figure.delaxes(Axes[j])
            plt.tight_layout()
            plt.show()
        return self

    def Plot3D(
        self,
        x: str = None,
        Type: str = "Call",
        StrikeRange: tuple = None,
        YToExpiryRange: tuple = None,
        FigSize: tuple = (12, 12),
        CMap: str = "viridis",
        EdgeColor: str = "none",
        Alpha: float = 0.9,
        ViewAngle: tuple = (15, 315),
        BoxAspect: tuple = (36, 36, 18),
        ShowScatter: bool = True,
    ):
        """
        Plots in 3D the specified variable 'x' as a function of strike and time until maturity.

        If 'x' is specified, a single 3D plot is displayed. If 'x' is None, 3D plots for the following 7 Variables are shown,
        each in its own subplot:
            - Option Price ("Contract Last Price")
            - Implied Volatility ("Implied Volatility")
            - Delta
            - Gamma
            - Theta
            - Vega
            - Rho

        Parameters:
            x (str, optional): The variable to plot (e.g., 'delta', 'implied volatility', etc.). If None, plots all Variables.
            Type (str, optional): Filter by option type (e.g., 'Call' or 'Put'). If None, plots both.
            StrikeRange (tuple, optional): (min, max) range to filter the 'Contract Strike' column.
            YToExpiryRange (tuple, optional): (min, max) range to filter the 'Years Until Expiry' column.
            FigSize (tuple, optional): Figure size.
            CMap (str, optional): Colormap to use.
            EdgeColor (str, optional): Edge color for the surface.
            Alpha (float, optional): Opacity of the surface.
            ViewAngle (tuple, optional): Viewing angle (elevation, azimuth).
            BoxAspect (tuple, optional): Aspect ratio of the 3D plot.
            ShowScatter (bool, optional): Whether to display the original Data points.
        """
        sns.set_style("whitegrid")

        Data = self.Data.copy()
        if Type:
            Data = Data[Data["Contract Type"] == Type.capitalize()]
        if StrikeRange:
            Data = Data[Data["Contract Strike"].between(StrikeRange[0], StrikeRange[1])]
        if YToExpiryRange:
            Data = Data[Data["Years Until Expiry"].between(YToExpiryRange[0], YToExpiryRange[1])]

        Data["Implied Volatility"] = Data["Implied Volatility"].replace([np.inf, -np.inf], np.nan)
        Data = Data.dropna(subset=["Implied Volatility"])

        Data = RemoveOutliers(Data, "Implied Volatility", Threshold=3)

        Mapping = {
            "option price": "Contract Last",
            "price": "Contract Last",
            "implied volatility": "Implied Volatility",
            "iv": "Implied Volatility",
            "delta": "Delta",
            "gamma": "Gamma",
            "theta": "Theta",
            "vega": "Vega",
            "rho": "Rho",
        }

        def Plot3DColumn(Column, ax):

            Data["Expiry (Months)"] = (Data["Years Until Expiry"] * 12 / 3).round(0) * 3
            Data["Strike (rounded10)"] = (Data["Contract Strike"] // 10) * 10
            Grouped = Data.groupby(["Expiry (Months)", "Strike (rounded10)"])[Column].mean().reset_index().dropna()
            Pivot = Grouped.pivot(index="Strike (rounded10)", columns="Expiry (Months)", values=Column)
            Strikes = Pivot.index.values
            Expiries = Pivot.columns.values
            ExpiryGrid, StrikeGrid = np.meshgrid(Expiries, Strikes)
            Z = Pivot.values

            Surface = ax.plot_surface(ExpiryGrid, StrikeGrid, Z, cmap=CMap, edgecolor=EdgeColor, alpha=Alpha)
            ax.set_xlabel("Months until Expiry")
            ax.set_ylabel("Contract Strike price")
            ax.set_zlabel(Column)
            ax.view_init(ViewAngle[0], ViewAngle[1])
            ax.set_box_aspect(BoxAspect)
            if ShowScatter:
                ax.scatter(ExpiryGrid, StrikeGrid, Z, color="black", marker="+", s=5)

            Asset = Data["Underlying Symbol"].iloc[0]
            if Column == "Contract Last":
                Column = "Option Price"
            if Data["Contract Type"].unique().size == 1:
                Type = Data["Contract Type"].unique()[0]
                ax.set_title(
                    f"{Asset} {Type} {Column} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')}) for {Type} Options"
                )
            else:
                ax.set_title(f"{Asset} {Column} over Time to Expiry and Strike Price ({datetime.datetime.today().strftime('%B %d, %Y')})")
            return Surface

        if x:
            Key = x.lower().strip()
            if Key not in Mapping:
                raise ValueError("x must be one of: 'option price', 'implied volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'")
            Column = Mapping[Key]
            Figure = plt.figure(figsize=FigSize)
            ax = Figure.add_subplot(111, projection="3d")
            Surface = Plot3DColumn(Column, ax)
            Figure.colorbar(Surface, shrink=0.5, aspect=12, label=Column)
            plt.show()
        else:
            Variables = list(dict.fromkeys(Mapping.values()))
            NVariables = len(Variables)
            NColumns = 4
            nrows = math.ceil(NVariables / NColumns)
            Figure = plt.figure(figsize=(FigSize[0] * NColumns, FigSize[1] * nrows))
            for i, Variable in enumerate(Variables):
                ax = Figure.add_subplot(nrows, NColumns, i + 1, projection="3d")
                Surface = Plot3DColumn(Variable, ax)
                Figure.colorbar(Surface, ax=ax, shrink=0.5, aspect=12, label=Variable)
            plt.tight_layout()
            plt.show()
        return self
