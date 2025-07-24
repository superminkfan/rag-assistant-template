# Тонкий клиент Java

Тонкий клиент Java — легковесный клиент DataGrid, который подключается к кластеру по стандартному сокетному соединению. Он не является частью топологии кластера, не хранит данные и не используется в качестве пункта назначения для вычислений при использовании DataGrid в качестве Compute Grid. Тонкий клиент устанавливает сокетное соединение с серверным узлом DataGrid и выполняет все операции через него. Тонкие клиенты основаны на протоколе [Binary Client](binary_client_protocol.md), который позволяет поддерживать подключение к DataGrid с любого языка программирования.

## Установка

Если в приложении используются Maven или Gradle, добавьте в него зависимость `ignite-core`:

::::{md-tab-set}
:::{md-tab-item} Maven
```bash
<properties>
    <ignite.version>18.0.0</ignite.version>
</properties>

<dependencies>
    <dependency>
        <groupId>com.sbt.ignite</groupId>
        <artifactId>ignite-core</artifactId>
        <version>${ignite.version}</version>
    </dependency>
</dependencies>
```
:::

:::{md-tab-item} Gradle
```bash
def igniteVersion = '18.0.0'

dependencies {
    compile group: 'com.sbt.ignite', name: 'ignite-core', version: igniteVersion
}
```
:::
::::

В качестве альтернативы можно использовать библиотеку `ignite-core-18.0.0.jar` из дистрибутива DataGrid.

## Подключение к кластеру

Чтобы инициировать тонкий клиент, используйте метод `Ignition.startClient(ClientConfiguration)`. Он принимает объект `ClientConfiguration`, который определяет параметры подключения клиента.

Метод возвращает интерфейс `IgniteClient`, который обеспечивает различные методы доступа к данным. `IgniteClient` — auto-closeable (автоматически закрывающийся) ресурс. Чтобы закрыть тонкий клиент и освободить связанные с подключением ресурсы, используйте конструкцию `try-with-resources`.

:::{code-block} java
:caption: Java
ClientConfiguration cfg = new ClientConfiguration().setAddresses("xxx.x.x.x:10800");
try (IgniteClient client = Ignition.startClient(cfg)) {
    ClientCache<Integer, String> cache = client.cache("myCache");
    // Получите данные из кеша.
}
:::

Можно указывать адреса нескольких узлов. В этом случае тонкий клиент пытается подключиться ко всем серверам из списка в случайном порядке. Если все серверы недоступны, клиент сгенеририует исключение `ClientConnectionException`.

:::{code-block} java
:caption: Java
try (IgniteClient client = Ignition.startClient(new ClientConfiguration().setAddresses("node1_address:10800",
        "node2_address:10800", "node3_address:10800"))) {
} catch (ClientConnectionException ex) {
    // Все серверы недоступны.
}
:::

Код выше обеспечивает отказоустойчивый механизм для случаев сбоя серверного узла. Подробнее об этом написано ниже в разделе [«Поведение при сбоях узлов»](#поведение-при-сбоях-узлов).

## Partition Awareness

Функция Partition Awareness позволяет тонкому клиенту отправлять запросы напрямую узлу, который содержит нужные данные. Без этой функции приложение, которое подключено к кластеру с помощью тонкого клиента, выполняет все запросы и операции на одном серверном узле (он служит прокси-сервером для входящих запросов). Затем эти операции перенаправляются на узел, где хранятся нужные данные. Это приводит к возникновению узкого места, которое может помешать линейному масштабированию приложения.

Запросы должны проходить через прокси-сервер, откуда они перенаправляются на корректный узел:

![Partition-awareness-off](./resources/partition-awareness-off.png)

С функцией Partition Awareness тонкий клиент может напрямую отправлять запросы основным узлам, где хранятся нужные данные. Функция устраняет узкое место и позволяет приложению проще масштабироваться:

![Partition-awareness-on](./resources/partition-awareness-on.png)

Partition Awareness помогает избежать дополнительного сетевого перехода в следующих сценариях:

1. API операций с одним ключом, например `put()`, `get()` и так далее. Partition Awareness никак не влияет на эти операции внутри явных транзакций, которые инициируются с помощью `ClientTransaction#txStart()`. Подробнее об этом написано ниже в разделе [«Транзакции»](#транзакции).
2. Scan queries и index queries принимают номер партиции в качестве параметра, с помощью которого запрос направляется определенному серверному узлу с нужными данными. Подробнее об этом написано ниже в разделе [«Выполнение Scan Queries»](#выполнение-scan-queries) и в подразделе [«Использование Cache Queries»](using_cache_queries.md) раздела «Использование Key-Value API».

::::{admonition} Пример, как использовать функцию Partition Awareness в тонком клиенте Java
:class: hint
:collapsible:

:::{code-block} java
:caption: Java
ClientConfiguration cfg = new ClientConfiguration()
        .setAddresses("node1_address:10800", "node2_address:10800", "node3_address:10800")
        .setPartitionAwarenessEnabled(true);

try (IgniteClient client = Ignition.startClient(cfg)) {
    ClientCache<Integer, String> cache = client.cache("myCache");
    // Получите, поместите или удалите данные из кеша.
    cache.put(0, "Hello, world!");
    // Номер партиции можно также указать с помощью `IndexQuery#setPartition(Integer)`.
    ScanQuery scanQuery = new ScanQuery().setPartition(part);
} catch (ClientException e) {
    System.err.println(e.getMessage());
}
:::
::::

Пример использования пользовательского ключа кеша для функции маппинга партиций, чтобы включить Affinity Awareness на стороне тонкого клиента, если кеш уже существует в кластере или его создали с помощью пользовательских функций `AffinityFunction` и `AffinityKeyMapper`:

::::{admonition} Пример
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
// Функция Partition Awareness включена по умолчанию.
ClientConfiguration cfg = new ClientConfiguration()
    .setAddresses("node1_address:10800", "node2_address:10800", "node3_address:10800")
    .setPartitionAwarenessMapperFactory(new ClientPartitionAwarenessMapperFactory() {
        /** {@inheritDoc} */
        @Override public ClientPartitionAwarenessMapper create(String cacheName, int partitions) {
            AffinityFunction aff = new RendezvousAffinityFunction(false, partitions);

            return aff::partition;
        }
    })

try (IgniteClient client = Ignition.startClient(cfg)) {
    ClientCache<Integer, String> cache = client.cache(PART_CUSTOM_AFFINITY_CACHE_NAME);
    // Получите, поместите или удалите данные из кеша. Функция Partition Awareness будет включена.
}
catch (ClientException e) {
    System.err.println(e.getMessage());
}
:::
::::

Если список серверных узлов динамически меняется или масштабируется, можно настроить подключение с помощью пользовательской реализации `ClientAddressFinder`. Она должна предоставлять количество действующих адресов сервера каждый раз, когда клиент их запрашивает. 

::::{admonition} Пример, как использовать `ClientAddressFinder`
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
ClientAddressFinder finder = () -> {
    String[] dynamicServerAddresses = fetchServerAddresses();

    return dynamicServerAddresses;
};

ClientConfiguration cfg = new ClientConfiguration()
    .setAddressesFinder(finder)
    .setPartitionAwarenessEnabled(true);

try (IgniteClient client = Ignition.startClient(cfg)) {
    ClientCache<Integer, String> cache = client.cache("myCache");
    // Получите, поместите или удалите данные из кеша.
} catch (ClientException e) {
    System.err.println(e.getMessage());
}
:::
::::

Фрагмент кода выше показывает, как может выглядеть реализация, чтобы клиенты получали адреса сервера динамически:

- `ClientAddressFinder` — функциональный интерфейс, который предоставляет только метод `getAddresses()`.
- `fetchServerAddress()` — пользовательская функция, которая динамически предоставляет адреса сервера.
- `ClientConfiguration.setAddressFinder(finder)` — конфигурация клиента.

## Использование Key-Value API

Тонкий клиент Java поддерживает большинство операций типа «ключ-значение», которые доступны в толстом клиенте. Чтобы выполнить операции «ключ-значение» в определенном кеше, получите его экземпляр и используйте один из его методов.

### Получение экземпляра кеша

Интерфейс `ClientCache` предоставляет Key-Value API. Чтобы получить экземпляр `ClientCache`, используйте методы:

- `IgniteClient.cache(String)` предполагает, что кеш с указанным именем существует. Метод не взаимодействует с кластером, чтобы проверить, что такой кеш существует. Если его не существует, последующие операции кеширования завершаются неудачей.
- `IgniteClient.getOrCreateCache(String)`, `IgniteClient.getOrCreateCache(ClientCacheConfiguration)` получают существующий кеш с указанным именем или создают кеш, если его не существует. Первая операция создает кеш с конфигурацией по умолчанию.
- `IgniteClient.createCache(String)`, `IgniteClient.createCache(ClientCacheConfiguration)` создают кеш с указанным именем и завершаются неудачей, если он уже существует.

Чтобы просмотреть все существующие кеши, используйте `IgniteClient.cacheNames()`:

:::{code-block} java
:caption: Java
ClientCacheConfiguration cacheCfg = new ClientCacheConfiguration().setName("References")
        .setCacheMode(CacheMode.REPLICATED)
        .setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);

ClientCache<Integer, String> cache = client.getOrCreateCache(cacheCfg);
:::

### Основные операции кеша

::::{admonition} Пример, как выполнять основные операции кеша из тонкого клиента
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
Map<Integer, String> data = IntStream.rangeClosed(1, 100).boxed()
        .collect(Collectors.toMap(i -> i, Object::toString));

cache.putAll(data);

assert !cache.replace(1, "2", "3");
assert "1".equals(cache.get(1));
assert cache.replace(1, "1", "3");
assert "3".equals(cache.get(1));

cache.put(101, "101");

cache.removeAll(data.keySet());
assert cache.size() == 1;
assert "101".equals(cache.get(101));

cache.removeAll();
assert 0 == cache.size();
:::
::::

### Выполнение Scan Queries

Используйте класс `ScanQuery<K, V>`, чтобы получить набор записей, которые соответствуют заданному условию. Тонкий клиент отправляет запрос узлу кластера, где он выполняется как обычный запрос сканирования. Подробнее об этом написано в подразделе [«Использование Cache Queries»](using_cache_queries.md).

Условие запроса задает объект `IgniteBiPredicate<K, V>`, который передается конструктору запроса в качестве аргумента. Предикат применяется на стороне сервера. Если предикат не указан, запрос возвращает все записи кеша.

:::{admonition} Важно
:class: attention

Классы предикатов должны быть доступны на серверных узлах кластера.
:::

Результаты запроса передаются клиенту постранично. Каждая страница содержит определенное количество записей и передается клиенту только тогда, когда запрашиваются ее записи. Чтобы изменить количество записей на странице, используйте метод `ScanQuery.setPageSize(int pageSize)` (значение по умолчанию — 1024):

:::{code-block} java
:caption: Java
ClientCache<Integer, Person> personCache = client.getOrCreateCache("personCache");

Query<Cache.Entry<Integer, Person>> qry = new ScanQuery<Integer, Person>(
        (i, p) -> p.getName().contains("Smith"));

try (QueryCursor<Cache.Entry<Integer, Person>> cur = personCache.query(qry)) {
    for (Cache.Entry<Integer, Person> entry : cur) {
        // Обработать запись.
    }
}
:::

Метод `IgniteClient.query(…​)` возвращает экземпляр `FieldsQueryCursor`. Всегда закрывайте курсор после получения всех экземпляров.

### Транзакции

Клиентские транзакции поддерживаются для кешей с режимом `AtomicityMode.TRANSACTIONAL`.

#### Выполнение транзакций

Чтобы запустить транзакцию, получите объект `ClientTransactions` из `IgniteClient`. В `ClientTransactions` есть несколько методов `txStart(…​)`. Каждый из них запускает новую транзакцию и возвращает объект `ClientTransaction`, который представляет транзакцию. Используйте этот объект, чтобы выполнить коммит (commit) или rollback транзакции.

:::{code-block} java
:caption: Java
ClientCache<Integer, String> cache = client.cache("my_transactional_cache");

ClientTransactions tx = client.transactions();

try (ClientTransaction t = tx.txStart()) {
    cache.put(1, "new value");

    t.commit();
}
:::

#### Конфигурация транзакций

У клиентских транзакций могут быть разные режимы параллелизма (concurrency), уровни изоляции и тайм-ауты выполнения, которые можно установить сразу для всех для транзакций или отдельно для каждой. Подробнее о режимах параллелизма и уровнях изоляции написано в разделе [«Выполнение транзакций»](execution_of_transactions.md).

Объект `ClientConfiguration` устанавливает режим параллелизма, уровень изоляции и тайм-аут по умолчанию для всех транзакций, которые запущены с помощью данного клиентского интерфейса.

:::{code-block} java
:caption: Java
ClientConfiguration cfg = new ClientConfiguration();
cfg.setAddresses("localhost:10800");

cfg.setTransactionConfiguration(new ClientTransactionConfiguration().setDefaultTxTimeout(10000)
        .setDefaultTxConcurrency(TransactionConcurrency.OPTIMISTIC)
        .setDefaultTxIsolation(TransactionIsolation.REPEATABLE_READ));

IgniteClient client = Ignition.startClient(cfg);
:::

Можно указать режим параллелизма, уровень изоляции и тайм-аут перед началом индивидуальной транзакции. В этом случае указанные значения заменят настройки по умолчанию.

:::{code-block} java
:caption: Java
ClientTransactions tx = client.transactions();
try (ClientTransaction t = tx.txStart(TransactionConcurrency.OPTIMISTIC,
        TransactionIsolation.REPEATABLE_READ)) {
    cache.put(1, "new value");
    t.commit();
}
:::

### Работа с бинарными объектами

Тонкий клиент полностью поддерживает `BinaryObject` API. Чтобы переключить кеш в бинарный режим и начать работать непосредственно с бинарными объектами, используйте `CacheClient.withKeepBinary()` — это поможет избежать сериализации и десериализации. Чтобы получить экземпляр `IgniteBinary` и построить объект с нуля, используйте `IgniteClient.binary()`.

:::{code-block} java
:caption: Java
IgniteBinary binary = client.binary();

BinaryObject val = binary.builder("Person").setField("id", 1, int.class).setField("name", "Joe", String.class)
        .build();

ClientCache<Integer, BinaryObject> cache = client.cache("persons").withKeepBinary();

cache.put(1, val);

BinaryObject value = cache.get(1);
:::

Подробнее о работе с бинарными объектами написано в разделе подразделе [«Работа с бинарными объектами»](working_with_binary_objects.md) раздела «Использование Key-Value API»

### Прослушивание записей кеша

При изменении кеша (вставке, обновлении, удалении или истечении срока действия записи) можно отправить событие для уведомления клиента. Чтобы прослушивать эти события, используйте один из подходов:

- непрерывные запросы;
- методы кеша `registerCacheEntryListener`.

Оба подхода требуют предоставить локального слушателя, который срабатывает при каждом событии изменения кеша.

Для обоих подходов можно также указать удаленный фильтр, чтобы сузить диапазон записей, которые отслеживаются на предмет обновлений. Этот фильтр выполняется для каждой обновленной записи на стороне сервера и решает, следует ли передавать событие локальному слушателю клиента.

:::{admonition} Важно
:class: attention

Классы удаленной фабрики фильтров должны быть доступны на серверных узлах кластера.
:::

Подробнее о continuous queries (непрерывных запросах) написано в разделе [«Использование API continuous query»](using_continuous_query_api.md).

Если соединение с сервером разорвано, тонкий клиент не может автоматически переподключиться с гарантией, что никакие события не потерялись. Поэтому continuous queries и зарегистрированные слушатели событий кеша закрываются после разрыва соединения с сервером. Также существует несколько методов с дополнительным параметром `disconnectListener`. Он позволяет перехватывать события отключения сервера и реагировать на них.

:::{code-block} java
:caption: Java
ClientCache<Integer, String> cache = client.getOrCreateCache("myCache");

ContinuousQuery<Integer, String> query = new ContinuousQuery<>();

query.setLocalListener(new CacheEntryUpdatedListener<Integer, String>() {
    @Override public void onUpdated(Iterable<CacheEntryEvent<? extends Integer, ? extends String>> events)
        throws CacheEntryListenerException {
        // Отреагируйте на событие обновления.
    }
});

ClientDisconnectListener disconnectListener = new ClientDisconnectListener() {
    @Override public void onDisconnected(Exception reason) {
        // Отреагируйте на событие отсоединения.
    }
};

cache.query(query, disconnectListener);
:::

## Выполнение SQL-запросов

Чтобы выполнять SQL-запросы, тонкий клиент Java поставляется с SQL API. SQL-запросы объявляются с помощью объекта `SqlFieldsQuery` и выполняются с помощью метода `IgniteClient.query(SqlFieldsQuery)`.

:::{code-block} java
:caption: Java
:collapsible:

client.query(new SqlFieldsQuery(String.format(
        "CREATE TABLE IF NOT EXISTS Person (id INT PRIMARY KEY, name VARCHAR) WITH \"VALUE_TYPE=%s\"",
        Person.class.getName())).setSchema("PUBLIC")).getAll();

int key = 1;
Person val = new Person(key, "Person 1");

client.query(new SqlFieldsQuery("INSERT INTO Person(id, name) VALUES(?, ?)").setArgs(val.getId(), val.getName())
        .setSchema("PUBLIC")).getAll();

FieldsQueryCursor<List<?>> cursor = client
        .query(new SqlFieldsQuery("SELECT name from Person WHERE id=?").setArgs(key).setSchema("PUBLIC"));

// Получите результаты. Метод `getAll()` закрывает курсор. Не нужно
// вызывать `cursor.close()`.
List<List<?>> results = cursor.getAll();

results.stream().findFirst().ifPresent(columns -> {
    System.out.println("name = " + columns.get(0));
});
:::

Метод `query(SqlFieldsQuery)` возвращает экземпляр `FieldsQueryCursor`, который можно использовать для перебора результатов. После получения результатов нужно закрыть курсор, чтобы освободить связанные с ним ресурсы.

:::{admonition} Важно
:class: attention

Метод `getAll()` извлекает результаты из курсора и закрывает его.
:::

Подробнее об использовании `SqlFieldsQuery` и SQL API написано в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/SQL/sql-api).

## Использование API кластера

API кластера позволяют создать в нем группу узлов и выполнять с ней различные операции. Интерфейс `ClientCluster` служит точкой входа в API, который можно использовать для:

- получения и изменения состояния кластера;
- получения списка всех узлов кластера;
- создания логических групп узлов кластера и использования API DataGrid для выполнения операций с группами узлов.

Используйте экземпляр `IgniteClient` для получения ссылки на интерфейс `ClientCluster`.

:::{code-block} java
:caption: Java
try (IgniteClient client = Ignition.startClient(clientCfg)) {
    ClientCluster clientCluster = client.cluster();
    clientCluster.state(ClusterState.ACTIVE);
}
:::

### Логическая группировка узлов

Интерфейс API кластера `ClientClusterGroup` можно использовать для создания различных групп узлов. Например, можно создать группу с только серверными узлами или группу с узлами, которые соответствуют определенному формату адресов TCP/IP.

::::{admonition} Пример, как создать группу серверных узлов, которые расположены в центре обработки данных `dc1`
:class: hint

:::{code-block} java
:caption: Java
try (IgniteClient client = Ignition.startClient(clientCfg)) {
    ClientClusterGroup serversInDc1 = client.cluster().forServers().forAttribute("dc", "dc1");
    serversInDc1.nodes().forEach(n -> System.out.println("Node ID: " + n.id()));
}
:::
::::

Подробнее о логической группировке написано в подразделе [«Группы кластеров»](cluster_groups.md) раздела «Распределенные вычисления».

## Выполнение вычислительных задач

В настоящее время тонкий клиент Java поддерживает базовые вычислительные возможности: позволяет выполнять только вычислительные задачи, которые уже развернуты в кластере. Подробнее о вычислительных возможностях написано в разделе [«Распределенные вычисления»](distributed_computing.md).

Задачу можно запустить на всех узлах кластера или на определенной [группе узлов](#логическая-группировка-узлов). Для развертывания создайте JAR-файл с вычислительными задачами и добавьте его в classpath узлов кластера.

По умолчанию выполнение задач, которые запускает тонкий клиент, отключено на стороне кластера. Установите ненулевое значение для параметра `ThinClientConfiguration.maxActiveComputeTasksPerConnection` в конфигурации серверных узлов и толстых клиентов:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="clientConnectorConfiguration">
        <bean class="org.apache.ignite.configuration.ClientConnectorConfiguration">
            <property name="thinClientConfiguration">
                <bean class="org.apache.ignite.configuration.ThinClientConfiguration">
                    <property name="maxActiveComputeTasksPerConnection" value="100" />
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
ThinClientConfiguration thinClientCfg = new ThinClientConfiguration()
        .setMaxActiveComputeTasksPerConnection(100);

ClientConnectorConfiguration clientConnectorCfg = new ClientConnectorConfiguration()
        .setThinClientConfiguration(thinClientCfg);

IgniteConfiguration igniteCfg = new IgniteConfiguration()
        .setClientConnectorConfiguration(clientConnectorCfg);

Ignite ignite = Ignition.start(igniteCfg);
```
:::
::::


::::{admonition} Пример, как получить доступ к вычислительному API с помощью интерфейса `ClientCompute` и выполнить вычислительную задачу `MyTask`
:class: hint

:::{code-block} java
:caption: Java
try (IgniteClient client = Ignition.startClient(clientCfg)) {
    // Предполагается, что класс `MyTask` уже развернут в кластере.
    client.compute().execute(
        MyTask.class.getName(), "argument");
}
:::
::::

## Выполнение сервисов DataGrid

Чтобы вызвать сервис DataGrid, который уже развернут в кластере, используйте API `ClientServices` на тонком клиенте. Подробнее о сервисах написано в разделе [«Сервисы DataGrid»](datagrid_services.md).

::::{admonition} Пример, как вызвать сервис с названием `MyService`
:class: hint

:::{code-block} java
:caption: Java
try (IgniteClient client = Ignition.startClient(clientCfg)) {
    // Выполнение сервиса `MyService`, который 
    // уже развернут в кластере.
    client.services().serviceProxy(
        "MyService", MyService.class).myServiceMethod();
}
:::
::::

Развернутый сервис может быть реализован на Java или .NET.

## Обработка исключений

### Поведение при сбоях узлов

Если в конфигурации клиента указаны адреса нескольких узлов, при сбое текущего соединения клиент автоматически переключается на следующий узел и перезапускает любую осуществляемую операцию.

В случае атомарных операций аварийный переход к другому узлу прозрачен для пользователя. Если выполняются scan queries или запросы `SELECT`, при итерации по курсору запроса может сгенерироваться исключение `ClientConnectionException`. Это может произойти из-за того, что запросы возвращают данные в страницах. Если узел, к которому подключен клиент, падает во время передачи страниц, для обеспечения согласованности результатов запроса генерируется исключение.

Если запущена явная транзакция, при сбое подключения к серверному узлу операции кеширования, которые привязаны к транзакции, могут также сгенерировать исключение `ClientException`. Пользовательский код должен обрабатывать такие исключения и соответствующим образом реализовывать логику перезапуска.

Администратор кластера может прервать соединение с тонким клиентом с помощью управляющей команды `--kill CLIENT` (подробнее о ней написано в разделе «[](/documents/administration-guide/operational-commands.md#kill-client)» документа «Руководство по системному администрированию»). В этом случае клиентский узел будет вести себя так же, как при сетевой недоступности между серверным узлом и тонким клиентом. 

На стороне клиента сгенерируется исключение `ClientConnectionException`, которое можно обработать на стороне прикладного кода. Чтобы повторно подключить клиентский узел, воспользуйтесь инструкцией в разделе «[](connecting_client_nodes.md#повторное-подключение-клиентского-узла)».

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу данных между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

Чтобы включить зашифрованную передачу данных в тонком клиенте, укажите в конфигурации хранилище ключей (`keystore`), в котором лежит ключ шифрования, и хранилище доверенных сертификатов (`truststore`).

:::{code-block} java
:caption: Java
ClientConfiguration clientCfg = new ClientConfiguration().setAddresses("xxx.x.x.x:10800");

clientCfg.setSslMode(SslMode.REQUIRED).setSslClientCertificateKeyStorePath(KEYSTORE)
        .setSslClientCertificateKeyStoreType("JKS").setSslClientCertificateKeyStorePassword("123456")
        .setSslTrustCertificateKeyStorePath(TRUSTSTORE).setSslTrustCertificateKeyStorePassword("123456")
        .setSslTrustCertificateKeyStoreType("JKS").setSslKeyAlgorithm("SunX509").setSslTrustAll(false)
        .setSslProtocol(SslProtocol.TLS);

try (IgniteClient client = Ignition.startClient(clientCfg)) {
    // ...
}
:::

Таблица параметров шифрования конфигурации клиента:

| Параметр | Описание | Значение по умолчанию |
|---|---|---|
| `sslMode` | `REQURED` или `DISABLED` | `DISABLED`  |
| `sslClientCertificateKeyStorePath` | Путь к файлу `keystore` с приватным ключом | — |
| `sslClientCertificateKeyStoreType` | Тип хранилища ключей | `JKS` |
| `sslClientCertificateKeyStorePassword` | Пароль от хранилища ключей | — |
| `sslTrustCertificateKeyStorePath` | Путь к файлу хранилища доверенных сертификатов (`truststore`) | — |
| `sslTrustCertificateKeyStoreType` | Тип хранилища доверенных сертификатов (`truststore`) | `JKS` |
| `sslTrustCertificateKeyStorePassword` | Пароль от хранилища доверенных сертификатов | — |
| `sslKeyAlgorithm` | Алгоритм для создания менеджера управления ключами | `SunX509`  |
| `sslTrustAll` | Если установлено значение `true`, сертификаты не проверяются | — |
| `sslProtocol` | Название протокола, который используется для шифрования данных | `TLS` |

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента:

:::{code-block} java
:caption: Java
ClientConfiguration clientCfg = new ClientConfiguration().setAddresses("xxx.x.x.x:10800").setUserName("joe")
        .setUserPassword("passw0rd!");

try (IgniteClient client = Ignition.startClient(clientCfg)) {
    // ...
} catch (ClientAuthenticationException e) {
    // Обработайте сбой аутентификации.
}
:::

## Асинхронные API

У большей части сетевых API тонких клиентов есть асинхронные аналоги, например `ClientCache.get` или `ClientCache.getAsync`.

:::{code-block} java
:caption: Java
IgniteClient client = Ignition.startClient(clientCfg);
ClientCache<Integer, String> cache = client.getOrCreateCache("cache");

IgniteClientFuture<Void> putFut = cache.putAsync(1, "hello");
putFut.get(); // Блокирующее ожидание.

IgniteClientFuture<String> getFut = cache.getAsync(1);
getFut.thenAccept(val -> System.out.println(val)); // Неблокирующее продолжение.
:::

Особенности асинхронных API:

- Асинхронные методы не блокируют вызывающий поток.
- Асинхронные методы возвращают интерфейс `IgniteClientFuture<T>` — комбинацию `Future<T>` и `CompletionStage<T>`.
- Асинхронные продолжения выполняются с использованием `ClientConfiguration.AsyncContinuationExecutor`, который по умолчанию использует `ForkJoinPool#commonPool()`. Например, команда `cache.getAsync(1).thenAccept(val → System.out.println(val))` выполнит вызов `println` с помощью потока из `commonPool`.