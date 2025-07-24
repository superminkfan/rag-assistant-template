# Конфигурация кеша

## Коды операций

После успешного подтверждения подключения к узлу сервера DataGrid клиент может выполнять операции по настройке кеша. Клиент отправляет запрос (подробнее о структуре запросов и ответов написано в разделах ниже) с конкретным кодом операции:

| Операция | Код операции |
|---|---|
| `OP_CACHE_GET_NAMES` | 1050 |
| `OP_CACHE_CREATE_WITH_NAME` | 1051 |
| `OP_CACHE_GET_OR_CREATE_WITH_NAME` | 1052 |
| `OP_CACHE_CREATE_WITH_CONFIGURATION` | 1053 |
| `OP_CACHE_GET_OR_CREATE_WITH_CONFIGURATION` | 1054 |
| `OP_CACHE_GET_CONFIGURATION` | 1055 |
| `OP_CACHE_DESTROY` | 1056 |
| `OP_QUERY_SCAN` | 2000 |
| `OP_QUERY_SCAN_CURSOR_GET_PAGE` | 2001 |
| `OP_QUERY_SQL` | 2002 |
| `OP_QUERY_SQL_CURSOR_GET_PAGE` | 2003 |
| `OP_QUERY_SQL_FIELDS` | 2004 |
| `OP_QUERY_SQL_FIELDS_CURSOR_GET_PAGE` | 2005 |
| `OP_BINARY_TYPE_NAME_GET` | 3000 |
| `OP_BINARY_TYPE_NAME_PUT` | 3001 |
| `OP_BINARY_TYPE_GET` | 3002 |
| `OP_BINARY_TYPE_PUT` | 3003 |

Указанные выше коды операций являются частью заголовка запроса — подробнее написано в подразделе «Стандартный заголовок сообщения» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md).

:::{admonition} Пользовательские методы, которые используются при реализации примеров фрагментов кода ниже
:class: note

В некоторых примерах кода ниже используются:

- метод `readDataObject()`, который описан в подразделе «Объекты данных» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md);
- методы, которые используют порядок байтов little-endian для чтения и записи значений, состоящих из нескольких байтов — они включены в раздел [«Формат данных»](data_format.md).
:::

## OP_CACHE_CREATE_WITH_NAME

Создает кеш с указанным именем. Можно применить шаблон кеша, если в его названии есть символ `*`. Если кеш с указанным именем уже существует, генерируется исключение.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `String` | Имя кеша |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
DataOutputStream out = new DataOutputStream(socket.getOutputStream());

String cacheName = "myNewCache";

int nameLength = cacheName.getBytes("UTF-8").length;

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5 + nameLength, OP_CACHE_CREATE_WITH_NAME, 1, out);  

// Имя кеша. 
writeString(cacheName, out);  

// Отправить запрос. 
out.flush();
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);
```
:::
::::

## OP_CACHE_GET_OR_CREATE_WITH_NAME

Создает кеш с указанным именем. Можно применить шаблон кеша, если в его названии есть символ `*`. Если кеш с указанным именем уже существует, никаких действий не выполняется.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `String` | Имя кеша |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
DataOutputStream out = new DataOutputStream(socket.getOutputStream());

String cacheName = "myNewCache";

int nameLength = cacheName.getBytes("UTF-8").length;

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5 + nameLength, OP_CACHE_GET_OR_CREATE_WITH_NAME, 1, out);  

// Имя кеша. 
writeString(cacheName, out);  

// Отправить запрос. 
out.flush();
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);
```
:::
::::

## OP_CACHE_GET_NAMES

Получает имена существующих кешей.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `int` | Количество кешей |
| `String` | Имя кеша. Повторяется столько раз, сколько кешей указано в предыдущем параметре |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5, OP_CACHE_GET_NAMES, 1, out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);  

// Количество кешей. 
int cacheCount = readIntLittleEndian(in);  

// Имена кешей.
for (int i = 0; i < cacheCount; i++) {
  int type = readByteLittleEndian(in); // Код типа.

  int strLen = readIntLittleEndian(in); // Длина.

  byte[] buf = new byte[strLen];

  readFully(in, buf, 0, strLen);

  String s = new String(buf); // Имя кеша.

  System.out.println(s);
}
```
:::
::::

## OP_CACHE_GET_CONFIGURATION

Получает конфигурацию для указанного кеша.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Флаг |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `int` | Длина конфигурации в байтах (все параметры конфигурации) |
| `CacheConfiguration` | Структура конфигурации кеша — подробнее написано в таблице ниже |

:::{list-table} Конфигурация кеша
:header-rows: 1
+   *   Тип поля
    *   Описание
+   *   `int`
    *   Количество резервных копий (backups)
+   *   `int`
    *   `CacheMode`:
        - `LOCAL = 0`;
        - `REPLICATED = 1`;
        - `PARTITIONED = 2`
+   *   `bool`
    *   `CopyOnRead`
+   *   `String`
    *   `DataRegionName`
+   *   `bool`
    *   `EagerTTL`
+   *   `bool`
    *   `StatisticsEnabled`
+   *   `String`
    *   `GroupName`
+   *   `bool`
    *   `Invalidate`
+   *   `long`
    *   `DefaultLockTimeout` (мс)
+   *   `String`
    *   Название
+   *   `bool`
    *   `IsOnheapCacheEnabled`
+   *   `int`
    *   `PartitionLossPolicy`:
        - `READ_ONLY_SAFE = 0`;
        - `READ_ONLY_ALL = 1`;
        - `READ_WRITE_SAFE = 2`;
        - `READ_WRITE_ALL = 3`;
        - `IGNORE = 4`
+   *   `int`
    *   `QueryDetailMetricsSize`
+   *   `int`
    *   `QueryParellelism`
+   *   `bool`
    *   `ReadFromBackup`
+   *   `int`
    *   `RebalanceBatchSize`
+   *   `long`
    *   `RebalanceBatchesPrefetchCount`
+   *   `long`
    *   `RebalanceDelay` (мс)
+   *   `int`
    *   `RebalanceMode`:
        - `SYNC = 0`;
        - `ASYNC = 1`;
        - `NONE = 2`
+   *   `int`
    *   `RebalanceOrder`
+   *   `long`
    *   `RebalanceThrottle` (мс)
+   *   `long`
    *   `RebalanceTimeout` (мс)
+   *   `bool`
    *   `SqlEscapeAll`
+   *   `int`
    *   `SqlIndexInlineMaxSize`
+   *   `String`
    *   `SqlSchema`
+   *   `int`
    *   `WriteSynchronizationMode`:
        - `FULL_SYNC = 0`;
        - `FULL_ASYNC = 1`;
        - `PRIMARY_SYNC = 2`
+   *   `int`
    *   Количество полей `CacheKeyConfiguration`
+   *   `CacheKeyConfiguration`
    *   Структура `CacheKeyConfiguration`:
        - `String` — название типа;
        - `String` — название поля affinity-ключа.

        Повторяется столько раз, сколько полей указано в предыдущем параметре
+   *   `int`
    *   Количество свойств `QueryEntity`
+   *   `QueryEntity * count`
    *   Структура `QueryEntity` — подробнее в таблице ниже
:::

:::{list-table} `QueryEntity`
:header-rows: 1
 
+   *   Тип поля
    *   Описание
+   *   `String`
    *   Название типа ключа
+   *   `String`
    *   Название типа значения
+   *   `String`
    *   Название таблицы
+   *   `String`
    *   Название поля ключа
+   *   `String`
    *   Название поля значения
+   *   `int`
    *   Количество полей `QueryField`
+   *   `QueryField * count`
    *   Структура `QueryField`:
        - `String` — название;
        - `String` — название типа;
        - `bool` — поле ключа;
        - `bool` — поле ограничения `notNull`.

        Повторяется столько раз, сколько полей указано в предыдущем параметре
+   *   `int`
    *   Количество псевдонимов
+   *   `(String + String) * count`
    *   Псевдонимы названий полей
+   *   `int`
    *   Количество индексов `QueryIndex`
+   *   `QueryIndex * count`
    *   Структура `QueryIndex`:
        - `String` — названия индекса;
        - `byte` — тип индекса:
          - `SORTED = 0`;
          - `FULLTEXT = 1`;
          - `GEOSPATIAL = 2`.
        - `int` — свойство `inline-size`;
        - `int` — количество полей;
        - `(string + bool) * count` — поля (названия + `IsDescending`)
:::

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
String cacheName = "myCache";

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5, OP_CACHE_GET_CONFIGURATION, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);

// Длина конфигурации.
int configLen = readIntLittleEndian(in);

// `CacheAtomicityMode`.
int cacheAtomicityMode = readIntLittleEndian(in);

// Резервные копии.
int backups = readIntLittleEndian(in);

// `CacheMode`.
int cacheMode = readIntLittleEndian(in);

// `CopyOnRead`.
boolean copyOnRead = readBooleanLittleEndian(in);

// Другие конфигурации.
```
:::
::::

## OP_CACHE_CREATE_WITH_CONFIGURATION

Создает кеш с предоставленной конфигурацией. Если кеш с указанным именем уже существует, генерируется исключение.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Длина конфигурации в байтах (все параметры конфигурации) |
| `short` | Количество параметров конфигурации |
| `short` + `property type` | Данные о свойствах конфигурации.<br><br>Количество повторений соответствует общему количеству параметров конфигурации |

Можно указать любое количество параметров конфигурации. Поле `Name` обязательное. Данные конфигурации кеша задаются в форме «ключ-значение», где ключ — идентификатор свойства типа `short`, а значение — данные, которые относятся к конкретному свойству.

:::{list-table} Все доступные параметры конфигурации
:header-rows: 1
 
+   *   Код свойства
    *   Тип свойства
    *   Описание 
+   *   2
    *   `int`
    *   `CacheAtomicityMode`:
        - `TRANSACTIONAL = 0`;
        - `ATOMIC = 1`
+   *   3 
    *   `int`
    *   Резервные копии (backups)
+   *   1
    *   `int`
    *   `CacheMode`:
        - `LOCAL = 0`;
        - `REPLICATED = 1`;
        - `PARTITIONED = 2`
+   *   5
    *   `boolean`
    *   `CopyOnRead`
+   *   100
    *   `String`
    *   `DataRegionName`
+   *   405
    *   `boolean`
    *   `EagerTtl`
+   *   406
    *   `boolean`
    *   `StatisticsEnabled`
+   *   400
    *   `String`
    *   `GroupName`
+   *   402
    *   `long`
    *   `DefaultLockTimeout` (мс)
+   *   403
    *   `int`
    *   `MaxConcurrentAsyncOperations`
+   *   206
    *   `int`
    *   `MaxQueryIterators`
+   *   0
    *   `String`
    *   Название
+   *   101
    *   `bool`
    *   `IsOnheapcacheEnabled`
+   *   404
    *   `int`
    *   `PartitionLossPolicy`:
        - `READ_ONLY_SAFE = 0`;
        - `READ_ONLY_ALL = 1`;
        - `READ_WRITE_SAFE = 2`;
        - `READ_WRITE_ALL = 3`;
        - `IGNORE = 4`
+   *   202
    *   `int`
    *   `QueryDetailMetricsSize`
+   *   201
    *   `int`
    *   `QueryParallelism`
+   *   6
    *   `bool`
    *   `ReadFromBackup`
+   *   303
    *   `int`
    *   `RebalanceBatchSize`
+   *   304
    *   `long`
    *   `RebalanceBatchesPrefetchCount`
+   *   301
    *   `long`
    *   `RebalanceDelay` (мс)
+   *   300
    *   `int`
    *   `RebalanceMode`:
        - `SYNC = 0`;
        - `ASYNC = 1`;
        - `NONE = 2`
+   *   305
    *   `int`
    *   `RebalanceOrder`
+   *   306
    *   `long`
    *   `RebalanceThrottle` (мс)
+   *   302
    *   `long`
    *   `RebalanceTimeout` (мс)
+   *   205
    *   `bool`
    *   `SqlEscapeAll`
+   *   204
    *   `int`
    *   `SqlIndexInlineMaxSize`
+   *   203
    *   `String`
    *   `SqlSchema`
+   *   4
    *   `int`
    *   `WriteSynchronizationMode`:
        - `FULL_SYNC = 0`;
        - `FULL_ASYNC = 1`;
        - `PRIMARY_SYNC = 2`
+   *   401
    *   `int` + `CacheKeyConfiguration * count`
    *   Количество свойств `CacheKeyConfiguration` + `CacheKeyConfiguration`. Структура `CacheKeyConfiguration`:
        - `String` название типа;
        - `String` — название поля affinity-ключа
+   *   200
    *   `int` + `QueryEntity * count`
    *   Количество свойств `QueryEntity` + `QueryEntity`.
    
        Структура `QueryEntity` описана в таблице ниже
:::

:::{list-table} `QueryEntity`
:header-rows: 1
 
+   *   Тип поля
    *   Описание
+   *   `String`
    *   Название типа ключа
+   *   `String`
    *   Название типа значения
+   *   `String`
    *   Название таблицы
+   *   `String`
    *   Название поля ключа
+   *   `String`
    *   Название поля значения
+   *   `int`
    *   Количество `QueryField`
+   *   `QueryField`
    *   Структура `QueryField`:
        - `String` — название;
        - `String` — название типа;
        - `bool` — поле ключа;
        - `bool` — поле ограничения `notNull`.

        Повторяется столько раз, сколько полей указано в предыдущем параметре
+   *   `int`
    *   Количество псевдонимов
+   *   `String` + `String`
    *   Псевдонимы названий полей. 
    
        Повторяется столько раз, сколько псевдонимов указано в предыдущем параметре
+   *   `int`
    *   Количество `QueryIndex`
+   *   `QueryIndex`
    *   Структура `QueryIndex`:
        - `String` — названия индекса;
        - `byte` — тип индекса:
          - `SORTED = 0`;
          - `FULLTEXT = 1`;
         - `GEOSPATIAL = 2`.
        - `int` — свойство `inline-size`;
        - `int` — количество полей;
        - `string + bool` — поля (названия + `IsDescending`).

        Повторяется столько раз, сколько индексов указано в предыдущем параметре
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(30, OP_CACHE_CREATE_WITH_CONFIGURATION, 1, out);

// Длина конфигурации в байтах.
writeIntLittleEndian(16, out);

// Количество свойств.
writeShortLittleEndian(2, out);

// Код операции резервной копии.
writeShortLittleEndian(3, out);

// Количество резервных копий: 2.
writeIntLittleEndian(2, out);

// Название кода операции.
writeShortLittleEndian(0, out);

// Название.
writeString("myNewCache", out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_GET_OR_CREATE_WITH_CONFIGURATION

Создает кеш с предоставленной конфигурацией. Если кеш с указанным именем уже существует, никаких действий не выполняется.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `CacheConfiguration` | Конфигурация кеша — подробнее о формате написано в таблицах выше |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
DataOutputStream out = new DataOutputStream(socket.getOutputStream());

writeRequestHeader(30, OP_CACHE_GET_OR_CREATE_WITH_CONFIGURATION, 1, out);

// Длина конфигурации в байтах.
writeIntLittleEndian(16, out);

// Количество свойств.
writeShortLittleEndian(2, out);

// Код операции резервной копии.
writeShortLittleEndian(3, out);

// Количество резервных копий: 2.
writeIntLittleEndian(2, out);

// Название кода операции.
writeShortLittleEndian(0, out);

// Название.
writeString("myNewCache", out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_DESTROY

Уничтожает кеш с указанным именем.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
String cacheName = "myCache";

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(4, OP_CACHE_DESTROY, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Отправить запрос. 
out.flush();
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);
```
:::
::::