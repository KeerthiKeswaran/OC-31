from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def init_pipeline():
    groq_api_key = GROQ_API_KEY

    llmAnalysis = ChatGroq(
        temperature=0.2,
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile"
    )
    
    llm_prompt = """
    You are an AI assistant trained to analyze logs and system metrics in real-time for a web service. Your task is to:
    1. Identify any anomalies or performance degradation based on the provided metrics and logs.
    2. Suggest improvements and optimizations based on the identified issues.
    
    The following are the available data:
    - **Logs**: {logs}
    - **Metrics**: 
      - CPU Usage: {cpu_usage}
      - Memory Usage: {memory_usage}
      - Response Time: {response_time}
      - Error Rate: {error_rate}
      - DB Query Time: {db_query_time}
      - Throughput: {throughput}
    - **Code Context**: {code_context}

    Your response should include a structured breakdown with the following information:

    1. **Root Cause**: [Summarize the likely cause of the issue]
    2. **Severity Level**: [Categorize as low, medium, or high]
    3. **Affected Services**: [List any services affected, e.g., user-service, payment-gateway]
    4. **Metrics Analysis**: 
       - **CPU Usage**: {{ cpu_usage }} 
       - **Memory Usage**: {memory_usage}
       - **Response Time**: {{ response_time }} 
       - **Error Rate**: {{ error_rate }} 
       - **DB Query Time**: {db_query_time}
       - **Throughput**: {throughput}
    5. **Log Analysis**: 
       - Include relevant log entries with timestamps and the log level.
    6. **Performance Comparison**: [Include deviations in performance metrics]
    7. **Recommended Solution**: [Propose actionable solutions to resolve the issue]
    8. **Next Steps**: [Propose follow-up actions]

    If the issue is related to an external factor (e.g., a third-party API), indicate it clearly.

    Provide the relevant solution only for the {logs} provided.

    Please provide a detailed and actionable report in JSON format. Just give me the JSON stuctured response alone, no need of anything other than that.
    """

    template = PromptTemplate(
        input_variables=["logs","cpu_usage","code_context", "memory_usage", 
                         "response_time", "error_rate", "db_query_time", "throughput"],
        template=llm_prompt
    )
    
    chain_analysis = template | llmAnalysis
    
    return chain_analysis
