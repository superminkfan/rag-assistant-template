# Работа с SQL и Apache Calcite

## Описание SQL-движка на основе Apache Calcite

:::{admonition} Внимание
:class: danger

Новый SQL-движок находится в статусе beta.
:::

Начиная с версии 4.2130 DataGrid поставляется с новым SQL-движком, который основан на фреймворке Apache Calcite.

Apache Calcite — фреймворк динамического управления данными, который служит посредником между приложениями, одним или несколькими местами хранения данных и механизмами их обработки.

У текущего SQL-движка, основанного на H2, есть набор фундаментальных ограничений, которые связаны с исполнением SQL-запросов в распределенной среде. Новый движок позволяет обойти эти ограничения. Он использует инструменты Apache Calcite для планирования и обработки запросов и новый процесс для их исполнения.

Фазы выполнения запроса через Calcite:

1. Обработка:

    - Вход — строка самого запроса.
    - Выход — синтаксическое дерево (AST — Abstract Syntax Tree).

2. Валидация (семантический анализ):

    - Вход — синтаксическое дерево (AST) и метаданные. На данном этапе синтаксическое дерево проверяется на соответствие метаданным.
    - Выход — AST с привязкой к конкретным метаданным.

3. Построение логического плана запроса на основе AST:

    - Вход — AST.
    - Выход — логический план запроса (дерево реляционных операторов).

4. Оптимизация:

    - Вход — логический план запроса и статистика.
    - Выход — физический план запроса (дерево реляционных операторов с привязкой к конкретному способу выполнения запроса).

5. Выполнение:

    - Вход — физический план запроса.
    - Выход — результат выполнения (курсор).

## Способы настройки SQL-движка на основе Apache Calcite

### Режим Standalone

При запуске кластера в режиме Standalone перед запуском скрипта `ignite.sh` или `ignite.bat` переместите подкаталоги `optional/ignite-calcite` и `optional/ignite-slf4j` в каталог `libs`. В этом случае контент папки, в которой находится модуль, добавится в classpath.

### Конфигурация Maven

Если в проекте используются библиотеки DataGrid, добавьте в зависимости модуль `ignite-calcite`. В случае использования Maven добавьте следующую зависимость (замените параметр `${ignite.version}` на необходимую версию DataGrid):

:::{code-block} xml
:caption: XML
<dependency>
    <groupId>org.apache.ignite</groupId>
    <artifactId>ignite-calcite</artifactId>
    <version>${ignite.version}</version>
</dependency>
:::

## Конфигурация SQL-движков

Для включения SQL-движка на основе Apache Calcite укажите `CalciteQueryEngineConfiguration` в разделе `SqlConfiguration.QueryEnginesConfiguration`.

Пример конфигурации двух SQL-движков (H2 и Calcite), где движок по умолчанию — Calcite:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="sqlConfiguration">
        <bean class="org.apache.ignite.configuration.SqlConfiguration">
            <property name="queryEnginesConfiguration">
                <list>
                    <bean class="org.apache.ignite.indexing.IndexingQueryEngineConfiguration">
                        <property name="default" value="false"/>
                    </bean>
                    <bean class="org.apache.ignite.calcite.CalciteQueryEngineConfiguration">
                        <property name="default" value="true"/>
                    </bean>
                </list>
            </property>
        </bean>
    </property>
    ...
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration().setSqlConfiguration(
    new SqlConfiguration().setQueryEnginesConfiguration(
        new IndexingQueryEngineConfiguration(),
        new CalciteQueryEngineConfiguration().setDefault(true)
    )
);
```
:::
::::

## Исполнение запросов с указанием SQL-движка

Обычно все запросы направляются в SQL-движок, который настроен по умолчанию. Если в `queryEnginesConfiguration` настроено более одного движка, можно указать один из них для исполнения отдельных запросов или всего подключения к базе данных.

### JDBC

Чтобы выбрать SQL-движок для JDBC-соединения, используйте параметр `queryEngine`.

:::{admonition} Пример
:class: hint

```bash
jdbc:ignite:thin://xxx.x.x.x:10800?queryEngine=calcite
```

где `queryEngine=calcite` — используемый движок.
:::

### ODBC

SQL-движок для ODBC-соединения можно настроить с помощью свойства `QUERY_ENGINE`.

:::{admonition} Пример
:class: hint

```bash
[IGNITE_CALCITE]
DRIVER={Apache Ignite};
SERVER=xxx.x.x.x;
PORT=10800;
SCHEMA=PUBLIC;
QUERY_ENGINE=CALCITE
```
:::

### Подсказка QUERY_ENGINE

Используйте подсказку (hint) `QUERY_ENGINE`, чтобы выбрать определенный движок для отдельных запросов:

:::{code-block} sql
:caption: SQL
SELECT /*+ QUERY_ENGINE('calcite') */ fld FROM table;
:::

## Плагин calcite-oracle-dialect-plugin

Плагин `calcite-oracle-dialect-plugin` добавляет в SQL-движок, который основан на Apache Calcite, некоторые операторы из диалекта Oracle.

### Конфигурация

**Способы конфигурации:**

::::{md-tab-set}
:::{md-tab-item} XML

1. Добавьте новый плагин в конфигурацию серверного узла `<bean class="com.sbt.ignite.calcite.CalciteOracleDialectPluginProvider"/>`:

   ```xml
           <property name="pluginProviders">
               <list>
                   <bean class="com.sbt.ignite.calcite.CalciteOracleDialectPluginProvider"/>
               </list>
           </property>
   ```

2. Переместите библиотеку `ise-calcite-oracle-dialect-plugin` из поддиректории `libs/optionals` в директорию `libs`.
:::

:::{md-tab-item} Java

Дополните конфигурацию `IgniteConfiguration`:

```java
IgniteConfiguration cfg = ...

cfg.setPluginProviders(new CalciteOracleDialectPluginProvider());
```
:::
::::

:::{admonition} Пример успешного запуска плагина в лог-файле серверного узла
:class: hint

```bash
YYYY-MM-DD 10:43:12.223 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- CALCITE_ORACLE_DIALECT_PROVIDER 1.0
YYYY-MM-DD 10:43:12.223 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- null
YYYY-MM-DD 10:43:12.223 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor] 
YYYY-MM-DD 10:43:12.224 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- Check Parameters 1.0.0-SNAPSHOT
YYYY-MM-DD 10:43:12.224 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- SberTech
YYYY-MM-DD 10:43:12.224 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor] 
```
:::

### Операторы

**Плагин добавляет в SQL-движок операторы:**

- Арифметика между датами и числами (`DATE + NUMBER | NUMBER + DATE | DATE - NUMBER | TIMESTAMP + NUMBER | NUMBER + TIMESTAMP | TIMESTAMP - NUMBER`). Для данного оператора числовой аргумент означает количество дней (в том числе с плавающей точкой).
- `SUBSTR(STRING, NUMERIC, NUMERIC) / SUBSTR(STRING, NUMERIC)` — аналог `SUBSTRING` с теми же параметрами.
- `TRUNC(d TIMESTAMP)` — аналог `FLOOR(d TO DAY)`.
- `LTRIM(s STRING, c STRING)` — аналог `TRIM(LEADING c FROM s)`.
- `RTRIM(s STRING, c STRING)` — аналог `TRIM(TRAILING c FROM s)`.
- `NVL2(s STRING, a1 ANY, a2 ANY)` — аналог `CASE s IS NOT NULL THEN a1 ELSE a2 END`.
- `TO_NUMBER(STRING)` — перевод строки в число.
- `TO_CHAR(NUMBER, STRING)` — перевод числа в строку с пользовательским форматом.
- `INSTR(string STRING, seek STRING[, from INTEGER[, occurrence INTEGER]])` — аналог `POSITION(seek, string, from, occurrence)`.
- `REPLACE(a STRING, b STRING)` — аналог `REPLACE(a, b, ‘’)`.
- `REGEXP_INSTR(STRING, STRING[, INTEGER[, INTEGER]])` — поиск шаблона в строке по регулярному выражению. 
- `LPAD(STRING, NUMERIC[, STRING])/RPAD(STRING, NUMERIC[, STRING])` — дополнение строки слева или справа до заданного размера.

## Пользовательские SQL-функции

Пользовательские SQL-функции — публичные статические методы, которые помечены аннотацией `@QuerySqlFunction`. SQL-движок позволяет добавлять пользовательские SQL-функции на Java в перечень SQL-функций, которые определены спецификацией ANSI-99.

Класс, в котором находится пользовательская SQL-функция, нужно зарегистрировать в конфигурации кеша (`CacheConfiguration`) с помощью метода `setSqlFunctionClasses(...)`. При запуске кеша с указанной конфигурацией появится возможность вызова пользовательской функции внутри SQL-запросов.

Пользовательская SQL-функция может быть реализована в виде табличной функции (User-Defined Table Functions, UDTF). Результат табличной функции представлен в виде набора строк (таблицы), который доступен другим SQL-операторам. UDTF позволяет пользователям определять собственные табличные функции, которые могут возвращать наборы строк и использоваться в SQL-запросах как обычные таблицы.

::::{admonition} Пример использования
:class: hint

:::{code-block} sql
:caption: SQL
SELECT * FROM TABLE(my_custom_function(param1, param2))
:::

где `my_custom_function` — пользовательская табличная функция, которая принимает параметры `param1` и `param2` и возвращает результат в виде таблицы.
::::

Пользовательская SQL-функция в виде табличной функции представлена как публичный метод с аннотацией `@QuerySqlTableFunction`. Метод должен возвращать объект типа `Iterable`, который состоит из набора строк. Каждая строка может быть представлена массивом объектов `Object[]` или коллекцией. Количество элементов в массиве или коллекции должно совпадать с количеством колонок, которые описаны в аннотации. Типы значений в строках должны совпадать с типами столбцов или допускать преобразование в соответствующие типы.

Аннотация должна описывать возвращаемые колонки и их типы данных.

::::{admonition} Пример аннотации
:class: hint

:::{code-block} java
:caption: Java
@QuerySqlTableFunction(
    alias = "persons", 
    columnNames = {"ID", "NAME", "SALARY"}, 
    columnTypes = {Integer.class, String.class, Double.class}
)
public static Iterable<Object[]> persons() {
    return List.of(
        new Object[] {1, "Name 1", 100d}, 
        new Object[] {2, "Name 2", 200d}
    );
}
:::
::::

:::{admonition} Примечание
:class: note

В настоящее время табличные функции доступны только совместно с Apache Calcite.
:::

:::{admonition} Примечание
:class: note

Классы, которые зарегистрированы с помощью метода `CacheConfiguration.setSqlFunctionClasses(...)`, необходимо включить в `classpath` всех узлов, где могут быть запущены эти пользовательские функции. В противном случае при попытке их использования сгенерируется исключение `ClassNotFoundException`.
:::

## Планировщик задач для блокировки запросов в Apache Calcite

Архитектура SQL-движка Apache Calcite в DataGrid требует, чтобы задачи по одному и тому же запросу не могли выполняться конкурентно. Выполнение SQL-запроса и относящихся к нему задач привязывается к конкретному потоку из пула. Для привязки используется хеш-код идентификатора запроса. Если пользователь добавил собственную SQL-функцию (User-Defined Function, UDF), которая также выполняет некоторый SQL-запрос, это может привести к коллизиям при выборе потока и к взаимоблокировке (deadlock). Поток блокируется задачей, которая синхронно ждет выполнения нового SQL-запроса, а он не может быть выполнен, так как новый SQL-запрос по идентификатору запроса назначен на тот же поток.

Для решения этой проблемы в DataGrid добавлен новый исполнитель задач (task executor) — `QueryBlockingTaskExecutor`. Он основан на общей очереди задач для всех потоков, но за счет дополнительной синхронизации позволяет обеспечить гарантии, которые требуются SQL-движку при отсутствии конкуренции между задачами одного запроса. Это позволяет избежать взаимоблокировок при выполнении SQL-запросов внутри пользовательской функции.

:::{admonition} Важно
:class: attention

Свойство `IGNITE_CALCITE_USE_QUERY_BLOCKING_TASK_EXECUTOR` позволяет переключить стандартный способ выполнения задач запросов `StripedQueryTaskExecutor` в Apache Calcite на общую очередь — `QueryBlockingTaskExecutor`. 

Свойство `IGNITE_CALCITE_USE_QUERY_BLOCKING_TASK_EXECUTOR` позволяет вызывать запросы внутри пользовательских SQL-функций, но уменьшает производительность, поэтому включается опционально (значение по умолчанию — `false`, свойство выключено).
:::

::::{admonition} Пример создания пользовательской SQL-функции и SQL-запроса внутри нее
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
import org.apache.ignite.Ignite;
import org.apache.ignite.IgniteCache;
import org.apache.ignite.Ignition;
import org.apache.ignite.cache.QueryEntity;
import org.apache.ignite.cache.query.SqlFieldsQuery;
import org.apache.ignite.configuration.CacheConfiguration;
import org.apache.ignite.internal.processors.query.QuerySqlFunction;
 
import java.util.Collections;
import java.util.List;
 
public class IgniteUdfExample {
    public static void main(String[] args) {
        // Включите механизм выполнения задач `QueryBlockingTaskExecutor`.
        System.setProperty("IGNITE_CALCITE_USE_QUERY_BLOCKING_TASK_EXECUTOR", "true");
 
        Ignite ignite = Ignition.start();
 
        IgniteUdfExample example = new IgniteUdfExample();
        example.testInnerSql();
        example.testUdfInSql();
    }
 
    // Создайте конфигурацию кеша.
    public CacheConfiguration<Integer, Employer> cacheConfiguration() {
        return new CacheConfiguration<Integer, Employer>()
            .setName("emp4")
            .setSqlFunctionClasses(UserDefinedSqlFunction.class)
            .setSqlSchema("PUBLIC")
            .setQueryEntities(Collections.singletonList(
                new QueryEntity(Integer.class, Employer.class).setTableName("emp4")
            ));
    }
  
    // Создайте кеш и заполните его данными.
    public void testInnerSql() {
        IgniteCache<Integer, Employer> emp4 = ignite.getOrCreateCache(this.cacheConfiguration());
 
        for (int i = 0; i < 100; i++) {
            emp4.put(i, new Employer("Name" + i, (double) i));
        }
    }
 
    public void testUdfInSql() {
        // Создайте кеш.
        IgniteCache<Integer, Employer> emp4 = ignite.getOrCreateCache(this.cacheConfiguration());
 
        // Вызовите SQL-запрос внутри пользовательской SQL-функции.
        SqlFieldsQuery sql = new SqlFieldsQuery("SELECT name, salary(?, key) FROM emp4 WHERE key = ?")
            .setArgs("igniteInstanceName", 1);
 
        List<List<?>> result = emp4.query(sql).getAll();
 
        for (List<?> row : result) {
            System.out.println("Name: " + row.get(0) + ", Salary: " + row.get(1));
        }
    }
 
    // Создайте пользовательскую SQL-функцию.
    public static class UserDefinedSqlFunction {
        @QuerySqlFunction
        public static double salary(String igniteInstanceName, int key) {
            return (double) Ignition.ignite(igniteInstanceName)
                .cache("emp4")
                .query(new SqlFieldsQuery("SELECT salary FROM emp4 WHERE _key = ?").setArgs(key))
                .getAll().get(0).get(0);
        }
    }
 
    // Создайте класс `Employer` для хранения информации о сотрудниках.
    public static class Employer {
        private String name;
        private double salary;
 
        public Employer(String name, double salary) {
            this.name = name;
            this.salary = salary;
        }
 
        public String getName() {
            return name;
        }
 
        public double getSalary() {
            return salary;
        }
    }
}
:::
::::

## Transaction-aware SQL и scan-запросы

DataGrid предоставляет несколько интерфейсов для запросов данных, например:

- Key-Value API;
- SQL;
- scan-запросы (scan queries);
- индексированные scan-запросы (index scan query).

DataGrid поддерживает ACID-транзакции для Key-Value API, но ранее существовало ограничение: изменения, которые внесены в рамках текущей транзакции, не были видны для SQL- и scan-запросов. Это в некоторых случаях приводило к несогласованности данных при выполнении запросов внутри транзакции. Начиная с версии DataGrid 17.5.0 доступны transaction-aware SQL и scan-запросы. Они повышают согласованность и изоляцию при выполнении запросов данных в рамках транзакций.

:::{admonition} Примечание
:class: note

Transaction-aware SQL и scan-запросы в настоящее время поддерживаются только для SQL-движка на основе Apache Calcite и на уровне изоляции `READ_COMMITTED`.
:::

Чтобы включить transaction-aware SQL и scan-запросы, установите свойство `txAwareQueriesEnabled` в конфигурации транзакций (`TransactionConfiguration`). После активации SQL- и scan-запросы будут в реальном времени отражать изменения, которые связаны с транзакциями.

:::{code-block} java
:caption: Пример использования

try (Transaction tx = srv.transactions().txStart(PESSIMISTIC, READ_COMMITTED)) {
    cache.put(1, 2);

    List<List<?>> sqlData = executeSql(srv, "SELECT COUNT(*) FROM TBL.TBL");
    List<Entry<Integer, Integer>> scanData = cache.query(new ScanQuery<Integer, Integer>()).getAll();

    assertEquals("Must see transaction related data", 1L, sqlData.get(0).get(0));
    assertEquals("Must see transaction related data", 1, scanData.size());

    tx.commit();
}
:::

## Справочник по SQL

### DDL

DDL-команды (Data Definition Language, язык описания данных) совместимы со старым движком на основе H2. Подробнее об этом написано в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/sql-reference/ddl).

### DML

Новый SQL-движок в основном наследует синтаксис DML (Data Manipulation Language, язык манипулирования данными) от фреймворка Apache Calcite.

В большинстве случаев синтаксис команд совместим со старым SQL-движком, но есть некоторые отличия между DML-диалектами в движках на основе H2 и Calcite. Например, изменился синтаксис команды `MERGE`. Подробнее об этом написано в [SQL-справочнике Apache Calcite](https://calcite.apache.org/docs/reference.html).

### Поддерживаемые функции

SQL-движок на основе Calcite поддерживает функции:

| Группа | Список функций |
|---|---|
| Агрегатные функции | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `ANY_VALUE`, `LISTAGG`, `GROUP_CONCAT`, `STRING_AGG`, `ARRAY_AGG`, `ARRAY_CONCAT_AGG`, `EVERY`, `SOME` |
| Строковые функции | `UPPER`, `LOWER`, `INITCAP`, `TO_BASE64`, `FROM_BASE64`, `MD5`, `SHA1`, `SUBSTRING`, `LEFT`, `RIGHT`, `REPLACE`, `TRANSLATE`, `CHR`, `CHAR_LENGTH`, `CHARACTER_LENGTH`, `LENGTH`, `CONCAT`, `OVERLAY`, `POSITION`, `ASCII`, `REPEAT`, `SPACE`, `STRCMP`, `SOUNDEX`, `DIFFERENCE`, `REVERSE`, `TRIM`, `LTRIM`, `RTRIM`, `REGEXP_REPLACE` |
| Математические функции | `MOD`, `EXP`, `POWER`, `LN`, `LOG10`, `ABS`, `RAND`, `RAND_INTEGER`, `ACOS`, `ASIN`, `ATAN`, `ATAN2`, `SQRT`, `CBRT`, `COS`, `COSH`, `COT`, `DEGREES`, `RADIANS`, `ROUND`, `SIGN`, `SIN`, `SINH`, `TAN`, `TANH`, `TRUNCATE`, `PI` |
| Функции даты и времени | `EXTRACT`, `FLOOR`, `CEIL`, `TIMESTAMPADD`, `TIMESTAMPDIFF`, `LAST_DATE`, `DAYNAME`, `MONTHNAME`, `DAYOFMONTH`, `DAYOFWEEK`, `DAYOFYEAR`, `YEAR`, `QUARTER`, `MONTH`, `WEEK`, `HOUR`, `MINUTE`, `SECOND`, `TIMESTAMP_SECONDS`, `TIMESTAMP_MILLIS`, `TIMESTAMP_MICROS`, `UNIX_SECONDS`, `UNIX_MILLIS`, `UNIX_MICROS`, `UNIX_DATE`, `DATE_FROM_UNIX_DATE`, `DATE`, `TIME`, `DATETIME`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`, `CURRENT_DATE`, `LOCALTIME`, `LOCALTIMESTAMP` |
| XML-функции | `EXTRACTVALUE`, `XMLTRANSFORM`, `EXTRACT`, `EXISTSNODE` |
| JSON-функции | `JSON_VALUE`, `JSON_QUERY`, `JSON_TYPE`, `JSON_EXISTS`, `JSON_DEPTH`, `JSON_KEYS`, `JSON_PRETTY`, `JSON_LENGTH`, `JSON_REMOVE`, `JSON_STORAGE_SIZE`, `JSON_OBJECT`, `JSON_ARRAY` |
| Другие функции | `ROW`, `CAST`, `COALESCE`, `NVL`, `NULLIF`, `CASE`, `DECODE`, `LEAST`, `GREATEST`, `COMPRESS`, `OCTET_LENGTH`, `TYPEOF`, `QUERY_ENGINE` |

Подробнее о функциях написано в [SQL-справочнике Apache Calcite](https://calcite.apache.org/docs/reference.html).

### Поддерживаемые типы данных

Типы данных, которые поддерживает SQL-движок на основе Calcite:

| Тип данных | Java-класс |
|---|---|
| `BOOLEAN` | `java.lang.Boolean` |
| `DECIMAL` | `java.math.BigDecimal` |
| `DOUBLE` | `java.lang.Double` |
| `REAL/FLOAT` | `java.lang.Float` |
| `INT` | `java.lang.Integer` |
| `BIGINT` | `java.lang.Long` |
| `SMALLINT` | `java.lang.Short` |
| `TINYINT` | `java.lang.Byte` |
| `CHAR/VARCHAR` | `java.lang.String` |
| `DATE` | `java.sql.Date` |
| `TIME` | `java.sql.Time` |
| `TIMESTAMP` | `java.sql.Timestamp` |
| `INTERVAL YEAR TO MONTH` | `java.time.Period` |
| `INTERVAL DAY TO SECOND` | `java.time.Duration` |
| `BINARY/VARBINARY` | `byte[]` |
| `UUID` | `java.util.UUID` |
| `OTHER` | `java.lang.Object` |

## Оптимизация запросов с помощью подсказок

Оптимизатор запросов пытается построить самый быстрый план выполнения, но это возможно сделать не для всех случаев. Пользователь больше знает о структуре данных, архитектуре приложения и распределении данных в кластере. Чтобы сделать оптимизацию более рациональной и быстрее построить план выполнения запросов, можно использовать подсказки (hints) SQL.

:::{admonition} Примечание
:class: note

Подсказки SQL не обязательно использовать, в некоторых случаях их можно пропустить.
:::

### Формат подсказок

Подсказки SQL задаются специальным комментарием `/*+ HINT */`, который называется блоком подсказок. Пробелы до и после названия подсказки обязательны. Блок подсказок размещается сразу после реляционного оператора, обычно после `SELECT`. Несколько блоков для одного реляционного оператора использовать нельзя.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX */ T1.* FROM TBL1 where T1.V1=? and T1.V2=?
:::
::::

Допускается задавать несколько подсказок для одного реляционного оператора. Для этого разделите их запятыми (пробелы необязательны).

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX, EXPAND_DISTINCT_AGG */ SUM(DISTINCT V1), AVG(DISTINCT V2) FROM TBL1 GROUP BY V3 WHERE V3=?
:::
::::

#### Параметры подсказок

Если требуются параметры подсказок, поместите их в скобки после названия подсказки и разделите запятыми.

Параметры можно заключать в кавычки — они становятся чувствительными к регистру. Параметры с кавычками и без них нельзя определить для одной и той же подсказки.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ FORCE_INDEX(TBL1_IDX2,TBL2_IDX1) */ T1.V1, T2.V1 FROM TBL1 T1, TBL2 T2 WHERE T1.V1 = T2.V1 AND T1.V2 > ? AND T2.V2 > ?;
 
SELECT /*+ FORCE_INDEX('TBL2_idx1') */ T1.V1, T2.V1 FROM TBL1 T1, TBL2 T2 WHERE T1.V1 = T2.V1 AND T1.V2 > ? AND T2.V2 > ?;
:::
::::

### Области видимости подсказок

Подсказки определяются для реляционного оператора, обычно для `SELECT`.

Большинство подсказок видны своим реляционным операторам, последующим операторам, запросам и подзапросам. Определенные в подзапросе подсказки видны только ему самому и его подзапросам. Подсказку не видно предыдущему реляционному оператору, если ее определили после него.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX(TBL1_IDX2), FORCE_INDEX(TBL2_IDX2) */ T1.V1 FROM TBL1 T1 WHERE T1.V2 IN (SELECT T2.V2 FROM TBL2 T2 WHERE T2.V1=? AND T2.V2=?);
 
SELECT T1.V1 FROM TBL1 T1 WHERE T1.V2 IN (SELECT /*+ FORCE_INDEX(TBL2_IDX2) */ T2.V2 FROM TBL2 T2 WHERE T2.V1=? AND T2.V2=?);
:::
::::

В примере ниже подсказка есть только у первого запроса:

:::{code-block} sql
:caption: SQL
SELECT /*+ FORCE_INDEX */ V1 FROM TBL1 WHERE V1=? AND V2=?
UNION ALL
SELECT V1 FROM TBL1 WHERE V3>?
:::

Исключение: подсказки уровня движка или оптимизатора, например `DISABLE_RULE` и `QUERY_ENGINE`, нужно определять в начале запроса. Они относятся ко всему запросу.

### Ошибки в подсказках

Оптимизатор пытается применить каждую подсказку и ее параметры, если это возможно. Он пропускает подсказку или параметр, если:

- такой подсказки не существует или она не поддерживается;
- не передали необходимые для подсказки параметры;
- параметры подсказки передали, но она их не поддерживает;
- параметр подсказки некорректен или ссылается на несуществующий объект (например, индекс или таблицу);
- текущая подсказка или ее параметры несовместимы с предыдущими, например принудительное использование и отключение одного и того же индекса.

### Поддерживаемые подсказки

#### FORCE_INDEX

Принудительно использует индексы для сканирования таблиц.

**Параметры:**

- **Пусто** — принудительно использует индексы для сканирования таблиц. Оптимизатор выберет любой доступный индекс.
- **Одно название индекса** — оптимизатор использует указанный индекс.
- **Несколько названий индексов** (могут относиться к разным таблицам) — оптимизатор выберет указанные индексы при сканировании.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ FORCE_INDEX */ T1.* FROM TBL1 T1 WHERE T1.V1 = T2.V1 AND T1.V2 > ?;

SELECT /*+ FORCE_INDEX(TBL1_IDX2, TBL2_IDX1) */ T1.V1, T2.V1 FROM TBL1 T1, TBL2 T2 WHERE T1.V1 = T2.V1 AND T1.V2 > ? AND T2.V2 > ?;
:::
::::

#### NO_INDEX

Отключает сканирование индексов.

**Параметры:**

- **Пусто** — не использовать индексы при сканировании таблиц. Оптимизатор отключит все индексы.
- **Одно название индекса** — оптимизатор пропустит указанный индекс.
- **Несколько названий индексов** (могут относиться к разным таблицам) — оптимизатор пропустит указанные индексы при сканировании.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX */ T1.* FROM TBL1 T1 WHERE T1.V1 = T2.V1 AND T1.V2 > ?;

SELECT /*+ NO_INDEX(TBL1_IDX2, TBL2_IDX1) */ T1.V1, T2.V1 FROM TBL1 T1, TBL2 T2 WHERE T1.V1 = T2.V1 AND T1.V2 > ? AND T2.V2 > ?;
:::
::::

#### ENFORCE_JOIN_ORDER

Устанавливает порядок соединений (`JOIN`), который указан в запросе. Оптимизатор не будет пытаться изменить порядок исполнения. Позволяет ускорить построение плана запроса с большим количеством соединений.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ ENFORCE_JOIN_ORDER */ T1.V1, T2.V1, T2.V2, T3.V1, T3.V2, T3.V3 FROM TBL1 T1 JOIN TBL2 T2 ON T1.V3=T2.V1 JOIN TBL3 T3 ON T2.V3=T3.V1 AND T2.V2=T3.V2

SELECT t1.v1, t3.v2 FROM TBL1 t1 JOIN TBL3 t3 on t1.v3=t3.v3 WHERE t1.v2 in (SELECT /*+ ENFORCE_JOIN_ORDER */ t2.v2 FROM TBL2 t2 JOIN TBL3 t3 ON t2.v1=t3.v1)
:::
::::

#### EXPAND_DISTINCT_AGG

Принудительно разворачивает несколько операций агрегирования с ключевым словом `DISTINCT` через соединения (`JOIN`). Удаляет дубликаты перед объединением (`JOIN`) и ускоряет его.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ EXPAND_DISTINCT_AGG */ SUM(DISTINCT V1), AVG(DISTINCT V2) FROM TBL1 GROUP BY V3
:::
::::

#### QUERY_ENGINE

Выбирает конкретный движок для выполнения отдельных запросов. Указание на уровне движка.

**Параметры:**

Требуется один параметр — название движка.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ QUERY_ENGINE('calcite') */ V1 FROM TBL1
:::
::::

#### DISABLE_RULE

Отключает определенные правила оптимизатора. Указание на уровне оптимизатора.

**Параметры:**

Одно или несколько правил оптимизатора для пропуска.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ DISABLE_RULE('MergeJoinConverter') */ T1.* FROM TBL1 T1 JOIN TBL2 T2 ON T1.V1=T2.V1 WHERE T2.V2=?
:::
::::