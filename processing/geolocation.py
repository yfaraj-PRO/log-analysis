import requests as http
import logging

logger = logging.getLogger(__name__)

from requests import Response

def geo_location(ip):
    try:
        response = http.get(
            "https://ipinfo.io/" + ip + "/json",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("country", "Inconnu")

        logger.error(
            f"Erreur HTTP {response.status_code} pour l'IP {ip}"
        )
        return "Inconnu"

    except Exception as e:
        logger.error(f"Erreur de géolocalisation pour l'IP {ip} : {e}")
        return "Inconnu"