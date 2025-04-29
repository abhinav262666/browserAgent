# Browser Automation UI

A beautiful Streamlit interface for running browser automation tasks using natural language instructions.

## Features

- **Natural Language Instructions**: Define browser tasks using simple step-by-step instructions
- **Model Selection**: Choose between OpenAI, DeepSeek, or AWS Bedrock for task interpretation
- **Example Tasks**: Pre-configured example tasks to get started quickly
- **Beautiful UI**: Modern, responsive interface with real-time task progress
- **Password Protection**: Credentials are stored in environment variables, not in the code

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   uv venv --python 3.11
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=your_aws_region
   LLM_MODEL=your_bedrock_model
   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ```

## Running the Application

Use the provided shell script:
```
./run.sh
```

Or run directly with Streamlit:
```
streamlit run app.py
```

## How to Use

1. Enter your browser automation instructions in the text area
2. Select the AI model you want to use for interpretation
3. Choose whether to run in headless mode or with a visible browser
4. Click "Run Task" to start the automation
5. View the results in real-time

## Example Use Cases

- Download reports from financial websites
- Extract data from multiple web pages
- Automate form filling and submissions
- Perform repetitive web tasks

## Dependencies

- browser-use: For browser automation
- streamlit: For the user interface
- langchain: For LLM integration
- python-dotenv: For environment variable management

## License

MIT # browseruseAgent
# browserAgent
# browserAgent
