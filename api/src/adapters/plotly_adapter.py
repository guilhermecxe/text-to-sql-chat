import plotly.graph_objects as go

from src.ports.chart_designer import ChartDesigner
from src.models.chart_models import BarChart, LineChart, FunnelChart
from src.settings import Settings

class PlotlyChartDesigner(ChartDesigner):
    """Implementação de ChartDesigner usando Plotly + Kaleido para exportar SVG.

    Cores e paletas são resolvidas em tempo de renderização a partir do tema
    solicitado, sem estado mutável entre chamadas.
    """

    def __init__(self, settings: Settings):
        self.color_sequence = settings.chart_color_sequence
        self.palettes = settings.chart_palettes

    def draw_bar_chart(self, data: BarChart, theme: str) -> str:
        """Renderiza um gráfico de barras e retorna o SVG como string.

        Suporta orientação vertical/horizontal, agrupamento e empilhamento de
        séries, e três regras de coloração: ``fixed`` (sequência automática),
        ``sign`` (positivo/negativo) e ``threshold`` (acima/abaixo de um limite).

        Args:
            data (BarChart): Configuração completa do gráfico, incluindo séries,
                rótulos, orientação e opções de exibição de valores.
            theme (str): Esquema de cores a usar; deve ser uma chave válida de
                ``settings.chart_palettes`` (ex.: ``"dark"`` ou ``"light"``).

        Returns:
            str: String UTF-8 contendo o SVG gerado pelo Kaleido.

        Raises:
            ValueError: Se mais de uma série com ``color_rule="sign"`` tiver
                labels diferentes, tornando o significado das cores ambíguo.
        """
        palette = self.palettes[theme]

        if len(data.series) > 10:
            raise ValueError(f"You can only set up to 10 series, but it was sent {len(data.series)} series")
        
        # Quando há color_rule="sign" e múltiplas labels, o significado das cores
        # das barras fica ambíguo (estão diferenciando sinal ou label?).
        # Então aqui não permitimos essa combinação.
        sign_series = [s for s in data.series if s.color_rule == "sign"]
        if len(sign_series) > 1:
            labels = {s.label for s in sign_series}
            if len(labels) > 1:
                raise ValueError(
                    "Múltiplas séries com color_rule='sign' e labels diferentes "
                    "são ambíguas: a cor representa o sinal do valor, não a série. "
                    "Use um único label ou troque para color_rule='fixed' com color=list."
                )
        
        traces = []
        for i, s in enumerate(data.series):
            # Resolvendo esquema de cores das barras
            if s.color_rule == "fixed":
                bar_colors = self.color_sequence[i % len(self.color_sequence)]

            elif s.color_rule == "sign":
                bar_colors = [
                    palette["positive"] if v >= 0 else palette["negative"]
                    for v in s.y
                ]

            elif s.color_rule == "threshold":
                bar_colors = [
                    palette["positive"] if v >= s.threshold else palette["negative"]
                    for v in s.y
                ]

            else:
                bar_colors = self.color_sequence[i % len(self.color_sequence)]

            # Resolvendo o formato dos rótulos de valor de cada barra
            formatted = [
                f"{data.value_prefix}{v:{data.value_format}}{data.value_suffix}"
                for v in s.y
            ]

            # Alterando orientação entre vertical ou horizontal
            if data.orientation == "vertical":
                trace_kwargs = dict(x=s.x, y=s.y)
            else:
                trace_kwargs = dict(y=s.x, x=s.y, orientation="h")

            # Criando cada barra
            traces.append(
                go.Bar(
                    name=s.label,
                    marker_color=bar_colors,
                    marker_line_width=0,
                    text=formatted if data.show_values else None,

                    # "auto" coloca o label dentro da barra quando não cabe fora,
                    # evitando corte nas barras mais altas
                    textposition="auto",

                    # permite que o texto ultrapasse os limites do plot area
                    # sem ser recortado pelo clippath do SVG
                    cliponaxis=False,
                    outsidetextfont=dict(
                        family="JetBrains Mono, monospace",
                        size=15,
                        color=palette["text_muted"],
                    ),
                    insidetextfont=dict(
                        family="JetBrains Mono, monospace",
                        size=15,
                        color=palette["bg"],   # #061222 — contraste com a barra
                    ),
                    insidetextanchor="middle", # label alinhado no centro da barra
                    **trace_kwargs,
                )
            )

        # Criando o layout do resto do gráfico
        title_text = f"<b>{data.title}</b>" if data.title else ""
        if data.subtitle:
            title_text += f"<br><span style='font-size:15px;color:{palette['text_muted']}'>{data.subtitle}</span>"

        # Calculando o range do eixo em que os valores aparecem com base no tipo de gráfico
        n = len(data.series[0].y)
        if data.mode == "stack":
            # soma positivos e negativos separadamente por posição
            pos_totals = [sum(s.y[i] for s in data.series if s.y[i] > 0) for i in range(n)]
            neg_totals = [sum(s.y[i] for s in data.series if s.y[i] < 0) for i in range(n)]

            y_max = max(pos_totals) * 1.20
            y_min = min(0, min(neg_totals)) * 1.20
        else:
            all_values = [v for s in data.series for v in s.y]
            y_max = max(all_values) * 1.20
            y_min = 0

        range_ = [y_min, y_max]

        # No modo horizontal, o eixo y físico carrega as categorias (s.x) e o
        # eixo x físico carrega os valores (s.y) — título e range precisam
        # seguir essa troca, senão ficam no eixo errado.
        if data.orientation == "vertical":
            xaxis_title, yaxis_title = data.x_label, data.y_label
            xaxis_range, yaxis_range = None, range_
        else:
            xaxis_title, yaxis_title = data.y_label, data.x_label
            xaxis_range, yaxis_range = range_, None

        fig = go.Figure(data=traces)
        fig.update_layout(
            width=data.width,
            height=data.height,
            barmode=data.mode,
            paper_bgcolor=palette["bg"],
            plot_bgcolor=palette["bg"],
            margin=dict(l=12, r=12, t=80 if data.title else 24, b=12),
            title=dict(
                text=title_text,
                font=dict(family="JetBrains Mono, monospace", size=18, color=palette["text"]),
                x=0,
                xanchor="left",
                pad=dict(l=4),
            ),
            legend=dict(
                font=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                y=-0.15,
            ),
            xaxis=dict(
                title=dict(text=xaxis_title, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"], # Cor do grid
                linecolor=palette["grid"], # Cor da linha do eixo
                showline=True,
                zeroline=False, # Se dá um destaque ao valor 0 do eixo
                range=xaxis_range,
            ),
            yaxis=dict(
                title=dict(text=yaxis_title, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"],
                linecolor="rgba(0,0,0,0)",
                zeroline=False,
                showgrid=True,
                range=yaxis_range,
            ),
            bargap=0.28, # Diferença entre grupos de barras ou entre barras se só existir um grupo
            bargroupgap=0.08, # Diferença entre barras de um mesmo grupo
        )

        # Exportando SVG via kaleido
        svg_bytes: bytes = fig.to_image(format="svg", scale=1)
        return svg_bytes.decode("utf-8")

    def draw_line_chart(self, data: LineChart, theme: str) -> str:
        """Renderiza um gráfico de linhas e retorna o SVG como string.

        Cada série é desenhada como um traço ``go.Scatter``. Suporta marcadores,
        diferentes estilos de traço (dash) e preenchimento até o zero (fill).

        Args:
            data (LineChart): Configuração do gráfico, incluindo séries, rótulos
                dos eixos e opções de exibição de valores.
            theme (str): Esquema de cores a usar; deve ser uma chave válida de
                ``settings.chart_palettes`` (ex.: ``"dark"`` ou ``"light"``).

        Returns:
            str: String UTF-8 contendo o SVG gerado pelo Kaleido.
        """
        palette = self.palettes[theme]

        traces = []
        for i, s in enumerate(data.series):
            color = self.color_sequence[i % len(self.color_sequence)]

            mode = "lines+markers" if s.show_markers else "lines"
            if data.show_values:
                mode += "+text"

            formatted = None
            if data.show_values:
                formatted = [
                    f"{data.value_prefix}{v:{data.value_format}}{data.value_suffix}"
                    for v in s.y
                ]

            traces.append(
                go.Scatter(
                    name=s.label,
                    x=s.x,
                    y=s.y,
                    mode=mode,
                    line=dict(color=color, width=2, dash=s.dash),
                    marker=dict(color=color, size=8) if s.show_markers else None,
                    fill=s.fill if s.fill != "none" else None,
                    text=formatted,
                    textposition="top center",
                    textfont=dict(
                        family="JetBrains Mono, monospace",
                        size=13,
                        color=palette["text_muted"],
                    ),
                    cliponaxis=False,
                )
            )

        title_text = f"<b>{data.title}</b>" if data.title else ""
        if data.subtitle:
            title_text += f"<br><span style='font-size:15px;color:{palette['text_muted']}'>{data.subtitle}</span>"

        all_values = [v for s in data.series for v in s.y]
        y_max = max(all_values)
        y_min = min(all_values)
        if any(s.fill == "tozeroy" for s in data.series):
            y_min = min(0, y_min)
            y_max = max(0, y_max)
        padding = (y_max - y_min) * 0.15 or abs(y_max) * 0.15 or 1
        range_ = [y_min - padding, y_max + padding]

        fig = go.Figure(data=traces)
        fig.update_layout(
            width=data.width,
            height=data.height,
            paper_bgcolor=palette["bg"],
            plot_bgcolor=palette["bg"],
            margin=dict(l=12, r=12, t=80 if data.title else 24, b=12),
            title=dict(
                text=title_text,
                font=dict(family="JetBrains Mono, monospace", size=18, color=palette["text"]),
                x=0,
                xanchor="left",
                pad=dict(l=4),
            ),
            legend=dict(
                font=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                y=-0.15,
            ),
            xaxis=dict(
                title=dict(text=data.x_label, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"],
                linecolor=palette["grid"],
                showline=True,
                zeroline=False,
            ),
            yaxis=dict(
                title=dict(text=data.y_label, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"],
                linecolor="rgba(0,0,0,0)",
                zeroline=False,
                showgrid=True,
                range=range_,
            ),
        )

        svg_bytes: bytes = fig.to_image(format="svg", scale=1)
        return svg_bytes.decode("utf-8")

    def draw_funnel_chart(self, data: FunnelChart, theme: str) -> str:
        """Renderiza um gráfico de funil e retorna o SVG como string.

        Os estágios ficam no eixo Y e os valores no eixo X, seguindo a convenção
        de ``go.Funnel``. Quando uma banda é estreita demais para exibir o texto
        internamente, ``textposition="auto"`` move o rótulo para fora.

        Args:
            data (FunnelChart): Configuração do gráfico, incluindo séries com
                estágios e valores, e flags para exibição de valores e percentuais.
            theme (str): Esquema de cores a usar; deve ser uma chave válida de
                ``settings.chart_palettes`` (ex.: ``"dark"`` ou ``"light"``).

        Returns:
            str: String UTF-8 contendo o SVG gerado pelo Kaleido.
        """
        palette = self.palettes[theme]

        traces = []
        for i, s in enumerate(data.series):
            color = self.color_sequence[i % len(self.color_sequence)]

            formatted = [
                f"{data.value_prefix}{v:{data.value_format}}{data.value_suffix}"
                for v in s.y
            ] if data.show_values else None

            if data.show_values and data.show_percent:
                textinfo = "text+percent initial"
            elif data.show_values:
                textinfo = "text"
            elif data.show_percent:
                textinfo = "percent initial"
            else:
                textinfo = "none"

            traces.append(
                go.Funnel(
                    name=s.label,
                    y=s.x,  # stage names on the vertical axis
                    x=s.y,  # values on the horizontal axis
                    text=formatted,
                    textinfo=textinfo,
                    textposition="auto",
                    insidetextfont=dict(
                        family="JetBrains Mono, monospace",
                        size=14,
                        color=palette["bg"],
                    ),
                    outsidetextfont=dict(
                        family="JetBrains Mono, monospace",
                        size=14,
                        color=palette["text_muted"],
                    ),
                    marker=dict(
                        color=color,
                        line=dict(width=0),
                    ),
                    connector=dict(
                        line=dict(color=palette["grid"], width=1),
                    ),
                )
            )

        title_text = f"<b>{data.title}</b>" if data.title else ""
        if data.subtitle:
            title_text += f"<br><span style='font-size:15px;color:{palette['text_muted']}'>{data.subtitle}</span>"

        fig = go.Figure(data=traces)
        fig.update_layout(
            width=data.width,
            height=data.height,
            paper_bgcolor=palette["bg"],
            plot_bgcolor=palette["bg"],
            margin=dict(l=12, r=12, t=80 if data.title else 24, b=12),
            title=dict(
                text=title_text,
                font=dict(family="JetBrains Mono, monospace", size=18, color=palette["text"]),
                x=0,
                xanchor="left",
                pad=dict(l=4),
            ),
            legend=dict(
                font=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                y=-0.15,
            ),
            yaxis=dict(
                title=dict(text=data.y_label, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"],
                linecolor=palette["grid"],
                showline=True,
            ),
            xaxis=dict(
                title=dict(text=data.x_label, font=dict(size=14, color=palette["neutral"])),
                tickfont=dict(family="JetBrains Mono, monospace", size=14, color=palette["text_muted"]),
                gridcolor=palette["grid"],
                linecolor="rgba(0,0,0,0)",
                zeroline=False,
                showgrid=True,
            ),
        )

        svg_bytes: bytes = fig.to_image(format="svg", scale=1)
        return svg_bytes.decode("utf-8")