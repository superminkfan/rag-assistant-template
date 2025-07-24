# Политика устаревания записей (Expiry Policy)

Политика устаревания записей (`expiryPolicy`) определяет, сколько времени должно пройти до устаревания и удаления записи. Отсчет времени можно вести с момента создания, изменения или последнего доступа к записи.

В зависимости от конфигурации памяти записи удаляются из оперативной памяти или с диска:

- **Режим полностью in-memory** (данные хранятся только в оперативной памяти) — устаревшие записи удаляются из оперативной памяти.
- **Персистентный режим** (Native Persistence) — устаревшие записи удаляются из оперативной памяти и с диска. Политика устаревания удаляет записи из файлов партиций без освобождения места. После удаления дисковое пространство можно повторно использовать для добавления новых записей.
- **Режим in-memory + внешнее хранилище** — устаревшие записи удаляются только из оперативной памяти (из DatGrid) и не удаляются из внешнего хранилища (из RDBMS, NoSQL и других баз данных).
- **Режим in-memory + SWAP** — устаревшие записи удаляются из ОЗУ и файлов SWAP.

Чтобы установить политику устаревания записей, используйте любую из стандартных реализаций `javax.cache.expiry.ExpiryPolicy` или создайте собственную.

## Настройка

Пример конфигурации `expiryPolicy`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.CacheConfiguration">
    <property name="name" value="myCache"/>
    <property name="expiryPolicyFactory">
        <bean class="javax.cache.expiry.CreatedExpiryPolicy" factory-method="factoryOf">
            <constructor-arg>
                <bean class="javax.cache.expiry.Duration">
                    <constructor-arg value="MINUTES"/>
                    <constructor-arg value="5"/>
                </bean>
            </constructor-arg>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration<Integer, String> cfg = new CacheConfiguration<Integer, String>();
cfg.setName("myCache");
cfg.setExpiryPolicyFactory(CreatedExpiryPolicy.factoryOf(Duration.FIVE_MINUTES));
```
:::

:::{md-tab-item} C\#/.NET
```c#
class ExpiryPolicyFactoryImpl : IFactory<IExpiryPolicy>
{
    public IExpiryPolicy CreateInstance()
    {
        return new ExpiryPolicy(TimeSpan.FromMilliseconds(100), TimeSpan.FromMilliseconds(100),
            TimeSpan.FromMilliseconds(100));
    }
}

public static void Example()
{
    var cfg = new CacheConfiguration
    {
        Name = "cache_name",
        ExpiryPolicyFactory = new ExpiryPolicyFactoryImpl()
    };
```
:::
::::

Также можно изменить или установить политику устаревания для отдельных операций кеша. Для этого используется специальная обертка кеша, а политика применяется для каждой кеш-операции:

```bash
CacheConfiguration<Integer, String> cacheCfg = new CacheConfiguration<Integer, String>("myCache");

ignite.createCache(cacheCfg);

IgniteCache cache = ignite.cache("myCache")
        .withExpiryPolicy(new CreatedExpiryPolicy(new Duration(TimeUnit.MINUTES, 5)));

// Если кеш не содержит ключ 1, срок действия записи истечет через 5 минут.
cache.put(1, "first value");
```

Тонкий клиент также позволяет устанавливать и менять политику устаревания для отдельных записей — подробнее об этом написано в [официальной документации Apache Ignite](https://ignite.apache.org/releases/latest/javadoc/org/apache/ignite/client/ClientCache.html#withExpirePolicy-javax.cache.expiry.ExpiryPolicy).

## Eager TTL

Устаревшие записи можно удалять из кеша сразу или при первом обращении к ним во время кеш-операции. Данное поведение задается с помощью параметра `eagerTtl` в конфигурации кеша.

Если есть хотя бы один кеш, который настроили с eager TTL (`eagerTtl=true`), DataGrid создает один поток для удаления устаревших записей в фоновом режиме.

Если у параметра `eagerTtl` установлено значение `false`, устаревшие записи удалятся не сразу, а при запросе потоком, который выполняет кеш-операцию. Значение `CacheConfiguration.eagerTtl` по умолчанию — `true`.

Настройка параметра `eagerTtl`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.CacheConfiguration">
    <property name="eagerTtl" value="true"/>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration<Integer, String> cfg = new CacheConfiguration<Integer, String>();
cfg.setName("myCache");

cfg.setEagerTtl(true);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new CacheConfiguration
{
    Name = "cache_name",
    EagerTtl = true
};
```
:::
::::