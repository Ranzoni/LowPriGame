from shared.models import GamePrice


def __format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"

def __format_percentual(value: float) -> str:
    formatted = f"{value:,.2f}"
    return f"{formatted}%"

def __format_game_sale(game_sale: GamePrice) -> str:
    platforms = ", ".join(game_sale.platforms) if game_sale.platforms else "-"
    voucher = game_sale.voucher or "-"

    return "\n".join(
        [
            f"Jogo: {game_sale.name}",
            f"Preço: {__format_currency(game_sale.price)}",
            f"Preço comum: {__format_currency(game_sale.price_info.regular_price)}",
            f"Desconto: {__format_currency(game_sale.price_info.discont)}",
            f"Desconto (%): {__format_percentual(game_sale.price_info.discount_percentage)}",
            f"Cupom: {voucher}",
            f"Loja: {game_sale.store}",
            f"Link: {game_sale.link}",
            f"Plataformas: {platforms}",
        ]
    )

def build_sales_email_body(sales: list[GamePrice]) -> str:
    if not sales:
        return "Nenhuma promoção foi encontrada no momento."

    sections = ["Promoções encontradas:", ""]

    for index, game_sale in enumerate(sales, start=1):
        sections.append(f"#{index}")
        sections.append(__format_game_sale(game_sale))
        sections.append("-" * 51)

    return "\n".join(sections).rstrip()
