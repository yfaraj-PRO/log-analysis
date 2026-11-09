import logging
import matplotlib.pyplot as plt


logger = logging.getLogger(__name__)


def draw_dashboard(
    failures_by_country,
    success_by_user,
    invalid_user_failures
):
    sorted_countries = sorted(
        failures_by_country,
        key=failures_by_country.get,
        reverse=True
    )

    countries_per_chart = 15

    number_of_charts = max(
        1,
        (len(sorted_countries) + countries_per_chart - 1)
        // countries_per_chart
    )

    # Même échelle pour tous les graphiques de pays.
    max_failures = max(failures_by_country.values(), default=0)
    common_limit = max(1, max_failures * 1.35)

    fig = plt.figure(
        figsize=(20, 11),
        facecolor="#f5f7fa"
    )

    grid = fig.add_gridspec(
        6,
        number_of_charts * 2,
        height_ratios=[1, 1, 1, 1, 0.9, 1.2],
        left=0.09,
        right=0.97,
        bottom=0.12,
        top=0.86,
        wspace=1.6,
        hspace=0.5
    )

    fig.suptitle(
        "Analyse des tentatives d’authentification SSH",
        fontsize=18,
        fontweight="bold",
        y=0.97
    )

    fig.text(
        0.5,
        0.92,
        "Échecs par pays — classement décroissant",
        ha="center",
        fontsize=12,
        color="#475569"
    )

    # 1. Échecs par pays.
    for index in range(number_of_charts):
        start = index * countries_per_chart
        end = start + countries_per_chart

        countries = sorted_countries[start:end]
        counts = [
            failures_by_country[country]
            for country in countries
        ]

        ax = fig.add_subplot(
            grid[:4, index * 2:(index + 1) * 2]
        )

        bars = ax.barh(
            countries,
            counts,
            height=0.5,
            color="#477fa8"
        )

        ax.set_ylim(countries_per_chart - 0.5, -0.8)
        ax.set_xlim(0, common_limit)

        ax.bar_label(
            bars,
            padding=5,
            fmt="%d",
            fontsize=10
        )

        if countries:
            ax.set_title(
                f"Rangs {start + 1} à {start + len(countries)}",
                fontsize=11,
                pad=15
            )
        else:
            ax.set_title("Aucun échec", fontsize=11)

        ax.set_xlabel(
            "Nombre d’échecs",
            fontsize=9,
            labelpad=8
        )

        ax.tick_params(
            axis="y",
            labelsize=10,
            length=0,
            pad=6
        )

        ax.tick_params(
            axis="x",
            labelsize=8
        )

        ax.locator_params(
            axis="x",
            nbins=3,
            integer=True
        )

        ax.grid(
            axis="x",
            linestyle="--",
            alpha=0.25
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    # La rangée 4 reste vide pour séparer les graphiques.

    # 2. Réussites par utilisateur.
    ax_users = fig.add_subplot(
        grid[5, :number_of_charts]
    )

    users = sorted(
        success_by_user,
        key=success_by_user.get,
        reverse=True
    )

    successes = [
        success_by_user[user]
        for user in users
    ]

    bars_users = ax_users.barh(
        users,
        successes,
        height=0.4,
        color="#2f8a60"
    )

    ax_users.bar_label(
        bars_users,
        padding=6,
        fmt="%d",
        fontsize=12
    )

    ax_users.set_title(
        "Réussites par utilisateur",
        fontsize=12,
        pad=12
    )

    ax_users.set_ylim(
        max(len(users), 2) - 0.5,
        -0.5
    )

    ax_users.tick_params(
        axis="y",
        labelsize=10,
        length=0,
        pad=6
    )

    ax_users.set_xticks([])

    if successes:
        ax_users.set_xlim(0, max(successes) * 1.25)
    else:
        ax_users.text(
            0.5,
            0.5,
            "Aucune réussite",
            transform=ax_users.transAxes,
            ha="center",
            va="center"
        )

    for spine in ax_users.spines.values():
        spine.set_visible(False)

    # 3. Échecs avec utilisateur invalide.
    ax_invalid = fig.add_subplot(
        grid[5, number_of_charts:]
    )

    ax_invalid.axis("off")

    ax_invalid.set_title(
        "Échecs avec utilisateur invalide",
        fontsize=12,
        pad=12
    )

    ax_invalid.text(
        0.5,
        0.60,
        f"{invalid_user_failures:,}".replace(",", " "),
        transform=ax_invalid.transAxes,
        ha="center",
        va="center",
        fontsize=30,
        fontweight="bold",
        color="#b73939"
    )

    ax_invalid.text(
        0.5,
        0.05,
        "Inclus dans les échecs par pays",
        transform=ax_invalid.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="#475569"
    )

    fig.text(
        0.5,
        0.035,
        "Même échelle pour tous les pays — "
        "les nombres indiquent les valeurs exactes.",
        ha="center",
        fontsize=10,
        color="#475569"
    )

    plt.show()


def show_dashboard(
    failures_by_country,
    success_by_user,
    invalid_user_failures
):
    try:
        draw_dashboard(
            failures_by_country,
            success_by_user,
            invalid_user_failures
        )

    except Exception as e:
        logger.error(
            f"Erreur pendant l'affichage du dashboard : {e}"
        )
        print(
            "Impossible d'afficher le dashboard. "
            "Consultez app.log pour connaître l'erreur."
        )