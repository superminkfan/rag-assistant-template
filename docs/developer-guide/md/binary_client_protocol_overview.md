# Обзор бинарного протокола клиента

Бинарный протокол клиента позволяет пользовательским приложениям подключаться к существующему кластеру DataGrid без развертывания полноценного нового узла. Приложение может подключаться к кластеру через «голый» TCP-сокет. Когда соединение установится, приложение сможет взаимодействовать с кластером и выполнять операции с его кешем в установленном формате.

Формат данных и детали соединения, которые клиент должен соблюдать для подключения к кластеру DataGrid, описаны в разделах ниже.

## Формат данных

### Порядок байтов

DataGrid использует порядок байтов little-endian.

### Объекты данных

Пользовательские данные, например ключи и значения кеша, представлены в формате бинарных объектов DataGrid. Подробнее о бинарных объектах написано в подразделе [«Работа с бинарными объектами»](working_with_binary_objects.md) раздела «Использование Key-Value API».

Объект данных может быть стандартного (предопределенного) типа или сложным объектом. Полный список поддерживаемых типов данных находится в разделе [«Формат данных»](data_format.md).

## Формат сообщения

Все сообщения (запросы и ответы), включая handshake, начинаются с определения длины сообщения с помощью типа `int` без первых четырех байтов. После этого следует полезная нагрузка — тело сообщения.

### Подтверждение подключения (handshake)

Бинарный протокол клиента требует подтверждения подключения, чтобы гарантировать совместимость версий клиента и сервера. Таблицы ниже показывают структуру сообщения запроса и ответа:

| Тип поля запроса | Описание |
|---|---|
| `int` | Длина полезной нагрузки handshake |
| `byte` | Код подтверждения подключения, всегда равен `1` |
| `short` | Мажорная версия |
| `short` | Минорная версия |
| `short` | Версия патча |
| `byte` | Код клиента, всегда равен `2` |
| `String` | Имя пользователя |
| `String` | Пароль |

| Тип поля ответа (успех) | Описание |
|---|---|
| `int` | Длина сообщения об успехе, `1` |
| `byte` | Флаг успеха, `1` |

| Тип поля ответа (ошибка) | Описание |
|---|---|
| `int` | Длина сообщения об ошибке |
| `byte` | Флаг успеха, `0` |
| `short` | Мажорная версия сервера |
| `short` | Минорная версия сервера |
| `short` | Версия патча сервера |
| `String` | Сообщение об ошибке |

Подробнее о том, как отправлять и получать запросы на подтверждение подключения и ответ соответственно, написано ниже в разделе [«Пример»](#пример).

### Стандартный заголовок сообщения

Сообщения клиента состоят из заголовка и данных, которые относятся к конкретной операции. У каждой операции есть собственный формат данных запроса и ответа с общим заголовком — подробнее написано ниже в разделе [«Клиентские операции»](#клиентские-операции).

Структура запросов и ответов заголовка операционного сообщения клиента в таблицах и примерах:

| Тип поля запроса | Описание |
|---|---|
| `int` | Длина полезной нагрузки |
| `short` | Код операции |
| `long` | Идентификатор запроса, который создается клиентом и возвращается как есть (as-is) в ответе |

:::{admonition} Пример заголовка запроса
:class: hint 
:collapsible:

```bash
private static void writeRequestHeader(int reqLength, short opCode, long reqId, DataOutputStream out) throws IOException {
  // Длина сообщения.
  writeIntLittleEndian(10 + reqLength, out);

  // Код операции.
  writeShortLittleEndian(opCode, out);

  // Идентификатор запроса.
  writeLongLittleEndian(reqId, out);
}
```

| Тип поля ответа | Описание |
|---|---|
| `int` | Длина ответного сообщения |
| `long` | Идентификатор запроса (подробнее написано выше) |
| `int` | Код статуса (в случае успеха `0`, в остальных случаях — ошибка) |
| `String` | Сообщение об ошибке (появляется, только если статус не `0`) |
:::

:::{admonition} Пример заголовка ответа
:class: hint 
:collapsible:

```bash
private static void readResponseHeader(DataInputStream in) throws IOException {
  // Длина ответа.
  final int len = readIntLittleEndian(in);

  // Идентификатор запроса.
  long resReqId = readLongLittleEndian(in);

  // Код успеха.
  int statusCode = readIntLittleEndian(in);
}
```
:::

## Соединение

### TCP-сокет

Клиентские приложения должны подключаться к узлам сервера через TCP-сокет. По умолчанию соединение включено на порту `10800`. Настроить номер порта и другие параметры подключения на стороне сервера можно в свойстве `clientConnectorConfiguration` конфигурационного файла `IgniteConfiguration` кластера:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean id="ignite.cfg" class="org.apache.ignite.configuration.IgniteConfiguration">
    <!-- Настройка подключения к тонкому клиенту. -->
    <property name="clientConnectorConfiguration">
        <bean class="org.apache.ignite.configuration.ClientConnectorConfiguration">
            <property name="host" value="xxx.x.x.x"/>
            <property name="port" value="10900"/>
            <property name="portRange" value="30"/>
        </bean>
    </property>

    <!-- Другие настройки DataGrid. -->

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

ClientConnectorConfiguration ccfg = new ClientConnectorConfiguration();
ccfg.setHost("xxx.x.x.x");
ccfg.setPort(10900);
ccfg.setPortRange(30);

// Установите конфигурацию клиентского подключения в `IgniteConfiguration`.
 cfg.setClientConnectorConfiguration(ccfg);

// Запустите узел DataGrid.
Ignition.start(cfg);
```
:::
::::

## Подтверждение подключения (connection handshake)

Кроме установления сокетного соединения, протокол тонкого клиента запрашивает подтверждение подключения для проверки совместимости версий клиента и сервера. Подтверждение подключения должно быть первым сообщением после установки соединения.

Подробнее о структуре запроса и ответа сообщения о подтверждении подключения написано выше в разделе [«Подтверждение подключения (handshake)»](#подтверждение-подключения-handshake).

### Пример

Сокет и подтверждение соединения:

```bash
Socket socket = new Socket();
socket.connect(new InetSocketAddress("xxx.x.x.x", 10800));

String username = "yourUsername";

String password = "yourPassword";

DataOutputStream out = new DataOutputStream(socket.getOutputStream());

// Длина сообщения.
writeIntLittleEndian(18 + username.length() + password.length(), out);

// Операция подтверждения подключения.
writeByteLittleEndian(1, out);

// Протокол версии 1.0.0.
writeShortLittleEndian(1, out);
writeShortLittleEndian(1, out);
writeShortLittleEndian(0, out);

// Код клиента: тонкий клиент.
writeByteLittleEndian(2, out);

// Имя пользователя.
writeString(username, out);

// Пароль.
writeString(password, out);

// Отправить запрос.
out.flush();

// Получить ответ с подтверждением.
DataInputStream in = new DataInputStream(socket.getInputStream());
int length = readIntLittleEndian(in);
int successFlag = readByteLittleEndian(in);

// Так как в бинарном протоколе DataGrid используется порядок байтов little-endian,
// нужно реализовать преобразование методов записи и чтения
// из формата big-endian в формат little-endian.

// Записать `int` в порядке байтов little-endian.
private static void writeIntLittleEndian(int v, DataOutputStream out) throws IOException {
  out.write((v >>> 0) & 0xFF);
  out.write((v >>> 8) & 0xFF);
  out.write((v >>> 16) & 0xFF);
  out.write((v >>> 24) & 0xFF);
}

// Записать `short` в порядке байтов little-endian.
private static final void writeShortLittleEndian(int v, DataOutputStream out) throws IOException {
  out.write((v >>> 0) & 0xFF);
  out.write((v >>> 8) & 0xFF);
}

// Записать `byte` в порядке байтов little-endian.
private static void writeByteLittleEndian(int v, DataOutputStream out) throws IOException {
  out.writeByte(v);
}

// Прочитать `int` в порядке байтов little-endian.
private static int readIntLittleEndian(DataInputStream in) throws IOException {
  int ch1 = in.read();
  int ch2 = in.read();
  int ch3 = in.read();
  int ch4 = in.read();
  if ((ch1 | ch2 | ch3 | ch4) < 0)
    throw new EOFException();
  return ((ch4 << 24) + (ch3 << 16) + (ch2 << 8) + (ch1 << 0));
}

// Прочитать `byte` в порядке байтов little-endian.
private static byte readByteLittleEndian(DataInputStream in) throws IOException {
  return in.readByte();
}

// Другие методы записи и чтения.
```

## Клиентские операции

После успешного подтверждения подключения клиент может выполнять различные операции с кешем, подробнее написано в разделах:

- [Запросы типа «ключ-значение»](key_value_queries.md)
- [SQL-запросы и Scan Queries](sql_and_scan_queries.md)
- [Метаданные бинарного типа](binary_type_metadata.md)
- [Конфигурация кеша](cache_configuration.md)