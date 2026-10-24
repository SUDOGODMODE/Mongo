import requests
import time
import json

# Builds Prompt for LLM
# Also builds JSON Schema if necessary for answer
# returns message + schema
def build_request(ticket, evals):

    prompt = "Analyze the following Incident ticket:\n"

    properties = {}

    if "impact" in evals:
        prompt += """
        Perform an IT incident impact analysis and rate the severity from 1 to 10.

        Consider the following criteria:
        - Number of affected users or systems
        - Business impact and service availability
        - Criticality of the affected system or service
        - Availability of a workaround
        - Potential security or data integrity risks

        Rating guidelines:
        1-2: Very Low - Minor issue, negligible business impact, individual user affected.
        3-4: Low - Limited impact, few users affected, normal operations mostly possible.
        5-6: Medium - Noticeable disruption, multiple users affected, important functions impaired.
        7-8: High - Major disruption, critical service impaired or unavailable, many users affected.
        9-10: Critical - Business-critical outage, widespread impact, production stopped or severe security/data integrity risk.

        Instructions:
        - Base the rating only on the provided incident information.
        - Do not assume missing information.
        - Rate the actual impact, not the potential worst-case scenario.
        - Give a short explanation for the rating.
        - Return the severity rating and reason in the specified JSON format.
        """

        properties["impact_rating"] = {
            "type": "integer",
            "minimum": 1,
            "maximum": 10
        }
        properties["impact_reason"] = {
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