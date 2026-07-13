from sales_provider import SalesProvider
from email_sender import send_email
from json_reader import get_games_list
from isthereanydeal_api import get_sale_games_itad
from buscape_scraping import Buscape_Provider


def _get_providers(games: list[str]) -> list[SalesProvider]:
    return [
        Buscape_Provider(games)
    ]

def _format_currency(value) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"

def _format_game_sale(game_sale) -> str:
    os_list = ", ".join(game_sale.os_list) if game_sale.os_list else "-"
    platforms = ", ".join(game_sale.platforms) if game_sale.platforms else "-"
    voucher = game_sale.voucher or "-"

    return "\n".join(
        [
            f"Jogo: {game_sale.name}",
            f"Preço: {_format_currency(game_sale.price)}",
            f"Preço comum: {_format_currency(game_sale.regular_price)}",
            f"Cupom: {voucher}",
            f"Loja: {game_sale.store}",
            f"Sistemas: {os_list}",
            f"Plataformas: {platforms}",
        ]
    )

def _build_email_body(sales) -> str:
    if not sales:
        return "Nenhuma promocao foi encontrada no momento."

    sections = ["Promoções encontradas:", ""]

    for index, game_sale in enumerate(sales, start=1):
        sections.append(f"#{index}")
        sections.append(_format_game_sale(game_sale))
        sections.append("-" * 51)

    return "\n".join(sections).rstrip()

def main() -> None:
    games = get_games_list()
    providers = _get_providers(games)

    for provider in providers:
        sales = provider.get_sale_games()

        for sale in sales:
            print(f"Jogo: {sale.name}")
            print(f"Preço: {sale.price}")
            print(f"Link: {sale.link}")
            print(f"Loja: {sale.store}")

    # sales = get_sale_games_itad(games)
    # email_body = _build_email_body(sales)

    # success = send_email("Promoções encontradas!", email_body)

    # if not success:
    #     raise SystemExit("Falha ao enviar e-mail")

if __name__ == "__main__":
    main()
