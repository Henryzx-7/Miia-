# web_tools.py
from duckduckgo_search import DDGS

def buscar_en_web(query: str):
    """
    Realiza una búsqueda web y devuelve un resumen del contexto y una lista de fuentes.
    """
    print(f"🔎 Realizando búsqueda web para: '{query}'")
    try:
        with DDGS() as ddgs:
            # Buscamos 3 resultados del último mes para mantener la relevancia
            results = [{"snippet": r['body'], "url": r['href']} for r in ddgs.text(query, region='wt-wt', safesearch='off', timelimit='m', max_results=3)]
            if not results:
                return "No se encontraron resultados relevantes.", []

            # Preparamos el contexto para la IA
            context_text = "\n\n".join([f"Fuente {i+1}: {r['snippet']}" for i, r in enumerate(results)])
            sources = [r for r in results]
            return context_text, sources
    except Exception as e:
        print(f"Error en la búsqueda web: {e}")
        return f"Ocurrió un error al intentar buscar en la web: {e}", []
