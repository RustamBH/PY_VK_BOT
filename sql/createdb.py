import psycopg

pg_server = 'localhost'
pg_port = '5432'
bot_db = 'py_vk_bot'


def drop_bot_db(conn, bot_db):
    query = f"""DROP DATABASE IF EXISTS {bot_db}"""
    conn.execute(query)


def create_bot_db(conn, bot_db):
    query = f"""CREATE DATABASE {bot_db}"""
    conn.execute(query)


def create_bot_db_user(conn):
    query = f"""DROP USER IF EXISTS pyvkbot"""
    conn.execute(query)
    query = f"""CREATE USER pyvkbot with password 'pyvkbot'"""
    conn.execute(query)
    query = f"""GRANT ALL PRIVILEGES ON DATABASE py_vk_bot TO pyvkbot"""
    conn.execute(query)
    query = f"""GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pyvkbot"""
    conn.execute(query)


def alt_bot_db(conn):
    query = f"""ALTER DATABASE PY_VK_BOT OWNER TO pyvkbot"""
    conn.execute(query)


def create_bot_tables(con):
    query = f"""CREATE TABLE users (id int primary key,
                   name varchar(40) not Null,
                   city varchar(40),
                   sex int,
				   profile text,
				   last_seen int DEFAULT 0,
				   n_search int DEFAULT 0,
                   update_time date not Null)"""
    conn.execute(query)
    query = f"""CREATE TABLE userFotos (userid int not Null,
                       link varchar(255) not Null)"""
    conn.execute(query)
    query = f"""CREATE TABLE pairs (userid int not Null references users(id),
                    pairid int not Null,
					position int not Null,
					saved boolean not Null,
					constraint pk primary key (userid, pairid))"""
    conn.execute(query)
    conn.commit()


if __name__ == '__main__':
    print(f'Данная программа создает базу данных для бота на сервере {pg_server}:{pg_port}.\n'
          'Если на сервер уже есть база "PY_VK_BOT", то она будет УДАЛЕНА! \n'
          'Адрес и порт сервера можно поменять в программе.\n'
          'Для этого нам потребуются имя и пароль пользователя с правами администратора. \n'
          'Пользователь и пароль нигде не будут сохранены и не будту никуда отправлены\n')
    adm_user = input("Введите имя пользователя с правами админинистратора: ")
    adm_pass = input("Введите пароль пользователя с правами админинистратора: ")

    conn_string = f'postgresql://{adm_user}:{adm_pass}@{pg_server}:{pg_port}/postgres'
    conn = psycopg.connect(conn_string, autocommit=True)
    drop_bot_db(conn, bot_db)
    create_bot_db(conn, bot_db)
    create_bot_db_user(conn)
    alt_bot_db(conn)
    conn.close()
    conn_string = f'postgresql://pyvkbot:pyvkbot@{pg_server}:{pg_port}/{bot_db}'
    conn = psycopg.connect(conn_string)
    create_bot_tables(conn)
    conn.close()
    print('База создана')
