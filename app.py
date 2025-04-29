import streamlit as st
import asyncio
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain_deepseek import ChatDeepSeek
from browser_use import Agent, Browser, BrowserConfig
import os
from dotenv import load_dotenv
import json
import nest_asyncio
import time
import logging
import io
import threading
import sys
from contextlib import redirect_stdout, redirect_stderr

# Apply nest_asyncio to make asyncio work in Streamlit
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Set up logging to capture browser-use logs
log_stream = io.StringIO()
logging.basicConfig(
    stream=log_stream,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# Custom stdout and stderr capture for browser-use output
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

# Set page config
st.set_page_config(
    page_title="Browser Automation",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    body {
        background-color: #0e1117;
        color: white;
    }
    .main {
        background-color: #0e1117;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .css-1d391kg {
        padding: 1rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 2.5rem;
        background-color: #4B61D1;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #3A4DA3;
    }
    .example-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid #2d3250;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        cursor: pointer;
        color: white;
    }
    .example-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        border: 1px solid #4B61D1;
    }
    .example-card h4 {
        color: white;
        margin-bottom: 0.5rem;
    }
    .example-card p {
        color: #a9b4f4;
        margin-bottom: 0;
    }
    .task-container {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #2d3250;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .stTextArea>div>div {
        background-color: #262b3d;
    }
    .stTextArea textarea {
        color: white !important;
    }
    .stTextArea textarea::placeholder {
        color: #a9b4f4 !important;
    }
    .title-with-logo {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .title-with-logo h1 {
        margin: 0;
        padding: 0;
    }
    .stCheckbox label p {
        color: white !important;
    }
    .stSelectbox div {
        background-color: #262b3d;
    }
    .subtitle {
        color: #a9b4f4 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .log-container {
        background-color: #0a0e14;
        color: #e0e0e0;
        font-family: monospace;
        padding: 10px;
        border-radius: 5px;
        height: 400px;
        overflow-y: auto;
        border: 1px solid #2d3250;
        font-size: 0.85rem;
        line-height: 1.5;
        white-space: pre-wrap;
        margin-top: 0.5rem;
    }
    .log-container p {
        margin: 0;
        padding: 0;
    }
    .log-title {
        color: #a9b4f4;
        font-weight: bold;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }
    .task-execution-section {
        margin-top: 1rem;
        background-color: #1e2130;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #2d3250;
    }
    .compact-text {
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }
    .st-bc {
        padding-top: 0.5rem !important;
    }
    .compact-container {
        padding: 0.75rem !important;
        margin-bottom: 0.75rem;
    }
    .compact-divider {
        margin: 0.5rem 0;
        border-top: 1px solid #2d3250;
    }
</style>
""", unsafe_allow_html=True)

# Function to run async tasks in Streamlit
def run_async(coroutine):
    return asyncio.run(coroutine)

# Custom function to run async code synchronously
def run_sync(coroutine):
    """Run an async coroutine in a synchronous context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

# Create a thread-safe container for logs
class LogContainer:
    def __init__(self):
        self.logs = []
        self.lock = threading.Lock()
    
    def add_log(self, log):
        with self.lock:
            self.logs.append(log)
    
    def get_logs(self):
        with self.lock:
            return self.logs.copy()
    
    def clear_logs(self):
        with self.lock:
            self.logs.clear()

# Create a global log container
if 'log_container' not in st.session_state:
    st.session_state.log_container = LogContainer()

# Main title with logo
st.markdown('<div class="title-with-logo"><img src="https://img.icons8.com/fluency/48/000000/globe.png"/><h1>Browser Automation Assistant</h1></div>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Automate browser tasks with natural language</p>', unsafe_allow_html=True)

# Define example tasks with team credentials
example_tasks = [
    {
        "title": "BSE - Reliance Industries Report",
        "description": "Download the annual report PDF for Reliance Industries from BSE India",
        "task": """1. go to https://www.bseindia.com/
2. Close the small pop up tab you see and proceed
3. On the Search Bar, search for "Reliance Industries Ltd"
4. Click on "Reliance Industries Ltd"
5. Click on "Financials"
6. Click on "Annual Report"
7. Click on "pdf sign" and open the pdf file
8. Download the pdf"""
    },
    {
        "title": "Screener.in - Reliance Data",
        "description": "Download Excel report for Reliance Industries from Screener.in",
        "task": """Go to "https://www.screener.in/"
1. Click "Sign in"
2. Enter email "team@onfinance.in"
3. Enter password "@1234asdf"
4. Search for "Reliance Industries" and dont press enter, wait for suggestion drop down to appear
5. Click on the suggestion "Reliance Industries"
6. Download the excel report"""
    },
    {
        "title": "OnFinance Login",
        "description": "Login to OnFinance UAT environment",
        "task": """1. Go to "https://uat.onfinance.ai/login"
2. Login with email "team@onfinance.in" and password "all@financedisruption"
3. Expand the Side Bar"""
    }
]

# Initialize session state variables if they don't exist
if 'task_input' not in st.session_state:
    st.session_state.task_input = ""
if 'result' not in st.session_state:
    st.session_state.result = None
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'log_container' not in st.session_state:
    st.session_state.log_container = LogContainer()

# Create a main container for the task creation
with st.container():
    st.markdown('<div class="task-container">', unsafe_allow_html=True)
    st.markdown("### Create Task")
    
    # Task input area
    task_input = st.text_area(
        "Enter your task instructions:",
        height=150,
        placeholder="Enter step-by-step instructions for the browser to follow...",
        help="Be specific about URLs, buttons to click, and actions to take.",
        value=st.session_state.task_input
    )
    
    # Controls in a single row
    control_col1, control_col2, control_col3, control_col4 = st.columns([2, 1, 1, 1])
    
    with control_col1:
        # Model selection
        model_options = {
            "OpenAI GPT-4o": "openai",
            "DeepSeek": "deepseek",
            "AWS Bedrock (Claude)": "bedrock"
        }
        
        selected_model = st.selectbox(
            "Select AI Model:",
            options=list(model_options.keys()),
            index=0
        )
    
    with control_col2:
        # Headless mode option
        headless_mode = st.checkbox("Headless mode", value=False, help="Run without browser window")
    
    with control_col3:
        # Run and stop buttons
        if st.button("🚀 Run Task", use_container_width=True):
            if not task_input.strip():
                st.error("Please enter task instructions")
            else:
                # Clear previous logs when starting a new task
                st.session_state.log_container.clear_logs()
                
                # Store the task details in session state
                st.session_state.task_input = task_input
                st.session_state.status = "running"
                st.session_state.model = model_options[selected_model]
                st.session_state.headless = headless_mode
                st.session_state.result = None
                st.session_state.stop_requested = False
                
                # Rerun to start the task
                st.rerun()
    
    with control_col4:
        if 'status' in st.session_state and st.session_state.status == "running":
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.stop_requested = True
                st.warning("Stopping...")
                time.sleep(0.5)
                st.rerun()
        else:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.task_input = ""
                st.session_state.result = None
                st.session_state.log_container.clear_logs()
                st.session_state.stop_requested = False
                if 'status' in st.session_state:
                    del st.session_state.status
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Examples section - horizontal layout with cards
st.markdown("### Example Tasks")
example_cols = st.columns(len(example_tasks))

for idx, (col, example) in enumerate(zip(example_cols, example_tasks)):
    with col:
        st.markdown(f"""
        <div class='example-card' id='example-{idx}'>
            <h4>{example['title']}</h4>
            <p>{example['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Use Example", key=f"btn_{idx}", use_container_width=True):
            # Use the task directly 
            st.session_state.task_input = example['task']
            st.rerun()

# Log capture function
def capture_logs(message):
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"{timestamp} - {message}"
    st.session_state.log_container.add_log(log_entry)

# Handle task execution
if 'status' in st.session_state and st.session_state.status == "running":
    # Create a container for results
    with st.container():
        st.markdown("### Task Execution")
        
        # Split the execution display into left and right columns
        exec_col1, exec_col2 = st.columns([1, 1])
        
        with exec_col1:
            # Show task details
            st.markdown("**Selected model:** " + next(k for k, v in model_options.items() if v == st.session_state.model))
            st.markdown("**Headless mode:** " + ("Yes" if st.session_state.headless else "No"))
            st.markdown("**Task:**")
            st.code(st.session_state.task_input, language="text")
            
            # Create a placeholder for the run button that will be shown after completion
            run_again_placeholder = st.empty()
            
            # Display final results
            if st.session_state.result and st.session_state.result["success"]:
                st.markdown("#### Results:")
                results_data = st.session_state.result["results"]
                
                if isinstance(results_data, list):
                    for item in results_data:
                        st.markdown(f"- {item}")
                elif isinstance(results_data, str):
                    st.code(results_data)
                else:
                    st.json(results_data)
                
                # Button to run another task
                if run_again_placeholder.button("Run Another Task", key="run_another"):
                    st.session_state.pop('status')
                    st.rerun()
        
        with exec_col2:
            # Run the task
            st.markdown("#### Running Task...")
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Create log display area
            st.markdown('<p class="log-title">Agent Logs:</p>', unsafe_allow_html=True)
            log_area = st.empty()
            log_area.markdown('<div class="log-container"><p>Initializing...</p></div>', unsafe_allow_html=True)
            
            try:
                # Get task parameters from session state
                model_type = st.session_state.model
                task = st.session_state.task_input
                headless = st.session_state.headless
                
                # Capture initial log
                capture_logs(f"Starting task with model: {model_type}")
                
                # Display initial status
                status_placeholder.markdown("Setting up model and browser...")
                progress_bar = progress_placeholder.progress(10)
                
                # Initialize LLM based on selection
                if model_type == "openai":
                    llm = ChatOpenAI(
                        model_id="gpt-4o",
                        api_key=os.getenv("OPENAI_API_KEY")
                    )
                    capture_logs("Initialized OpenAI GPT-4o model")
                elif model_type == "deepseek":
                    llm = ChatDeepSeek(
                        base_url='https://api.deepseek.com/v1',
                        model='deepseek-chat',
                        api_key=os.getenv("DEEPSEEK_API_KEY"),
                    )
                    capture_logs("Initialized DeepSeek Chat model")
                elif model_type == "bedrock":
                    llm = ChatBedrock(
                        model_id=os.getenv("LLM_MODEL"),
                    )
                    capture_logs("Initialized AWS Bedrock Claude model")
                
                # Update logs display
                logs = st.session_state.log_container.get_logs()
                log_display = '<div class="log-container">'
                for log in logs:
                    log_display += f"<p>{log}</p>"
                log_display += '</div>'
                log_area.markdown(log_display, unsafe_allow_html=True)
                
                # Update progress
                progress_bar.progress(20)
                status_placeholder.markdown("Initializing browser...")
                capture_logs("Initializing browser...")
                
                # Define a callback to update logs in the UI
                def update_logs():
                    try:
                        logs = st.session_state.log_container.get_logs()
                        log_display = '<div class="log-container">'
                        for log in logs[-100:]:  # Show last 100 logs to avoid overload
                            log_display += f"<p>{log}</p>"
                        log_display += '</div>'
                        log_area.markdown(log_display, unsafe_allow_html=True)
                    except Exception as e:
                        # Silently handle UI update errors
                        pass
                
                # Create and initialize browser with logging
                try:
                    # Store original stdout before entering try block
                    old_stdout = sys.stdout
                    
                    # Set up logging callbacks
                    class StdoutRedirector:
                        def write(self, message):
                            if message.strip():
                                capture_logs(message.strip())
                            sys.__stdout__.write(message)
                        
                        def flush(self):
                            sys.__stdout__.flush()
                    
                    # Redirect stdout to capture logs
                    sys.stdout = StdoutRedirector()
                    
                    # Create a simple async function following the pattern from main.py
                    async def run_agent_task():
                        # Create browser
                        capture_logs("Creating browser...")
                        browser_config = BrowserConfig(headless=headless)
                        browser = Browser(config=browser_config)
                        capture_logs("Browser created successfully")
                        
                        # Update UI
                        progress_bar.progress(40)
                        status_placeholder.markdown("Browser initialized. Creating agent...")
                        
                        # Check if stop requested
                        if st.session_state.stop_requested:
                            capture_logs("Task terminated by user request")
                            try:
                                # Try to close the browser gracefully
                                if hasattr(browser, 'cleanup'):
                                    await browser.cleanup()
                                elif hasattr(browser, 'close'):
                                    await browser.close()
                                elif hasattr(browser, 'quit'):
                                    await browser.quit()
                                else:
                                    # As a last resort, try to access the driver directly
                                    if hasattr(browser, 'driver'):
                                        browser.driver.quit()
                            except Exception as e:
                                capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                            return "Task terminated by user request"
                        
                        # Create agent
                        capture_logs("Creating agent with the specified task...")
                        agent = Agent(
                            task=task,
                            browser=browser,
                            llm=llm,
                            use_vision=True
                        )
                        capture_logs("Agent created successfully")
                        
                        # Update UI
                        progress_bar.progress(60)
                        status_placeholder.markdown("Agent created. Running task...")
                        
                        # Check if stop requested
                        if st.session_state.stop_requested:
                            capture_logs("Task terminated by user request")
                            try:
                                # Try to close the browser gracefully
                                if hasattr(browser, 'cleanup'):
                                    await browser.cleanup()
                                elif hasattr(browser, 'close'):
                                    await browser.close()
                                elif hasattr(browser, 'quit'):
                                    await browser.quit()
                                else:
                                    # As a last resort, try to access the driver directly
                                    if hasattr(browser, 'driver'):
                                        browser.driver.quit()
                            except Exception as e:
                                capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                            return "Task terminated by user request"
                        
                        # Run the task
                        capture_logs("Starting task execution...")
                        try:
                            # Run with periodic checks for stop request
                            original_run = agent.run
                            
                            async def run_with_stop_check():
                                # Override agent's run function to check for stop
                                steps = 0
                                results = None
                                
                                # Start the original run but check periodically
                                task = asyncio.create_task(original_run())
                                
                                while not task.done():
                                    # Wait a short time and check stop flag
                                    await asyncio.sleep(1)
                                    steps += 1
                                    
                                    if steps % 3 == 0:  # Check every 3 seconds
                                        # Update logs
                                        update_logs()
                                    
                                    if st.session_state.stop_requested:
                                        capture_logs("🛑 Stop requested! Terminating task...")
                                        # Clean up and cancel
                                        task.cancel()
                                        try:
                                            # Try to close the browser gracefully
                                            if hasattr(browser, 'cleanup'):
                                                await browser.cleanup()
                                            elif hasattr(browser, 'close'):
                                                await browser.close()
                                            elif hasattr(browser, 'quit'):
                                                await browser.quit()
                                            else:
                                                # As a last resort, try to access the driver directly
                                                if hasattr(browser, 'driver'):
                                                    browser.driver.quit()
                                        except Exception as e:
                                            capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                                        return "Task terminated by user request"
                                
                                # If we get here, the task completed normally
                                results = await task
                                return results
                            
                            results = await run_with_stop_check()
                            
                            # Check one more time after getting results
                            if st.session_state.stop_requested:
                                capture_logs("Task terminated by user after completion")
                                try:
                                    # Try to close the browser gracefully
                                    if hasattr(browser, 'cleanup'):
                                        await browser.cleanup()
                                    elif hasattr(browser, 'close'):
                                        await browser.close()
                                    elif hasattr(browser, 'quit'):
                                        await browser.quit()
                                    else:
                                        # As a last resort, try to access the driver directly
                                        if hasattr(browser, 'driver'):
                                            browser.driver.quit()
                                except Exception as e:
                                    capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                                return "Task terminated by user request"
                            
                            capture_logs("Task execution completed")
                            return results
                        except asyncio.CancelledError:
                            capture_logs("Task was cancelled")
                            try:
                                # Try to close the browser gracefully
                                if hasattr(browser, 'cleanup'):
                                    await browser.cleanup()
                                elif hasattr(browser, 'close'):
                                    await browser.close()
                                elif hasattr(browser, 'quit'):
                                    await browser.quit()
                                else:
                                    # As a last resort, try to access the driver directly
                                    if hasattr(browser, 'driver'):
                                        browser.driver.quit()
                            except Exception as e:
                                capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                            return "Task cancelled by user"
                        except Exception as e:
                            capture_logs(f"Error during execution: {str(e)}")
                            try:
                                # Try to close the browser gracefully
                                if hasattr(browser, 'cleanup'):
                                    await browser.cleanup()
                                elif hasattr(browser, 'close'):
                                    await browser.close()
                                elif hasattr(browser, 'quit'):
                                    await browser.quit()
                                else:
                                    # As a last resort, try to access the driver directly
                                    if hasattr(browser, 'driver'):
                                        browser.driver.quit()
                            except Exception as e:
                                capture_logs(f"Warning: Could not clean up browser properly: {str(e)}")
                            raise
                    
                    # Run the async function using asyncio
                    results = asyncio.run(run_agent_task())
                    
                    # Update UI with success
                    progress_bar.progress(100)
                    status_placeholder.markdown("Task completed successfully!")
                    st.success("Task completed successfully!")
                    
                    # Store results
                    st.session_state.result = {"success": True, "results": results}
                    
                    # Restore stdout
                    sys.stdout = old_stdout
                    
                except Exception as e:
                    # Handle errors during execution
                    error_msg = str(e)
                    capture_logs(f"Error during execution: {error_msg}")
                    st.error(f"Error: {error_msg}")
                    st.session_state.result = {"success": False, "error": error_msg}
                    
                    # Restore stdout
                    sys.stdout = old_stdout
                    
                    # Final log update
                    update_logs()
            
            except Exception as e:
                # Handle errors during setup
                error_msg = str(e)
                capture_logs(f"Error during setup: {error_msg}")
                st.error(f"Error: {error_msg}")
                st.session_state.result = {"success": False, "error": error_msg}
                
                # Final log update
                logs = st.session_state.log_container.get_logs()
                log_display = '<div class="log-container">'
                for log in logs[-100:]:
                    log_display += f"<p>{log}</p>"
                log_display += '</div>'
                log_area.markdown(log_display, unsafe_allow_html=True)
            
# Documentation section at the bottom
with st.expander("📚 How to use this tool"):
    st.markdown("""
    ### Getting Started
    
    This tool allows you to automate browser tasks using natural language instructions. Here's how to use it:
    
    1. **Enter Instructions**: Type step-by-step instructions for what you want the browser to do
    2. **Select Model**: Choose which AI model will interpret your instructions
    3. **Configure Options**: Decide if you want to see the browser window or run in headless mode
    4. **Run Task**: Click the Run button and watch as the browser follows your instructions
    
    ### Tips for Writing Good Instructions
    
    - Be specific about URLs, button labels, and text fields
    - Number your steps for clarity
    - Mention exactly what text to enter in forms
    - Specify exactly what to click on each page
    
    ### Example Use Cases
    
    - Automating data collection from websites
    - Downloading reports from financial platforms
    - Checking information across multiple sites
    - Filling out forms or applications
    """)

# Add credit at the bottom
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>Browser Automation UI | Built with Streamlit</p>",
    unsafe_allow_html=True
) 