# Ребалансировка

## Введение

Если в кластер добавился новый серверный узел или старый узел вышел из него, происходит PME (Partition Map Exchange) — процесс обмена информацией между узлами об актуальном состоянии партиций. В результате выполнения PME начинается ребалансировка — процесс перераспределения основных (primary) и резервных (backup) партиций по всем узлам в новой топологии кластера. DataGrid реализован так, чтобы минимальное количество данных подверглось ребалансировке при вводе или выводе узла из кластера.

Если серверный узел покидает кластер и в конфигурации кеша не настроено количество резервных (backup) партиций, данные этого узла будут утеряны. Если резервные копии настроены, при выходе узла одна из них становится основной (primary) партицией, и запускается процесс ребалансировки данных.

Процесс ребалансировки происходит при изменении количества серверных узлов в кластере. В in-memory-кластерах ребалансировка по умолчанию начинается, когда узел покидает кластер или присоединяется к нему (то есть когда меняется базовая топология). В persistence-кластерах по умолчанию базовую топологию можно изменить только вручную. Чтобы автоматически менять базовую топологию, подключите для нее автоматическую настройку.

DataGrid поддерживает два режима ребалансировки, которые настраиваются в конфигурации кластера:

- Полная ребалансировка — режим, который перемещает партиции между узлами в кластере целиком, а не в виде дельты изменений, как при исторической ребалансировке.
- Историческая ребаланcировка — режим, который поддерживается для кластеров с Native Persistence. Он нужен для случаев, когда узлы покидают кластер на короткое время и на диске хранится большой объем данных. С исторической ребалансировкой партиция получает только дельту изменений, которые произошли, пока ее узел был оффлайн. Подробнее об этом написано в разделе [«Историческая ребалансировка»](historical_rebalancing.md).

## Настройка режима ребалансировки

В DataGrid можно настроить синхронную и асинхронную ребалансировку или отключить ее полностью. В синхронном режиме выполнение ребалансировки блокирует каждую операцию над кешами. В асинхронном режиме процесс ребалансировки выполняется асинхронно. Выполнение ребалансировки данных можно отключить для конкретного кеша.

Чтобы изменить режим ребалансировки данных, установите одно из значений в настройках кеша:

- `SYNC` — синхронный режим. Каждый вызов кеша через публичный API блокируется до окончания ребалансировки данных.
- `ASYNC` — асинхронный режим (выбран по умолчанию). Распределенные кеши доступны во время ребалансировки и в фоновом режиме загружают нужные данные с других узлов кластера.
- `NONE` — режим без ребалансировки данных. Кеши явно заполняются или загружаются по требованию из постоянного хранилища, когда данные доступны.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
        <property name="cacheConfiguration">
            <list>
                <bean class="org.apache.ignite.configuration.CacheConfiguration">
                    <property name="name" value="mycache"/>
                    <!-- Подключите режим синхронной ребалансировки данных. -->
                    <property name="rebalanceMode" value="SYNC"/>
                </bean>
            </list>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

CacheConfiguration cacheCfg = new CacheConfiguration("mycache");

cacheCfg.setRebalanceMode(CacheRebalanceMode.SYNC);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
IgniteConfiguration cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "mycache",
            RebalanceMode = CacheRebalanceMode.Sync
        }
    }
};

// Запустите узел.
var ignite = Ignition.Start(cfg);
```
:::
::::

## Настройка пула потоков ребалансировки данных

По умолчанию ребалансировка данных выполняется в одном потоке на каждом узле. Это значит, что в каждый момент времени используется только один поток для передачи batches из одного узла в другой или для обработки batches, которые поступают из удаленного узла.

Можно увеличить количество потоков, которые берутся из системного пула и используются для ребалансировки. Системный поток берется из пула каждый раз, когда:

- один узел должен отправить batch данных на другой (удаленный) узел;
- узлу нужно обработать batch данных, который поступил из другого (удаленного) узла.

После обработки batch данных поток останавливается.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
        <property name="rebalanceThreadPoolSize" value="4"/>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setRebalanceThreadPoolSize(4);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

:::{admonition} Внимание
:class: danger

Пул системных потоков широко используется во всех операциях, которые связаны с SQL-движком, кешем (`put`, `get` и так далее) и другими модулями. Если увеличить размер пула потоков, которые используются для ребалансировки данных, его производительность может значительно повыситься, а пропускная способность — понизиться.
:::

## Настройка замедления сообщений о ребалансировке (throttling)

При передаче данных с одного узла на другой весь объем делится на batches, каждый из которых отправляется отдельным сообщением. Размер batch и интервал времени, которое узел ждет между сообщениями, можно настроить.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
        <!-- Установите размер batch. -->
        <property name="rebalanceBatchSize" value="#{2 * 1024 * 1024}"/>
        <!-- Установите количество batches, которые питающий узел создаст в начале процесса ребалансировки. -->
        <property name="rebalanceBatchesPrefetchCount" value="3"/>
        <!-- Установите интервал между сообщениями о ребалансировке. -->
        <property name="rebalanceThrottle" value="100"/>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setRebalanceBatchSize(2 * 1024 * 1024);
cfg.setRebalanceBatchesPrefetchCount(3);
cfg.setRebalanceThrottle(100);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
IgniteConfiguration cfg = new IgniteConfiguration
{
    RebalanceBatchSize = 2 * 1024 * 1024,
    RebalanceThrottle = new TimeSpan(0, 0, 0, 0, 100),
    RebalanceBatchesPrefetchCount = 3
};

// Запустите узел.
var ignite = Ignition.Start(cfg);
```
:::
::::

## Другие свойства

В таблице ниже указаны свойства `IgniteConfiguration`, которые относятся к ребалансировке:

:::{admonition} Внимание
:class: danger

`rebalanceDelay` и относящиеся к нему API не рекомендуются к использованию и будут удалены в ближайших релизах.
:::

| Свойство | Описание | Значение по умолчанию |
|---|---|---|
| `rebalanceThreadPoolSize` | Размер пула потоков ребалансировки. Ограничение количества потоков, которые используются для ребалансировки | `min(4, max(1, AVAILABLE_PROC_CNT / 4))` |
| `rebalanceBatchSize` | Размер одного сообщения о ребалансировке, Кб. Перед отправкой алгоритм ребалансировки делит данные каждого узла на несколько batches | `512` |
| `rebalanceBatchesPrefetchCount` | Количество batches, которые питающий узел создаст в начале процесса ребалансировки | `3` |
| `rebalanceThrottle` | Интервал между сообщениями о ребалансировке | `0` (throttling отключен) |
| `rebalanceOrder` | Последовательность, по которой должна выполняться ребаланcировка. Значение больше нуля можно установить только для кешей с режимом ребалансировки `SYNC` или `ASYNC`. Ребалансировка для кешей с меньшим значением выполняется первой. По умолчанию ребалансировка не упорядочена | `0` |
| `rebalanceTimeout` | Тайм-аут для ожидания сообщений о ребалансировке между узлами (в секундах) | `10` |
| `rebalanceDelay` | **Важно:** свойство не рекомендуется к использованию и будет удалено в ближайших релизах.<br><br>Задержка до начала процесса ребалансировки, который запускается после подключения или отключения узла из топологии (в миллисекундах).<br><br>Задержка нужна, если в кластере будет перезапуск узлов, запуск нескольких узлов одновременно или один за другим, и при этом ребалансировка данных не нужна, пока все узлы не будут запущены | `0` (без задержки) |

## Мониторинг процесса ребалансировки

Отслеживать процесс ребалансировки для конкретных кешей можно с помощью JMX.