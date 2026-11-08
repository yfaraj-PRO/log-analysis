from ingestion import read
from processing import extract_transform
from processing import geolocation
import logging


if __name__ == "__main__" :
    logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s|%(name)s|%(levelname)s|%(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
    rows=read.ingest("./data")
    if rows:
        attempts = []

        for row in rows:
            result = extract_transform.extract(row)

            if result:
                attempts.append(result)

        print("Nombre de tentatives extraites :", len(attempts))

        success_by_user = {}

        for attempt in attempts:
            if attempt["status"] == "Accepted":
                user = attempt["user"]

                if user not in success_by_user:
                    success_by_user[user] = 0

                success_by_user[user] += 1

        print(success_by_user)
        invalid_user_failures = 0

        for attempt in attempts:
            if attempt["status"] == "Failed" and attempt["invalid"] is not None:
                invalid_user_failures += 1

        print("Échecs avec utilisateur invalide :", invalid_user_failures)
        country_by_ip = {}
        try:
            with open("ip_countries.txt", "r", encoding="utf-8") as f:
                for line in f:
                    ip, country = line.strip().split(",")
                    country_by_ip[ip] = country

        except FileNotFoundError:
            logging.info(
                "Cache des pays absent : première utilisation."
            )
        failures_by_country = {}

        for attempt in attempts:
            if attempt["status"] == "Failed":
                ip = attempt["ip"]

                if ip not in country_by_ip:
                    print("Recherche du pays pour :", ip, flush=True)
                    country_by_ip[ip] = geolocation.geo_location(ip)
                    country = country_by_ip[ip]

                    if country != "Inconnu":
                        with open("ip_countries.txt", "a", encoding="utf-8") as f:
                            f.write(f"{ip},{country}\n")

                country = country_by_ip[ip]

                if country not in failures_by_country:
                    failures_by_country[country] = 0

                failures_by_country[country] += 1

        print("Échecs par pays :", failures_by_country)
        total_failures = sum(failures_by_country.values())
        total_successes = sum(success_by_user.values())

        print("Total des échecs :", total_failures)
        print("Total des réussites :", total_successes)
        print("Total comptabilisé :", total_failures + total_successes)