# SQL-запросы и Scan Queries

## Коды операций

После успешного подтверждения подключения к узлу сервера DataGrid клиент может выполнять различные SQL-запросы и запросы сканирования. Клиент отправляет запрос (подробнее о структуре запросов и ответов написано в разделах ниже) с конкретным кодом операции:

| Операция | Код операции |
|---|---|
| `OP_QUERY_SQL` | 2002 |
| `OP_QUERY_SQL_CURSOR_GET_PAGE` | 2003 |
| `OP_QUERY_SQL_FIELDS` | 2004 |
| `OP_QUERY_SQL_FIELDS_CURSOR_GET_PAGE` | 2005 |
| `OP_QUERY_SCAN` | 2000 |
| `OP_QUERY_SCAN_CURSOR_GET_PAGE` | 2001 |
| `OP_RESOURCE_CLOSE` | 0 |

Указанные выше коды операций являются частью заголовка запроса — подробнее написано в подразделе «Стандартный заголовок сообщения» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md).

:::{admonition} Пользовательские методы, которые используются при реализации примеров фрагментов кода ниже
:class: hint

В некоторых примерах кода ниже используются:

- метод `readDataObject()`, который описан в подразделе «Объекты данных» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md);
- методы, которые используют порядок байтов little-endian для чтения и записи значений, состоящих из нескольких байтов — они включены в раздел [«Формат данных»](data_format.md).
:::

## OP_QUERY_SQL

Выполняет SQL-запрос к данным, которые хранятся в кластере. Запрос возвращает запись целиком (ключ и значение).

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша;  хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `String` | Название типа или SQL-таблицы |
| `String` | Строка SQL-запроса |
| `int` | Количество аргументов запроса |
| `Data Object` | Аргумент запроса. Повторяется столько раз, сколько аргументов указано в предыдущем параметре |
| `bool` | Распределенные присоединения |
| `bool` | Локальный запрос |
| `bool` | Только реплицированный: содержит ли запрос только реплицированные таблицы или нет |
| `int` | Размер страницы курсора |
| `long` | Тайм-аут в миллисекундах. Значение тайм-аута должно быть неотрицательным. Нулевое значение отключает тайм-аут |

Ответ включает первую страницу результатов:

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Идентификатор курсора. Можно закрыть с помощью `OP_RESOURSE_CLOSE` |
| `int` | Количество строк на первой странице |
| `Key Data Object` + `Value Data Object` | Записи в формате пар «ключ-значение». Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SQL_CURSOR_GET_PAGE`. Если принимает значение `true`, курсор запроса автоматически закрывается |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
String entityName = "Person";
int entityNameLength = getStrLen(entityName); // Байты в кодировке UTF-8.

String sql = "Select * from Person";
int sqlLength = getStrLen(sql);

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(34 + entityNameLength + sqlLength, OP_QUERY_SQL, 1, out);  

// Идентификатор кеша. 
String queryCacheName = "personCache";
writeIntLittleEndian(queryCacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Query Entity. 
writeString(entityName, out);  

// SQL-запрос. 
writeString(sql, out);  

// Количество аргументов. 
writeIntLittleEndian(0, out);  

// Присоединения. 
out.writeBoolean(false);  

// Локальный запрос. 
out.writeBoolean(false);  

// Реплицированный. 
out.writeBoolean(false);  

// Размер страницы курсора. 
writeIntLittleEndian(1, out);  

// Тайм-аут. 
writeLongLittleEndian(5000, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результат. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

long cursorId = readLongLittleEndian(in);

int rowCount = readIntLittleEndian(in);  

// Прочитать записи как пользовательские объекты. 
for (int i = 0; i < rowCount; i++) {
  Object key = readDataObject(in);
  Object val = readDataObject(in);

  System.out.println("CacheEntry: " + key + ", " + val);
}

boolean moreResults = readBooleanLittleEndian(in);
```
:::
::::

## OP_QUERY_SQL_CURSOR_GET_PAGE

Извлекает следующую страницу курсора SQL-запроса по идентификатору курсора из `OP_QUERY_SQL`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `long` | Идентификатор курсора |

Формат ответа выглядит так:

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Идентификатор курсора |
| `int` | Количество строк |
| `Key Data Object` + `Value Data Object` | Записи в формате пар «ключ-значение». Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SQL_CURSOR_GET_PAGE`. Если принимает значение `true`, курсор запроса автоматически закрывается |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(8, OP_QUERY_SQL_CURSOR_GET_PAGE, 1, out);  

// Идентификатор курсора (получен из операции SQL-запроса). 
writeLongLittleEndian(cursorId, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результат. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

int rowCount = readIntLittleEndian(in);  

// Прочитать записи как пользовательские объекты. 
for (int i = 0; i < rowCount; i++){
  Object key = readDataObject(in);
  Object val = readDataObject(in);

  System.out.println("CacheEntry: " + key + ", " + val);
}

boolean moreResults = readBooleanLittleEndian(in);
```
:::
::::

## OP_QUERY_SQL_FIELDS

Выполняет SQL-запрос по полям.

:::{list-table}
:header-rows: 1
 
+   *   Тип поля запроса
    *   Описание
+   *   `Header`
    *   Заголовок запроса
+   *   `int`
    *   Идентификатор кеша; хеш-код имени кеша в Java-стиле
+   *   `byte`
    *   Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах
+   *   `String`
    *   Схема для запроса; может принимать значение `NULL` — в этом случае используется схема `PUBLIC` по умолчанию
+   *   `int`
    *   Размер страницы курсора запроса
+   *   `int`
    *   Максимальное количество строк
+   *   `String`
    *   SQL-запрос
+   *   `int`
    *   Количество аргументов
+   *   `Data Object`
    *   Аргумент запроса. Повторяется столько раз, сколько аргументов указано в предыдущем параметре
+   *   `byte`
    *   Тип запроса:
        - `ANY = 0`;
        - `SELECT = 1`;
        - `UPDATE = 2`
+   *   `bool`
    *   Распределенные присоединения
+   *   `bool`
    *   Локальный запрос
+   *   `bool`
    *   Только реплицированный: содержит ли запрос только реплицированные таблицы или нет
+   *   `bool`
    *   Обеспечивает соблюдение порядка присоединения
+   *   `bool`
    *   Коллоцированный: коллоцированы данные или нет
+   *   `bool`
    *   Ленивое (lazy) выполнение запроса
+   *   `long`
    *   Тайм-аут в миллисекундах
+   *   `bool`
    *   Включает названия полей
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Идентификатор курсора. Можно закрыть с помощью `OP_RESOURSE_CLOSE` |
| `int` | Количество полей (столбцов) |
| `String` (необязательный тип) | Требуется, только если в запросе для параметра `IncludeFieldNames` указано значение `true`.<br><br>Название столбца.<br><br>Повторяется столько раз, сколько полей указано в предыдущем параметре |
| `int` | Количество строк на первой странице. Значение столбца (поля) объекта данных. Повторяется столько раз, сколько полей указано.<br><br>Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SQL_FIELDS_CURSOR_GET_PAGE` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
String sql = "Select id, salary from Person";
int sqlLength = sql.getBytes("UTF-8").length;

String sqlSchema = "PUBLIC";
int sqlSchemaLength = sqlSchema.getBytes("UTF-8").length;

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(43 + sqlLength + sqlSchemaLength, OP_QUERY_SQL_FIELDS, 1, out);  

// Идентификатор кеша. 
String queryCacheName = "personCache";
int cacheId = queryCacheName.hashCode();
writeIntLittleEndian(cacheId, out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Схема. 
writeByteLittleEndian(9, out);
writeIntLittleEndian(sqlSchemaLength, out);
out.writeBytes(sqlSchema); //`sqlSchemaLength`.  

// Размер страницы курсора. 
writeIntLittleEndian(2, out);  

// Максимальное количество строк. 
writeIntLittleEndian(5, out);  

// SQL-запрос. 
writeByteLittleEndian(9, out);
writeIntLittleEndian(sqlLength, out);
out.writeBytes(sql);//`sqlLength`.  

// Количество аргументов. 
writeIntLittleEndian(0, out);  

// Тип запроса. 
writeByteLittleEndian(1, out);  

// Присоединения. 
out.writeBoolean(false);  

// Локальный запрос. 
out.writeBoolean(false);  

// Реплицированный. 
out.writeBoolean(false);  

// Обеспечивает соблюдение порядка присоединения. 
out.writeBoolean(false);  

// Коллоцированный. 
out.writeBoolean(false);  

// Ленивое (lazy) выполнение запроса. 
out.writeBoolean(false);  

// Тайм-аут. 
writeLongLittleEndian(5000, out);  

// Реплицированный. 
out.writeBoolean(false);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результат. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

long cursorId = readLongLittleEndian(in);

int colCount = readIntLittleEndian(in);

int rowCount = readIntLittleEndian(in);  

// Прочитать записи. 
for (int i = 0; i < rowCount; i++) {
  long id = (long) readDataObject(in);
  int salary = (int) readDataObject(in);

  System.out.println("Person id: " + id + "; Person Salary: " + salary);
}

boolean moreResults = readBooleanLittleEndian(in);
```
:::
::::

## OP_QUERY_SQL_FIELDS_CURSOR_GET_PAGE

Извлекает следующую страницу результатов запроса по идентификатору курсора из `OP_QUERY_SQL_FIELDS`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `long` | Идентификатор курсора, который получен из `OP_QUERY_SQL_FIELDS` |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `int` | Количество строк |
| `Data Object` | Значение столбца (поля). Повторяется столько раз, сколько полей указано.<br><br>Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SQL_FIELDS_CURSOR_GET_PAGE` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(8, QUERY_SQL_FIELDS_CURSOR_GET_PAGE, 1, out);  

// Идентификатор курсора. 
writeLongLittleEndian(1, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

int rowCount = readIntLittleEndian(in);  

// Прочитать записи как пользовательские объекты. 
for (int i = 0; i < rowCount; i++){
   // Прочитать произведение объектов и столбцов.
}

boolean moreResults = readBooleanLittleEndian(in);
```
:::
::::

## OP_QUERY_SCAN

Выполняет scan queries (запросы сканирования).

:::{list-table}
:header-rows: 1
 
+   *   Тип поля запроса
    *   Описание
+   *   `Header`
    *   Заголовок запроса
+   *   `int`
    *   Идентификатор кеша; хеш-код имени кеша в Java-стиле
+   *   `byte`
    *   Флаг. Передайте `0` по умолчанию или `1`, чтобы оставить значение в бинарном виде
+   *   `Data Object`
    *   Объект фильтра. Если не нужно фильтровать данные в кластере, установите значение `NULL`. Добавьте класс фильтра в classpath серверных узлов
+   *   `byte`
    *   Платформа фильтра (передавайте этот параметр, только если значение объекта фильтра не `NULL`):
        - `JAVA = 1`;
        - `DOTNET = 2`;
        - `CPP = 3`
+   *   `int`
    *   Размер страницы курсора
+   *   `int`
    *   Количество запрашиваемых партиций (если значение отрицательное, выполнится запрос всего кеша)
+   *   `bool`
    *   Локальный флаг: должен ли этот запрос выполняться только на локальном узле
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Идентификатор курсора |
| `int` | Количество строк |
| `Key Data Object` + `Value Data Object` | Записи в формате пар «ключ-значение».<br><br>Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SCAN_CURSOR_GET_PAGE`. Если принимает значение `true`, курсор запроса автоматически закрывается |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_QUERY_SCAN, 1, out);  

// Идентификатор кеша. 
String queryCacheName = "personCache";
writeIntLittleEndian(queryCacheName.hashCode(), out);

// Флаги.
writeByteLittleEndian(0, out);

// Объект фильтра.
writeByteLittleEndian(101, out); // `NULL`.  

// Размер страницы курсора. 
writeIntLittleEndian(1, out);

// Количество запрашиваемых партиций.
writeIntLittleEndian(-1, out);

// Локальный флаг.
out.writeBoolean(false);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результат. 
DataInputStream in = new DataInputStream(socket.getInputStream());

// Заголовок ответа.
readResponseHeader(in);  

// Идентификатор курсора. 
long cursorId = readLongLittleEndian(in);

int rowCount = readIntLittleEndian(in);  

// Прочитать записи как пользовательские объекты. 
for (int i = 0; i < rowCount; i++) {
  Object key = readDataObject(in);
  Object val = readDataObject(in);

  System.out.println("CacheEntry: " + key + ", " + val);
}

boolean moreResults = readBooleanLittleEndian(in);
```
:::
::::

## OP_QUERY_SCAN_CURSOR_GET_PAGE

Получает следующую страницу курсора SQL-запроса по идентификатору курсора, который получен из `OP_QUERY_SCAN`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `long` | Идентификатор курсора |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Идентификатор курсора |
| `long` | Количество строк |
| `Key Data Object` + `Value Data Object` | Записи в формате пар «ключ-значение». Повторяется столько раз, сколько строк указано в предыдущем параметре |
| `bool` | Указывает, доступны ли дополнительные результаты для извлечения с помощью `OP_QUERY_SCAN_CURSOR_GET_PAGE`. Если принимает значение `true`, курсор запроса автоматически закрывается |

## OP_RESOURCE_CLOSE

Закрывает ресурс, например курсор запроса.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `long` | Идентификатор ресурса |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(8, OP_RESOURCE_CLOSE, 1, out);

// Идентификатор ресурса.
long cursorId = 1;
writeLongLittleEndian(cursorId, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результат. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::