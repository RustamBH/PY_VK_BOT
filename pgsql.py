from datetime import date


def get_age(bdate):
    bdate = bdate.split('.')
    if len(bdate) == 3:
        age = int(date.today().year) - int(bdate[2])
        return age
    else:
        return 0


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


def get_user(position, conn):
    query = f"""select u.name, u.profile, uf.link
                from userfotos uf
                left join users u on uf.userid = u.id  
                left join pairs p on u.id = p.pairid 
                where uf.userid  = (
                    select pairid
                    from pairs
                    where position = {position})"""
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    return result[0], result[1], result[2]


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


def save_user_photo(userid, link, conn):
    query = f"""insert into userfotos(userid, link)
                values ({userid}, '{link}')
                ON CONFLICT (userid) DO NOTHING"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()


def get_max_rec(userid, conn):
    query = f"select count(*) from pairs where userid = {userid}"
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    if result[0] is None:
        return 0
    else:
        return int(result[0])


def add_in_favorites(pairid, conn):
    query = f"""update pairs
                set saved = true
                where pairid = {pairid}"""
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()


def get_pair_id(position, conn):
    query = f"select pairid from pairs where position = {position}"
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    return result


def get_favorites(conn):
    query = f"""select u.name, u.profile
                from users u
                left join pairs p on
                    u.id = p.userid
                where
                    u.id in (select pairid
                    from pairs
                    where saved = true)"""
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    return result
