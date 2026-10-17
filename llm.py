import requests
import time
import json

# Builds Prompt for LLM
# Also builds JSON Schema if necessary for answer
# returns message + schema
def build_request(ticket, evals):

    prompt = "Analyze the following ITSM ticket:\n"

    properties = {}

    if "description_quality" in evals:
        prompt += """
        \n- Rate the ticket description quality from 1 to 10.
        Evaluate whether the description clearly explains the issue or request.
        The rating has to consider, wheter the description gives a clear picture, what is needed or what isn't working.
        Only evaluate the subject and description fields.

        Rating guidelines:
        1-2: Missing, meaningless, or impossible to understand.
        3-4: Issue is vaguely described. Essential information is missing.
        5-6: Main issue is understandable, but relevant details or context are missing.
        7-8: Clear description with sufficient information to understand the issue or request.
        9-10: Clear, concise, and complete description with relevant context and details.

        Do not penalize simple issues for not requiring extensive descriptions.
        Give a short reason for the rating.
        """
        properties["description_quality"] = {
            "type": "integer",
            "minimum": 1,
            "maximum": 10
        }
        properties["description_quality_reason"] = {
            "type": "string",
            "maxLength": 1000
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
def send_request(base_url, model, message, api_key=None, temperature=0.1, schema=None):

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
        timeout=600
    )

    duration = time.perf_counter() - start

    response.raise_for_status() #Catch HTTP Errors
    data = response.json()

    content = data["choices"][0]["message"]["content"]

    if schema is not None:
        content = json.loads(content)

    metrics = {
        "duration_seconds": round(duration, 2),
        "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
        "total_tokens": data.get("usage", {}).get("total_tokens", 0)
    }

    return content, metrics