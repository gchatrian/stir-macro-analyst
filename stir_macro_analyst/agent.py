# agent.py

"""STIR Macro Analyst - Root Agent."""

import logging
import warnings
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from . import agent_prompt
from .tools.policy_rate_tool import get_policy_rate  
from .tools.stir_scenario_tool import analyze_stir_scenarios  
from .tools.meeting_dates_tool import count_central_bank_meetings
from .tools.plot_rnd_tool import plot_rnd_analysis  

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

logger = logging.getLogger(__name__)

# Carica variabili d'ambiente da .env (inclusa OPENAI_API_KEY)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY non è settata. Le chiamate a OpenAI falliranno.")

# Modello OpenAI via LiteLlm / ADK
MODEL = LiteLlm(
    model="openai/gpt-4o-mini",
    api_key=OPENAI_API_KEY,
)

logger.debug("Using MODEL: %s", MODEL)

root_agent = Agent(
    model=MODEL,
    name="stir_macro_analyst",
    description=(
        "Expert quantitative analyst for Short-Term Interest Rate (STIR) futures "
        "and options markets. Performs SABR calibration, generates Risk Neutral "
        "Densities, and analyzes market-implied rate expectations through scenario "
        "probability analysis."
    ),
    instruction=agent_prompt.SYSTEM_PROMPT,
    tools=[
        get_policy_rate,         
        analyze_stir_scenarios,  
        plot_rnd_analysis, 
        count_central_bank_meetings     
    ],
)
