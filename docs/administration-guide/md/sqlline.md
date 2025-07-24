# Утилиты SQLLine (sqlline.sh, ise-sqlline.sh)

DataGrid поставляется с SQLLine — консольной утилитой для подключения к реляционным базам данных и выполнения SQL-запросов. Утилита `ise-sqlline.sh` нужна для работы с кластером, в котором настроен плагин безопасности. В остальных случаях используйте `sqlline.sh`.

## Подключение к кластеру

:::{admonition} Внимание
:class: danger

Если кластер настроен на работу с плагином безопасности, используйте утилиту `ise-sqlline.sh`.

Чтобы подключиться к кластеру с плагином безопасности, используйте команду:

```bash
sh $IGNITE_HOME/bin/ise-sqlline.sh -u "<dbc:ignite:thin://<hostname>/?sslMode=require
&sslClientCertificateKeyStoreUrl=<путь к хранилищу ключей (keystore)>
&sslTrustCertificateKeyStoreUrl=<путь к доверенному хранилищу (truststore)>"
-n <имя пользователя>
```

Если не указать обязательные параметры ключей `-u` и `-n`, система запросит их через консоль.

Пример запуска:

```bash
sh $IGNITE_HOME/bin/ise-sqlline.sh -u "jdbc:ignite:thin://xxx.x.x.x/?sslMode=require
&sslClientCertificateKeyStoreUrl=src/main/resources/validUser.jks
&sslTrustCertificateKeyStoreUrl=src/main/resources/truststore.jks"
-n validUser
```
:::

**Подключиться к узлу:**

```bash
./sqlline.sh --verbose=true -u jdbc:ignite:thin://<hostname>/
```

Если ключ `--verbose` принимает значение `true`, при возникновении ошибки выведется вся трассиовка стека Java и информация об отладке.

После подключения к кластеру можно выполнять SQL-запросы и команды SQLLine.

**Получить справку по SQLLine:**

```bash
./sqlline.sh -h
./sqlline.sh --help
```

## Команды SQLLine

**Описание команд:**

| Команда | Описание |
|---|---|
| !all | Выполнить указанный SQL-запрос для всех текущих соединений |
| !batch | Выполнить набор SQL-запросов |
| !brief | Включить режим краткого вывода |
| !closeall | Закрыть все текущие открытые соединения |
| !columns | Вывести все столбцы всех таблиц |
| !connect | Подключиться к базе данных |
| !dbinfo | Вывести информацию о текущем соединении |
| !dropall | Удалить все таблицы в базе данных |
| !go | Перейти на другое активное соединение |
| !help | Вывести справочную информацию |
| !history | Вывести историю команд |
| !indexes | Отобразить все индексы всех таблиц |
| !list | Отобразить все активные соединения |
| !manual | Показать руководство по SQLLine |
| !nickname | Создать понятное имя для подключения (обновляет командную строку) |
| !outputformat | Изменить метод отображения результатов SQL-запросов |
| !primarykeys | Отобразить столбцы первичного ключа таблицы |
| !properties | Подключиться к базе данных, которая определена в конфигурационном файле |
| !quit | Выйти из SQLLine |
| !reconnect | Переподключиться к текущей базе данных |
| !record | Начать записывать весь вывод SQL-запросов |
| !run | Выполнить набор команд из файла |
| !script | Сохранить выполненные команды в файл |
| !sql | Выполнить SQL-запрос |
| !tables | Вывести список всех таблиц |
| !verbose | Включить режим подробного вывода |

## Примеры

**Создать таблицы:**

```bash
0: jdbc:ignite:thin://xxx.x.x.x/> CREATE TABLE City (id LONG PRIMARY KEY, name VARCHAR) WITH "template=replicated";
No rows affected (0.301 seconds)
 
0: jdbc:ignite:thin://xxx.x.x.x/> CREATE TABLE Person (id LONG, name VARCHAR, city_id LONG, PRIMARY KEY (id, city_id))WITH "backups=1, affinityKey=city_id";
No rows affected (0.078 seconds)
 
0: jdbc:ignite:thin://xxx.x.x.x/> !tables
+-----------+--------------+--------------+-------------+-------------+
| TABLE_CAT | TABLE_SCHEM  |  TABLE_NAME  | TABLE_TYPE  | REMARKS     |
+-----------+--------------+--------------+-------------+-------------+
|           | PUBLIC       | CITY         | TABLE       |             |
|           | PUBLIC       | PERSON       | TABLE       |             |
+-----------+--------------+--------------+-------------+-------------+
```

**Создать индексы:**

```bash
0: jdbc:ignite:thin://xxx.x.x.x/> CREATE INDEX idx_city_name ON City (name);
No rows affected (0.039 seconds)
 
0: jdbc:ignite:thin://xxx.x.x.x/> CREATE INDEX idx_person_name ON Person (name);
No rows affected (0.013 seconds)
 
0: jdbc:ignite:thin://xxx.x.x.x/> !indexes
+-----------+--------------+--------------+-------------+-----------------+
| TABLE_CAT | TABLE_SCHEM  |  TABLE_NAME  | NON_UNIQUE  | INDEX_QUALIFIER |
+-----------+--------------+--------------+-------------+-----------------+
|           | PUBLIC       | CITY         | true        |                 |
|           | PUBLIC       | PERSON       | true        |                 |
+-----------+--------------+--------------+-------------+-----------------+
```