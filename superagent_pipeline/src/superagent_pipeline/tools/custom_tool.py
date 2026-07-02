"""Custom tools untuk superagent content pipeline.

Web search pake DuckDuckGo (GRATIS, tanpa API key, tanpa batas).
"""

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from ddgs import DDGS


class WebSearchInput(BaseModel):
    """Input untuk web research tool."""
    query: str = Field(description="Kata kunci pencarian untuk riset")


class WebSearchTool(BaseTool):
    """Cari info dari web — GRATIS, tanpa API key, tanpa batas query."""
    
    name: str = "Web Search"
    description: str = """Cari informasi terbaru dari internet. 
Gunakan untuk riset topik, cari berita terbaru, cek data spesifik.
Hasil: judul + snippet + URL.
Contoh query: 'bitcoin price June 2026', 'GPT-5 benchmark Claude', 'AI news today'"""
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=8))
            
            if not results:
                return f"⚠️ Tidak ada hasil untuk: {query}. Coba dengan kata kunci berbeda."
            
            output = f"🔍 Hasil pencarian: {query}\n\n"
            for i, r in enumerate(results, 1):
                title = r.get("title", "No title")
                body = r.get("body", "")
                href = r.get("href", "")
                output += f"{i}. **{title}**\n"
                if body:
                    output += f"   {body[:250]}...\n"
                if href:
                    output += f"   {href}\n"
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"⚠️ Web search error: {str(e)}\nGunakan pengetahuan internal sebagai fallback."
