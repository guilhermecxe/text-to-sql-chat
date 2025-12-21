from langchain.tools import tool
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile

sns.set_theme(style="whitegrid")

@tool
def barplot_tool(x: list, y: list, hue: list, title: str, xlabel: str, ylabel: str, figsize: tuple = (8, 5)):
    """
    Query a read-only Chinook music database to answer questions about music data.
    Call this agent whenever you need to interact with the Chinook database.
    It is not allowed to perform actions that modify the database, just read queries.

    The database contains information about:
    - Artists,
    - Albums,
    - Tracks,
    - Genres,
    - Playlists
    - and others relates.

    Args:
        question: A natural language question about the music database.
        
    Rerturns:
        A concise, factual answer derived strictly from the database query results.
    """
    dpi = 150 * ((figsize[0] * figsize[1])/40)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    sns.barplot(x=x, y=y, hue=hue)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False
    )

    fig.savefig(tmp.name, dpi=dpi, bbox_inches="tight")

    plt.close(fig)
    
    return tmp.name