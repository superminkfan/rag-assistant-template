# Конфигурация кешей

В разделе описывается, как выполнить конфигурирование кеша. После создания кеша его конфигурацию изменить нельзя.

:::{admonition} Кеши и таблицы в DataGrid
:class: hint

Конфигурирование кешей можно выполнить с помощью настройки экземпляров `CacheConfiguration` или через стандартные команды SQL, например `CREATE TABLE`. Подробнее о том, как соотносятся кеши и таблицы в DataGrid, написано в подразделе [«Введение»](introduction.md) раздела «Моделирование данных».
:::

## Пример

Пример настройки кешей:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="myCache"/>
            <property name="cacheMode" value="PARTITIONED"/>
            <property name="backups" value="2"/>
            <property name="rebalanceMode" value="SYNC"/>
            <property name="writeSynchronizationMode" value="FULL_SYNC"/>
            <property name="partitionLossPolicy" value="READ_ONLY_SAFE"/>
            <!-- Другие параметры. -->
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration("myCache");
 
cacheCfg.setCacheMode(CacheMode.PARTITIONED);
cacheCfg.setBackups(2);
cacheCfg.setRebalanceMode(CacheRebalanceMode.SYNC);
cacheCfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
cacheCfg.setPartitionLossPolicy(PartitionLossPolicy.READ_ONLY_SAFE);
 
IgniteConfiguration cfg = new IgniteConfiguration();
fg.setCacheConfiguration(cacheCfg);
 
// Запустите узел.
Ignition.start(cfg);
```
:::

:::{md-tab-item} С#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "myCache",
            CacheMode = CacheMode.Partitioned,
            Backups = 2,
            RebalanceMode = CacheRebalanceMode.Sync,
            WriteSynchronizationMode = CacheWriteSynchronizationMode.FullSync,
            PartitionLossPolicy = PartitionLossPolicy.ReadOnlySafe
        }
    }
};
Ignition.Start(cfg);
```
:::

:::{md-tab-item} SQL
```sql
CREATE TABLE IF NOT EXISTS Person (
id int,
city_id int,
name varchar,
age int,
company varchar,
PRIMARY KEY (id, city_id)
) WITH "cache_name=myCache,template=partitioned,backups=2";
```
:::
::::

:::{list-table} Параметры в SQL
:header-rows: 1
 
+   *   Параметр
    *   Описание
    *   Значение по умолчанию
+   *   `name`
    *   Имя кеша
    *   —
+   *   `cacheMode`
    *   Устанавливает способ распределения данных кеша в кластере.
    
        В режиме `PARTITIONED` общий объем данных разделен на партиции, которые равномерно распределяются между узлами.
        
        В режиме `REPLICATED` все данные копируются на каждый узел кластера.
        
        Подробнее об этом написано в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных»
    *   `PARTITIONED`
+   *   `writeSynchronizationMode`
    *   Режим синхронизации записи. Подробнее о нем написано в разделе [«Настройка резервных партиций»](setting_up_backup_partitions.md)
    *   `PRIMARY_SYNC`
+   *   `rebalanceMode`
    *   Режим ребалансировки. Возможные значения:
        - `SYNC` — любые запросы на API кеша заблокированы до завершения ребалансировки.
        - `ASYNC` — ребалансировка выполняется в фоновом режиме.
        - `NONE` — ребалансировка не выполняется
    *   `ASYNC`
+   *   `backups`
    *   Количество резервных партиций кеша. Подробнее о них написано разделе в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных»
    *   `0`
+   *   `partitionLossPolicy`
    *   [Политика потери партиций](partition_loss_policy.md)
    *   `IGNORE`
+   *   `readFromBackup`
    *   Задает возможность чтения записей кеша из резервной (backup) партиции, если она доступна на локальном узле, вместо отправки запроса на удаленный основной (primary) узел
    *   `true`
+   *   `queryParallelism`
    *   Количество потоков в узле при обработке SQL-запроса. Подробнее об этом написано в подразделе «Параллелизм запросов» документа [«Настройка производительности»](../../troubleshooting-and-performance/md/performance-tuning.md)
    *   `1`
:::

## Шаблоны кеша (Cache Template)

Шаблон кеша — экземпляр `CacheConfiguration`, который можно зарегистрировать в кластере и использовать как основу для создания новых кешей или SQL-таблиц. Кеш или таблица, которые созданы на основе шаблона, наследуют все его свойства.

Шаблоны можно использовать:

- на серверах и клиентах (тонких и толстых);
- в SQL, например `CREATE TABLE`;
- в таких командах, как `createCache` и `getOrCreateCache`;
- в вызовах REST API.

Например, тонкие клиенты и SQL не поддерживают некоторые свойства конфигурации кеша. Для обхода этого ограничения можно использовать шаблоны.

Для создания шаблона определите конфигурацию кеша и добавьте ее в экземпляр DataGrid, как показано в примере ниже. Для определения шаблона кеша в файле XML-конфигурации добавьте в название шаблона символ `*`. Он указывает на то, что конфигурация является шаблоном, а не реальным кешем.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <list>
            <bean abstract="true" class="org.apache.ignite.configuration.CacheConfiguration" id="cache-template-bean">
                <!-- При создании шаблона с помощью XML-конфигурации нужно добавить символ `*` в название шаблона. -->
                <property name="name" value="myCacheTemplate*"/>
                <property name="cacheMode" value="PARTITIONED"/>
                <property name="backups" value="2"/>
                <!-- Другие параметры кеша. -->
            </bean>
        </list>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration igniteCfg = new IgniteConfiguration();
 
try (Ignite ignite = Ignition.start(igniteCfg)) {
    CacheConfiguration cacheCfg = new CacheConfiguration("myCacheTemplate");
 
    cacheCfg.setBackups(2);
    cacheCfg.setCacheMode(CacheMode.PARTITIONED);
 
    // Регистрация шаблона кеша.
    ignite.addCacheConfiguration(cacheCfg);
}
```
:::

:::{md-tab-item} С#/.NET
```c#
var ignite = Ignition.Start();
 
var cfg = new CacheConfiguration
{
    Name = "myCacheTemplate*",
    CacheMode = CacheMode.Partitioned,
    Backups = 2
};
 
ignite.AddCacheConfiguration(cfg);
```
:::
::::

Как только шаблон кеша зарегистрирован в кластере, его можно использовать для создания другого кеша с такой же конфигурацией.