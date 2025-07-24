# Включение и прослушивание событий

DataGrid может генерировать события для различных операций, которые происходят в кластере, и уведомлять о них приложение. Существует множество типов событий: события кеша, события обнаружения узлов, события выполнения распределенных задач и другие. Список типов находится в разделе [«События»](events.md).

## Подключение событий

По умолчанию события отключены. Чтобы использовать их в приложении, явно включите каждый тип событий. Для этого перечислите их в свойстве `includeEventTypes` конфигурационного файла `IgniteConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:util="http://www.springframework.org/schema/util"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="         http://www.springframework.org/schema/beans
    http://www.springframework.org/schema/beans/spring-beans.xsd
    http://www.springframework.org/schema/util
    http://www.springframework.org/schema/util/spring-util.xsd">

    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="includeEventTypes">
            <list>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_CACHE_OBJECT_PUT"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_CACHE_OBJECT_READ"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_CACHE_OBJECT_REMOVED"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_NODE_LEFT"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_NODE_JOINED"/>
            </list>
        </property>
    </bean>

</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Подключите события кеша.
cfg.setIncludeEventTypes(EventType.EVT_CACHE_OBJECT_PUT, EventType.EVT_CACHE_OBJECT_READ,
        EventType.EVT_CACHE_OBJECT_REMOVED, EventType.EVT_NODE_JOINED, EventType.EVT_NODE_LEFT);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    IncludedEventTypes = new[]
    {
        EventType.CacheObjectPut,
        EventType.CacheObjectRead,
        EventType.CacheObjectRemoved,
        EventType.NodeJoined,
        EventType.NodeLeft
    }
};
var ignite = Ignition.Start(cfg);
```
:::
::::

## Получение интерфейса событий

Функциональные возможности событий доступны через интерфейс событий. В нем есть методы для прослушивания событий кластера. Интерфейс можно получить из экземпляра `Ignite`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteEvents events = ignite.events();
```
:::

:::{md-tab-item} C\#/.NET
```c#
var ignite = Ignition.GetIgnite();
var events = ignite.GetEvents();
```
:::
::::

Интерфейс событий может быть связан с набором узлов (подробнее о них написано в подразделе [«Группы кластеров»](cluster_groups.md) раздела «Распределенные вычисления»). Это значит, что можно получить доступ к событиям, которые происходят на заданном наборе узлов. В примере интерфейс событий получен для множества узлов, на которых хранятся данные по кешу `Person`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.ignite();

IgniteEvents events = ignite.events(ignite.cluster().forCacheNodes("person"));
```
:::

:::{md-tab-item} C\#/.NET
```c#
var ignite = Ignition.GetIgnite();
var events = ignite.GetCluster().ForCacheNodes("person").GetEvents();
```
:::
::::

## Прослушивание событий

Можно прослушивать локальные (local) и удаленные (remote) события. Локальные события генерируются на узле, в котором зарегистрирован слушатель. Удаленные события происходят на других узлах.

Некоторые события могут быть запущены на нескольких узлах, даже если соответствующее реальное (real-world) событие происходит всего один раз. Например, когда узел покидает кластер, на всех оставшихся узлах генерируется событие `EVT_NODE_LEFT`.

Другой пример — когда объект помещается в кеш. На узле с основной (primary) партицией, на которую записывается объект и которая может отличаться от узла с вызовом метода `put(…​)`, происходит событие `EVT_CACHE_OBJECT_PUT`. Оно запускается на всех узлах, на которых хранятся резервные (backup) партиции кеша, если они настроены. Подробнее об основных и резервных партициях написано в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных».

Интерфейс событий предоставляет методы для:

- прослушивания только локальных событий;
- или прослушивания одновременно локальных и удаленных событий.

### Прослушивание локальных событий (local events)

Для прослушивания локальных событий используйте метод `localListen(listener, eventTypes…​)`. Он принимает слушатель событий, который вызывается каждый раз, когда на локальном узле происходит событие.

Чтобы отключить локальный слушатель, верните значение `false` в его функциональном методе.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteEvents events = ignite.events();

// Локальный слушатель, который прослушивает локальные события.
IgnitePredicate<CacheEvent> localListener = evt -> {
    System.out.println("Received event [evt=" + evt.name() + ", key=" + evt.key() + ", oldVal=" + evt.oldValue()
            + ", newVal=" + evt.newValue());

    return true; // Продолжайте прослушивание событий.
};

// Подпишитесь на события кеша, которые происходят на локальном узле.
events.localListen(localListener, EventType.EVT_CACHE_OBJECT_PUT, EventType.EVT_CACHE_OBJECT_READ,
        EventType.EVT_CACHE_OBJECT_REMOVED);
```
:::

:::{md-tab-item} С#/.NET
```c#
class LocalListener : IEventListener<CacheEvent>
{
    public bool Invoke(CacheEvent evt)
    {
        Console.WriteLine("Received event [evt=" + evt.Name + ", key=" + evt.Key + ", oldVal=" + evt.OldValue
                          + ", newVal=" + evt.NewValue);
        return true;
    }
}

public static void LocalListenDemo()
{
    var cfg = new IgniteConfiguration
    {
        IncludedEventTypes = new[]
        {
            EventType.CacheObjectPut,
            EventType.CacheObjectRead,
            EventType.CacheObjectRemoved,
        }
    };
    var ignite = Ignition.Start(cfg);
    var events = ignite.GetEvents();
    events.LocalListen(new LocalListener(), EventType.CacheObjectPut, EventType.CacheObjectRead,
        EventType.CacheObjectRemoved);

    var cache = ignite.GetOrCreateCache<int, int>("myCache");
    cache.Put(1, 1);
    cache.Put(2, 2);
}
```
:::
::::

Слушатель событий — реализация функционального интерфейса `IgnitePredicate<E>` с обобщенным типом, соответствующим типу событий, которые будет обрабатывать слушатель. Например, события кеша (`EVT_CACHE_OBJECT_PUT`, `EVT_CACHE_OBJECT_READ` и другие) относятся к классу `CacheEvent`, discovery-события (`EVT_NODE_LEFT`, `EVT_NODE_JOINED` и другие) — к классу `DiscoveryEvent`, и так далее.

Чтобы слушать события разных типов, используйте обобщенный интерфейс `Event`:

```bash
IgnitePredicate<Event> localListener = evt -> {
    // Обработайте событие.
    return true;
};
```

### Прослушивание удаленных событий (remote events)

Метод `IgniteEvents.remoteListen(localListener, filter, types)` можно использовать для прослушивания удаленных и локальных событий. Метод принимает локальный слушатель, фильтр и список типов событий, которые будут прослушиваться.

Фильтр развертывается на всех узлах, которые связаны с интерфейсом событий, в том числе на локальном узле. События, которые проходят фильтр, отправляются локальному слушателю.

Метод `IgniteEvents.stopRemoteListen(uuid)` возвращает уникальный идентификатор, который можно использовать для отключения слушателя и фильтров. Другой способ отключения слушателя — вернуть значение `false` в методе  `apply()`.

:::{code-block} java
:caption: Java
IgniteEvents events = ignite.events();

IgnitePredicate<CacheEvent> filter = evt -> {
    System.out.println("remote event: " + evt.name());
    return true;
};

// Подпишитесь на прослушивание событий кеша на всех узлах, где он есть.
UUID uuid = events.remoteListen(new IgniteBiPredicate<UUID, CacheEvent>() {

    @Override
    public boolean apply(UUID uuid, CacheEvent e) {

        // Обработайте событие.

        return true; // Продолжайте прослушивание событий.
    }
}, filter, EventType.EVT_CACHE_OBJECT_PUT);
:::

### Пакетная обработка событий

Каждое действие в кеше может привести к генерации и отправке уведомлений о событии. В системах с высокой активностью кеша получение уведомлений о каждом событии приведет к интенсивной нагрузке на сеть. В результате производительность операций кеша может снизиться.

Чтобы снизить влияние на производительность, можно группировать события и отправлять их пакетами или настроить отправку событий через определенные промежутки времени:

:::{code-block} java
:caption: Java
Ignite ignite = Ignition.ignite();

// Получите экземпляр кеша.
final IgniteCache<Integer, String> cache = ignite.cache("cacheName");

// Пример удаленного фильтра, принимающего только события для ключей,
// которые больше или равны 10.
IgnitePredicate<CacheEvent> rmtLsnr = new IgnitePredicate<CacheEvent>() {
    @Override
    public boolean apply(CacheEvent evt) {
        System.out.println("Cache event: " + evt);

        int key = evt.key();

        return key >= 10;
    }
};

// Подпишитесь на прослушивание событий кеша, которые запускаются на всех узлах,
// где он есть.
// Отправляйте уведомления пакетами по 10 событий.
ignite.events(ignite.cluster().forCacheNodes("cacheName")).remoteListen(10 /* batch size */,
        0 /* time intervals */, false, null, rmtLsnr, EventType.EVTS_CACHE);

// Создайте события кеша.
for (int i = 0; i < 20; i++)
    cache.put(i, Integer.toString(i));
:::

## Хранение и запрос событий

Можно настроить хранилище событий. Оно будет хранить события на узлах, где они происходят. После этого можно запрашивать события в приложении.

Хранилище событий можно настроить для хранения:

- событий за определенный период;
- только последних событий;
- событий, которые соответствуют определенному фильтру.

Пример конфигурации хранилища событий:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="eventStorageSpi" >
        <bean class="org.apache.ignite.spi.eventstorage.memory.MemoryEventStorageSpi">
            <property name="expireAgeMs" value="600000"/>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
MemoryEventStorageSpi eventStorageSpi = new MemoryEventStorageSpi();
eventStorageSpi.setExpireAgeMs(600000);

IgniteConfiguration igniteCfg = new IgniteConfiguration();
igniteCfg.setEventStorageSpi(eventStorageSpi);

Ignite ignite = Ignition.start(igniteCfg);
```
:::

:::{md-tab-item} С#/.NET
```c#
var cfg = new IgniteConfiguration
{
    EventStorageSpi = new MemoryEventStorageSpi()
    {
        ExpirationTimeout = TimeSpan.FromMilliseconds(600000)
    },
    IncludedEventTypes = new[]
    {
        EventType.CacheObjectPut,
        EventType.CacheObjectRead,
        EventType.CacheObjectRemoved,
    }
};
var ignite = Ignition.Start(cfg);
```
:::
::::

### Запрос локальных событий

Пример, как запрашивать локальные события `EVT_CACHE_OBJECT_PUT`, которые находятся в хранилище событий:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Collection<CacheEvent> cacheEvents = events.localQuery(e -> {
    // Обработайте событие.
    return true;
}, EventType.EVT_CACHE_OBJECT_PUT);
```
:::

:::{md-tab-item} С#/.NET
```c#
var events = ignite.GetEvents();
var cacheEvents = events.LocalQuery(EventType.CacheObjectPut);
```
:::
::::

### Запрос удаленных событий

Пример запроса удаленных событий:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Collection<CacheEvent> storedEvents = events.remoteQuery(e -> {
    // Обработайте событие.
    return true;
}, 0, EventType.EVT_CACHE_OBJECT_PUT);
```
:::

:::{md-tab-item} С#/.NET
```c#
class EventFilter : IEventFilter<CacheEvent>
{
    public bool Invoke(CacheEvent evt)
    {
        return true;
    }
}
// ....


    var events = ignite.GetEvents();
    var storedEvents = events.RemoteQuery(new EventFilter(), null, EventType.CacheObjectPut);
```
:::
::::