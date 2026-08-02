from src.adapters.plotly_adapter import PlotlyChartDesigner
from src.models.chart_models import BarChart, BarSeries
from src.settings import Settings


def test_draw_bar_chart_runs_without_error():
    designer = PlotlyChartDesigner(Settings())
    chart = BarChart(
        title="Test",
        subtitle="",
        x_label="X",
        y_label="Y",
        orientation="vertical",
        mode="group",
        series=[BarSeries(label="A", x=["Jan", "Fev"], y=[10, 20], color_rule=None)],
    )
    result = designer.draw_bar_chart(chart, theme="light")
    assert isinstance(result, str)
    assert "<svg" in result
