import requests
import asyncio
from requests.exceptions import ConnectionError, Timeout, HTTPError


async def generate_response(prompt: str) -> str:
    def call_ollama():
        try:
            # Send prompt to Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gpt-oss:20b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=5000  # Max wait time for the model response
            )

            # Raise exception for HTTP errors (4xx / 5xx)
            response.raise_for_status()

            # Return parsed JSON response
            return response.json()

        except ConnectionError:
            # Ollama is not running or unreachable
            return {"error": "Ollama no está iniciado o no se puede conectar."}

        except Timeout:
            # Request took too long
            return {"error": "Tiempo de espera excedido al generar la respuesta."}

        except HTTPError as e:
            # Authentication or permission error
            status_code = e.response.status_code if e.response else None
            if status_code in (401, 403):
                return {"error": "Token incorrecto o acceso no autorizado."}

            # Other HTTP-related errors
            return {"error": f"Error HTTP ({status_code})."}

        except Exception:
            # Catch any unexpected error
            return {"error": "Ocurrió un error inesperado al generar la respuesta."}

    # Run the blocking request in a separate thread
    data = await asyncio.to_thread(call_ollama)

    # If an error occurred, return it directly
    if "error" in data:
        return data["error"]

    # Return model response or fallback message
    return data.get("response", "No se pudo generar respuesta.")
