# Near-кеши

Near-кеш — локальный кеш, хранящий данные на локальном узле, которые запрашивали недавно или чаще всего. Например, приложение запускает клиентский узел и регулярно запрашивает справочные данные (коды стран). Так как клиентские узлы не хранят данные, запросы всегда извлекают их с удаленных узлов. Настройка near-кешей позволит хранить коды стран на локальном узле во время работы приложения.

Near-кеш настраивается для обычного кеша и содержит данные только для него. Near-кеш хранит данные в heap-памяти. Максимальный размер кеша и политики вытеснения записей для near-кеша можно настроить отдельно.

:::{admonition} Важно
:class: attention

Near-кеш полностью транзакционный и автоматически обновляется или становится недействительным при каждом обновлении данных на серверных узлах.
:::

## Настройка near-кеша

Пример, как настроить near-кеш для конкретного кеша:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.CacheConfiguration">
    <property name="name" value="myCache"/>
    <property name="nearConfiguration">
        <bean class="org.apache.ignite.configuration.NearCacheConfiguration">
            <property name="nearEvictionPolicyFactory">
                <bean class="org.apache.ignite.cache.eviction.lru.LruEvictionPolicyFactory">
                    <property name="maxSize" value="100000"/>
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
// Настройте near-кеш для `myCache`.
NearCacheConfiguration<Integer, Integer> nearCfg = new NearCacheConfiguration<>();

// Используйте политику вытеснения записей LRU, чтобы автоматически вытеснять из near-кеша
// записи каждый раз, когда их количество достигает 100 000.
nearCfg.setNearEvictionPolicyFactory(new LruEvictionPolicyFactory<>(100_000));

CacheConfiguration<Integer, Integer> cacheCfg = new CacheConfiguration<Integer, Integer>("myCache");

cacheCfg.setNearConfiguration(nearCfg);

// Создайте распределенный кеш на серверных узлах.
IgniteCache<Integer, Integer> cache = ignite.getOrCreateCache(cacheCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cacheCfg = new CacheConfiguration
{
    Name = "myCache",
    NearConfiguration = new NearCacheConfiguration
    {
        EvictionPolicy = new LruEvictionPolicy
        {
            MaxSize = 100_000
        }
    }
};

var cache = ignite.GetOrCreateCache<int, int>(cacheCfg);
```
:::
::::

Если настроить near-кеш как в примере выше, он создастся на любом узле, который запрашивает данные из основного кеша (включая серверные и клиентские узлы). Near-кеш создается на серверных и толстых клиентских узлах, но не создается на тонких клиентских узлах.

При получении экземпляра кеша и работе с ним запросы будут происходить через near-кеш.

:::{code-block} java
:caption: Java
IgniteCache<Integer, Integer> cache = ignite.cache("myCache");

int value = cache.get(1);
:::

Near-кеш наследует большую часть базовых параметров конфигурации кеша. Например, если в базовом кеше настроена политика устаревания записей, срок действия записей в near-кеше истекает на основе этой же политики. Подробнее о ней написано в разделе [«Политика устаревания записей (Expiry Policy)»](expiry_policy.md).

Параметры, которые не наследуются от конфигурации основного кеша:

| Параметр | Описание | Значение по умолчанию |
|---|---|---|
| `nearEvictionPolicy` | Политика вытеснения записей для near-кеша. Подробнее о ней написано в подразделе [«Политика вытеснения данных из кеша (Eviction Policies)»](eviction_policies.md) раздела «Настройка памяти» | — |
| `nearStartSize` | Начальное количество записей, которое содержит near-кеш | `375000` |

## Динамическое создание near-кешей на клиентских узлах

При создании запроса с клиентского узла в кеш, для которого не был настроен near-кеш, его можно создать динамически. Это повысит производительность за счет хранения «горячих» данных локально на стороне клиентского узла. Такой near-кеш будет работать только на узле, где он был создан.

Чтобы создать near-кеш динамически, создайте его конфигурацию и передайте ее в качестве аргумента методу, который получает экземпляр кеша:

::::{md-tab-set}
:::{md-tab-item} Java
```java
// Создайте конфигурацию для near-кеша.
NearCacheConfiguration<Integer, String> nearCfg = new NearCacheConfiguration<>();  

// Используйте политику вытеснения записей LRU, чтобы автоматически вытеснять из near-кеша
// записи каждый раз, когда их количество достигает 100 000. 
nearCfg.setNearEvictionPolicyFactory(new LruEvictionPolicyFactory<>(100_000));

// Получите кеш с названием `myCache` и создайте near-кеш для него.
IgniteCache<Integer, String> cache = ignite.getOrCreateNearCache("myCache", nearCfg);

String value = cache.get(1);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var ignite = Ignition.Start(new IgniteConfiguration
{
    DiscoverySpi = new TcpDiscoverySpi
    {
        LocalPort = 48500,
        LocalPortRange = 20,
        IpFinder = new TcpDiscoveryStaticIpFinder
        {
            Endpoints = new[]
            {
                "xxx.x.x.x:48500..48520"
            }
        }
    },
    CacheConfiguration = new[]
    {
        new CacheConfiguration {Name = "myCache"}
    }
});
var client = Ignition.Start(new IgniteConfiguration
{
    IgniteInstanceName = "clientNode",
    ClientMode = true,
    DiscoverySpi = new TcpDiscoverySpi
    {
        LocalPort = 48500,
        LocalPortRange = 20,
        IpFinder = new TcpDiscoveryStaticIpFinder
        {
            Endpoints = new[]
            {
                "xxx.x.x.x:48500..48520"
            }
        }
    }
});
// Создайте конфигурацию для near-кеша.
var nearCfg = new NearCacheConfiguration
{
    // Используйте политику вытеснения записей LRU, чтобы автоматически вытеснять из near-кеша
    //  записи каждый раз, когда их количество достигает 100 000.
    EvictionPolicy = new LruEvictionPolicy()
    {
        MaxSize = 100_000
    }
};


// Получите кеш с названием `myCache` и создайте near-кеш для него.
var cache = client.GetOrCreateNearCache<int, string>("myCache", nearCfg);
```
:::
::::