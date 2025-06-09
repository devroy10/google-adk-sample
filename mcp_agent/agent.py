import datetime
import os
from zoneinfo import ZoneInfo

import opik
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from opik.integrations.adk import OpikTracer

AGENT_MODEL = "gemini-2.0-flash-lite"
AGENT_NAME = "weather_time_city_agent"


def get_weather(city: str) -> dict:
    print(f'. [TOOL] "get_weather" - City: {city}.')
    city_normalized = city.lower().replace(" ", "")

    mock_weather = {
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 45 F.",
        },
        "london": {
            "status": "success",
            "report": "It's cloudy in London with a temperature of 55 F.",
        },
        "tokyo": {
            "status": "success",
            "report": "Tokyo is experiencing light rain and a temperature of 72 F.",
        },
    }

    if city_normalized in mock_weather:
        return mock_weather[city_normalized]
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have weather information for '{city}'.",
        }


def get_current_time(city: str) -> dict:
    print(f'. [TOOL] "get_current_time" - City: {city}.')
    city_normalized = city.lower().replace(" ", "")

    timezones = {
        "newyork": "America/New_York",
        "london": "Europe/London",
        "tokyo": "Asia/Tokyo",
    }

    if city_normalized in timezones:
        timezone = timezones[city_normalized]
    else:
        return {
            "status": "error",
            "error_message": (f"Sorry, I don't have timezone information for {city}."),
        }

    tz = ZoneInfo(timezone)
    now = datetime.datetime.now(tz)
    report = f"The current time in {city} is {now.strftime('%H:%M')}"
    return {"status": "success", "report": report}


opik.configure(use_local=False)
opik_tracer = OpikTracer()

root_agent = LlmAgent(
    name=AGENT_NAME,
    model=AGENT_MODEL,
    description=(
        "Agent to answer questions about the time and weather in a city and "
        "provide directions between two cities."
    ),
    instruction=(
        "You are a helpful assistant. When the user asks for "
        "a specific city, use the 'get_weather' and the "
        "'get_current_time' tools to find the weather and current time "
        "information. If the tools return an error, inform the user. "
        "If the tools are successful, present the report clearly."
    ),
    tools=[
        get_weather,
        get_current_time,
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-google-maps",
                ],
                env={
                    "GOOGLE_MAPS_API_KEY": os.environ.get(
                        "GOOGLE_MAPS_PLATFORM_API_KEY"
                    )
                },
            ),
        ),
    ],
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback,
    before_tool_callback=opik_tracer.before_tool_callback,
    after_tool_callback=opik_tracer.after_tool_callback,
)