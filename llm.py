import config
import requests
import time
import json

# Builds Prompt for LLM
# Also builds JSON Schema if necessary for answer
# returns message + schema
def build_request(ticket, evals):

    prompt = config.LLM_PROMPT_DESCRIPTION

    properties = {}

    if "impact" in evals:
        prompt += config.LLM_IMPACT_PROMPT

        properties["impact_rating"] = {
            "type": "integer",
            "minimum": 1,
            "maximum": 10
        }
        properties["impact_reason"] = {
            "type": "string",
            "maxLength": 250
        }


    schema = {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False
    }

    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": json.dumps(ticket, ensure_ascii=False)
        }
    ]

    return messages, schema


# Send to LLM Endpoint
# Returns answer as string when not using schema
# Return JSON when using schema
def send_request(base_url, model, message, api_key=None, temperature=None, schema=None):

    if api_key is None:
        api_key = config.LLM_API_KEY
    if temperature is None:
        temperature = config.LLM_TEMPERATURE

    headers = {
        "Content-Type": "application/json"
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": message,
        "temperature": temperature,
        "stream": False
    }


    if schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "dynamic_response",
                "strict": True,
                "schema": schema
            }
        }

    start = time.perf_counter()

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=config.LLM_REQUEST_TIMEOUT
    )

    duration = time.perf_counter() - start

    response.raise_for_status() #Catch HTTP Errors
    data = response.json()

    content = data["choices"][0]["message"]["content"]

    if schema is not None:
        content = json.loads(content)

    metrics = {
        "model": model,
        "duration_seconds": round(duration, 2),
        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
        "total_tokens": data.get("usage", {}).get("total_tokens", 0)
    }

    return content, metrics
