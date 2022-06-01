import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from datetime import date
import psycopg
from pgsql import save_user, get_pair, get_year, save_pair, save_user_photo, get_pair_position_max, add_in_favorites, get_pair_id, \
    get_favorites, get_n_search, save_n_search, get_last_seen, save_last_seen

pg_server = 'localhost'
pg_port = '5432'
bot_db = 'py_vk_bot'

conn_string = f'postgresql://pyvkbot:pyvkbot@{pg_server}:{pg_port}/{bot_db}'
conn = psycopg.connect(conn_string)


def get_tokens(file_name):
    with open(file_name, 'r') as f:
        tokens = json.load(f)
    return tokens


def send_some_msg(id, some_text):
    group_vk_session.method("messages.send", {"user_id": id, "message": some_text, "random_id": 0})


def send_photos(id, link):
    group_vk_session.method("messages.send",
                       {"user_id": id, "message": 'Фотографии', "attachment": f'{link}',
                        "random_id": 0})


def show_kbd(id, some_text='Вот клавиатура'):
    group_vk_session.method("messages.send",
                       {"user_id": id, "message": some_text, "keyboard": keyboard.get_keyboard(), "random_id": 0})


def get_user_bio(id):
    user_data = group_vk_session.method("users.get", {"user_ids": id, "fields": "sex, bdate, city, country"})
    return user_data


def search_users(sex, city, offset, search_limit, b_year):
    if b_year == 0:
        b_year = int(date.today().year) - 20
    if sex == 1:
        sex = 2
    else:
        sex = 1
    result = vk_session.method("users.search",
                               {"sort": 0, "offset": offset, "city": city["id"], "hometown": city["title"], "sex": sex,
                                "birth_year": b_year,
                                "count": search_limit,
                                "fields": "sex, bdate, city, country"})
    return result


def get_photos(pair_id, res_photos):
    likes_dict = {}
    for item in res_photos["items"]:
        likes_dict[f"{item['id']}"] = item["likes"]["count"]

    sorted_likes_dict = {k: likes_dict[k] for k in sorted(likes_dict, key=likes_dict.get, reverse=True)}
    top3_photo_list = []
    for n, id_photo in enumerate(sorted_likes_dict.keys()):
        if n >= 3:
            break
        top3_photo_list.append(id_photo)

    link_photos = ""
    if len(top3_photo_list) == 1:
        link_photos = f"photo{pair_id}_{top3_photo_list[0]}"
    elif len(top3_photo_list) == 2:
        link_photos = f"photo{pair_id}_{top3_photo_list[0]},photo{pair_id}_{top3_photo_list[1]}"
    elif len(top3_photo_list) == 3:
        link_photos = f"photo{pair_id}_{top3_photo_list[0]},photo{pair_id}_{top3_photo_list[1]},photo{pair_id}_{top3_photo_list[2]}"

    return link_photos


def search_top_photos(pair_id, conn):
    res_photos = vk_session.method("photos.get",
                                   {"owner_id": pair_id, "album_id": "profile", "extended": 1, "count": 100})
    link_3_photo = get_photos(pair_id, res_photos)
    save_user_photo(user['id'], link_3_photo, conn)


def pars_result(result):
    return result[0], result[1], result[2]


def show_user(result, id):
    name, profile, link = pars_result(result)
    send_some_msg(id, name)
    send_some_msg(id, profile)
    send_photos(id, link=link)


tokens = get_tokens('tokens')
vk_session = vk_api.VkApi(token=tokens['app'])
group_vk_session = vk_api.VkApi(token=tokens['group'])
group_session_api = group_vk_session.get_api()
group_longpool = VkLongPoll(group_vk_session)

keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('Предыдущий', color=VkKeyboardColor.NEGATIVE)
keyboard.add_button('Следующий', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Список избранных', color=VkKeyboardColor.SECONDARY)

position = 0
limit = 5

for event in group_longpool.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg = event.text.lower()
            id = event.user_id
            udata = get_user_bio(id)[0]
            save_user(udata, conn)
            n_search = get_n_search(id, conn)
            if msg == 'hi':
                show_kbd(id, "Нажмите 'Поиск' для поиска знакомств")
            elif msg == 'поиск':
                b_year = get_year(udata['bdate'])
                result = search_users(udata['sex'], udata['city'], limit * n_search, limit, b_year)
                for user in result["items"]:
                    if not user["is_closed"]:
                        if save_user(user, conn):
                            save_pair(id, user['id'], conn)
                            search_top_photos(user["id"], conn)
                save_n_search(id, n_search + 1, conn)
                text = f"Для просмотра нажмите 'Следующий' или Предыдущий'"
                send_some_msg(id, text)
            elif msg == 'следующий':
                max_records = get_pair_position_max(id, conn)
                position = get_last_seen(id, conn) + 1
                if position > max_records:
                    position = max_records
                    text = f"Для продолжения нажмите 'Поиск'!"
                    send_some_msg(id, text)
                result = get_pair(id, position, conn)
                if result is not None:
                    show_user(result, id)
                    save_last_seen(id, position, conn)
            elif msg == 'предыдущий':
                max_records = get_pair_position_max(id, conn)
                position = get_last_seen(id, conn) - 1
                if position <= 0:
                    position = 1
                result = get_pair(id, position, conn)
                if result is None:
                    text = f"Для начала нажмите 'Поиск'!"
                    send_some_msg(id, text)
                else:
                    show_user(result, id)
                    save_last_seen(id, position, conn)
            elif msg == 'в избранное':
                pairid = get_pair_id(id, position, conn)
                if pairid is not None:
                    add_in_favorites(id, pairid[0], conn)
                    send_some_msg(id, "Добавлено в избранное")
            elif msg == 'список избранных':
                favor_list = get_favorites(id, conn)
                for user in favor_list:
                    text = f"{user[0]}, {user[1]}"
                    send_some_msg(id, text)
            else:
                show_kbd(id)
