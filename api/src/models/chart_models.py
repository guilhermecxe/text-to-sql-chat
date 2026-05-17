from pydantic import BaseModel, Field
from typing import Literal


class BarSeries(BaseModel):
    label: str
    x: list
    y: list
    # color: str | list[str] | None = None
    color_rule: Literal["fixed", "threshold", "sign"] | None
    threshold: float | None = None

class BarChart(BaseModel):
    title: str
    subtitle: str
    x_label: str
    y_label: str
    orientation: str = Field(..., pattern="^(vertical|horizontal)$")
    mode: str = Field(..., pattern="^(group|stack)$")
    width: int = 800
    height: int = 600
    show_values: bool = Field(default=True, description="Whether to show values on the bars")
    value_prefix: str = Field(default="", description="Prefix to add before values (e.g., 'R$ ' for currency)")
    value_suffix: str = Field(default="", description="Suffix to add after values (e.g., ' %' for percentages)")
    value_format: str = Field(default=",.0f", description="Format string for values (e.g., ':.2f' for 2 decimal places)")
    series: list[BarSeries]


class LineSeries(BaseModel):
    label: str
    x: list
    y: list
    # color: str | None = None
    dash: Literal["solid", "dot", "dash", "longdash", "dashdot"] = "solid"
    show_markers: bool = False
    fill: Literal["none", "tozeroy", "tonexty"] = "none"

class LineChart(BaseModel):
    title: str
    subtitle: str = ""
    x_label: str = ""
    y_label: str = ""
    width: int = 800
    height: int = 600
    show_values: bool = False
    value_prefix: str = ""
    value_suffix: str = ""
    value_format: str = ",.0f"
    series: list[LineSeries]


class FunnelSeries(BaseModel):
    label: str
    x: list = Field(..., description="Stage names (categories), from top to bottom")
    y: list = Field(..., description="Numeric value for each stage; must match len(x)")

class FunnelChart(BaseModel):
    title: str
    subtitle: str = ""
    x_label: str = ""
    y_label: str = ""
    width: int = 800
    height: int = 600
    show_values: bool = Field(default=True, description="Show the formatted value inside each funnel band")
    show_percent: bool = Field(default=True, description="Show % relative to the first stage (percent initial) alongside each value")
    value_prefix: str = ""
    value_suffix: str = ""
    value_format: str = Field(default=",.0f", description="Format string for values (e.g., ',.2f' for 2 decimal places)")
    series: list[FunnelSeries]
