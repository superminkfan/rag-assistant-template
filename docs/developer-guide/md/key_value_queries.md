# Запросы типа «ключ-значение»

В разделе описываются операции с данными типа «ключ-значение», которые можно выполнять с кешем. Они аналогичны собственным операциям с кешем DataGrid. У каждой операции есть заголовок и дополнительные данные. Подробнее о заголовках написано в подразделе «Стандартный заголовок сообщения» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md).

Доступные типы и подробные описания форматов данных находятся в разделе [«Формат данных»](data_format.md).

## Коды операций

После получения подтверждения подключения к узлу сервера клиент может начать выполнять различные операции с данными типа «ключ-значение». Клиент отправляет запрос (подробнее о структуре запросов и ответов написано в разделах ниже) с конкретным кодом операции:

| Операция | Код операции |
|---|---|
| `OP_CACHE_GET` | 1000 |
| `OP_CACHE_PUT` | 1001 |
| `OP_CACHE_PUT_IF_ABSENT` | 1002 |
| `OP_CACHE_GET_ALL` | 1003 |
| `OP_CACHE_PUT_ALL` | 1004 |
| `OP_CACHE_GET_AND_PUT` | 1005 |
| `OP_CACHE_GET_AND_REPLACE` | 1006 |
| `OP_CACHE_GET_AND_REMOVE` | 1007 |
| `OP_CACHE_GET_AND_PUT_IF_ABSENT` | 1008 |
| `OP_CACHE_REPLACE` | 1009 |
| `OP_CACHE_REPLACE_IF_EQUALS` | 1010 |
| `OP_CACHE_CONTAINS_KEY` | 1011 |
| `OP_CACHE_CONTAINS_KEYS` | 1012 |
| `OP_CACHE_CLEAR` | 1013 |
| `OP_CACHE_CLEAR_KEY` | 1014 |
| `OP_CACHE_CLEAR_KEYS` | 1015 |
| `OP_CACHE_REMOVE_KEY` | 1016 |
| `OP_CACHE_REMOVE_IF_EQUALS` | 1017 |
| `OP_CACHE_REMOVE_KEYS` | 1018 |
| `OP_CACHE_REMOVE_ALL` | 1019 |
| `OP_CACHE_GET_SIZE` | 1020 |

Указанные выше коды операций являются частью заголовка запроса — подробнее написано в подразделе «Стандартный заголовок сообщения» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md).

:::{admonition} Пользовательские методы, которые используются при реализации примеров фрагментов кода ниже
:class: hint

В некоторых примерах кода ниже используются:

- метод `readDataObject()`, который описан в подразделе «Объекты данных» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md);
- методы, которые используют порядок байтов little-endian для чтения и записи значений, состоящих из нескольких байтов — они включены в раздел [«Формат данных»](data_format.md).
:::

## OP_CACHE_GET

Извлекает значения из кеша по ключу. Если в кеше нет ключа, возвращается `NULL`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша;  хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ записи кеша, которую нужно вернуть |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `Data Object` | Значение, которое соответствует данному ключу. Если в кеше нет ключа, значение — `null` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());

// Заголовок запроса.
writeRequestHeader(10, OP_CACHE_GET, 1, out);

// Идентификатор кеша.
writeIntLittleEndian(cacheName.hashCode(), out);

// Нет флагов.
writeByteLittleEndian(0, out);

// Объект данных.
writeByteLittleEndian(3, out);  // Код типа `int`.
writeIntLittleEndian(key, out);   // Ключ кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты.
DataInputStream in = new DataInputStream(socket.getInputStream());

// Заголовок ответа.
readResponseHeader(in);

// Конечное значение кеша (объект данных).
int resTypeCode = readByteLittleEndian(in);
int value = readIntLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_ALL

Извлекает несколько пар «ключ-значение» из кеша.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `int` | Количество ключевых полей |
| `Data Object` | Ключ к записи кеша. Повторяется столько раз, сколько указано в предыдущем параметре |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `int` | Количество результатов |
| `Key Data Object` + `Value Data Object` | Конечные пары «ключ-значение». Ключи, которые отсутствуют в кеше, не включаются.<br><br>Повторяется столько раз, сколько результатов получено в предыдущем параметре |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(19, OP_CACHE_GET_ALL, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Количество ключей. 
writeIntLittleEndian(2, out);  

// Первый объект данных. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key1, out);   // Ключ кеша. 

// Второй объект данных. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key2, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Количество результатов. 
int resCount = readIntLittleEndian(in);

for (int i = 0; i < resCount; i++) {
  // Конечный объект данных.   
  int resKeyTypeCode = readByteLittleEndian(in); // Код типа `int`.   
  int resKey = readIntLittleEndian(in); // Ключ кеша.     

  // Конечный объект данных.
  int resValTypeCode = readByteLittleEndian(in); // Код типа `int`.   
  int resValue = readIntLittleEndian(in); // Значение кеша. 
}
```
:::
::::

## OP_CACHE_PUT

Помещает значение с заданным ключом в кеш. Если значение уже есть, оно перезапишется.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |
| `Data Object` | Значение ключа |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_PUT, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_PUT_ALL

Помещает несколько пар «ключ-значение» в кеш. Если эти связи уже существуют, они перезапишутся.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `int` | Количество пар «ключ-значение» |
| `Key Data Object` + `Value Data` | Пары «ключ-значение» типа `object`. Повторяется столько раз, сколько указано в предыдущем параметре |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(29, OP_CACHE_PUT_ALL, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Количество записей. 
writeIntLittleEndian(2, out);  

// Первый объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`.
writeIntLittleEndian(key1, out);   // Ключ кеша.

// Первый объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`.
writeIntLittleEndian(value1, out);   // Значение кеша.

// Второй объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`.
writeIntLittleEndian(key2, out);   // Ключ кеша.

// Второй объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`.
writeIntLittleEndian(value2, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_CONTAINS_KEY

Возвращает значение, которое указывает, есть ли данный ключ в кеше.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Если в кеше есть ключ — `true`; в противном случае — `false` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(10, OP_CACHE_CONTAINS_KEY, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

// Результат.
boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_CONTAINS_KEYS

Возвращает значение, которое указывает, все ли ключи есть в кеше.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `int` | Количество ключей |
| `Data Object` | Ключ, который получили из кеша. Повторяется столько раз, сколько указано в предыдущем параметре |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Если в кеше есть ключи — `true`; в противном случае — `false` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(19, OP_CACHE_CONTAINS_KEYS, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);

// Нет флагов. 
writeByteLittleEndian(0, out);

// Количество.
writeIntLittleEndian(2, out);

// Первый объект данных ключа кеша.
int key1 = 11;
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key1, out);   // Ключ кеша.   

// Второй объект данных ключа кеша.
int key2 = 22;
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key2, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

// Конечное булевое значение.
boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_AND_PUT

Помещает ключ и связанное с ним значение в кеш и возвращает предыдущее значение этого ключа. Если в кеше нет ключа, создается новая запись и возвращается значение `NULL`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ, который нужно обновить |
| `Data Object` | Новое значение указанного ключа |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `Data Object` | Существующее значение, которое связано с указанным ключом, или `NULL` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_GET_AND_PUT, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

// Конечное значение кеша (объект данных).
int resTypeCode = readByteLittleEndian(in);
int value = readIntLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_AND_REPLACE

Заменяет связанное с данным ключом значение в конкретном кеше и возвращает предыдущее значение. Если в кеше нет ключа, операция возвращает значение `NULL` и не меняет данные кеша.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ, значение которого нужно заменить |
| `Data Object` | Новое значение, которое будет связано с указанным ключом |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `Data Object` | Предыдущее значение, которое связано с указанным ключом. Если ключа нет — `NULL` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_GET_AND_REPLACE, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Конечное значение кеша (объект данных). 
int resTypeCode = readByteLittleEndian(in);
int value = readIntLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_AND_REMOVE

Удаляет определенную запись из кеша и возвращает ее значение. Если ключа не существует, вернется значение `NULL`.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ, который нужно удалить |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `Data Object` | Существующее значение, которое связано с указанным ключом. Если ключа нет — `NULL` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(10, OP_CACHE_GET_AND_REMOVE, 1, out); 
 
// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Конечное значение кеша (объект данных). 
int resTypeCode = readByte(in);
int value = readInt(in);
```
:::
::::

## OP_CACHE_PUT_IF_ABSENT

Размещает запись в кеше, если ее не существует.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ записи,  которую нужно добавить |
| `Data Object` | Значение ключа, который нужно добавить |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Если создается новая запись — `true`; если она уже есть — `false` |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_PUT_IF_ABSENT, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

// Конечное булевое значение.
boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_AND_PUT_IF_ABSENT

Помещает запись в кеш, если ее еще нет. В противном случае возвращает существующее значение.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ записи,  которую нужно добавить |
| `Data Object` | Значение записи, которую нужно добавить |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `Data Object` | Если в кеше нет записи — `NULL`, создается новая запись. Если она есть — вернется существующее значение, которое связано с данным ключом |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_GET_AND_PUT_IF_ABSENT, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Конечное значение кеша (объект данных). 
int resTypeCode = readByteLittleEndian(in);
int value = readIntLittleEndian(in);
```
:::
::::

## OP_CACHE_REPLACE

Помещает в кеш значение с данным ключом, если он уже существует.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |
| `Data Object` | Значение ключа |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Значение указывает, была ли замена |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_REPLACE, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.
   
// Объект данных значения кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_REPLACE_IF_EQUALS

Помещает в кеш значение с данным ключом, если он уже существует и значение совпадает с представленным.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |
| `Data Object` | Значение, которое нужно сравнить с существующим в кеше для данного ключа |
| `Data Object` | Новое значение ключа |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Значение указывает, была ли замена |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(20, OP_CACHE_REPLACE_IF_EQUALS, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша для сравнения.

// Объект данных значения кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(newValue, out);   // Новое значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_CLEAR

Очищает кеш без уведомления слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5, OP_CACHE_CLEAR, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_CLEAR_KEY

Очищает ключ кеша без уведомления слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(10, OP_CACHE_CLEAR_KEY, 1, out);;  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша. 
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_CLEAR_KEYS

Очищает ключи кеша без уведомления слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `int` | Количество ключей |
| `Data Object * count` | Ключи |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(19, OP_CACHE_CLEAR_KEYS, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Количество ключей. 
writeIntLittleEndian(2, out);

// Первый объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key1, out);   // Ключ кеша.   

// Второй объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key2, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_REMOVE_KEY

Удаляет запись с данным ключом и уведомляет слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ к записи кеша |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Значение указывает, было ли удаление |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(10, OP_CACHE_REMOVE_KEY, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key1, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Конечное булевое значение. 
boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_REMOVE_IF_EQUALS

Удаляет запись с данным ключом, если указанное значение совпадает с текущим. Уведомляет слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `Data Object` | Ключ от записи, которую нужно удалить |
| `Data Object` | Значение, которое нужно сравнить с текущим |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `bool` | Значение указывает, было ли удаление |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(15, OP_CACHE_REMOVE_IF_EQUALS, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key, out);   // Ключ кеша.   

// Объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(value, out);   // Значение кеша.
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Конечное булевое значение. 
boolean res = readBooleanLittleEndian(in);
```
:::
::::

## OP_CACHE_GET_SIZE

Получает количество записей в кеше. Данный метод идентичен `IgniteCache.size(CachePeekMode…​ peekModes)`.

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
+   *   `int`
    *   Количество peek-режимов, которые нужно запросить. Если установлено значение `0`, используется режим `CachePeekMode.ALL`. Если установлено положительное значение, в следующих полях укажите, какие записи нужно считать: все, резервные (backup), основные (primary) или записи near-кеша
+   *   `byte`
    *   Указывает, какие записи нужно считать (это поле нужно обеспечить столько раз, сколько указано в предыдущем):
        - `0` — все;
        - `1` — записи near-кеша;
        - `2` — основные (primary) записи;
        - `3` — резервные (backup) записи
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `long` | Размер кеша |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(10, OP_CACHE_GET_SIZE, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);

// Количество peek-режимов. '0' означает все.
writeIntLittleEndian(0, out);

// Peek-режим. 
writeByteLittleEndian(0, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);

// Количество записей в кеше. 
long cacheSize = readLongLittleEndian(in);
```
:::
::::

## OP_CACHE_REMOVE_KEYS

Удаляет записи с данными ключами и уведомляет слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |
| `int` | Количество ключей, которые нужно удалить |
| `Data Object` | Ключ, который нужно удалить. Если в кеше нет ключа, поле игнорируется. Поле нужно указать для каждого удаляемого ключа |
| ... | ... |
| `Data Object` | Ключ, который нужно удалить |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(19, OP_CACHE_REMOVE_KEYS, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);  

// Количество ключей. 
writeIntLittleEndian(2, out);

// Первый объект данных ключа кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key1, out);   // Ключ кеша.   

// Второй объект данных значения кеша.
writeByteLittleEndian(3, out);  // Код типа `int`. 
writeIntLittleEndian(key2, out);   // Ключ кеша. 
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);
```
:::
::::

## OP_CACHE_REMOVE_ALL

Удаляет все записи из кеша и уведомляет слушателей и cache writers.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор кеша; хеш-код имени кеша в Java-стиле |
| `byte` | Используйте `0`. Поле не рекомендуется к использованию и будет удалено в ближайших релизах |

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```java
DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5, OP_CACHE_REMOVE_ALL, 1, out);  

// Идентификатор кеша. 
writeIntLittleEndian(cacheName.hashCode(), out);  

// Нет флагов. 
writeByteLittleEndian(0, out);
```
:::

:::{md-tab-item} Пример ответа
```java
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

// Длина ответа.
final int len = readIntLittleEndian(in);

// Идентификатор запроса.
long resReqId = readLongLittleEndian(in);

// Успех.
int statusCode = readIntLittleEndian(in);
```
:::
::::