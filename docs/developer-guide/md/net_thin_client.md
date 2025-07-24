# Тонкий клиент .NET

## Требования

Для работы с тонким клиентом .NET потребуется:

- среда исполнения — .NET версии 4.0 и новее, .NET Core версии 2.0 и новее;
- операционная система — Windows, Linux, macOS (любые операционные системы, которые поддерживает .NET Core версии 2.0 и новее).

## Установка

API тонкого клиента .NET поставляется из библиотеки Ignite.NET API, которая находится в каталоге `{IGNITE_HOME}/platforms/dotnet` дистрибутива DataGrid. API находятся в сборке `Apache.Ignite.Core`.

## Соединение с кластером

Точка входа в API тонкого клиента — метод `Ignition.StartClient(IgniteClientConfiguration)`. Свойство `IgniteClientConfiguration.Endpoints` является обязательным. Оно должно указывать на хост, на котором запущен серверный узел.

:::{code-block} c#
:caption: C\#
var cfg = new IgniteClientConfiguration
{
    Endpoints = new[] {"xxx.x.x.x:10800"}
};

using (var client = Ignition.StartClient(cfg))
{
    var cache = client.GetOrCreateCache<int, string>("cache");
    cache.Put(1, "Hello, World!");
}
:::

### Отказоустойчивость

Можно указать адреса нескольких узлов. В этом случае тонкий клиент подключается к случайному узлу в списке, и включается механизм отказоустойчивого соединения. Если серверный узел выходит из строя, клиент пробует установить связь по другим известным адресам и автоматически переподключается. Если серверный узел отключился во время выполнения клиентской операции, может сгенерироваться исключение `IgniteClientException`. Пользовательский код должен обработать это исключение и соответствующим образом реализовывать логику перезапуска.

### Автоматическое обнаружение серверных узлов

Тонкий клиент может автоматически обнаруживать серверные узлы кластера, если не включена функция [Partition Awareness](#partition-awareness).

Обнаружение сервера — асинхронный процесс, который происходит в фоновом режиме. Помимо этого, тонкий клиент получает обновления топологии только при выполнении операций. Это нужно, чтобы уменьшить нагрузку от неактивных подключений на сервер и сетевой трафик.

Чтобы следить за процессом обнаружения, включите логирование и/или вызовите метод `IIgniteClient.GetConnections`.

:::{code-block} c#
:caption: C\#
var cfg = new IgniteClientConfiguration
{
    Endpoints = new[] {"xxx.x.x.x:10800"},
    EnablePartitionAwareness = true,

    // Чтобы наблюдать за процессом обнаружения, включите логирование с уровнем `TRACE`.
    Logger = new ConsoleLogger { MinLevel = LogLevel.Trace }
};

var client = Ignition.StartClient(cfg);

// Выполните любую операцию и перейдите в режим ожидания, чтобы клиент мог
// асинхронно обнаруживать серверные узлы.
client.GetCacheNames();
Thread.Sleep(1000);

foreach (IClientConnection connection in client.GetConnections())
{
    Console.WriteLine(connection.RemoteEndPoint);
}
:::

:::{admonition} Внимание
:class: danger

Обнаружение серверных узлов может не работать, если они находятся за NAT или подключены к прокси. Серверные узлы предоставляют клиенту свои адреса и порты. Если клиент находится в другой подсети, эти адреса не будут работать.
:::

## Partition Awareness

Функция Partition Awareness позволяет тонкому клиенту отправлять запросы напрямую узлу, который содержит нужные данные. Без этой функции приложение, которое подключено к кластеру с помощью тонкого клиента, выполняет все запросы и операции на одном серверном узле (он служит прокси-сервером для входящих запросов). Затем эти операции перенаправляются на узел, где хранятся нужные данные. Это приводит к возникновению узкого места, которое может помешать линейному масштабированию приложения.

Запросы должны проходить через прокси-сервер, откуда они перенаправляются на корректный узел:

![Partition-awareness-off](./resources/partition-awareness-off.png)

С функцией Partition Awareness тонкий клиент может напрямую отправлять запросы основным узлам, где хранятся нужные данные. Функция устраняет узкое место и позволяет приложению проще масштабироваться:

![Partition-awareness-on](./resources/partition-awareness-on.png)

Чтобы включить функцию, установите значение `true` для свойства `IgniteClientConfiguration.EnablePartitionAwareness`. Вместе с Partition Awareness автоматически включится функция [обнаружения узлов](#автоматическое-обнаружение-серверных-узлов). Если клиент находится за NAT или подключен к прокси, автоматическое обнаружение серверных узлов может не работать. В этом случае укажите адреса всех серверных узлов в конфигурации подключения клиента.

## Использование Key-Value API

### Получение экземпляра кеша

Key-Value-API предоставляется интерфейсом `ICacheClient`. Чтобы получить экземпляр `ICacheClient`, используйте методы:

- `GetCache(cacheName)` — возвращает экземпляр существующего кеша;
- `CreateCache(cacheName)` — создает кеш с указанным именем;
- `GetOrCreateCache(CacheClientConfiguration)` — получает или создает кеш с указанной конфигурацией.

:::{code-block} c#
:caption: C\#
var cacheCfg = new CacheClientConfiguration
{
    Name = "References",
    CacheMode = CacheMode.Replicated,
    WriteSynchronizationMode = CacheWriteSynchronizationMode.FullSync
};
var cache = client.GetOrCreateCache<int, string>(cacheCfg);
:::

Чтобы получить список всех существующих кешей, используйте метод `IIgniteClient.GetCacheNames()`.

### Основные операции кеша

Пример, как выполнять основные операции для определенного кеша:

:::{code-block} c#
:caption: C\#
var data = Enumerable.Range(1, 100).ToDictionary(e => e, e => e.ToString());

cache.PutAll(data);

var replace = cache.Replace(1, "2", "3");
Console.WriteLine(replace); // false

var value = cache.Get(1);
Console.WriteLine(value); // 1

replace = cache.Replace(1, "1", "3");
Console.WriteLine(replace); // true

value = cache.Get(1);
Console.WriteLine(value); // 3

cache.Put(101, "101");

cache.RemoveAll(data.Keys);
var sizeIsOne = cache.GetSize() == 1;
Console.WriteLine(sizeIsOne); // true

value = cache.Get(101);
Console.WriteLine(value); // 101

cache.RemoveAll();
var sizeIsZero = cache.GetSize() == 0;
Console.WriteLine(sizeIsZero); // true
:::

### Работа с бинарными объектами

Тонкий клиент .NET поддерживает `BinaryObject` API — подробнее написано в подразделе [«Работа с бинарными объектами»](working_with_binary_objects.md) раздела «Использование Key-Value API». Чтобы переключить кеш в бинарный режим и начать работать непосредственно с бинарными объектами, используйте `ICacheClient.WithKeepBinary()` — это поможет избежать сериализации и десериализации.

Чтобы получить экземпляр `IBinary` и построить объект с нуля, используйте `IIgniteClient.GetBinary()`.

:::{code-block} c#
:caption: C\#
var binary = client.GetBinary();

var val = binary.GetBuilder("Person")
    .SetField("id", 1)
    .SetField("name", "Joe")
    .Build();

var cache = client.GetOrCreateCache<int, object>("persons").WithKeepBinary<int, IBinaryObject>();

cache.Put(1, val);

var value = cache.Get(1);
:::

## Scan Queries

Чтобы получить набор записей, которые соответствуют заданному условию, используйте запросы сканирования. Тонкий клиент отправляет запрос на узел кластера, где он выполняется как обычный scan query. Условие запроса задается с помощью объекта `ICacheEntryFilter`, который передается конструктору запроса в качестве аргумента.

Определите фильтр запроса:

:::{code-block} c#
:caption: C\#
class NameFilter : ICacheEntryFilter<int, Person>
{
    public bool Invoke(ICacheEntry<int, Person> entry)
    {
        return entry.Value.Name.Contains("Smith");
    }
}
:::

Выполните запрос сканирования:

:::{code-block} c#
:caption: C\#
var cache = client.GetOrCreateCache<int, Person>("personCache");

cache.Put(1, new Person {Name = "John Smith"});
cache.Put(2, new Person {Name = "John Johnson"});

using (var cursor = cache.Query(new ScanQuery<int, Person>(new NameFilter())))
{
    foreach (var entry in cursor)
    {
        Console.WriteLine("Key = " + entry.Key + ", Name = " + entry.Value.Name);
    }
}
:::

## Выполнение SQL-запросов

Чтобы выполнять SQL-запросы, тонкий клиент предоставляет SQL API. SQL-запросы объявляются с помощью объектов `SqlFieldsQuery` и выполняются с помощью метода `ICacheClient.Query(SqlFieldsQuery)`.

:::{code-block} c#
:caption: C\#
var cache = client.GetOrCreateCache<int, Person>("Person");
cache.Query(new SqlFieldsQuery(
        $"CREATE TABLE IF NOT EXISTS Person (id INT PRIMARY KEY, name VARCHAR) WITH \"VALUE_TYPE={typeof(Person)}\"")
    {Schema = "PUBLIC"}).GetAll();

var key = 1;
var val = new Person {Id = key, Name = "Person 1"};

cache.Query(
    new SqlFieldsQuery("INSERT INTO Person(id, name) VALUES(?, ?)")
    {
        Arguments = new object[] {val.Id, val.Name},
        Schema = "PUBLIC"
    }
).GetAll();

var cursor = cache.Query(
    new SqlFieldsQuery("SELECT name FROM Person WHERE id = ?")
    {
        Arguments = new object[] {key},
        Schema = "PUBLIC"
    }
);

var results = cursor.GetAll();

var first = results.FirstOrDefault();
if (first != null)
{
    Console.WriteLine("name = " + first[0]);
}
:::

Также SQL-запросы можно выполнять с помощью поставщика DataGrid LINQ.

## Использование API кластера

API кластера позволяют создать в нем группу узлов и выполнять с ней различные операции. Интерфейс `IClientCluster` служит точкой входа в API, которые можно использовать для:

- получения и изменения состояния кластера;
- получения списка всех узлов кластера;
- создания логических групп узлов кластера и использования API DataGrid для выполнения операций с группами узлов.

Используйте экземпляр `IClientCluster`, чтобы получить ссылку на интерфейс `IClientCluster`, который содержит все узлы кластера, активировать кластер и WAL-логирование для кеша `my-cache`.

:::{code-block} c#
:caption: C\#
IIgniteClient client = Ignition.StartClient(cfg);
IClientCluster cluster = client.GetCluster();
cluster.SetActive(true);
cluster.EnableWal("my-cache");
:::

### Логическая группировка узлов

Интерфейс API кластера `IClientClusterGroup` можно использовать для создания различных групп узлов. Например, можно создать группу с только серверными узлами или группу с узлами, которые соответствуют определенному формату адресов TCP/IP.

Пример, как создать группу серверных узлов, которые расположены в центре обработки данных `dc1`:

:::{code-block} c#
:caption: C\#
IIgniteClient client = Ignition.StartClient(cfg);
IClientClusterGroup serversInDc1 = client.GetCluster().ForServers().ForAttribute("dc", "dc1");
foreach (IClientClusterNode node in serversInDc1.GetNodes())
    Console.WriteLine($"Node ID: {node.Id}");
:::

:::{admonition} Примечание
:class: note

Подробнее о логической группировке написано в подразделе [«Группы кластеров»](cluster_groups.md) раздела «Распределенные вычисления».
:::

## Выполнение вычислительных задач

В настоящее время тонкий клиент .NET поддерживает базовые вычислительные возможности: позволяет выполнять только вычислительные задачи, которые уже развернуты в кластере. Подробнее о вычислительных возможностях написано в разделе [«Распределенные вычисления»](distributed_computing.md).

По умолчанию выполнение задач, которые запускает тонкий клиент, отключено на стороне кластера. Установите ненулевое значение для параметра `ThinClientConfiguration.MaxActiveComputeTasksPerConnection` в конфигурации серверных узлов и толстых клиентов:

::::{md-tab-set}
:::{md-tab-item} Spring XML
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

:::{md-tab-item} C\#
```c#
var igniteCfg = new IgniteConfiguration
{
    ClientConnectorConfiguration = new ClientConnectorConfiguration
    {
        ThinClientConfiguration = new ThinClientConfiguration
        {
            MaxActiveComputeTasksPerConnection = 10
        }
    }
};

IIgnite ignite = Ignition.Start(igniteCfg);
```
:::
::::

Пример, как получить доступ к вычислительному API с помощью интерфейса `IComputeClient` и выполнить вычислительную задачу `org.foo.bar.AddOneTask` с входным параметром `1`:

:::{code-block} c#
:caption: C\#
IIgniteClient client = Ignition.StartClient(cfg);
IComputeClient compute = client.GetCompute();
int result = compute.ExecuteJavaTask<int>("org.foo.bar.AddOneTask", 1);
:::

## Выполнение сервисов DataGrid

Чтобы вызвать сервис DataGrid, который уже развернут в кластере, используйте API тонкого клиента `IServicesClient`. Подробнее о сервисах написано в разделе [«Сервисы DataGrid»](datagrid_services.md).

Пример, как вызвать сервис `MyService`:

:::{code-block} c#
:caption: C\#
IIgniteClient client = Ignition.StartClient(cfg);
IServicesClient services = client.GetServices();
IMyService serviceProxy = services.GetServiceProxy<IMyService>("MyService");
serviceProxy.MyServiceMethod("hello");
:::

Тонкий клиент позволяет выполнять сервисы, которые реализованы на Java или .NET.

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу данных между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

Пример, как настроить параметры SSL в тонком клиенте:

:::{code-block} c#
:caption: C\#
var cfg = new IgniteClientConfiguration
{
    Endpoints = new[] {"xxx.x.x.x:10800"},
    SslStreamFactory = new SslStreamFactory
    {
        CertificatePath = ".../certs/client.pfx",
        CertificatePassword = "password",
    }
};
using (var client = Ignition.StartClient(cfg))
{
    //...
}
:::

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента:

:::{code-block} c#
:caption: C\#
var cfg = new IgniteClientConfiguration
{
    Endpoints = new[] {"xxx.x.x.x:10800"},
    UserName = "*****",
    Password = "*****"
};
using (var client = Ignition.StartClient(cfg))
{
    //...
}
:::