import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import psycopg
from pgsql import save_user, get_user, get_year, save_pair, save_user_photo, get_max_rec, add_in_favorites, get_pair_id, \
    get_favorites

pg_server = '10.168.88.113' #'localhost'
pg_port = '5432'
bot_db = 'py_vk_bot'

conn_string = f'postgresql://pyvkbot:pyvkbot@{pg_server}:{pg_port}/{bot_db}'
conn = psycopg.connect(conn_string)


def get_tokens(file_name):
    with open(file_name, 'r') as f:
        tokens = json.load(f)
    return tokens


def send_some_msg(id, some_text):
    gvk_session.method("messages.send", {"user_id": id, "message": some_text, "random_id": 0})


def send_photos(id, some_text, link):
    gvk_session.method("messages.send",
                       {"user_id": id, "message": some_text, "attachment": f'{link}',
                        "random_id": 0})


def show_kbd(id, some_text='Вот клавиатура'):
    gvk_session.method("messages.send",
                       {"user_id": id, "message": some_text, "keyboard": keyboard.get_keyboard(), "random_id": 0})


def get_user_bio(id):
    user_data = gvk_session.method("users.get", {"user_ids": id, "fields": "sex, bdate, city, country"})
    return user_data


def search_users(sex, city, offset, limit=50, b_year=1997):
    if sex == 1:
        sex = 2
    else:
        sex = 1
    result = vk_session.method("users.search",
                               {"sort": 0, "offset": offset, "city": city["id"], "hometown": city["title"], "sex": sex,
                                "birth_year": b_year,
                                "count": limit,
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


def pars_sesult(result):
    return result[0], result[1], result[2]


tokens = get_tokens('tokens')
vk_session = vk_api.VkApi(token=tokens['app'])
gvk_session = vk_api.VkApi(token=tokens['group'])
gsession_api = gvk_session.get_api()
glongpool = VkLongPoll(gvk_session)

keyboard = VkKeyboard(one_time=False)
keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('Предыдущий', color=VkKeyboardColor.NEGATIVE)
keyboard.add_button('Следующий', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Список избранных', color=VkKeyboardColor.SECONDARY)

max_records = 0
position = 0
limit = 5
n_search = 0

for event in glongpool.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            msg = event.text.lower()
            id = event.user_id
            udata = get_user_bio(id)[0]
            save_user(udata, conn)
            if msg == 'hi':
                show_kbd(id, "Нажмите 'Поиск' для поиска знакомств")
            elif msg == 'поиск':
                b_year = get_year(udata['bdate'])
                if b_year == 0:
                    result = search_users(udata['sex'], udata['city'], limit * n_search, limit)
                else:
                    result = search_users(udata['sex'], udata['city'], limit * n_search, limit, b_year)
                for user in result["items"]:
                    if not user["is_closed"]:
                        save_user(user, conn)
                        save_pair(id, user['id'], conn)
                        max_records = get_max_rec(id, conn)
                        search_top_photos(user["id"], conn)
                n_search += 1
                text = f"Для просмотра нажмите 'Следующий' или Предыдущий'"
                send_some_msg(id, text)
            elif msg == 'следующий':
                if max_records == 0:
                    max_records = get_max_rec(id, conn)
                position += 1
                if position > max_records:
                    position = max_records
                    text = f"Для продолжения нажмите 'Поиск'!"
                    send_some_msg(id, text)
                result = get_user(position, conn)
                if result is None:
                    text = f"Для начала нажмите 'Поиск'!"
                    send_some_msg(id, text)
                else:
                    name, profile, link = pars_sesult(result)
                    send_some_msg(id, name)
                    send_some_msg(id, profile)
                    send_photos(id, "3 фото", link=link)
            elif msg == 'предыдущий':
                if max_records == 0:
                    max_records = get_max_rec(id, conn)
                position -= 1
                if position <= 0:
                    position = 1
                result = get_user(position, conn)
                if result is None:
                    text = f"Для начала нажмите 'Поиск'!"
                    send_some_msg(id, text)
                else:
                    name, profile, link = pars_sesult(result)
                    send_some_msg(id, name)
                    send_some_msg(id, profile)
                    send_photos(id, "3 фото", link=link)
            elif msg == 'stop':
                exit()
            elif msg == 'в избранное':
                pairid = get_pair_id(position, conn)
                add_in_favorites(pairid[0], conn)
                send_some_msg(id, "Добавлено в избранное")
            elif msg == 'список избранных':
                favor_list = get_favorites(conn)
                for user in favor_list:
                    text = f"{user[0]}, {user[1]}"
                    send_some_msg(id, text)
            else:
                show_kbd(id)
