from abc import ABC, abstractmethod

from src.models.chart_models import BarChart, LineChart, FunnelChart

class ChartDesigner(ABC):
    def __init__(self, color_sequence, palette):
        self.color_sequence = color_sequence
        self.palette = palette

    @abstractmethod
    def draw_bar_chart(self, data: BarChart, theme: str) -> str:
        pass

    @abstractmethod
    def draw_line_chart(self, data: LineChart, theme: str) -> str:
        pass

    @abstractmethod
    def draw_funnel_chart(self, data: FunnelChart, theme: str) -> str:
        pass
