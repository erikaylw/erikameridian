"""
Superagent Pipeline — Content Crew
Supervisor-style: Researcher → Writer → Reviewer

Bisa jalan GRATIS pake DeepSeek atau model open source.
Web search pake DuckDuckGo (no API key needed).
"""

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from superagent_pipeline.tools.custom_tool import WebSearchTool
import os
from datetime import datetime


@CrewBase
class SuperagentPipeline():
    """Superagent pipeline buat bikin konten Twitter/X."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        # Setup tools — DuckDuckGo GRATIS, no API key!
        self.web_tool = WebSearchTool()
        
        # Setup LLM
        self.llm = self._get_llm()

    def _get_llm(self):
        """Auto-detect LLM dengan prioritas murah/gratis."""
        
        # 1️⃣ DeepSeek (murah & powerful — recommended)
        if os.getenv("DEEPSEEK_API_KEY"):
            print("🧠 LLM: DeepSeek (via API)")
            return LLM(
                model="deepseek/deepseek-chat",
                base_url="https://api.deepseek.com/v1",
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                temperature=0.7,
            )
        
        # 2️⃣ OpenAI
        if os.getenv("OPENAI_API_KEY"):
            print("🧠 LLM: OpenAI GPT-4o")
            return LLM(
                model="openai/gpt-4o",
                temperature=0.7,
            )
        
        # 3️⃣ OpenRouter (akses banyak model, bayar per token)
        if os.getenv("OPENROUTER_API_KEY"):
            print("🧠 LLM: Claude Sonnet (via OpenRouter)")
            return LLM(
                model="openrouter/anthropic/claude-sonnet-4",
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                temperature=0.7,
            )
        
        # 4️⃣ Ollama (LOKAL, GRATIS total)
        print("🧠 LLM: Ollama (lokal — install: ollama pull llama3.2)")
        return LLM(
            model="ollama/llama3.2",
            base_url="http://localhost:11434",
            temperature=0.7,
        )

    # ─── Agent Definitions ───────────────────────────────────
    
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=self.llm,
            tools=[self.web_tool],
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    # ─── Task Definitions ────────────────────────────────────
    
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config["writing_task"],
            output_file=f"output/thread_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_task"],
        )

    # ─── Crew (SUPERAGENT) ───────────────────────────────────
    
    @crew
    def crew(self) -> Crew:
        """Superagent dengan proses HIERARCHICAL.
        
        Supervisor (manager_llm) otomatis:
        1. Breakdown request jadi subtasks
        2. Assign ke agent yang tepat (Researcher → Writer → Reviewer)
        3. Evaluate hasil tiap langkah
        4. Repeat atau lanjut
        
        Ini SUPERAGENT karena:
        - Ada orchestrator (manager_llm) yang ngatur
        - Agent fokus di role masing-masing
        - Hierarkis, bukan sekedar parallel
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,  # ← KUNCI: supervisor style
            manager_llm=self.llm,          # Supervisor pake LLM
            verbose=True,
        )
