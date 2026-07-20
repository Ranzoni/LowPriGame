from shared.models import GamePrice


def __format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"

def __format_percentual(value: float) -> str:
    formatted = f"{value:,.2f}"
    return f"{formatted}%"

def __game_group_key(game_sale: GamePrice) -> str:
    return game_sale.name.strip().lower()

def __platforms_text(game_sale: GamePrice) -> str:
    if not game_sale.platforms:
        return "-"

    platforms = sorted({platform.strip() for platform in game_sale.platforms if platform and platform.strip()})
    return ", ".join(platforms) if platforms else "-"

def __format_offer(index: int, game_sale: GamePrice) -> list[str]:
    voucher = game_sale.voucher or "-"
    link = game_sale.link or "-"

    return [
        f"  {index}. {game_sale.store}",
        f"     Plataformas: {__platforms_text(game_sale)}",
        f"     Preço: {__format_currency(game_sale.price)} | Preço comum: {__format_currency(game_sale.price_info.regular_price)}",
        f"     Desconto: {__format_currency(game_sale.price_info.discont)} ({__format_percentual(game_sale.price_info.discount_percentage)})",
        f"     Cupom: {voucher}",
        f"     Link: {link}",
    ]

def __dedupe_offers(game_sales: list[GamePrice]) -> list[GamePrice]:
    deduped: list[GamePrice] = []
    seen = set()

    for sale in game_sales:
        key = (
            sale.store,
            round(sale.price, 2),
            round(sale.price_info.regular_price, 2),
            round(sale.price_info.discont, 2),
            round(sale.price_info.discount_percentage, 2),
            sale.voucher or "",
            sale.link or "",
            tuple(sorted((sale.platforms or []))),
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(sale)

    return deduped

def __format_game_block(game_name: str, game_sales: list[GamePrice], index: int) -> str:
    offers = __dedupe_offers(game_sales)
    offers.sort(key=lambda sale: sale.price)

    best_price = offers[0].price
    lines = [
        f"#{index} {game_name}",
        f"Menor preço encontrado: {__format_currency(best_price)}",
        f"Total de ofertas: {len(offers)}",
        "",
        "Ofertas:",
    ]

    for offer_index, offer in enumerate(offers, start=1):
        lines.extend(__format_offer(offer_index, offer))
        if offer_index < len(offers):
            lines.append("")

    return "\n".join(lines)

def build_sales_email_body(sales: list[GamePrice]) -> str:
    if not sales:
        return "Nenhuma promoção foi encontrada no momento."

    grouped_sales: dict[str, list[GamePrice]] = {}
    game_names: dict[str, str] = {}

    for sale in sales:
        key = __game_group_key(sale)
        grouped_sales.setdefault(key, []).append(sale)
        game_names.setdefault(key, sale.name)

    sorted_keys = sorted(grouped_sales.keys(), key=lambda key: game_names[key].lower())
    total_offers = sum(len(__dedupe_offers(grouped_sales[key])) for key in sorted_keys)

    sections = [
        "PROMOÇÕES ENCONTRADAS",
        "=" * 65,
        f"Jogos com promoção: {len(sorted_keys)}",
        f"Ofertas únicas encontradas: {total_offers}",
        "",
    ]

    for index, key in enumerate(sorted_keys, start=1):
        sections.append(__format_game_block(game_names[key], grouped_sales[key], index))
        sections.append("")
        sections.append("-" * 65)
        sections.append("")

    return "\n".join(sections).rstrip()
