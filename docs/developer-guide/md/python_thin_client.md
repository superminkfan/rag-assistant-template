# Тонкий клиент Python

## Требования

Python версии 3.7 или новее.

## Установка

Тонкий клиент Python можно установить с помощью менеджера пакетов `pip` или собрать самостоятельно из репозитория с исходным кодом.

### Менеджер пакетов (PIP)

Пакет тонкого клиента Python называется `pyignite`. Для установки используйте команду:

```bash
pip install pyignite
```

### Установка из исходников

Тонкий клиент можно установить из репозитория, который доступен для скачивания в [GitHub Apache Ignite](https://github.com/apache/ignite-python-thin-client):

```bash
git clone git@github.com:apache/ignite-python-thin-client.git
pip install -e .
```

Это позволит установить `pyignite` в так называемом режиме `develop` или `editable`. Подробнее о режиме написано в [официальной документации PIP](https://pip.pypa.io/en/stable/cli/pip_install/).

Проверьте каталог `requirements` и при необходимости установите дополнительные требования с помощью команды:

```bash
pip install -r requirements/<your task>.txt
```

Подробнее об использовании `setup.py` написано в [документации Setuptools](https://setuptools.pypa.io/en/latest/).

## Подключение к кластеру

В ZIP-архиве дистрибутива есть доступные для запуска примеры, которые показывают основные сценарии использования тонкого клиента Python. Примеры находятся в каталоге `{client_dir}/examples`.

::::{admonition} Пример, как подключиться к кластеру из тонкого клиента Python
:class: hint

:::{code-block} python
:caption: Python
from pyignite import Client

\#\# Откройте соединение.
client = Client()
client.connect('xxx.x.x.x', 10800)
:::
::::

## Отказоустойчивость клиента

Можно настроить клиент автоматически подключаться к другому узлу при сбое соединения с текущим или истечении тайм-аута.

При сбое соединения клиент пробрасывает исходное исключение (`OSError` или `SocketError`), но сохраняет параметры своего конструктора неизменными и пытается явно восстановить соединение. Если клиенту не удается восстановить соединение, он генерирует специальное исключение `ReconnectError`.

В примере ниже клиенту предоставили адреса трех узлов кластера.

::::{admonition} Пример
:class: hint 
:collapsible:

:::{code-block} python
:caption: Python
from pyignite import Client
from pyignite.datatypes.cache_config import CacheMode
from pyignite.datatypes.prop_codes import *
from pyignite.exceptions import SocketError

nodes = [
    ('xxx.x.x.x', 10800),
    ('xxx.xx.x.x', 10800),
    ('xxx.xx.xx.x', 10800),
]

client = Client(timeout=40.0)
client.connect(nodes)
print('Connected to {}'.format(client))

my_cache = client.get_or_create_cache({
    PROP_NAME: 'my_cache',
    PROP_CACHE_MODE: CacheMode.REPLICATED,
})
my_cache.put('test_key', 0)

\# Абстрактный основной цикл.
while True:
    try:
        # Выполните работу.
        test_value = my_cache.get('test_key')
        my_cache.put('test_key', test_value + 1)
    except (OSError, SocketError) as e:
        # Восстановите работу после ошибки (в зависимости от задачи: повторите
        # последнюю команду, проверьте согласованность данных или продолжите работу).
        print('Error: {}'.format(e))
        print('Last value: {}'.format(my_cache.get('test_key')))
        print('Reconnected to {}'.format(client))
:::
::::

## Partition Awareness

Функция Partition Awareness позволяет тонкому клиенту отправлять запросы напрямую узлу, который содержит нужные данные. Без этой функции приложение, которое подключено к кластеру с помощью тонкого клиента, выполняет все запросы и операции на одном серверном узле (он служит прокси-сервером для входящих запросов). Затем эти операции перенаправляются на узел, где хранятся нужные данные. Это приводит к возникновению узкого места, которое может помешать линейному масштабированию приложения.

Запросы должны проходить через прокси-сервер, откуда они перенаправляются на корректный узел:

![Partition-awareness-off](./resources/partition-awareness-off.png)

С функцией Partition Awareness тонкий клиент может напрямую отправлять запросы основным узлам, где хранятся нужные данные. Функция устраняет узкое место и позволяет приложению проще масштабироваться:

![Partition-awareness-on](./resources/partition-awareness-on.png)

Чтобы включить Partition Awareness, передайте параметр `partition_aware` в значении `True` в конструктор класса `Client` и укажите адреса всех серверных узлов в строке подключения.

:::{code-block} python
:caption: Python
client = Client(partition_aware=True)
nodes = [
    ('xxx.x.x.x', 10800),
    ('xxx.xx.x.x', 10800),
    ('xxx.xx.xx.x', 10800),
]

client.connect(nodes)
:::

## Создание кеша

Чтобы получить экземпляр кеша, используйте один из методов:

- `get_cache(settings)` — создает объект локального кеша с указанным именем или набором параметров. Кеш должен существовать в кластере, в противном случае при попытке выполнить операцию над ним сгенерируется исключение.
- `create_cache(settings)` — создает кеш с указанным именем или набором параметров.
- `get_or_create_cache(settings)` — возвращает существующий кеш или создает, если его еще нет.

Каждый метод принимает имя кеша или словарь свойств, который представляет конфигурацию кеша.

:::{code-block} python
:caption: Python
from pyignite import Client

\# Откройте соединение.
client = Client()
client.connect('xxx.x.x.x', 10800)

\# Создайте кеш.
my_cache = client.create_cache('myCache')
:::

::::{admonition} Пример создания кеша с набором свойств
:class: hint 
:collapsible:

:::{code-block} python
:caption: Python
from collections import OrderedDict

from pyignite import Client, GenericObjectMeta
from pyignite.datatypes import *
from pyignite.datatypes.prop_codes import *

\# Откройте соединение.
client = Client()
client.connect('xxx.x.x.x', 10800)

cache_config = {
    PROP_NAME: 'my_cache',
    PROP_BACKUPS_NUMBER: 2,
    PROP_CACHE_KEY_CONFIGURATION: [
        {
            'type_name': 'PersonKey',
            'affinity_key_field_name': 'companyId'
        }
    ]
}

my_cache = client.create_cache(cache_config)

class PersonKey(metaclass=GenericObjectMeta, type_name='PersonKey', schema=OrderedDict([
    ('personId', IntObject),
    ('companyId', IntObject),
])):
    pass

personKey = PersonKey(personId=1, companyId=1)
my_cache.put(personKey, 'test')

print(my_cache.get(personKey))
:::
::::

Список поддерживаемых свойств кеша есть в следующем разделе.

### Конфигурация кеша

:::{list-table} Поддерживаемые свойства кеша
:header-rows: 1
 
+   *   Название свойства 
    *   Тип
    *   Описание
+   *   `PROP_NAME`
    *   `str`
    *   Имя кеша — единственное обязательное свойство
+   *   `PROP_CACHE_MODE`
    *   `int`
    *   Режим кеша:
        - `REPLICATED=1`;
        - `PARTITIONED=2`.
        
        Подробнее о режиме кеша написано в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных»
+   *   `PROP_CACHE_ATOMICITY_MODE`
    *   `int`
     *   Режим атомарности кеша:
         - `TRANSACTIONAL=0`;
         - `ATOMIC=1`.
         
         Подробнее о режиме атомарности кеша написано в подразделе [«Режимы атомарности»](atomicity_modes.md) раздела «Настройка кешей»
+   *   `PROP_BACKUPS_NUMBER`
    *   `int`
    *   Количество резервных (backup) копий партиций — подробнее об этом написано в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных»
+   *   `PROP_WRITE_SYNCHRONIZATION_MODE`
    *   `int`
    *   Режим синхронизации записи:
        - `FULL_SYNC=0`;
        - `FULL_ASYNC=1`;
        - `PRIMARY_SYNC=2`
+   *   `PROP_COPY_ON_READ`
    *   `bool`
    *   Флаг для копирования/отключения копирования данных при чтении. Значение по умолчанию — `True`
+   *   `PROP_READ_FROM_BACKUP`
    *   `bool`
    *   Флаг указывает, будут ли записи считываться из локальных резервных партиций, когда они доступны, или всегда запрашиваться из основных партиций. Значение по умолчанию — `True`
+   *   `PROP_DATA_REGION_NAME`
    *   `str`
    *   Название региона данных — подробнее об этом написано в подразделе [«Конфигурация регионов данных»](configuration_of_data_regions.md) раздела «Настройка памяти»
+   *   `PROP_IS_ONHEAP_CACHE_ENABLED`
    *   `bool`
    *   Флаг для включения/выключения on-heap-кеширования — подробнее об этом написано в подразделе [«Кеширование в heap-памяти (On-Heap)»](on-heap-caching.md) раздела «Настройка кешей»
+   *   `PROP_QUERY_ENTITIES`
    *   `list`
    *   Список сущностей запроса — подробнее написано ниже в разделе [«Сущности запроса (Query Entities)»](#сущности-запроса-query-entities)
+   *   `PROP_QUERY_PARALLELISM`
    *   `int`
    *   Количество потоков на одном узле для выполнения запроса
+   *   `PROP_QUERY_DETAIL_METRIC_SIZE`
    *   `int`
    *   Размер метрик в запросах
+   *   `PROP_SQL_SCHEMA`
    *   `str`
    *   Название схемы SQL-запроса
+   *   `PROP_SQL_INDEX_INLINE_MAX_SIZE`
    *   `int`
    *   Максимальный размер индексов в пределах кеша
+   *   `PROP_SQL_ESCAPE_ALL`
    *   `bool`
    *   Флаг для экранирования/деэкранирования двойными кавычками всех названий и полей в SQL-таблицах
+   *   `PROP_MAX_QUERY_ITERATORS`
    *   `int`
    *   Максимальное количество сохраняемых итераторов запроса
+   *   `PROP_REBALANCE_MODE`
    *   `int`
    *   Режим ребалансировки:
        - `SYNC=0`;
        - `ASYNC=1`;
        - `NONE=2`
+   *   `PROP_REBALANCE_DELAY`
    *   `int`
    *   Отсрочка ребалансировки (мс)
+   *   `PROP_REBALANCE_TIMEOUT`
    *   `int`
    *   Тайм-аут ребалансировки (мс)
+   *   `PROP_REBALANCE_BATCH_SIZE`
    *   `int`
    *   Размер batch ребалансировки
+   *   `PROP_REBALANCE_BATCHES_PREFETCH_COUNT`
    *   `int`
    *   Количество batches, которые создал питающий узел в начале процесса ребалансировки
+   *   `PROP_REBALANCE_ORDER`
    *   `int`
    *   Порядок ребалансировки
+   *   `PROP_REBALANCE_THROTTLE`
    *   `int`
    *   Интервал времени между сообщениями о ребалансировке (мс)
+   *   `PROP_GROUP_NAME`
    *   `str`
    *   Название группы
+   *   `PROP_CACHE_KEY_CONFIGURATION`
    *   `list`
    *   Конфигурация ключа кеша — подробнее написано ниже в разделе [«Ключ кеша»](#ключ-кеша)
+   *   `PROP_DEFAULT_LOCK_TIMEOUT`
    *   `int`
    *   Тайм-аут блокировки по умолчанию (мс)
+   *   `PROP_MAX_CONCURRENT_ASYNC_OPERATIONS`
    *   `int`
    *   Максимальное количество одновременных асинхронных операций
+   *   `PROP_PARTITION_LOSS_POLICY`
    *   `int`
    *   Политика потери партиций:
        - `READ_ONLY_SAFE=0`;
        - `READ_ONLY_ALL=1`;
        - `READ_WRITE_SAFE=2`;
        - `READ_WRITE_ALL=3`;
        - `IGNORE=4`.
        
        Подробнее о политике написано в подразделе [«Политика потери партиций (Partition Loss Policy)»](partition_loss_policy.md) раздела «Настройка кешей»
+   *   `PROP_EAGER_TTL`
    *   `bool`
    *   Подробнее о свойстве Eager TTL написано в подразделе [«Политика устаревания записей (Expiry Policy)»](expiry_policy.md) раздела «Настройка кешей»
+   *   `PROP_STATISTICS_ENABLED`
    *   `bool`
    *   Флаг, который включает статистику по кешам
:::

Список ключей свойств, которые можно указать, есть в модуле `prop_codes`.

#### Сущности запроса (Query Entities)

Сущности запроса — объекты, которые описывают [запрашиваемые поля](#поля-запроса) (поля объектов кеша, к которым можно обращаться с помощью SQL-запросов):

- `table_name` — название SQL-таблицы;
- `key_field_name` — название поля ключа;
- `key_type_name` — название типа ключа (типа данных Java или сложного объекта);
- `value_field_name` — название поля значения;
- `value_type_name` — название типа значения;
- `field_name_aliases` — список псевдонимов полей SQL-таблицы (подробнее написано ниже в разделе [«Псевдонимы названий полей»](#псевдонимы-названий-полей));
- `query_fields` — список названий полей запроса (подробнее написано ниже в разделе [«Поля запроса»](#поля-запроса));
- `query_indexes` — список индексов запросов (подробнее написано ниже в разделе [«Индексы запроса»](#индексы-запроса)).

##### Псевдонимы названий полей

Псевдонимы (aliases) названий полей используются, чтобы присвоить удобные названия полным именам свойства (`object.name → objectName`):

- `field_name` — название поля;
- `alias` — псевдоним (тип `str`).

##### Поля запроса

Поля запроса определяют, какие поля можно запрашивать:

- `name` — название поля.
- `type_name` — название типа данных Java или сложного объекта.
- `is_key_field` (необязательное) — настройка ключа и значения во время операции SQL DML, если на узлах кластера отсутствуют классы «ключ–значение» (значение `boolean`, по умолчанию `False`).
- `is_notnull_constraint_field` — названия ненулевых полей в SQL-таблице (значение `boolean`).
- `default_value` (необязательное) — все, что может быть преобразовано в тип `type_name`. Значение по умолчанию — `None (Null)`.
- `precision` (необязательное) — десятичная точность: общее количество цифр в десятичном значении. По умолчанию — `-1` (используется значение кластера по умолчанию). Не применяется для типов данных SQL, которые не являются десятичными, кроме `java.math.BigDecimal`.
- `scale` (необязательное) — десятичная точность: количество цифр после запятой. По умолчанию — `-1` (используется значение кластера по умолчанию). Не применяется для типов данных SQL, которые не являются десятичными.

##### Индексы запроса

Индексы запросов определяют поля, которые будут индексироваться:

- `index_name` — название индекса;
- `index_type` — код типа индекса (целое число в беззнаковом диапазоне байтов)
- `inline_size` — размер индекса кешей (целое число);
- `fields` — список индексируемых полей (подробнее написано ниже в разделе [«Поля»](#поля)).

##### Поля

Список индексируемых полей:

- `name` — название поля;
- `is_descending` (необязательное) — сортировка полей в порядке убывания (значение `boolean`, по умолчанию `False`).

##### Ключ кеша

Настройка ключа кеша:

- `type_name` — название сложного объекта;
- `affinity_key_field_name` — название поля affinity-ключа.

## Использование Key-Value API

Класс `pyignite.cache.Cache` предоставляет методы для работы с записями кеша при помощи Key-Value-операций (`put`, `get`, `putAll`, `getAll`, `replace` и других).

:::{code-block} python
:caption: Python
from pyignite import Client

client = Client()
client.connect('xxx.x.x.x', 10800)

\# Создайте кеш.
my_cache = client.create_cache('my cache')

\# Поместите значение в кеш.
my_cache.put('my key', 42)

\# Получите значение из кеша.
result = my_cache.get('my key')
print(result)  # 42

result = my_cache.get('non-existent key')
print(result)  # None

\# Получите несколько значений из кеша.
result = my_cache.get_all([
    'my key',
    'non-existent key',
    'other-key',
])
print(result)  # {'my key': 42}
:::

### Использование подсказок типов данных (type hints)

У методов `pyignite`, которые обрабатывают одно значение или ключ, есть дополнительный необязательный параметр, который принимает класс парсера или конструктора — `value_hint` или `key_hint`. Практически все структурные элементы типов `dict` или `list` можно заменить на 2-tuple — упорядоченную пару `(the element, type hint)`.

:::{code-block} python
:caption: Python
from pyignite import Client
from pyignite.datatypes import CharObject, ShortObject

client = Client()
client.connect('xxx.x.x.x', 10800)

my_cache = client.get_or_create_cache('my cache')

my_cache.put('my key', 42)
\# Значение ‘42’ занимает 9 байт памяти в качестве `LongObject`.

my_cache.put('my key', 42, value_hint=ShortObject)
\# Значение ‘42’ занимает только 3 байта в качестве `ShortObject`.

my_cache.put('a', 1)
\# `a` — ключ типа `String`.

my_cache.put('a', 2, key_hint=CharObject)
\# Создан еще один ключ ‘a’ типа `CharObject`.

value = my_cache.get('a')
print(value)  # 1

value = my_cache.get('a', key_hint=CharObject)
print(value)  # 2

\# Удаляются сразу оба ключа.
my_cache.remove_keys([
    'a',  # Ключ стандартного типа.
    ('a', CharObject),  # Ключ типа `CharObject`.
])
:::

## Scan Queries

Метод `scan()` можно использовать для получения всех объектов из кеша. Он возвращает генератор, который выдает упорядоченную пару `(key,value)`. 

::::{admonition} Пример, как перебирать сгенерированные пары
:class: hint 
:collapsible:

:::{code-block} python
:caption: Python
from pyignite import Client

client = Client()
client.connect('xxx.x.x.x', 10800)

my_cache = client.create_cache('myCache')

my_cache.put_all({'key_{}'.format(v): v for v in range(20)})
# {
#     'key_0': 0,
#     'key_1': 1,
#     'key_2': 2,
#     ... 20 elements in total...
#     'key_18': 18,
#     'key_19': 19
# }

result = my_cache.scan()

for k, v in result:
    print(k, v)
# 'key_17' 17
# 'key_10' 10
# 'key_6' 6,
# ... 20 elements in total...
# 'key_16' 16
# 'key_12' 12

result = my_cache.scan()
print(dict(result))
# {
#     'key_17': 17,
#     'key_10': 10,
#     'key_6': 6,
#     ... 20 elements in total...
#     'key_16': 16,
#     'key_12': 12
# }
:::

Также можно сразу преобразовать генератор в словарь:

:::{code-block} python
:caption: Python
result = my_cache.scan()
print(dict(result))
# {
#     'key_17': 17,
#     'key_10': 10,
#     'key_6': 6,
#     ... 20 elements in total...
#     'key_16': 16,
#     'key_12': 12
# }
:::
::::

:::{admonition} Внимание
:class: danger

Если кеш содержит большой набор данных, словарь может занять слишком много памяти.
:::

## Выполнение SQL-запросов

Тонкий клиент Python поддерживает все команды SQL, которые поддерживает DataGrid. Подробнее о командах SQL написано в подразделе «Справочник по SQL» раздела [«Работа с SQL и Apache Calcite»](working_with_sql_and_apache_calcite.md).

Метод `sql()` возвращает генератор, который выдает получившиеся строки.

:::{code-block} python
:caption: Python
from pyignite import Client

client = Client()
client.connect('xxx.x.x.x', 10800)

CITY_CREATE_TABLE_QUERY = '''CREATE TABLE City (
    ID INT(11),
    Name CHAR(35),
    CountryCode CHAR(3),
    District CHAR(20),
    Population INT(11),
    PRIMARY KEY (ID, CountryCode)
) WITH "affinityKey=CountryCode"'''

client.sql(CITY_CREATE_TABLE_QUERY)

CITY_CREATE_INDEX = '''CREATE INDEX idx_country_code ON city (CountryCode)'''

client.sql(CITY_CREATE_INDEX)

CITY_INSERT_QUERY = '''INSERT INTO City(
    ID, Name, CountryCode, District, Population
) VALUES (?, ?, ?, ?, ?)'''

CITY_DATA = [
    [3793, 'New York', 'USA', 'New York', 8008278],
    [3794, 'Los Angeles', 'USA', 'California', 3694820],
    [3795, 'Chicago', 'USA', 'Illinois', 2896016],
    [3796, 'Houston', 'USA', 'Texas', 1953631],
    [3797, 'Philadelphia', 'USA', 'Pennsylvania', 1517550],
    [3798, 'Phoenix', 'USA', 'Arizona', 1321045],
    [3799, 'San Diego', 'USA', 'California', 1223400],
    [3800, 'Dallas', 'USA', 'Texas', 1188580],
]

for row in CITY_DATA:
    client.sql(CITY_INSERT_QUERY, query_args=row)

CITY_SELECT_QUERY = "SELECT * FROM City"

cities = client.sql(CITY_SELECT_QUERY)
for city in cities:
    print(*city)
:::

Если для аргумента `include_field_names` установить значение `True`, метод `sql()` сгенерирует список названий столбцов в первом выводе. Чтобы получить доступ к названиям полей, используйте функцию Python `next`.

:::{code-block} python
:caption: Python
field_names = client.sql(CITY_SELECT_QUERY, include_field_names=True).__next__()
print(field_names)
:::

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу данных между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

::::{admonition} Пример конфигурации для включения SSL в тонком клиенте
:class: hint

:::{code-block} python
:caption: Python
from pyignite import Client
import ssl

client = Client(
                use_ssl=True,
                ssl_cert_reqs=ssl.CERT_REQUIRED,
                ssl_keyfile='/path/to/key/file',
                ssl_certfile='/path/to/client/cert',
                ssl_ca_certfile='/path/to/trusted/cert/or/chain',
)

client.connect('localhost', 10800)
:::
::::

:::{list-table} Поддерживаемые параметры
:header-rows: 1
 
+   *   Параметр
    *   Описание
+   *   `use_ssl`
    *   Чтобы включить протокол TLS версии 1.2 и выше на клиенте, установите значение `True`
+   *   `ssl_keyfile`
    *   Путь к файлу с SSL-ключом
+   *   `ssl_certfile`
    *   Путь к файлу с SSL-сертификатом
+   *   `ssl_ca_certfile`
    *   Путь к файлу с доверенными сертификатами
+   *   `ssl_cert_reqs`
    *   Параметры удаленного сертификата:
        - `ssl.CERT_NONE` — игнорировать удаленный сертификат (по умолчанию);
        - `ssl.CERT_OPTIONAL` — если удаленный сертификат предоставлен, он будет проверен;
        - `ssl.CERT_REQUIRED` — требуется действительный удаленный сертификат
+   *   `ssl_version`
    *   —
+   *   `ssl_ciphers`
    *   —
:::

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента.

:::{code-block} python
:caption: Python
from pyignite import Client
import ssl

client = Client(
                ssl_cert_reqs=ssl.CERT_REQUIRED,
                ssl_keyfile='/path/to/key/file',
                ssl_certfile='/path/to/client/cert',
                ssl_ca_certfile='/path/to/trusted/cert/or/chain',
                username='*****',
                password='*****',)

client.connect('localhost', 10800)
:::

::::{admonition} Внимание
:class: danger

При вводе учетных данных автоматически включается протокол SSL, так как не рекомендуется отправлять учетные данные по небезопасному каналу. Чтобы использовать аутентификацию без защиты соединения, отключите SSL при создании клиентского объекта:

:::{code-block} python
:caption: Python
client = Client(username='ignite', password='ignite', use_ssl=False)
:::
::::