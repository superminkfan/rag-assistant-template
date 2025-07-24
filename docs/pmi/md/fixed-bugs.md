# Исправленные ошибки

## Соответствие изменений и тестов для их проверки

Испытания работоспособности изменений в версии Platform V DataGrid 17.5.0 проводятся в порядке и объеме, указанном в таблице.

| Учетный код | Описание | Названия тестов |
| --- | --- | --- |
| SBTSUPPORT-53909 / SBTSUPPORT-8650 | Исправлена проблема с отсутствием синхронизации SQL-схемы на узле при возврате в топологию | [17.5.0 SBTSUPPORT-53909 — Проверка исправления проблемы с отсутствием синхронизации SQL-схемы на узле при возврате в топологию](#1) |
| SBTSUPPORT-56257 / SBTSUPPORT-12072 | Исправлена проблема с дефектом H2 при выполнении `MERGE` | [17.5.0 SBTSUPPORT-56257 — Проверка исправления проблемы с дефектом H2 при выполнении MERGE](#2) |
| SBTSUPPORT-55060 / SBTSUPPORT-10463 | Исправлена проблема с потерей табличных данных | Сценарии проверки данного исправления не предусмотрены |
| SBTSUPPORT-55102 / SBTSUPPORT-10687 | Исправлена проблема с ошибкой `java.lang.AssertionError` при пересоздании кеша | Сценарии проверки данного исправления не предусмотрены |
| SBTSUPPORT-55616 / SBTSUPPORT-11211 | Исправлена проблема с некорректной обработкой исключительной ситуации `CancelledKeyException` | Сценарии проверки данного исправления не предусмотрены |

(1)=
## 17.5.0 SBTSUPPORT-53909 — Проверка исправления проблемы с отсутствием синхронизации SQL-схемы на узле при возврате в топологию

### Шаги проверки

1. **Действие**: Предварительно в конфигурации укажите создание кеша:

   :::{code-block} xml
   :caption: XML
   <bean class="org.apache.ignite.configuration.CacheConfiguration">
       <property name="name" value="CACHEBUG"/>
       <property name="statisticsEnabled" value="true"/>
       <property name="backups" value="1"/>
       <property name="cacheMode" value="PARTITIONED"/>
       <property name="atomicityMode" value="TRANSACTIONAL"/>
   </bean>
   :::

   **Успешный результат**: Узел запущен, при запуске создан кеш.

2. **Действие**: Создайте SQL-таблицу для этого кеша:

   :::{code-block} sql
   :caption: SQL
   CREATE TABLE CACHEBUG (
       id INT PRIMARY KEY,
       name VARCHAR
   ) WITH CACHE_NAME=CACHEBUG;
   :::

   **Успешный результат**: SQL-таблица создана.

3. **Действие**: Перезапустите один из узлов кластера.

   **Успешный результат**: Узел перезапущен и вошел в топологию кластера.

4. **Действие**: Выполните запрос на проверку наличия таблиц: `control.sh --system-view TABLES --all-nodes`.

   **Успешный результат**: По системному представлению видно, что SQL-схема синхронизировалась:

   ```bash
   Command [SYSTEM-VIEW] started
   Arguments: --system-view TABLES --all-nodes
   --------------------------------------------------------------------------------
   Results from node with ID: xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxx
   ---
   cacheGroupId    cacheGroupName    cacheId      cacheName    schemaName    tableName    affinityKeyColumn    keyAlias    valueAlias    keyTypeName          valueTypeName                                               isIndexRebuildInProgress
      xxxxxxxxxx    CACHEBUG          xxxxxxxxxx    CACHEBUG     PUBLIC        CACHEBUG     null                 ID          null          java.lang.Integer    SQL_PUBLIC_CACHEBUG_xxxxxxxxx_xxxx_xxxx_xxxx_xxxxxxxxx    false                  
   ---
 
   Results from node with ID: xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxx
   ---
   cacheGroupId    cacheGroupName    cacheId      cacheName    schemaName    tableName    affinityKeyColumn    keyAlias    valueAlias    keyTypeName          valueTypeName                                               isIndexRebuildInProgress
      xxxxxxxxxx    CACHEBUG          xxxxxxxxx    CACHEBUG     PUBLIC        CACHEBUG     null                 ID          null          java.lang.Integer    SQL_PUBLIC_CACHEBUG_xxxxxxxxx_xxxx_xxxx_xxxx_xxxxxxxxx     false                  
   ---
   ```

(2)=
## 17.5.0 SBTSUPPORT-56257 — Проверка исправления проблемы с дефектом H2 при выполнении MERGE

### Предусловия

Запущенный кластер.

### Шаги проверки

1. **Действие**: Создайте таблицы:

   :::{code-block} sql
   :caption: SQL
   CREATE TABLE City (
       id LONG PRIMARY KEY,
       name VARCHAR
   ) WITH "template=replicated";
   CREATE TABLE Person (
       id LONG,
       city_id LONG,
       name VARCHAR,
    PRIMARY KEY (id, city_id)
   ) WITH "template=partitioned, backups=1, affinity_key=city_id";
   CREATE TABLE PersonStaging (
       id LONG,
       city_id LONG,
       name VARCHAR,
       PRIMARY KEY (id, city_id)
   ) WITH "template=partitioned, backups=1, affinity_key=city_id";
   :::

   **Успешный результат**: Таблицы созданы.

2. **Действие**: Добавьте в таблицы тестовые данные:

   :::{code-block} sql
   :caption: SQL
   INSERT INTO City (id, name) VALUES (1, 'Forest Hill');
   INSERT INTO City (id, name) VALUES (2, 'Denver');
   INSERT INTO City (id, name) VALUES (3, 'St. Petersburg');
   INSERT INTO Person (id, city_id, name) VALUES (1, 3, 'John Doe');
   INSERT INTO Person (id, city_id, name) VALUES (2, 2, 'Jane Roe');
   INSERT INTO Person (id, city_id, name) VALUES (3, 1, 'Mary Major');
   INSERT INTO Person (id, city_id, name) VALUES (4, 2, 'Richard Miles');
   INSERT INTO PersonStaging (id, city_id, name) VALUES (2, 1, 'Jane Smith');
   INSERT INTO PersonStaging (id, city_id, name) VALUES (5, 3, 'Samuel Green');
   :::

   **Успешный результат**: Данные добавлены.

3. **Действие**: Выполните операцию `MERGE`:

   :::{code-block} sql
   :caption: SQL
   MERGE INTO Person (id, city_id, name)
   (
       SELECT id, city_id, name FROM PersonStaging
   );  
   :::

   **Успешный результат**: В лог не попадают данные из запроса:

   ```bash
   YYYY-MM-DD 13:36:11.957 [WARN ][client-connector-#77][org.apache.ignite.internal.processors.query.running.HeavyQueriesTracker] Long running query is finished [globalQueryId=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx_xx, duration=41ms, type=DML, schema=PUBLIC, sql='MERGE INTO Person (id, city_id, name)
   (
       SELECT id, city_id, name FROM PersonStaging
   )']
   ```