from src.adapters.plotly_adapter import PlotlyChartDesigner
from src.models.chart_models import BarChart, BarSeries


PALETTE = {
    "positive": "#00ff00",
    "negative": "#ff0000",
    "text": "#ffffff",
    "text_muted": "#aaaaaa",
    "neutral": "#888888",
    "bg": "#061222",
    "grid": "#1a2a3a",
}


def test_draw_bar_chart_runs_without_error():
    designer = PlotlyChartDesigner(color_sequence=["#1f77b4"], palette=PALETTE)
    chart = BarChart(
        title="Test",
        subtitle="",
        x_label="X",
        y_label="Y",
        orientation="vertical",
        mode="group",
        series=[BarSeries(label="A", x=["Jan", "Fev"], y=[10, 20], color_rule=None)],
    )
    result = designer.draw_bar_chart(chart)
    assert isinstance(result, str)
    assert "<svg" in result
