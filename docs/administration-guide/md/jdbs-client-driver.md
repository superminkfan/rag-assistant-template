# Клиентский JDBC-драйвер

Клиентский JDBC-драйвер подключается к кластеру с помощью соединения клиентского узла. Для этого необходимо предоставить полный файл XML-конфигурации Spring в составе строки подключения JDBC, а также скопировать указанные ниже JAR-файлы в `classpath` приложения или SQL-инструмента:

- все JAR-файлы из директории `{IGNITE_HOME}\libs`;
- все JAR-файлы из директорий `{IGNITE_HOME}\ignite-indexing` и `{IGNITE_HOME}\ignite-spring`.

Клиентский драйвер более надежен, но может не поддерживать последние SQL-функции DataGrid. Но поскольку клиентский драйвер использует клиентское подключение к узлу, он может выполнять и распределять запросы, а также агрегировать их результаты непосредственно на стороне приложения.

**Формат URL-подключения JDBC:**

```bash
jdbc:ignite:cfg://[<params>@]<config_url>
```

где:

- `<config_url>` — обязательный параметр, URL-адрес конфигурационного файла клиентского узла. Этот узел будет запущен внутри клиентского JDBC-драйвера DataGrid при попытке установить соединение с кластером.
- `<params>` — необязательный параметр в формате: `param1=value1:param2=value2:...:paramN=valueN`.

Имя класса драйвера: `org.apache.ignite.IgniteJdbcDriver`. 

::::{admonition} Пример JDBC-соединения с кластером DataGrid
:class: hint 

:::{code-block} java
:caption: Java
// Регистрация JDBC-драйвера.
Class.forName("org.apache.ignite.IgniteJdbcDriver");

// Открытие JDBC-соединения (имя кеша не указано, используется кеш по умолчанию).
Connection conn = DriverManager.getConnection("jdbc:ignite:cfg://config/ignite-jdbc.xml");
:::
::::

## Поддерживаемые параметры

| Параметр | Описание | Значение по умолчанию |
|---|---|---|
| `cache` | Имя кеша. Если не указано, будет использоваться кеш по умолчанию. Обратите внимание: имя кеша чувствительно к регистру | — |
| `nodeId` | Идентификатор узла, на котором будет выполняться запрос. Полезно при выполнении запросов через локальные кеши | — |
| `local` | Если установлено значение `true`, запрос будет выполняться только на локальном узле. Используется в сочетании с `nodeId` для ограничения набора данных узлом | `false` |
| `collocated` | Флаг, который используется для оптимизации. Когда DataGrid выполняет распределенный запрос, он отправляет подзапросы отдельным узлам кластера. Если элементы запроса заранее известны как совместно размещенные на одном узле, DataGrid может значительно оптимизировать производительность и сетевую нагрузку | `false` |
| `distributedJoins` | Разрешает использование распределенных соединений для несогласованных (не совместно размещенных) данных | `false` |
| `streaming` | Включает режим массовой загрузки данных через операторы `INSERT`. Подробнее об этом написано ниже в разделе [«Режим потоковой передачи»](#режим-потоковой-передачи-streaming-mode) | `false` |
| `streamingAllowOverwrite` | Разрешает DataGrid перезаписывать существующие значения ключей при дублировании вместо их пропуска. Подробнее об этом написано ниже в разделе [«Режим потоковой передачи»](#режим-потоковой-передачи-streaming-mode) | `false` |
| `streamingFlushFrequency` | Тайм-аут (в миллисекундах), через который `DataStreamer` должен сбрасывать данные. По умолчанию данные сбрасываются при закрытии соединения. Подробнее об этом написано ниже в разделе [«Режим потоковой передачи»](#режим-потоковой-передачи-streaming-mode) | `0` |
| `streamingPerNodeBufferSize` | Размер буфера `DataStreamer` на узле. Подробнее об этом написано ниже в разделе [«Режим потоковой передачи»](#режим-потоковой-передачи-streaming-mode) | `1024` |
| `streamingPerNodeParallelOperations` | Количество параллельных операций `DataStreamer` на узле. Подробнее об этом написано ниже в разделе [«Режим потоковой передачи»](#режим-потоковой-передачи-streaming-mode) | `16` |
| `transactionsAllowed` | В настоящее время DataGrid поддерживает ACID-транзакции только на уровне Key-Value API. На уровне SQL DataGrid поддерживает атомарную, но не транзакционную согласованность. Это означает, что при попытке использовать транзакции JDBC-драйвер может вызвать исключение `Transactions are not supported`.<br><br>Если необходимо, чтобы синтаксис транзакций работал даже без транзакционной семантики (например, если некоторые BI-инструменты требуют транзакционного поведения), установите у параметра `transactionsAllowed` значение `true`, чтобы избежать возникновения исключений | `false` |
| `multipleStatementsAllowed` | Позволяет JDBC-драйверу обрабатывать несколько SQL-запросов одновременно, возвращая несколько объектов `ResultSet`. Если параметр отключен, запрос с несколькими операторами завершится с ошибкой | `false` |
| `skipReducerOnUpdate` | Включает функцию обновления на стороне сервера. При выполнении DML-операций DataGrid сначала извлекает все промежуточные затронутые строки для анализа на узле инициатора запроса (так называемом `reducer`), а затем подготавливает пакеты обновленных значений для отправки на удаленные узлы.<br><br>Такой подход может повлиять на производительность и перегрузить сеть, если DML-операция перемещает большое количество записей.<br><br>Установите значение флага `true`, чтобы указать DataGrid выполнять анализ и обновления «на месте» на соответствующих удаленных узлах данных, избегая отправки промежуточных результатов на инициатор запроса. Значение по умолчанию — `false` (это означает, что промежуточные результаты сначала будут отправлены на инициатор запроса) | `false` |

:::{admonition} Запросы между кешами (Cross-Cache Queries)
:class: note

Кеш, к которому подключается драйвер, рассматривается как схема по умолчанию. Для выполнения запросов между несколькими кешами можно использовать Cross-Cache Queries.
:::

## Режим потоковой передачи (Streaming Mode)

Добавление данных в кластер возможно в режиме потоковой передачи (bulk mode) с использованием JDBC-драйвера. В этом режиме драйвер внутренне создает `IgniteDataStreamer` и передает данные в него. Чтобы активировать этот режим, добавьте параметр `streaming=true` в строку подключения JDBC:

:::{code-block} java
:caption: Java
// Регистрация JDBC-драйвера.
Class.forName("org.apache.ignite.IgniteJdbcDriver");

// Открытие соединения в режиме потоковой передачи.
Connection conn = DriverManager.getConnection("jdbc:ignite:cfg://streaming=true@file:///etc/config/ignite-jdbc.xml");
:::

На данный момент режим потоковой передачи поддерживается только для операций `INSERT`. Этот режим полезен, когда требуется быстро загрузить данные в кеш. JDBC-драйвер поддерживает несколько параметров соединения, которые влияют на поведение потоковой передачи данных. Они описаны выше в разделе «[](#поддерживаемые-параметры)».

:::{admonition} Имя кеша
:class: note

При использовании потоковой передачи убедитесь, что вы указываете целевой кеш в качестве аргумента параметра `cache` в строке подключения JDBC. Если кеш не указан или не соответствует таблице, которая используется в DML-операторах потоковой передачи, обновления будут проигнорированы.
:::

Параметры потоковой передачи охватывают почти все настройки стандартного `IgniteDataStreamer` и позволяют настроить `DataStreamer` в соответствии с требованиями. Подробнее о настройке потоковой передачи написано в разделе [«Data Streaming»](../../developer-guide/md/data_streaming.md) документа «Руководство прикладного разработчика».

::::{admonition} Тайм-аут принудительной отправки данных (Time-Based Flushing)
:class: note
:collapsible:

По умолчанию данные передаются в кеш при закрытии соединения или при достижении значения `streamingPerNodeBufferSize`. Если необходимо передавать данные чаще, настройте параметр `streamingFlushFrequency`:

:::{code-block} java
:caption: Java
// Регистрация JDBC-драйвера.
   Class.forName("org.apache.ignite.IgniteJdbcDriver");

   // Открытие соединения в режиме потоковой передачи с принудительной отправкой данных по таймеру.
   Connection conn = DriverManager.getConnection("jdbc:ignite:cfg://streaming=true:streamingFlushFrequency=1000@file:///etc/config/ignite-jdbc.xml");

   PreparedStatement stmt = conn.prepareStatement(
     "INSERT INTO Person(_key, name, age) VALUES(CAST(? as BIGINT), ?, ?)");

   // Добавление данных.
   for (int i = 1; i < 100000; i++) {
         // Вставка объекта `Person` с ключом типа `long`.
         stmt.setInt(1, i);
         stmt.setString(2, "John Smith");
         stmt.setInt(3, 25);

         stmt.execute();
   }

   conn.close();

   // После закрытия соединения все данные гарантированно будут записаны в кеш.
:::
::::

## Пример использования

Для работы с данными в кластере необходимо создать объект `JDBC Connection`:

:::{code-block} java
:caption: Java
// Регистрация JDBC-драйвера.
Class.forName("org.apache.ignite.IgniteJdbcDriver");

// Открытие JDBC-соединения (имя кеша не указано, используется кеш по умолчанию).
Connection conn = DriverManager.getConnection("jdbc:ignite:cfg://file:///etc/config/ignite-jdbc.xml");
:::

После этого можно выполнять стандартные SQL-запросы (`SELECT`, `INSERT`, `MERGE`, `UPDATE`, `DELETE`) и использовать DML-операторы для изменения данных.

### SELECT

:::{code-block} java
:caption: Java
// Запрос имен всех людей.
ResultSet rs = conn.createStatement().executeQuery("select name from Person");

while (rs.next()) {
    String name = rs.getString(1);
}
:::

:::{code-block} java
:caption: Java
// Запрос людей определенного возраста с помощью подготовленного выражения (`PreparedStatement`).
PreparedStatement stmt = conn.prepareStatement("select name, age from Person where age = ?");

stmt.setInt(1, 30);

ResultSet rs = stmt.executeQuery();

while (rs.next()) {
    String name = rs.getString("name");
    int age = rs.getInt("age");
}
:::

Можно использовать DML-операторы для изменения данных.

### INSERT

:::{code-block} java
:caption: Java
// Вставка новой записи в таблицу `Person` с ключом типа `long`.
PreparedStatement stmt = conn.prepareStatement("INSERT INTO Person(_key, name, age) VALUES(CAST(? as BIGINT), ?, ?)");

stmt.setInt(1, 1);
stmt.setString(2, "John Smith");
stmt.setInt(3, 25);

stmt.execute();
:::

### MERGE

:::{code-block} java
:caption: Java
// Объединение (merge) записи в таблицу `Person` с ключом типа `long`.
PreparedStatement stmt = conn.prepareStatement("MERGE INTO Person(_key, name, age) VALUES(CAST(? as BIGINT), ?, ?)");

stmt.setInt(1, 1);
stmt.setString(2, "John Smith");
stmt.setInt(3, 25);

stmt.executeUpdate();
:::

### UPDATE

:::{code-block} java
:caption: Java
// Обновление данных в таблице `Person`.
conn.createStatement().
  executeUpdate("UPDATE Person SET age = age + 1 WHERE age = 25");
:::

### DELETE

:::{code-block} java
:caption: Java
// Удаление записей из таблицы `Person`.
conn.createStatement().execute("DELETE FROM Person WHERE age = 25");
:::