import asyncio
import datetime
from typing import Dict, List, Optional

from fastapi import WebSocket

from backend.report_type import BasicReport, DetailedReport
from backend.chat import ChatAgentWithMemory

from gpt_researcher.utils.enum import ReportType, Tone, ReportSource
from multi_agents.main import run_research_task
from gpt_researcher.actions import stream_output  # Import stream_output
from backend.server.server_utils import CustomLogsHandler


class WebSocketManager:
    """Manage websockets"""

    def __init__(self):
        """Initialize the WebSocketManager class."""
        self.active_connections: List[WebSocket] = []
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}
        self.chat_agent = None








    async def generate_response(
    self,
    task: str,
    report_type: str,
    report_source: str,  # Pass the report source as a string (e.g., "web")
    source_urls: List[str],
    document_urls: List[str],
    tone: str,  # Pass the tone as a string (e.g., "Objective")
    websocket: Optional[WebSocket] = None,
    headers: Optional[Dict] = None
    ) -> str:
     """
     Generate a response for the given task without streaming.
     Args:
         task (str): The task or prompt.
         report_type (str): The type of report to generate.
         report_source (str): The source of the report (e.g., "web", "local", "hybrid").
         source_urls (List[str]): URLs to use as sources.
         document_urls (List[str]): Documents to use as sources.
         tone (str): The tone of the response (e.g., "Objective").
         websocket (Optional[WebSocket]): The WebSocket connection (optional).
         headers (Optional[Dict]): Additional headers (optional).
     Returns:
         str: The generated response.
     """
     try:
         # Convert the tone string to the Tone enum
         tone_enum = Tone[tone]  # Map the tone string to the Tone enum
     except KeyError:
         valid_tones = [t.name for t in Tone]  # Get valid tone names
         raise ValueError(f"Invalid tone: {tone}. Valid tones are: {valid_tones}")

     try:
         # Convert the report_source string to the ReportSource enum
         report_source_enum = ReportSource(report_source)  # Map the report_source string to the ReportSource enum
     except ValueError:
         valid_report_sources = [s.value for s in ReportSource]  # Get valid report source values
         raise ValueError(f"Invalid report source: {report_source}. Valid report sources are: {valid_report_sources}")

     config_path = "default"  # Use the default config path

     # Run the agent and generate the report
     report = await run_agent(
         task, report_type, report_source_enum.value, source_urls, document_urls, tone_enum, websocket, headers, config_path
     )

     # Create a new Chat Agent if needed
     self.chat_agent = ChatAgentWithMemory(report, config_path, headers)

     return report



# Before Tavily
    # async def generate_response(
    # self,
    # task: str,
    # report_type: str,
    # report_source: str,  # Pass the report source as a string (e.g., "web")
    # source_urls: List[str],
    # document_urls: List[str],
    # tone: str,  # Pass the tone as a string (e.g., "Objective")
    # websocket: Optional[WebSocket] = None,
    # headers: Optional[Dict] = None
    # ) -> str:
    #     """
    #     Generate a response for the given task without streaming.
    #     Args:
    #         task (str): The task or prompt.
    #         report_type (str): The type of report to generate.
    #         report_source (str): The source of the report (e.g., "web", "local", "hybrid").
    #         source_urls (List[str]): URLs to use as sources.
    #         document_urls (List[str]): Documents to use as sources.
    #         tone (str): The tone of the response (e.g., "Objective").
    #         websocket (Optional[WebSocket]): The WebSocket connection (optional).
    #         headers (Optional[Dict]): Additional headers (optional).
    #     Returns:
    #         str: The generated response.
    #     """
    #     try:
    #         # Convert the tone string to the Tone enum
    #         tone_enum = Tone[tone]  # Map the tone string to the Tone enum
    #     except KeyError:
    #         valid_tones = [t.name for t in Tone]  # Get valid tone names
    #         raise ValueError(f"Invalid tone: {tone}. Valid tones are: {valid_tones}")

    #     try:
    #         # Convert the report_source string to the ReportSource enum
    #         report_source_enum = ReportSource(report_source)  # Map the report_source string to the ReportSource enum
    #     except ValueError:
    #         valid_report_sources = [s.value for s in ReportSource]  # Get valid report source values
    #         raise ValueError(f"Invalid report source: {report_source}. Valid report sources are: {valid_report_sources}")

    #     config_path = "default"  # Use the default config path

    #     # Run the agent and generate the report
    #     report = await run_agent(
    #         task, report_type, report_source_enum.value, source_urls, document_urls, tone_enum, websocket, headers, config_path
    #     )

    #     # Create a new Chat Agent if needed
    #     self.chat_agent = ChatAgentWithMemory(report, config_path, headers)

    #     return report


    # async def generate_response(
    # self,
    # task: str,
    # report_type: str,
    # report_source: str,
    # source_urls: List[str],
    # document_urls: List[str],
    # tone: str,  # Pass the tone as a string (e.g., "Analytical")
    # websocket: Optional[WebSocket] = None,
    # headers: Optional[Dict] = None
    # ) -> str:
    #     """
    #     Generate a response for the given task without streaming.
    #     Args:
    #         task (str): The task or prompt.
    #         report_type (str): The type of report to generate.
    #         report_source (str): The source of the report.
    #         source_urls (List[str]): URLs to use as sources.
    #         document_urls (List[str]): Documents to use as sources.
    #         tone (str): The tone of the response (e.g., "Analytical").
    #         websocket (Optional[WebSocket]): The WebSocket connection (optional).
    #         headers (Optional[Dict]): Additional headers (optional).
    #     Returns:
    #         str: The generated response.
    #     """
    #     try:
           
    #         tone_enum = Tone.Analytical  
    #     except KeyError:
    #         valid_tones = [t.name for t in Tone]  # Get valid tone names
    #         raise ValueError(f"Invalid tone: {tone}. Valid tones are: {valid_tones}")

    #     config_path = "default"  # Use the default config path

    #     # Run the agent and generate the report
    #     report = await run_agent(
    #         task, report_type, report_source, source_urls, document_urls, tone_enum, websocket, headers, config_path
    #     )

    #     # Create a new Chat Agent if needed
    #     self.chat_agent = ChatAgentWithMemory(report, config_path, headers)

    #     return report







    









    async def start_sender(self, websocket: WebSocket):
        """Start the sender task."""
        queue = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except:
                    break
            else:
                break

    async def connect(self, websocket: WebSocket):
        """Connect a websocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(
            self.start_sender(websocket))

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.sender_tasks[websocket].cancel()
            await self.message_queues[websocket].put(None)
            del self.sender_tasks[websocket]
            del self.message_queues[websocket]

    async def start_streaming(self, task, report_type, report_source, source_urls, document_urls, tone, websocket, headers=None):
        """Start streaming the output."""
        tone = Tone[tone]
        # add customized JSON config file path here
        config_path = "default"
        report = await run_agent(task, report_type, report_source, source_urls, document_urls, tone, websocket, headers = headers, config_path = config_path)
        #Create new Chat Agent whenever a new report is written
        self.chat_agent = ChatAgentWithMemory(report, config_path, headers)
        return report

    async def chat(self, message, websocket):
        """Chat with the agent based message diff"""
        if self.chat_agent:
            await self.chat_agent.chat(message, websocket)
        else:
            await websocket.send_json({"type": "chat", "content": "Knowledge empty, please run the research first to obtain knowledge"})





async def run_agent(task, report_type, report_source, source_urls, document_urls, tone: Tone, websocket, headers=None, config_path=""):
    """Run the agent."""
    start_time = datetime.datetime.now()

    # Create logs handler for this research task (if WebSocket is provided)
    logs_handler = CustomLogsHandler(websocket, task) if websocket else None

    # Initialize researcher based on report type
    if report_type == "multi_agents":
        report = await run_research_task(
            query=task,
            websocket=logs_handler,  # Use logs_handler if available
            stream_output=stream_output,
            tone=tone,  # Pass the Tone enum
            headers=headers
        )
        report = report.get("report", "")
    elif report_type == ReportType.DetailedReport.value:
        researcher = DetailedReport(
            query=task,
            report_type=report_type,
            report_source=report_source,  # Pass the report source
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,  # Pass the Tone enum
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler if available
            headers=headers
        )
        report = await researcher.run()
    else:
        researcher = BasicReport(
            query=task,
            report_type=report_type,
            report_source=report_source,  # Pass the report source
            source_urls=source_urls,
            document_urls=document_urls,
            tone=tone,  # Pass the Tone enum
            config_path=config_path,
            websocket=logs_handler,  # Use logs_handler if available
            headers=headers
        )
        report = await researcher.run()

    return report

# async def run_agent(task, report_type, report_source, source_urls, document_urls, tone: Tone, websocket, headers=None, config_path=""):
#     """Run the agent."""
#     start_time = datetime.datetime.now()

#     # Create logs handler for this research task (if WebSocket is provided)
#     logs_handler = CustomLogsHandler(websocket, task) if websocket else None

#     # Initialize researcher based on report type
#     if report_type == "multi_agents":
#         report = await run_research_task(
#             query=task,
#             websocket=logs_handler,  # Use logs_handler if available
#             stream_output=stream_output,
#             tone=tone,  # Pass the Tone enum
#             headers=headers
#         )
#         report = report.get("report", "")
#     elif report_type == ReportType.DetailedReport.value:
#         researcher = DetailedReport(
#             query=task,
#             report_type=report_type,
#             report_source=report_source,
#             source_urls=source_urls,
#             document_urls=document_urls,
#             tone=tone,  # Pass the Tone enum
#             config_path=config_path,
#             websocket=logs_handler,  # Use logs_handler if available
#             headers=headers
#         )
#         report = await researcher.run()
#     else:
#         researcher = BasicReport(
#             query=task,
#             report_type=report_type,
#             report_source=report_source,
#             source_urls=source_urls,
#             document_urls=document_urls,
#             tone=tone,  # Pass the Tone enum
#             config_path=config_path,
#             websocket=logs_handler,  # Use logs_handler if available
#             headers=headers
#         )
#         report = await researcher.run()

#     return report




















# async def run_agent(task, report_type, report_source, source_urls, document_urls, tone: Tone, websocket, headers=None, config_path=""):
#     """Run the agent."""
#     start_time = datetime.datetime.now()
    
#     # Create logs handler for this research task
#     logs_handler = CustomLogsHandler(websocket, task)
    
#     # Initialize researcher based on report type
#     if report_type == "multi_agents":
#         report = await run_research_task(
#             query=task, 
#             websocket=logs_handler,  # Use logs_handler instead of raw websocket
#             stream_output=stream_output, 
#             tone=tone, 
#             headers=headers
#         )
#         report = report.get("report", "")
        
#     elif report_type == ReportType.DetailedReport.value:
#         researcher = DetailedReport(
#             query=task,
#             report_type=report_type,
#             report_source=report_source,
#             source_urls=source_urls,
#             document_urls=document_urls,
#             tone=tone,
#             config_path=config_path,
#             websocket=logs_handler,  # Use logs_handler instead of raw websocket
#             headers=headers
#         )
#         report = await researcher.run()
        
#     else:
#         researcher = BasicReport(
#             query=task,
#             report_type=report_type,
#             report_source=report_source,
#             source_urls=source_urls,
#             document_urls=document_urls,
#             tone=tone,
#             config_path=config_path,
#             websocket=logs_handler,  # Use logs_handler instead of raw websocket
#             headers=headers
#         )
#         report = await researcher.run()

#     return report
