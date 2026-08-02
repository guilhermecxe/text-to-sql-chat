# Lógica de Gráficos (Charts)

## Visão geral

O sistema de gráficos converte dados tabulares em imagens SVG via **Plotly + Kaleido**, retorna essas imagens como strings ao frontend e as injeta diretamente no texto da resposta do agente. O agente referencia gráficos com a sintaxe `[[chart=<id>]]` no corpo da resposta; o frontend substitui essa tag pelo SVG redimensionado.

---

## Tipos de gráfico disponíveis

Definidos em [api/src/models/chart_models.py](../api/src/models/chart_models.py):

| Tipo | Classe de dados | Trace Plotly |
|------|----------------|-------------|
| Barras | `BarChart` + `BarSeries` | `go.Bar` |
| Linhas | `LineChart` + `LineSeries` | `go.Scatter` |
| Funil | `FunnelChart` + `FunnelSeries` | `go.Funnel` |

---

## Modelos de dados

### BarChart / BarSeries

```python
class BarSeries(BaseModel):
    label: str
    x: list
    y: list
    color_rule: Literal["fixed", "threshold", "sign"] | None
    threshold: float | None = None   # só usado quando color_rule="threshold"

class BarChart(BaseModel):
    title: str
    subtitle: str
    x_label: str
    y_label: str
    orientation: str          # "vertical" | "horizontal"
    mode: str                 # "group" | "stack"
    width: int = 800
    height: int = 600
    show_values: bool = True
    value_prefix: str = ""    # ex: "R$ "
    value_suffix: str = ""    # ex: " %"
    value_format: str = ",.0f"
    series: list[BarSeries]
```

### LineSeries / LineChart

```python
class LineSeries(BaseModel):
    label: str
    x: list
    y: list
    dash: Literal["solid", "dot", "dash", "longdash", "dashdot"] = "solid"
    show_markers: bool = False
    fill: Literal["none", "tozeroy", "tonexty"] = "none"
```

### FunnelSeries / FunnelChart

```python
class FunnelSeries(BaseModel):
    label: str
    x: list   # nomes dos estágios (categorias), de cima para baixo
    y: list   # valor numérico de cada estágio

class FunnelChart(BaseModel):
    show_values: bool = True
    show_percent: bool = True   # % relativa ao primeiro estágio
    ...
```

---

## Sistema de cores

### Paletas por tema

Definidas em [api/src/settings.py](../api/src/settings.py) como `chart_palettes`:

```python
chart_palettes: dict[str, dict[str, str]] = {
    "dark": {
        "positive": "#00ff00",
        "negative": "#ff0000",
        "text":      "#ffffff",
        "text_muted":"#aaaaaa",
        "neutral":   "#888888",
        "bg":        "#061222",
        "grid":      "#1a2a3a",
    },
    "light": {
        "positive": "#16a34a",
        "negative": "#dc2626",
        "text":      "#1a1a1a",
        "text_muted":"#6b7280",
        "neutral":   "#9ca3af",
        "bg":        "#ffffff",
        "grid":      "#e5e7eb",
    },
}
```

O tema (`"dark"` ou `"light"`) é fornecido pelo frontend na requisição e propagado até a renderização.

### Sequência de cores para séries

```python
chart_color_sequence: list[str] = [
    "#1f77b4", "#ff7f0e", "#2ca02c",
    "#d62728", "#9467bd", "#8c564b",
]
```

Cada série recebe a cor `color_sequence[i % len(color_sequence)]`, ciclando quando há mais de 6 séries.

### Regras de coloração de barras (`color_rule`)

| Regra | Comportamento |
|-------|--------------|
| `"fixed"` | Uma cor da sequência por série (índice `i`) |
| `"sign"` | `palette["positive"]` se `v >= 0`, `palette["negative"]` se `v < 0` |
| `"threshold"` | `palette["positive"]` se `v >= threshold`, senão `palette["negative"]` |
| `None` | Mesmo comportamento de `"fixed"` |

**Restrição:** múltiplas séries com `color_rule="sign"` e labels diferentes são recusadas — a cor estaria representando simultaneamente sinal e série, tornando o gráfico ambíguo.

---

## Limites do gráfico de barras

Há **dois** limites independentes, aplicados em camadas diferentes:

| Limite | Onde é checado | Quando dispara | Comportamento |
|--------|-----------------|-----------------|---------------|
| Máx. 10 séries | `PlotlyChartDesigner.draw_bar_chart` | `len(data.series) > 10` | Lança `ValueError` |
| Máx. 10 categorias no total | `ChartToolkit._bar_chart` | `sum(len(s.x) for s in data.series) > 10` | **Não lança exceção** — retorna uma string de erro em português como resultado da tool |

O segundo limite é checado **antes** de qualquer chamada ao `ChartService`/`PlotlyChartDesigner`, então uma violação nunca chega a gerar SVG. Como o retorno é uma string simples (não um dict `{"chart_id": ...}` nem uma exceção), o agente recebe a mensagem de erro como resultado normal da tool call e pode tentar novamente com dados agregados/filtrados.

---

## Fluxo de renderização

```
Request (theme, dados)
        │
        ▼
ChartToolkit._bar_chart / _line_chart / _funnel_chart
        │  lê o tema do ContextVar
        │  (bar) valida total de categorias ≤ 10 — retorna string de erro se violar
        ▼
ChartService.draw_*_chart(data, theme)
        │
        ▼
PlotlyChartDesigner.draw_*_chart(data, theme)   ← adapter Plotly
        │  palette = self.palettes[theme]
        │  monta traces go.Bar / go.Scatter / go.Funnel
        │  aplica layout (bg, grid, fontes, range dos eixos)
        │  fig.to_image(format="svg")  ← kaleido exporta SVG
        ▼
ChartService armazena SVG no dict _charts[id]
        │  retorna {"chart_id": N, "svg": "..."}
        ▼
ChartToolkit devolve apenas {"chart_id": N} ao agente
```

### Isolamento de tema por corrotina

O tema é armazenado em um `ContextVar`, não em estado de instância, garantindo isolamento em execuções concorrentes:

```python
# ChartToolkit
self._chart_theme: ContextVar[str] = ContextVar("chart_theme", default="None")

@contextmanager
def apply_theme(self, theme: str):
    token = self._chart_theme.set(theme)
    try:
        yield
    finally:
        self._chart_theme.reset(token)
```

O contexto é ativado em `ConversationalAgent.ainvoke`:

```python
with self._chart_toolkit.apply_theme(theme=theme):
    response = await self._agent.ainvoke(...)
```

---

## O que o agente vê

O agente **não recebe o SVG** — recebe apenas o `chart_id` após chamar uma ferramenta de gráfico. O system prompt ensina como referenciar o gráfico na resposta:

```
## About charts:
- Use [[chart=<id>]] at the user message to include a chart in the response,
  where <id> is the id of the chart.
- ALWAYS call a chart tool to generate charts, or reference a previous call result,
  otherwise it won't be rendered to the user.
```

As ferramentas disponíveis para o agente (registradas via `ChartToolkit.get_tools()`):

- `_bar_chart(data: BarChart) → {"chart_id": int}`
- `_line_chart(data: LineChart) → {"chart_id": int}`
- `_funnel_chart(data: FunnelChart) → {"chart_id": int}`

O agente formula os modelos Pydantic completos como argumentos das ferramentas.

---

## Armazenamento dos SVGs

`ChartService` funciona como um cache em memória por sessão de servidor:

```python
class ChartService:
    def __init__(self, chart_designer: ChartDesigner):
        self._charts = {}          # {chart_id: svg_string}
        self._chart_id_counter = 0

    def draw_bar_chart(self, data, theme):
        chart_svg = self.chart_designer.draw_bar_chart(data, theme=theme)
        self._chart_id_counter += 1
        self._charts[self._chart_id_counter] = chart_svg
        return {"chart_id": self._chart_id_counter, "svg": chart_svg}

    def get_chart(self, chart_id: int) -> str:
        chart = self._charts.get(chart_id)
        if chart is None:
            raise ValueError(f"Chart with ID {chart_id} not found.")
        return chart
```

A instância é singleton via `@lru_cache` no DI (`di.py`), então os IDs crescem monotonicamente durante o ciclo de vida do servidor.

---

## Retorno ao frontend

Após o agente terminar, `ConversationalAgent.ainvoke` extrai os SVGs referenciados na resposta:

```python
answer = response["messages"][-1].content

# Coleta apenas os gráficos citados na resposta
charts_svgs = self._chart_toolkit.gather_charts(answer)
# → {"1": "<svg...>", "3": "<svg...>"}

return {
    "answer": answer,        # texto com [[chart=1]], [[chart=3]] intactos
    "charts": charts_svgs,   # mapa id → SVG
    "thread_id": thread_id
}
```

`gather_charts` usa regex para encontrar as tags:

```python
def gather_charts(self, message: str):
    charts_ids = re.findall(r'\[\[chart=(\d+)\]\]', message)
    charts_svgs = {}
    for chart_id in charts_ids:
        svg = self._chart_service.get_chart(int(chart_id))
        charts_svgs[chart_id] = svg
    return charts_svgs
```

A rota `POST /agents/ask-conversational-agent` repassa os dois campos diretamente:

```python
return {
    "answer": result["answer"],
    "charts": result["charts"],
    "thread_id": result["thread_id"]
}
```

---

## Injeção no frontend

`APIClient._place_charts` ([frontend/controllers/api_client.py](../frontend/controllers/api_client.py)) substitui cada tag `[[chart=N]]` pelo SVG redimensionado:

```python
def _place_charts(self, answer: str, charts: dict[str, str]) -> str:
    def replace_chart(match):
        chart_id = match.group(1)
        svg = charts[chart_id]
        if svg is None:
            return match.group(0)
        return self._resize_svg(svg, width=600)

    return re.sub(r'\[\[chart=(\d+)\]\]', replace_chart, answer)

def _resize_svg(self, svg: str, width: int) -> str:
    w = float(re.search(r'width="([\d.]+)"', svg).group(1))
    h = float(re.search(r'height="([\d.]+)"', svg).group(1))
    scale = width / w
    svg = re.sub(r'width="[\d.]+"', f'width="{width}"', svg, count=1)
    svg = re.sub(r'height="[\d.]+"', f'height="{round(h * scale)}"', svg, count=1)

    # O renderizador de markdown do Streamlit trata "$...$" como LaTeX, o que
    # corrompe SVGs com cifrões literais (ex.: rótulos formatados em R$).
    svg = svg.replace("$", "&#36;")
    return svg
```

O SVG final (redimensionado para 600 px de largura, com `$` escapado) é injetado inline no markdown da resposta renderizada.

---

## Dependências e wiring (DI)

```
Settings
  └─ chart_color_sequence, chart_palettes
       │
       ▼
PlotlyChartDesigner(settings)   ← @lru_cache
       │
       ▼
ChartService(plotly_designer)   ← @lru_cache
       │
       ├─► ChartToolkit(chart_service)   ← usado pelo ConversationalAgent
       │
       └─► ConversationalAgent(
               ...,
               chart_service=get_chart_service()
           )
```

---

## Detalhes de renderização notáveis

- **Fonte:** `JetBrains Mono, monospace` em todo texto dos gráficos.
- **Range do eixo Y (bar):** calculado com 20% de margem acima do máximo. Em modo `stack`, positivos e negativos são somados separadamente.
- **Textos fora do eixo:** `cliponaxis=False` impede corte de rótulos de valor que ultrapassam o plot area.
- **Posição do texto (bar):** `textposition="auto"` move o label para dentro da barra quando não há espaço fora.
- **Cor do texto interno vs. externo (bar/funnel):** interno usa `palette["bg"]` (contraste com a barra); externo usa `palette["text_muted"]`.
- **Limites (bar):** máximo 10 séries (`ValueError` no adapter) e máximo 10 categorias no total somando todas as séries (string de erro no `ChartToolkit`, sem exceção) — ver [Limites do gráfico de barras](#limites-do-gráfico-de-barras).
- **Exportação:** `fig.to_image(format="svg", scale=1)` via Kaleido, decodificado como UTF-8.
