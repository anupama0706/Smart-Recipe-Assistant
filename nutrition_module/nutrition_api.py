"""Adapter that talks to an external Nutrition API.

The request body is intentionally generic. Map it to a specific
provider (headers, query authentication, response fields) when an
API is selected. Calculation code must not depend on this payload.
"""

import requests


def fetch_nutrition(ingredients, api_url, headers=None, timeout=15):
    """Send ingredient data to a configured nutrition endpoint.

    The request body and response format must be adapted
    to the selected provider's official API documentation.

    Raises:
        ValueError: If ingredients or the API URL are missing.
        RuntimeError: On timeout, network/HTTP failure, invalid JSON,
            or a JSON body that is not an object.
    """
    if not ingredients:
        raise ValueError("At least one ingredient is required")
    if not api_url:
        raise ValueError("Nutrition API URL is required")

    try:
        response = requests.post(
            api_url,
            json={"ingredients": ingredients},
            headers=headers or {},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as exc:
        raise RuntimeError("Nutrition API request timed out") from exc
    except ValueError as exc:
        # requests.JSONDecodeError subclasses both ValueError and
        # RequestException, so it must be handled before RequestException.
        raise RuntimeError("Nutrition API returned invalid JSON") from exc
    except requests.RequestException as exc:
        raise RuntimeError("Nutrition API request failed") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Nutrition API returned an unexpected response")

    return data
