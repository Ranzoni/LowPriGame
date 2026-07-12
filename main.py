from email_sender import send_email
from json_reader import get_games_list
from isthereanydeal_api import get_sale_games


def main() -> None:
    # success = send_email(
    #     "Promoção encontrada!",
    #     "Wukong está por R$ 129,90 na PSN!",
    # )

    # if not success:
    #     raise SystemExit("Falha ao enviar e-mail")

    games = get_games_list()

    for game_sale in get_sale_games(games):
        print(f"Jogo: {game_sale.name}")
        print(f"Preço: {game_sale.price}")
        print(f"Preço comum: {game_sale.regular_price}")
        print(f"Cupom: {game_sale.voucher}")
        print(f"Loja: {game_sale.store}")
        print(f"Sistemas: {game_sale.os_list}")
        print(f"Plataformas: {game_sale.platforms}")
        print("---------------------------------------------------")


if __name__ == "__main__":
    main()
