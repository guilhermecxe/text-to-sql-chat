from langchain_core.tools import StructuredTool
from langchain.agents import AgentState
from langchain.agents.middleware import after_agent
from langgraph.runtime import Runtime
from contextlib import contextmanager
from contextvars import ContextVar
import re

from src.services.chart_service import ChartService
from src.models.chart_models import BarChart, LineChart, FunnelChart


class ChartToolkit:
    """Toolkit de geração de gráficos para uso em agentes LangChain.

    Adapta os métodos de ChartService para ferramentas compatíveis com
    LangChain (StructuredTool). O tema ativo é gerenciado via ContextVar,
    garantindo isolamento por corrotina em execuções concorrentes.
    """

    def __init__(self, chart_service: ChartService):
        self._chart_service = chart_service
        self._chart_theme: ContextVar[str] = ContextVar("chart_theme", default="None")

    @contextmanager
    def apply_theme(self, theme: str):
        """Context manager que define o tema ativo para geração de gráficos.

        O tema é armazenado em ContextVar, garantindo isolamento por corrotina
        em execuções concorrentes.

        Args:
            theme (str): Nome do tema a aplicar (ex.: ``"dark"`` ou ``"light"``).

        Yields:
            None
        """
        token = self._chart_theme.set(theme)
        try:
            yield
        finally:
            self._chart_theme.reset(token)

    def _bar_chart(self, data: BarChart) -> dict:
        """Gera um gráfico de barras e retorna o ID do gráfico gerado.

        Args:
            data (BarChart): Configuração completa do gráfico de barras.

        Returns:
            dict: Dicionário com a chave ``chart_id`` (int) referenciando o SVG
                armazenado no ChartService.

        Raises:
            RuntimeError: Se a geração do gráfico falhar por qualquer motivo.
        """
        try:
            theme = self._chart_theme.get()
            chart_dict = self._chart_service.draw_bar_chart(data, theme=theme)

            return {
                "chart_id": chart_dict["chart_id"]
            }
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar gráfico de barras: {str(e)}")
        
    def _line_chart(self, data: LineChart) -> dict:
        """Gera um gráfico de linhas e retorna o ID do gráfico gerado.

        Args:
            data (LineChart): Configuração completa do gráfico de linhas.

        Returns:
            dict: Dicionário com a chave ``chart_id`` (int) referenciando o SVG
                armazenado no ChartService.

        Raises:
            RuntimeError: Se a geração do gráfico falhar por qualquer motivo.
        """
        try:
            theme = self._chart_theme.get()
            chart_dict = self._chart_service.draw_line_chart(data, theme=theme)

            return {
                "chart_id": chart_dict["chart_id"]
            }
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar gráfico de linhas: {str(e)}")
        
    def _funnel_chart(self, data: FunnelChart) -> dict:
        """Gera um gráfico de funil e retorna o ID do gráfico gerado.

        Args:
            data (FunnelChart): Configuração completa do gráfico de funil.

        Returns:
            dict: Dicionário com a chave ``chart_id`` (int) referenciando o SVG
                armazenado no ChartService.

        Raises:
            RuntimeError: Se a geração do gráfico falhar por qualquer motivo.
        """
        try:
            theme = self._chart_theme.get()
            chart_dict = self._chart_service.draw_funnel_chart(data, theme=theme)

            return {
                "chart_id": chart_dict["chart_id"]
            }
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar gráfico de funil: {str(e)}")
        
    def gather_charts(self, message: str):
        """Extrai IDs de gráficos de uma mensagem e retorna os SVGs correspondentes.

        Procura por ocorrências do padrão ``[[chart=<id>]]`` na mensagem e busca
        os SVGs no ChartService para cada ID encontrado.

        Args:
            message (str): Texto da mensagem que pode conter referências a gráficos.

        Returns:
            dict[str, str]: Mapeamento de ``chart_id`` (str) para o SVG correspondente.
        """
        charts_ids = re.findall(r'\[\[chart=(\d+)\]\]', message)
        charts_svgs = {}
        for chart_id in charts_ids:
            svg = self._chart_service.get_chart(int(chart_id))
            charts_svgs[chart_id] = svg
        return charts_svgs

    def get_tools(self) -> list[StructuredTool]:
        """Retorna as ferramentas registráveis em um agente LangChain.

        Returns:
            list[StructuredTool]: Ferramentas para geração de gráfico de barras,
                linhas e funil.
        """
        return [
            StructuredTool.from_function(self._bar_chart),
            StructuredTool.from_function(self._line_chart),
            StructuredTool.from_function(self._funnel_chart),
        ]
    