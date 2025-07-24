# Работа с SQL и Apache Calcite

## Конфигурация

### Режим Standalone

При запуске кластера в режиме Standalone до запуска скрипта `ignite.sh` или `ignite.bat` переместите подкаталоги `optional/ignite-calcite` и `optional/ignite-slf4j` в каталог `libs`. В этом случае контент папки, в которой находится модуль, добавится к classpath.

### Конфигурация Maven

Если для управления зависимостями в вашем проекте вы используете Maven, добавьте следующую зависимость (замените параметр `${ignite.version}` на необходимую вам версию DataGrid).

:::{code-block} xml
:caption: XML
<dependency>
    <groupId>com.sbt.ignite</groupId>
    <artifactId>ignite-calcite</artifactId>
    <version>${ignite.version}</version>
</dependency>
:::

### Конфигурация SQL-движков

Чтобы включить SQL-движок, явно добавьте экземпляр `CalciteQueryEngineConfiguration` в свойство `SqlConfiguration.QueryEnginesConfiguration`.

Ниже приведен пример конфигурации двух SQL-движков (H2 и Calcite), где движок на Calcite является движком по умолчанию:

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

### Направление запросов в SQL-движок

Обычно все запросы направляются в SQL-движок, сконфигурированный по умолчанию. Если в `queryEnginesConfiguration` сконфигурировано более одного движка, конкретный движок для исполнения отдельных запросов или для всего соединения можно выбрать при конфигурировании способа подключения к базе.

#### JDBC

Используйте параметр `queryEngine` для выбора SQL-движка для JDBC-соединения.

:::{admonition} Пример
:class: hint

```text
jdbc:ignite:thin://xxx.x.x.x:10800?queryEngine=calcite
```

где `queryEngine=calcite` — используемый движок.
:::

#### ODBC

Для ODBC-соединения SQL-движок можно сконфигурировать при помощи свойства `QUERY_ENGINE`.

:::{admonition} Пример
:class: hint

```text
[IGNITE_CALCITE]
DRIVER={Apache Ignite};
SERVER=xxx.x.x.x;
PORT=10800;
SCHEMA=PUBLIC;
QUERY_ENGINE=CALCITE
```
:::

#### Подсказка QUERY_ENGINE

Используйте подсказку `QUERY_ENGINE`, чтобы выбрать определенный движок для отдельных запросов.

:::{code-block} sql
:caption: SQL
SELECT /*+ QUERY_ENGINE('calcite') */ fld FROM table;
:::

### SQL Reference

#### DDL

DDL-команды (Data Definition Language, язык описания данных) совместимы со старым движком на основе H2.

#### DML

Новый SQL-движок наследует в основном синтаксис DML (Data Manipulation Language, язык манипулирования данными) от фреймворка Apache Calcite framework.

В большинстве случаев синтаксис команд совместим со старым SQL-движком. Но существуют и некоторые различия между DML-диалектами в движке на основе H2 и движке на основе Calcite. Например, изменился синтаксис команды MERGE.

Для получения дополнительной информации обратитесь к [SQL-справочнику Apache Calcite](https://calcite.apache.org/docs/reference.html).

#### Поддерживаемые функции

SQL-движок на основе Calcite на данный момент поддерживает:

| Группа | Список функций |
|---|---|
| Агрегатные функции | `COUNT, SUM, AVG, MIN, MAX, ANY_VALUE` |
| Строковые функции | `UPPER, LOWER, INITCAP, TO_BASE64, FROM_BASE64, MD5, SHA1, SUBSTRING, LEFT, RIGHT, REPLACE, TRANSLATE, CHR, CHAR_LENGTH, CHARACTER_LENGTH, LENGTH, CONCAT, OVERLAY, POSITION, ASCII, REPEAT, SPACE, STRCMP, SOUNDEX, DIFFERENCE, REVERSE, TRIM, LTRIM, RTRIM, REGEXP_REPLACE` |
| Математические функции | `MOD, EXP, POWER, LN, LOG10, ABS, RAND, RAND_INTEGER, ACOS, ASIN, ATAN, ATAN2, SQRT, CBRT, COS, COSH, COT, DEGREES, RADIANS, ROUND, SIGN, SIN, SINH, TAN, TANH, TRUNCATE, PI` |
| Функции даты и времени | `EXTRACT, FLOOR, CEIL, TIMESTAMPADD, TIMESTAMPDIFF, LAST_DATE, DAYNAME, MONTHNAME, DAYOFMONTH, DAYOFWEEK, DAYOFYEAR, YEAR, QUARTER, MONTH, WEEK, HOUR, MINUTE, SECOND, TIMESTAMP_SECONDS, TIMESTAMP_MILLIS, TIMESTAMP_MICROS, UNIX_SECONDS, UNIX_MILLIS, UNIX_MICROS, UNIX_DATE, DATE_FROM_UNIX_DATE, DATE, CURRENT_TIME, CURRENT_TIMESTAMP, CURRENT_DATE, LOCALTIME, LOCALTIMESTAMP` |
| XML-функции | `EXTRACTVALUE, XMLTRANSFORM, EXTRACT, EXISTSNODE` |
| JSON-функции | `JSON_VALUE, JSON_QUERY, JSON_TYPE, JSON_EXISTS, JSON_DEPTH, JSON_KEYS, JSON_PRETTY, JSON_LENGTH, JSON_REMOVE, JSON_STORAGE_SIZE, JSON_OBJECT, JSON_ARRAY` |
| Другие функции | `ROW, CAST, COALESCE, NVL, NULLIF, CASE, DECODE, LEAST, GREATEST, COMPRESS, OCTET_LENGTH, TYPEOF, QUERY_ENGINE` |

Дополнительную информацию по этим функциям смотрите в справочнике по [Apache Calcite SQL](https://calcite.apache.org/docs/reference.html#operators-and-functions).

#### Поддерживаемые типы данных

Ниже приведены типы данных, поддерживаемые SQL-движком на основе Calcite:

| Тип данных | Java класс |
|---|---|
| BOOLEAN | `java.lang.Boolean` |
| DECIMAL | `java.math.BigDecimal` |
| DOUBLE | `java.lang.Double` |
| REAL/FLOAT | `java.lang.Float` |
| INT | `java.lang.Integer` |
| BIGINT | `java.lang.Long` |
| SMALLINT | `java.lang.Short` |
| TINYINT | `java.lang.Byte` |
| CHAR/VARCHAR | `java.lang.String` |
| DATE | `java.sql.Date` |
| TIME | `java.sql.Time` |
| TIMESTAMP | `java.sql.Timestamp` |
| INTERVAL YEAR TO MONTH | `java.time.Period` |
| INTERVAL DAY TO SECOND | `java.time.Duration` |
| BINARY/VARBINARY | `byte[]` |
| UUID | `java.util.UUID` |
| OTHER | `java.lang.Object` |

## Оптимизация запросов с помощью подсказок (hints)

Оптимизатор запросов делает все возможное, чтобы построить самый быстрый план выполнения. Однако существующий оптимизатор запросов не может быть одинаково эфффективным для всех возможных случаев. Пользователь больше знает о структуре данных, архитектуре приложения или распределении данных в кластере. Подсказки (hints) SQL могут помочь оптимизатору сделать оптимизацию более рациональной или построить план выполнения быстрее.

:::{admonition} Примечание
:class: note

Подсказки SQL необязательны для использования и могут быть пропущены в некоторых случаях.
:::

### Формат подсказок

Подсказки SQL задаются специальным комментарием `/*+ HINT */`, называемым блоком подсказки. Пробелы перед и после имени подсказки обязательны. Блок подсказки размещается сразу после реляционного оператора, чаще всего после `SELECT`. Несколько блоков подсказок для одного реляционного оператора не допускаются.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX */ T1.* FROM TBL1 where T1.V1=? and T1.V2=?
:::
::::

Допускается задавать несколько подсказок для одного и того же реляционного оператора. Чтобы использовать несколько подсказок, разделите их запятыми (пробелы необязательны).

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX, EXPAND_DISTINCT_AGG */ SUM(DISTINCT V1), AVG(DISTINCT V2) FROM TBL1 GROUP BY V3 WHERE V3=?
:::
::::

#### Параметры подсказок

Параметры подсказки, если они требуются, помещаются в скобки после имени подсказки и разделяются запятыми.

Параметр подсказки может быть заключен в кавычки. Параметр в кавычках чувствителен к регистру. Параметры с кавычками и без кавычек не могут быть определены для одной и той же подсказки.

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

Большинство подсказок видны для своих реляционных операторов, для низлежащих операторов, запросов и подзапросов. Подсказки, определенные в подзапросе, видны только для этого подзапроса и его подзапросов. Подсказка не видна для вышележащего реляционного оператора, если она определена после него.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX(TBL1_IDX2), FORCE_INDEX(TBL2_IDX2) */ T1.V1 FROM TBL1 T1 WHERE T1.V2 IN (SELECT T2.V2 FROM TBL2 T2 WHERE T2.V1=? AND T2.V2=?);

SELECT T1.V1 FROM TBL1 T1 WHERE T1.V2 IN (SELECT /*+ FORCE_INDEX(TBL2_IDX2) */ T2.V2 FROM TBL2 T2 WHERE T2.V1=? AND T2.V2=?);
:::
::::

Обратите внимание, что только первый запрос имеет подсказку в следующем случае:

:::{code-block} sql
:caption: SQL
SELECT /*+ FORCE_INDEX */ V1 FROM TBL1 WHERE V1=? AND V2=?
UNION ALL
SELECT V1 FROM TBL1 WHERE V3>?
:::

**Исключение:** подсказки уровня движка или оптимизатора, такие как `DISABLE_RULE` или `QUERY_ENGINE`, должны быть определены в начале запроса и относятся ко всему запросу.

### Ошибки в подсказках

Оптимизатор пытается применить каждую подсказку и ее параметры, если это возможно. Но он пропускает подсказку или параметр подсказки, если:

-   не существует такой поддерживаемой подсказки;
-   необходимые параметры подсказки не переданы;
-   параметры подсказки были переданы, но подсказка не поддерживает какой-либо параметр;
-   параметр подсказки неверен или ссылается на несуществующий объект, например, несуществующий индекс или таблицу;
-   текущая подсказка или текущие параметры несовместимы с предыдущими, например, принудительное использование и отключение одного и того же индекса.

### Поддерживаемые подсказки

#### FORCE_INDEX

Принудительно заставляет использовать индексы для сканирования таблиц.

**Параметры:**

-   **пусто** — принудительное использование индексов для сканирования таблиц. Оптимизатор выберет любой доступный индекс;
-   **одно имя индекса** — оптимизатор использует указанный индекс;
-   **несколько имен индексов** (могут относиться к разным таблицам) — оптимизатор выберет указанные индексы при сканировании.

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

-   **пусто** — не использовать индексы при сканировании таблиц. Оптимизатор отключит все индексы;
-   **одно имя индекса** — оптимизатор пропустит указанный индекс;
-   **несколько имен индексов** (могут относиться к разным таблицам) — оптимизатор пропустит указанные индексы при сканировании.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ NO_INDEX */ T1.* FROM TBL1 T1 WHERE T1.V1 = T2.V1 AND T1.V2 > ?;

SELECT /*+ NO_INDEX(TBL1_IDX2, TBL2_IDX1) */ T1.V1, T2.V1 FROM TBL1 T1, TBL2 T2 WHERE T1.V1 = T2.V1 AND T1.V2 > ? AND T2.V2 > ?;
:::
::::

#### ENFORCE_JOIN_ORDER

Устанавливает порядок соединений (`JOIN`) в запросе. Ускоряет построение плана запроса, включающего много соединений.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ ENFORCE_JOIN_ORDER */ T1.V1, T2.V1, T2.V2, T3.V1, T3.V2, T3.V3 FROM TBL1 T1 JOIN TBL2 T2 ON T1.V3=T2.V1 JOIN TBL3 T3 ON T2.V3=T3.V1 AND T2.V2=T3.V2

SELECT t1.v1, t3.v2 FROM TBL1 t1 JOIN TBL3 t3 on t1.v3=t3.v3 WHERE t1.v2 in (SELECT /*+ ENFORCE_JOIN_ORDER */ t2.v2 FROM TBL2 t2 JOIN TBL3 t3 ON t2.v1=t3.v1)
:::
::::

#### EXPAND_DISTINCT_AGG

Принудительно разворачивает несколько операций агрегации с ключевым словом `DISTINCT` через соединения (`JOIN`).

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ EXPAND_DISTINCT_AGG */ SUM(DISTINCT V1), AVG(DISTINCT V2) FROM TBL1 GROUP BY V3
:::
::::

#### QUERY_ENGINE

Выбор конкретного движка для выполнения отдельных запросов. Подсказка на уровне движка.

**Параметры:**

Требуется один параметр — имя движка.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ QUERY_ENGINE('calcite') */ V1 FROM TBL1
:::
::::

#### DISABLE_RULE

Отключает определенные правила оптимизатора. Подсказка на уровне оптимизатора.

**Параметры:**

Одно или несколько правил оптимизатора для пропуска.

::::{admonition} Пример
:class: hint

:::{code-block} sql
:caption: SQL
SELECT /*+ DISABLE_RULE('MergeJoinConverter') */ T1.* FROM TBL1 T1 JOIN TBL2 T2 ON T1.V1=T2.V1 WHERE T2.V2=?
:::
::::

## SQL-статистика

DataGrid может вычислять статистику и использовать ее для построения оптимального плана выполнения SQL-запроса. На основании статистики оптимизатор решает, как он будет выполнять SQL-запрос, будет ли использоваться индекс, и если да — какой. Это позволяет значительно ускорить выполнение запроса.

Без статистики планировщик выполнения SQL-запросов пытается угадать избирательность условий запроса с помощью только общих эвристических методов. Чтобы получить более точные планы:

1. Убедитесь, что статистика [включена](#sql-statistic-on).
2. Настройте сбор статистики для таблиц, которые участвуют в запросе. Подробный пример описан ниже в разделе [«Получение наиболее эффективного плана выполнения с помощью статистики»](#получение-наиболее-эффективного-плана-выполнения-с-помощью-статистики).

Статистика проверяется и обновляется каждый раз после выполнения одного из следующих действий:

- запуск узла;
- изменение топологии;
- изменение конфигурации.

Узел проверяет разделы и собирает по каждому из них статистику, которую можно использовать для оптимизации SQL-запросов.

### Включение статистики

SQL-статистика включена по умолчанию. Статистика хранится локально, а параметры ее конфигурации — по всему кластеру. Чтобы просмотреть состояние использования статистики, выполните команду:

(sql-statistic-check)=
```bash
$ ./control.sh --property get --name 'statistics.usage.state'
```

(sql-statistic-on)=
Чтобы включить или отключить статистику при использовании кластера, выполните следующую команду и укажите значение `ON`, `OFF` или `NO_UPDATE`:

```bash
control.sh --property set --name 'statistics.usage.state' --val 'ON'
```

Можно задать значения по умолчанию для распределенных свойств (properties) на уровне конфигурации DataGrid. Эта функциональность будет полезной при использовании in-memory-кластеров.

::::{admonition} Пример задания значения с помощью конфигурации DataGrid
:class: hint

:::{code-block} xml
:caption: XML
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="DistributedPropertiesDefaultValues">
            <map>
                <entry key="statistics.usage.state" value="ON"/>
            </map>
        </property>
    </bean>
:::
::::

Чтобы проверить значение после запуска, используйте `statistics.usage.state` — подробнее указано [выше](#sql-statistic-check).

:::{admonition} Пример вывода
:class: hint
```bash
Command [PROPERTY] started
Arguments: --property get --name statistics.usage.state
--------------------------------------------------------------------------------
statistics.usage.state = ON
Command [PROPERTY] finished with code: 0
```
:::

### Устаревание статистики

У каждой партиции есть специальный счетчик для отслеживания общего количества измененных строк (добавленных, удаленных или обновленных). Если общее количество измененных строк превышает значение `MAX_CHANGED_PARTITION_ROWS_PERCENT`, партиция анализируется повторно. После этого узел заново собирает статистику.

Чтобы настроить параметр `MAX_CHANGED_PARTITION_ROWS_PERCENT`, повторно запустите команду `ANALYZE` с требуемым значением параметра. По умолчанию используется параметр `DEFAULT_OBSOLESCENCE_MAX_PERCENT = 15`. Эти параметры применяются ко всем указанным объектам.

:::{admonition} Примечание
:class: note
Поскольку статистические данные собираются с помощью полного сканирования каждой партиции, рекомендуется отключить функциональность устаревания статистики при работе с небольшим количеством изменяющихся строк. Это особенно актуально в случае работы с большими объемами данных, когда полное сканирование может привести к снижению производительности.

Когда данные меняются, статистику нужно пересобирать. Если сбор статистики [включен](#sql-statistic-on), она будет пересобираться автоматически при достижении установленного `MAX_CHANGED_PARTITION_ROWS_PERCENT` (по умолчанию 15%).
:::

Чтобы сэкономить ресурсы процессора (CPU) при отслеживании устаревания, используйте состояние `NO_UPDATE`:

```bash
control.sh --property set --name 'statistics.usage.state' --val 'NO_UPDATE'
```

### Получение наиболее эффективного плана выполнения с помощью статистики

Пример получения оптимизированного плана выполнения для базового запроса:

1. Создайте таблицу и добавьте в нее данные:

   :::{code-block} sql
   :caption: SQL
   CREATE TABLE statistics_test(col1 int PRIMARY KEY, col2 varchar, col3 date);

   INSERT INTO statistics_test(col1, col2, col3) VALUES(1, 'val1', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(2, 'val2', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(3, 'val3', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(4, 'val4', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(5, 'val5', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(6, 'val6', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(7, 'val7', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(8, 'val8', 'YYYY-MM-DD');
   INSERT INTO statistics_test(col1, col2, col3) VALUES(9, 'val9', 'YYYY-MM-DD');
   :::

2. Создайте индексы для каждого столбца:

   :::{code-block} sql
   :caption: SQL
   CREATE INDEX st_col1 ON statistics_test(col1);
   CREATE INDEX st_col2 ON statistics_test(col2);
   CREATE INDEX st_col3 ON statistics_test(col3);
   :::

3. Получите план выполнения для базового запроса:

   :::{admonition} Примечание
   :class: note
   Значение `col2` меньше максимального значения в таблице, а значение `col3` выше максимального. Весьма вероятно, что второе условие не вернет результат, что повышает его избирательность. Поэтому в базе данных следует использовать индекс `st_col3`.
   :::

   :::{code-block} sql
   :caption: SQL
   EXPLAIN SELECT * FROM statistics_test WHERE col2 > 'val2' AND col3 > 'YYYY-MM-DD'

   SELECT
   "__Z0"."COL1" AS "__C0_0",
   "__Z0"."COL2" AS "__C0_1",
   "__Z0"."COL3" AS "__C0_2"
   FROM "PUBLIC"."STATISTICS_TEST" "__Z0"
   /* PUBLIC.ST_COL2: COL2 > 'val2' */
   WHERE ("__Z0"."COL2" > 'val2')
   AND ("__Z0"."COL3" > DATE ‘YYYY-MM-DD’)
   :::

   Без собранной статистики в базе данных недостаточно информации для выбора правильного индекса (поскольку у обоих индексов одинаковая избирательность с точки зрения планировщика). Эта проблема устраняется в шагах ниже.

4. Соберите статистику для таблицы `statistics_test`:

   :::{code-block} sql
   :caption: SQL
   ANALYZE statistics_test;
   :::

5. Снова получите план выполнения и убедитесь, что выбран индекс `st_col3`:

   :::{code-block} sql
   :caption: SQL
   EXPLAIN SELECT * FROM statistics_test WHERE col2 > 'val2' AND col3 > 'YYYY-MM-DD'

   SELECT
   "__Z0"."COL1" AS "__C0_0",
   "__Z0"."COL2" AS "__C0_1",
   "__Z0"."COL3" AS "__C0_2"
   FROM "PUBLIC"."STATISTICS_TEST" "__Z0"
   /* PUBLIC.ST_COL3: COL3 > DATE ‘YYYY-MM-DD’ */
   WHERE ("__Z0"."COL2" > 'val2')
   AND ("__Z0"."COL3" > DATE ‘YYYY-MM-DD’)
   :::

### Обновление статистики

Собранные значения можно обновить — для этого укажите дополнительные параметры в команде `ANALYZE`. Указанные значения обновляют данные, которые собраны по одному на каждом узле в системном представлении `STATISTICS_LOCAL_DATA` (эти данные используются оптимизатором SQL-запросов), но не в `STATISTICS_PARTITION_DATA` (сохраняет реальную статистическую информацию по разделам). После этого оптимизатор SQL-запросов использует обновленные значения.

Подробнее о системных представлениях написано в разделе «События мониторинга»: [STATISTICS_LOCAL_DATA](../../administration-guide/md/monitoring-events.md#statistics_local_data) и [STATISTICS_PARTITION_DATA](../../administration-guide/md/monitoring-events.md#statistics_partition_data).

Каждая команда `ANALYZE` обновляет все такие значения для своих объектов. Например, если уже есть обновленное значение `TOTAL` и нужно обновить значение `DISTINCT`, используйте оба параметра в одной команде `ANALYZE`. Чтобы задать разные значения для разных столбцов, используйте несколько команд `ANALYZE` следующим образом:

:::{code-block} sql
:caption: SQL
ANALYZE MY_TABLE(COL_A) WITH 'DISTINCT=5,NULLS=6';
ANALYZE MY_TABLE(COL_B) WITH 'DISTINCT=500,NULLS=1000,TOTAL=10000';
:::