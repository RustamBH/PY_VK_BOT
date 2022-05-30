import psycopg
from datetime import date

pg_server = 'postgresql://pyvkbot:pyvkbot@10.168.88.113:5432/py_vk_bot'
conn = psycopg.connect(pg_server)

#{'id': 201642, 'bdate': '29.4', 'city': {'id': 2, 'title': 'Санкт-Петербург'}, 'country': {'id': 1, 'title': 'Россия'}, 'track_code': '90d07c571QicxIZ2JAlomJVEirMbVsBg7Lsq9Ih2Yd8fQ6kxqKKyYdjFjUUmCTufobdzRKMnrmrq00-Ghg', 'sex': 1, 'first_name': 'Алиса', 'last_name': 'Титова', 'can_access_closed': True, 'is_closed': False}


def get_age(bdate):
    bdate = bdate.split('.')
    if len(bdate) == 3:
        age = int(date.today().year) - int(bdate[2])
        return age
    else:
        return 0


def save_user(user_data, conn):
    id = user_data['id']
    name = f"{user_data['first_name']} {user_data['last_name']}"
    if 'city' in user_data:
        city = user_data['city']['id']
    else:
        return
    sex = user_data['sex']
    profile = f"https://vk.com/id{user_data['id']}"
    if 'bdate' in user_data:
        age = get_age(user_data['bdate'])
    else:
        age = 0
    update_time = date.today()
    query = f"""insert into users(id, name, city, sex, profile, age, last_seen, update_time) 
                values ({id}, '{name}', {city}, {sex}, '{profile}', {age}, 0, '{update_time}') 
                ON CONFLICT (id) DO NOTHING"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()


def save_last_seen(id, position, conn):
    query = f"""update users set last_seen = {position}
                where id = {id}"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()


def get_user(id, conn):
    query = f"select * from users where id = {id}"
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    return result


def get_pair_position_max(userid, conn):
    query = f"select max(position) from pairs where userid = {userid}"
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    if result[0] is None:
        return 0
    else:
        return int(result[0])


def save_pair(userid, pairid, conn):
    position = get_pair_position_max(userid, conn) + 1
    query = f"""insert into pairs(userid, pairid, position, saved)
                values ({userid}, {pairid}, {position}, False)
                ON CONFLICT (userid, pairid) DO NOTHING"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()