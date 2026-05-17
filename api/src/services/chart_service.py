from src.models.chart_models import BarChart, LineChart, FunnelChart
from src.ports.chart_designer import ChartDesigner


class ChartService:
    def __init__(self, chart_designer: ChartDesigner):
        self.chart_designer = chart_designer
        self._charts = {}  # Cache para gráficos gerados
        self._chart_id_counter = 0
        self._theme = "light"

    def set_theme(self, theme: str):
        if not theme in ["dark", "light"]:
            raise ValueError(f"The theme {theme} is not supported. Use 'dark' or 'light'.")
        self._theme = theme

    def get_chart(self, chart_id: int) -> str:
        chart = self._charts.get(chart_id)
        if chart is None:
            raise ValueError(f"Chart with ID {chart_id} not found.")
        return chart

    def draw_bar_chart(self, data: BarChart, theme: str):
        chart_svg = self.chart_designer.draw_bar_chart(data, theme=theme)
        self._chart_id_counter += 1
        self._charts[self._chart_id_counter] = chart_svg
        return {
            "chart_id": self._chart_id_counter,
            "svg": chart_svg
        }

    def draw_line_chart(self, data: LineChart, theme: str):
        chart_svg = self.chart_designer.draw_line_chart(data, theme=theme)
        self._chart_id_counter += 1
        self._charts[self._chart_id_counter] = chart_svg
        return {
            "chart_id": self._chart_id_counter,
            "svg": chart_svg
        }
    
    def draw_funnel_chart(self, data: FunnelChart, theme: str):
        chart_svg = self.chart_designer.draw_funnel_chart(data, theme=theme)
        self._chart_id_counter += 1
        self._charts[self._chart_id_counter] = chart_svg
        return {
            "chart_id": self._chart_id_counter,
            "svg": chart_svg
        }