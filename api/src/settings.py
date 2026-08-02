from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configurações globais da aplicação carregadas via variáveis de ambiente.
    """

    # Charts
    chart_color_sequence: list[str] = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    chart_palettes: dict[str, dict[str, str]] = {
        "dark": {
            "positive": "#00ff00",
            "negative": "#ff0000",
            "text": "#ffffff",
            "text_muted": "#aaaaaa",
            "neutral": "#888888",
            "bg": "#061222",
            "grid": "#1a2a3a",
        },
        "light": {
            "positive": "#16a34a",
            "negative": "#dc2626",
            "text": "#1a1a1a",
            "text_muted": "#6b7280",
            "neutral": "#9ca3af",
            "bg": "#ffffff",
            "grid": "#e5e7eb",
        },
    }

    # Agents
    conversational_agent_default_model: str = "openai:gpt-5.4-mini"
    sql_agent_default_model: str = "openai:gpt-5.4-mini"

    sql_agent_db_uri: str = "sqlite:///data/Chinook.db"