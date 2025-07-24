# Настройка резервных партиций

По умолчанию DataGrid сохраняет одну копию каждой партиции (одну копию всего набора данных). Если один или несколько узлов отключатся, доступ к партициям, которые хранятся на этих узлах, будет потерян. Если настроить сохранение резервных копий каждой партиции, этой проблемы можно избежать.

:::{admonition} Внимание
:class: danger

По умолчанию резервное копирование отключено.
:::

Резервные копии настраиваются для каждого кеша (таблицы). При настройке двух резервных копий в кластере будут храниться три копии каждой партиции. Одна из партиций будет называться основной (primary), а две другие — резервными (backup). В широком смысле узел с primary-партицией называется «основным узлом для ключей, которые хранятся в партиции». Узел с резервными (backup) партициями называется резервным.

Когда узел с основной для некоторого ключа партицией покидает кластер, DataGrid запускает процесс обмена картами партиций (PME). Если в кластере были настроены резервные партиции, процесс PME назначает одну из них как основную для ключа.

Резервные партиции повышают доступность данных, а в некоторых случаях и скорость операций чтения. DataGrid считывает данные из резервных партиций, если они доступны на локальном узле (это поведение по умолчанию, которое можно отключить — подробнее написано в разделе [«Конфигурация кешей»](cache_setup.md)). При этом резервные партиции увеличивают потребление памяти и размер постоянного хранилища, если оно включено.

## Настройка резервных партиций

Пример, как установить количество резервных партиций:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <!-- Установите имя кеша. -->
            <property name="name" value="cacheName"/>
            <!-- Установите режим кеша. -->
            <property name="cacheMode" value="PARTITIONED"/>
            <!-- Количество резервных копий. -->
            <property name="backups" value="1"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");
cacheCfg.setCacheMode(CacheMode.PARTITIONED);
cacheCfg.setBackups(1);

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "myCache",
            CacheMode = CacheMode.Partitioned,
            Backups = 1
        }
    }
};
Ignition.Start(cfg);
``` 
:::
::::

## Синхронное и асинхронное резервное копирование

Ниже описан пример, как настроить режим синхронизации записи в конфигурации кеша. Укажите синхронность или асинхронность для обновлений основных и резервных копий.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <!-- Установите имя кеша. -->
            <property name="name" value="cacheName"/>
            <!-- Количество резервных копий. -->
            <property name="backups" value="1"/>

            <property name="writeSynchronizationMode" value="FULL_SYNC"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");
cacheCfg.setBackups(1);
cacheCfg.setWriteSynchronizationMode(CacheWriteSynchronizationMode.FULL_SYNC);
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);

// Запустите узел.
Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "myCache",
            WriteSynchronizationMode = CacheWriteSynchronizationMode.FullSync,
            Backups = 1
        }
    }
};
Ignition.Start(cfg);
```
:::
::::

Возможные значения режима синхронизации записи:

| Значение | Описание |
|---|---|
| `FULL_SYNC` | Клиентский узел ожидает, когда запрос на запись или метод `Transaction.commit()` выполнится на всех участвующих удаленных узлах (основных и резервных) |
| `FULL_ASYNC` | Клиентский узел не ожидает ответа от участвующих узлов. Удаленные узлы могут обновить свое состояние после того, как завершится любой из методов на запись кеша, или после завершения метода `Transaction.commit()` |
| `PRIMARY_SYNC` | Режим по умолчанию. Клиентский узел ожидает записи или завершения метода `Transaction.commit()` на основном узле, но не ждет обновлений на узлах с резерными копиями партиций |