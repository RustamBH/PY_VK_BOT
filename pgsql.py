from datetime import date

def get_year(bdate):
    bdate = bdate.split('.')
    if len(bdate) == 3:
        b_year = int(bdate[2])
        return b_year
    else:
        return 0


def save_user(user_data, conn):
    id = user_data['id']
    name = f"{user_data['first_name']} {user_data['last_name']}"
    if 'city' in user_data:
        city = user_data['city']['id']
    else:
        return False
    sex = user_data['sex']
    profile = f"https://vk.com/id{user_data['id']}"
    update_time = date.today()
    query = f"""insert into users(id, name, city, sex, profile, last_seen, update_time) 
                values ({id}, '{name}', {city}, {sex}, '{profile}', 0, '{update_time}') 
                ON CONFLICT (id) DO NOTHING"""
    conn.execute(query)
    conn.commit()
    return True


def save_last_seen(id, position, conn):
    query = f"""update users set last_seen = {position}
                where id = {id}"""
    conn.execute(query)
    conn.commit()


def get_last_seen(id, conn):
    query = f"""select last_seen from users where id = {id}"""
    cur = conn.execute(query)
    result = cur.fetchone()
    if result[0] is None:
        return 0
    else:
        return int(result[0])


def save_n_search(id, n_search, conn):
    query = f"""update users set n_search = {n_search}
                where id = {id}"""
    conn.execute(query)
    conn.commit()


def get_n_search(id, conn):
    query = f"""select n_search from users where id = {id}"""
    cur = conn.execute(query)
    result = cur.fetchone()
    if result[0] is None:
        return 0
    else:
        return int(result[0])


def get_pair(id, position, conn):
    query = f"""select u.name, u.profile, uf.link
                from users u 
                left join userfotos uf on uf.userid = u.id
                join pairs p on u.id = p.pairid and p.userid = {id} and p.position = {position}"""
    cur = conn.execute(query)
    result = cur.fetchone()
    return result


def get_pair_position_max(userid, conn):
    query = f"select max(position) from pairs where userid = {userid}"
    cur = conn.execute(query)
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
    conn.execute(query)
    conn.commit()


def save_user_photo(userid, link, conn):
    query = f"""delete from userfotos where userid = {userid}"""
    conn.execute(query)
    query = f"""insert into userfotos(userid, link)
                values ({userid}, '{link}')"""
    conn.execute(query)
    conn.commit()


def add_in_favorites(id, pairid, conn):
    query = f"""update pairs
                set saved = true
                where pairid = {pairid} and userid = {id}"""
    conn.execute(query)
    conn.commit()


def get_pair_id(id, position, conn):
    query = f"select pairid from pairs where position = {position} and userid = {id}"
    cur = conn.execute(query)
    result = cur.fetchone()
    return result


def get_favorites(id, conn):
    query = f"""select u.name, u.profile
                from users u
                join pairs p on
                    u.id = p.pairid
                    and p.userid = {id}
                    and p.saved = true"""
    cur = conn.execute(query)
    result = cur.fetchall()
    return result
