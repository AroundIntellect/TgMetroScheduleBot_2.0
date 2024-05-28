from UsersDataBase import create_table, add_user, add_favorite_trip

YOUR_MAIN_BOT_TOKEN = "ваш_токен_основного_бота"
YOUR_FEEDBACK_BOT_TOKEN = "ваш_токен_бота_для_обратной_связи"

if __name__ == '__main__':
    create_table()
    add_user(1, "TOKENS", None, None, None)
    add_favorite_trip(1, YOUR_MAIN_BOT_TOKEN)
    add_favorite_trip(1, YOUR_FEEDBACK_BOT_TOKEN)
