import logging

from ingestion import read
from processing import extract_transform
from processing import geolocation
from dashboard import show_dashboard


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s|%(name)s|%(levelname)s|%(message)s",
        datefmt="%d/%m/%Y %H:%M:%S"
    )

    rows = read.ingest("./data")

    if rows:
        attempts = []

        for row in rows:
            result = extract_transform.extract(row)

            if result:
                attempts.append(result)

        print("Nombre de lignes extraites :", len(attempts))

        # 1. Réussites par utilisateur.
        success_by_user = {}

        for attempt in attempts:
            if attempt["status"] == "Accepted":
                user = attempt["user"]

                if user not in success_by_user:
                    success_by_user[user] = 0

                success_by_user[user] += attempt["count"]

        print("Réussites par utilisateur :", success_by_user)

        # 2. Échecs avec utilisateur invalide.
        invalid_user_failures = 0

        for attempt in attempts:
            if (
                attempt["status"] == "Failed"
                and attempt["invalid"] is not None
            ):
                invalid_user_failures += attempt["count"]

        print(
            "Échecs avec utilisateur invalide :",
            invalid_user_failures
        )

        # Lecture du cache des pays.
        country_by_ip = {}

        try:
            with open(
                "ip_countries.txt",
                "r",
                encoding="utf-8"
            ) as f:
                for line_number, line in enumerate(f, start=1):
                    parts = line.strip().split(",")

                    if len(parts) != 2:
                        logger.warning(
                            f"Cache : ligne {line_number} mal formée."
                        )
                        continue

                    ip, country = parts

                    if not ip or not country:
                        logger.warning(
                            f"Cache : IP ou pays vide "
                            f"à la ligne {line_number}."
                        )
                        continue

                    country_by_ip[ip] = country

        except FileNotFoundError:
            logger.info(
                "Cache des pays absent : première utilisation."
            )

        except (OSError, UnicodeError) as e:
            logger.error(
                f"Impossible de lire complètement le cache : {e}"
            )

        # 3. Échecs par pays.
        failures_by_country = {}

        for attempt in attempts:
            if attempt["status"] == "Failed":
                ip = attempt["ip"]

                if ip not in country_by_ip:
                    print(
                        "Recherche du pays pour :",
                        ip,
                        flush=True
                    )

                    country_by_ip[ip] = geolocation.geo_location(ip)
                    country = country_by_ip[ip]

                    if country != "Inconnu":
                        try:
                            with open(
                                "ip_countries.txt",
                                "a",
                                encoding="utf-8"
                            ) as f:
                                f.write(f"{ip},{country}\n")

                        except (OSError, UnicodeError) as e:
                            logger.error(
                                f"Impossible de sauvegarder "
                                f"le pays de l'IP {ip} : {e}"
                            )

                country = country_by_ip[ip]

                if country not in failures_by_country:
                    failures_by_country[country] = 0

                failures_by_country[country] += attempt["count"]

        print("Échecs par pays :", failures_by_country)

        # Totaux tenant compte des répétitions.
        total_failures = sum(failures_by_country.values())
        total_successes = sum(success_by_user.values())

        print("Total des échecs :", total_failures)
        print("Total des réussites :", total_successes)
        print(
            "Total comptabilisé :",
            total_failures + total_successes
        )

        show_dashboard(
            failures_by_country,
            success_by_user,
            invalid_user_failures
        )