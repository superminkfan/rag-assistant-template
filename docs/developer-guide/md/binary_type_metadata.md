# Метаданные бинарного типа

## Коды операций

После успешного подтверждения подключения к узлу сервера DataGrid клиент может выполнять операции с данными бинарного типа. Клиент отправляет запрос (подробнее о структуре запросов и ответов написано в разделах ниже) с конкретным кодом операции:

| Операция | Код операции |
|---|---|
| `OP_GET_BINARY_TYPE_NAME` | 3000 |
| `OP_REGISTER_BINARY_TYPE_NAME` | 3001 |
| `OP_GET_BINARY_TYPE` | 3002 |
| `OP_PUT_BINARY_TYPE` | 3003 |
| `OP_RESOURCE_CLOSE` | 0 |

Указанные выше коды операций являются частью заголовка запроса — подробнее написано в подразделе «Стандартный заголовок сообщения» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md).

:::{admonition} Пользовательские методы, которые используются при реализации примеров фрагментов кода ниже
:class: note

В некоторых примерах кода ниже используются:

- метод `readDataObject()`, который описан в подразделе «Объекты данных» раздела [«Обзор бинарного протокола клиента»](binary_client_protocol_overview.md);
- методы, которые используют порядок байтов little-endian для чтения и записи значений, состоящих из нескольких байтов — они включены в раздел [«Формат данных»](data_format.md).
:::

## OP_GET_BINARY_TYPE_NAME

Получает по идентификатору полное бинарное название типа, которое зависит от платформы. Например, .NET и Java могут отображаться как один тип `Foo`, но классы будут называться по-разному:

- `Apache.Ignite.Foo` в .NET;
- `org.apache.ignite.Foo` в Java.

Названия типов регистрируются с помощью операции [OP_REGISTER_BINARY_TYPE_NAME](#op_register_binary_type_name).

:::{list-table}
:header-rows: 1
 
+   *   Тип поля запроса 
    *   Описание
+   *   `Header`
    *   Заголовок запроса
+   *   `byte`
    *   Идентификатор платформы:
        - `JAVA = 0`;
        - `DOTNET = 1`
+   *   `int`
    *   Идентификатор типа; хеш-код названия типа в Java-стиле
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |
| `String` | Название бинарного типа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
String type = "ignite.myexamples.model.Person";
int typeLen = type.getBytes("UTF-8").length;

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(5, OP_GET_BINARY_TYPE_NAME, 1, out);  

// Идентификатор платформы. 
writeByteLittleEndian(0, out);  

// Идентификатор типа. 
writeIntLittleEndian(type.hashCode(), out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());  

// Заголовок ответа. 
readResponseHeader(in);  

// Результирующая строка. 
int typeCode = readByteLittleEndian(in); // Код типа.
int strLen = readIntLittleEndian(in); // Длина.

byte[] buf = new byte[strLen];

readFully(in, buf, 0, strLen);

String s = new String(buf);

System.out.println(s);
```
:::
::::

## OP_GET_BINARY_TYPE

Получает информацию о бинарном типе данных по идентификатору.

| Тип поля запроса | Описание |
|---|---|
| `Header` | Заголовок запроса |
| `int` | Идентификатор типа; хеш-код названия типа в Java-стиле |

:::{list-table}
:header-rows: 1

+   *   Тип поля ответа
    *   Описание
+   *   `Header`
    *   Заголовок ответа
+   *   `bool`
    *   - Если установлено значение `false`: бинарного типа не существует, конец ответа.
        - Если установлено значение `true`: бинарный тип существует, ответ следует далее
+   *   `int`
    *   Идентификатор типа; хеш-код названия типа в Java-стиле
+   *   `String`
    *   Название типа
+   *   `String`
    *   Название поля affinity-ключа
+   *   `int`
    *   Количество значений `BinaryField`
+   *   `BinaryField * count`
    *   Структура параметра `BinaryField`:
        - `String` — название поля.
        - `int` — идентификатор типа; хеш-код названия типа в Java-стиле.
        - `int` — идентификатор поля; хеш-код названия поля в в Java-стиле
+   *   `bool`
    *   Является ли типом `enum` или нет.

        Если установлено значение `true`, передайте следующие 2 параметра. В противном случае пропустите их
+   *   `int`
    *   Передавайте, только если у параметра `isEnum` установлено значение `true`. Количество полей типа `enum`
+   *   `String` + `int`
    *   Передавайте, только если у параметра `isEnum` установлено значение `true`. Значения типа `enum` — пара символьных (`String`) и числовых (`int`) значений. 
    
        Повторяется столько раз, сколько полей указано в предыдущем параметре
+   *   `int`
    *   Количество схем
+   *   `BinarySchema`
    *   Структура параметра `BinarySchema`:
        - `int` — уникальный идентификатор схемы.
        - `int` — количество полей в схеме.
        - `int` — идентификатор поля; хеш-код названия поля в Java-стиле. Количество повторений соответствует общему количеству полей в схеме.

        Повторяется столько раз, сколько схем указано в предыдущем параметре
:::

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
tring type = "ignite.myexamples.model.Person";

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(4, OP_BINARY_TYPE_GET, 1, out);  

// Идентификатор типа. 
writeIntLittleEndian(type.hashCode(), out);
```
:::

:::{md-tab-item} Пример ответа
```bash
// Прочитать результаты. 
DataInputStream in = new DataInputStream(socket.getInputStream());

readResponseHeader(in);

boolean typeExist = readBooleanLittleEndian(in);

int typeId = readIntLittleEndian(in);

String typeName = readString(in);

String affinityFieldName = readString(in);

int fieldCount = readIntLittleEndian(in);

for (int i = 0; i < fieldCount; i++)
    readBinaryTypeField(in);

boolean isEnum = readBooleanLittleEndian(in);

int schemaCount = readIntLittleEndian(in);

// Прочитать бинарные схемы.
for (int i = 0; i < schemaCount; i++) {
  int schemaId = readIntLittleEndian(in); // Идентификатор схемы.

  int fieldCount = readIntLittleEndian(in); // Количество полей.

  for (int j = 0; j < fieldCount; j++) {
    System.out.println(readIntLittleEndian(in)); // Идентификатор поля.
  }
}

private static void readBinaryTypeField (DataInputStream in) throws IOException{
  String fieldName = readString(in);
  int fieldTypeId = readIntLittleEndian(in);
  int fieldId = readIntLittleEndian(in);
  System.out.println(fieldName);
}
```
:::
::::

## OP_REGISTER_BINARY_TYPE_NAME

Регистрирует по идентификатору полное бинарное название типа, которое зависит от платформы. Например, .NET и Java могут отображаться как один тип `Foo`, но классы будут называться по-разному:

- `Apache.Ignite.Foo` в .NET;
- `org.apache.ignite.Foo` в Java.

:::{list-table}
:header-rows: 1
 
+   *   Тип поля запроса
    *   Описание
+   *   `Header`
    *   Заголовок запроса
+   *   `byte`
    *   Идентификатор платформы:
        - `JAVA = 0`;
        - `DOTNET = 1`
+   *   `int`
    *   Идентификатор типа; хеш-код названия типа в Java-стиле
+   *   `String`
    *   Название типа
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
String type = "ignite.myexamples.model.Person";
int typeLen = type.getBytes("UTF-8").length;

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(20 + typeLen, OP_PUT_BINARY_TYPE_NAME, 1, out);

// Идентификатор платформы.
writeByteLittleEndian(0, out);

// Идентификатор типа.
writeIntLittleEndian(type.hashCode(), out);

// Название типа.
writeString(type, out);
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

## OP_PUT_BINARY_TYPE

Регистрирует информацию о бинарном типе данных в кластере.

:::{list-table}
:header-rows: 1

+   *   Тип поля запроса
    *   Описание
+   *   `Header`
    *   Заголовок запроса
+   *   `int`
    *   Идентификатор типа; хеш-код названия типа в Java-стиле
+   *   `String`
    *   Название типа
+   *   `String`
    *   Название поля affinity-ключа
+   *   `int`
    *   Количество значений `BinaryField`
+   *   `BinaryField`
    *   Структура параметра `BinaryField`:
        - `String` — название поля.
        - `int` — идентификатор типа; хеш-код названия типа в Java-стиле.
        - `int` — идентификатор поля; хеш-код названия поля в Java-стиле.

        Повторяется столько раз, сколько значений указано в предыдущем параметре
+   *   `bool`
    *   Является ли типом `enum` или нет.
    
        Если установлено значение `true`, передайте следующие два параметра. В противном случае пропустите их
+   *   `int`
    *   Передавайте, только если у параметра `isEnum` установлено значение `true`. 
    
        Количество полей типа `enum`
+   *   `String` + `int`
    *   Передавайте, только если у параметра `isEnum` установлено значение `true`.
    
        Значения типа `enum` — пара символьных (`String`) и числовых (`int`) значений.
        
        Повторяется столько раз, сколько полей указано в предыдущем параметре
+   *   `int`
    *   Количество переданных структур `BinarySchema`
+   *   `BinarySchema`
    *   Структура параметра `BinarySchema`:
        - `int` — уникальный идентификатор схемы.
        - `int` — количество полей в схеме.
        - `int` — идентификатор поля; хеш-код названия поля в Java-стиле. Количество повторений соответствует общему количеству полей в схеме.

        Повторяется столько раз, сколько структур указано в предыдущем параметре
:::

| Тип поля ответа | Описание |
|---|---|
| `Header` | Заголовок ответа |

::::{md-tab-set}
:::{md-tab-item} Пример запроса
```bash
String type = "ignite.myexamples.model.Person";

DataOutputStream out = new DataOutputStream(socket.getOutputStream());  

// Заголовок запроса. 
writeRequestHeader(120, OP_BINARY_TYPE_PUT, 1, out);  

// Идентификатор типа. 
writeIntLittleEndian(type.hashCode(), out);

// Название типа.
writeString(type, out);

// Название поля affinity-ключа.
writeByteLittleEndian(101, out);

// Количество полей.
writeIntLittleEndian(3, out);

// Первое поле.
String field1 = "id";
writeBinaryTypeField(field1, "long", out);

// Второе поле.
String field2 = "name";
writeBinaryTypeField(field2, "String", out);

// Третье поле.
String field3 = "salary";
writeBinaryTypeField(field3, "int", out);

// `isEnum` — является ли типом `enum` или нет.
out.writeBoolean(false);

// Количество схем.
writeIntLittleEndian(1, out);

// Схема.
writeIntLittleEndian(657, out);  // Идентификатор схемы; может принимать любое пользовательское значение.
writeIntLittleEndian(3, out);  // Количество полей.
writeIntLittleEndian(field1.hashCode(), out);
writeIntLittleEndian(field2.hashCode(), out);
writeIntLittleEndian(field3.hashCode(), out);

private static void writeBinaryTypeField (String field, String fieldType, DataOutputStream out) throws IOException{
  writeString(field, out);
  writeIntLittleEndian(fieldType.hashCode(), out);
  writeIntLittleEndian(field.hashCode(), out);
}
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