DROP DATABASE IF EXISTS PY_VK_BOT;
CREATE DATABASE PY_VK_BOT;
CREATE USER pyvkbot with password 'pyvkbot';
ALTER DATABASE PY_VK_BOT OWNER TO pyvkbot;
GRANT ALL PRIVILEGES ON DATABASE py_vk_bot TO pyvkbot;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pyvkbot;
CREATE TABLE users (id int primary key,
                   name varchar(40) not Null,
                   city varchar(40),
                   sex int,
                   age int not Null,
				   profile text,
				   last_seen int,
                   update_time date not Null);
CREATE TABLE userFotos (userid int not Null,
                       link varchar(255) not Null);
CREATE TABLE pairs (userid int not Null references users(id),
                    pairid int not Null,
					position int not Null,
					saved boolean not Null,
					constraint pk primary key (userid, pairid));
					   
