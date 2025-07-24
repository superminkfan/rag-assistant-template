# События мониторинга

## Введение

Под мониторингом кластера DataGrid понимается мониторинг каждого узла топологии (как серверных, так и клиентских).

Основной задачей мониторинга является отслеживание критически важных атрибутов системы и оповещение администраторов при наличии проблем.

Помимо мониторинга кластера рекомендуется производить мониторинг JVM и ОС, в рамках которых происходит запуск DataGrid.

DataGrid имеет несколько механизмов мониторинга:

-   Legacy;
-   New Metrics System;
-   Системные представления (System Views).

## Legacy

Под Legacy понимают подход публикации метрик, который использовался до версии DataGrid 2.8.

Метрики при данном подходе публикуются преимущественно через JMX.

При данном подходе разработчик сам определяет:

-   формат имени метрики;
-   тип метрики;
-   способ публикации.

Доступ к метрикам осуществляется через JMX.

### Архитектура legacy-системы

Через JMX доступно следующее дерево групп метрик:

| Имя группы | Описание |
|---|---|
| `Persistent Store` | Метрики PDS (Persistent Data Store) |
| `SQL Query` | Свойства Timeout для SQL |
| `Thread Pools` | Метрики системных потоков |
| `Baseline` | Свойства Baseline |
| `Clients` | Информация об подключенных тонких клиентах |
| `Cache groups` | Метрики кеш-групп |
| `DataRegionMetrics` | Метрики региона данных (Data Region) |
| `DataStorage` | Дополнительные свойства PDS |
| `Encryption` | Информация об ключах безопасности |
| `IgniteCluster` | Информация об идентификации кластера |
| `Kernal` | Метрики локального узла DataGrid и кластера DataGrid |
| `SPIs` | Метрики различных подсистем (SPI) DataGrid |
| `TransactionMetrics` | Метрики транзакций |
| `Transactions` | Настройки свойств транзакций (Timeout/Threshold) |
| `Security` | Метрики плагина безопасности |
| `%Имя_кеша%` | Метрики кеша |

## New Metrics System

Начиная с версии DataGrid 2.8, доступен новый механизм сбора метрик — New Metrics System. Он заменяет собой старую систему сбора метрик — Legacy. Данный механизм доступен и в DataGrid.

У каждой метрики в системе есть название и значение, которое она возвращает. Это значение может быть представлено в виде переменных типов `long`, `String` или `double`, либо в виде Java-объекта. Некоторые метрики представлены в виде гистограмм.

Благодаря появлению New Metrics System, стало возможным экспортировать метрики, используя различные технологии, например:

-   JMX;
-   SQL View;
-   Prometheus (HTTP);
-   OpenCensus.

:::{admonition} Примечание
:class: note

В New Metrics System предусмотрена возможность создания пользовательских экспортеров при помощи интерфейса `MetricExporterSpi`.
:::

### Архитектура New Metrics System

В New Metrics System применены следующие решения относительно архитектуры:

-   В отличие от legacy-системы метрики в New Metrics System локальные. Они отражают состояние конкретного узла, на котором выполняется мониторинг.

    Данный подход обусловлен тем, что при использовании глобальных метрик DataGrid занимался подсчетом метрики для всего кластера, и это было затратной операцией, так как кластер может состоять из множества узлов.

-   В New Metrics System используется иерархическая структура метрик.

    Использование такой системы обусловлено наличием в DataGrid множества различных подсистем (SPI) на разных уровнях. Каждая из этих подсистем имеет определенный набор метрик. Среди этих подсистем есть те, которые обладают собственной иерархией, например, кеш. Метрики кеша собираются отдельно для каждого кеша, а не для всех сразу.

-   Был разработан стандарт названия метрик. Он основан на иерархической структуре метрик: `<registry_name>.<metric_name>`.

    :::{admonition} Пример
    :class: hint

    `tx.LastCommitTime`

    где:

    -   `tx` — имя реeстра;
    -   `LastCommitTime` — имя метрики.
    :::

В New Metrics System доступно следующее дерево групп метрик:

| Имя реeстра | Описание |
|---|---|
| `cache` | Метрики кеш-процессора |
| `cache.{cache_name}.{near}` | Метрики кеша |
| `cacheGroups.{group_name}` | Метрики кеш-группы |
| `client.connector` | Метрики коннектора тонкого клиента |
| `cluster` | Метрики кластера |
| `communication` | Метрики Communication SPI |
| `compute.jobs` | Метрики вычислительных задач |
| `ignite` | Метрики локального узла |
| `io.communication` | IO метрики Communication SPI |
| `io.datastorage` | IO метрики PDS |
| `io.dataregion.{data_region_name}` | IO метрики региона данных (Data Region) |
| `io.discovery` | IO метрики Discovery |
| `io.statistics.cacheGroups.{group_name}` | IO метрики кеш-группы |
| `io.statistics.sortedIndexes.{cache_name}.{index_name}` | IO метрики сортированных индексов |
| `pme` | Метрики PME |
| `rest.client` | Метрики коннектора тонкого REST-клиента |
| `security` | Метрики безопасности |
| `snapshot` | Метрики снепшотов |
| `snapshot-restore` | Метрики восстановления из снепшота |
| `sys` | Системные метрики |
| `sql.parser.cache` | Метрики кеша SQL-парсера |
| `sql.queries.user` | Метрики пользовательских SQL-запросов |
| `threadPools.{thread_pool_name}` | Метрики системных потоков |
| `tx` | Метрики транзакций |


### Конфигурация экспортеров и включение метрик в New Metrics System

:::{admonition} Важно
:class: attention
При включенном плагине безопасности трафик оборачивается в SSL и включается двухфакторная аутентификация. Для сбора метрик необходимо настроить HTTPS-соединение с передачей учетных записей.

Подробнее о плагине безопасности написано в подразделе [«Плагин безопасности для DataGrid»](administration-scenarios.md#плагин-безопасности-для-datagrid) раздела «Сценарии администрирования».
:::

Для включения возможности экспорта метрик укажите в конфигурации класса `IgniteConfiguration` конкретный экспортер (интерфейс `metricExporterSpi`), который должна использовать подсистема метрик:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="metricExporterSpi">
        <list>
            <bean class="org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi"/>
            <bean class="org.apache.ignite.spi.metric.jmx.JmxMetricExporterSpi"/>
            <bean class="org.apache.ignite.spi.metric.sql.SqlViewMetricExporterSpi"/>
            <bean class="org.apache.ignite.spi.metric.log.LogExporterSpi"/>
            <bean class="org.apache.ignite.spi.metric.opencensus.OpenCensusMetricExporterSpi"/>
        </list>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setMetricExporterSpi(new JmxMetricExporterSpi(), new SqlViewMetricExporterSpi());

Ignite ignite = Ignition.start(cfg);
```
:::
::::

#### Экспортер метрик `ignite-http-metrics-exporter`

`ignite-http-metrics-exporter` — это библиотека, позволяющая публиковать метрики мониторинга DataGrid на HTTP-странице. Метрики публикуются в формате, совместимом с системой мониторинга Prometheus.

:::{admonition} Примечание
:class: note

Библиотека может быть использована в случаях, когда нет возможности использовать технологию JMX.
:::

##### Установка

:::{admonition} Внимание
:class: danger

`ignite-http-metrics-exporter` имеет зависимость от библиотек `ignite-rest-http`. После развертывания и перед запуском DataGrid проверьте и убедитесь, что библиотеки `ignite-rest-http` установлены и запускаются вместе с DataGrid.

`<DataGrid lib path>` — путь к библиотекам DataGrid.
:::

Для установки библиотеки `ignite-http-metrics-exporter` скопируйте или перенесите директорию `ignite-http-metrics-exporter` из директории с дополнительными библиотеками (`<DataGrid lib path>/libs/optional`) в директорию с библиотеками, используемыми для запуска DataGrid (`<DataGrid lib path>/libs`).

:::{admonition} Пример
:class: hint

`cp -r <DataGrid lib path>/libs/optional/ignite-http-metrics-exporter` копируется в `<DataGrid lib path>/libs/`.
:::

##### Настройка

Настройка `ignite-http-metrics-exporter` позволяет предопределять HTTP-порт, на котором будут публиковаться метрики и ссылки (endpoint) с публикуемыми метриками.

**Настройка HTTP-порта**

Для настройки HTTP-порта объявите опцию `port` в классе `org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi`:

:::{code-block} xml
:caption: XML
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="metricExporterSpi">
        <bean class="org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi">
            <property name="port" value="8081"/>
        </bean>
    </property>
</bean>
:::

Если порт не задан, будет использован порт по умолчанию: `8081`.

Дополнительно порт можно задать в качестве JVM-опции или переменной окружения. Для этого укажите требуемый порт в переменной `http_metrics_exporter.port`. Если порт указан в нескольких местах, библиотека будет использовать порт по следующей схеме приоритетов:

-   0 — конфигурационный файл;
-   1 — JVM-опция;
-   2 — переменная окружения.

Где 0 — наивысший приоритет, а 2 — наименьший.

**Настройка конечных точек (endpoints)**

Для настройки конечных точек укажите требуемый реестр метрик и их конечный `endpoint` в конфигурации, как показано ниже. Категорию можно указывать как в виде списка, так и в виде регулярного выражения.

Для указания списка используется класс `org.apache.ignite.viewer.config.NamesListGroup`.

Для указания регулярного выражения используется класс `org.apache.ignite.viewer.config.RegExpGroup`.

::::{admonition} Пример конфигурации
:class: hint 
:collapsible:

:::{code-block} xml
:caption: XML
    <property name="metricExporterSpi">
      <list>
        <bean class="org.apache.ignite.spi.metric.jmx.JmxMetricExporterSpi"/>
        <bean class="org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi">
          <property name="port" value="8081"/>
          <property name="globalLabels">
            <list>
              <bean class="org.apache.ignite.viewer.config.Label">
                <constructor-arg index="0" value="globalLabel" />
                <constructor-arg index="1" value="123"/>
              </bean>
            </list>
          </property>

          <property name="groups">
            <list>
              <bean class="org.apache.ignite.viewer.config.RegExpGroup">
                <property name="context" value="/all"/>
                <property name="regExp" value=".*"/>
                <property name="labels">
                  <list>
                    <bean class="org.apache.ignite.viewer.config.Label">
                      <constructor-arg index="0" value="groupLabel" />
                      <constructor-arg index="1" value="value" />
                    </bean>
                  </list>
                </property>
              </bean>
              <bean class="org.apache.ignite.viewer.config.RegExpGroup">
                <property name="context" value="/threadPools"/>
                <property name="regExp" value="threadPools\..*"/>
              </bean>
              <bean class="org.apache.ignite.viewer.config.NamesListGroup">
                <property name="context" value="/pme"/>
                <property name="names">
                  <value>pme</value>
                </property>
              </bean>
              <bean class="org.apache.ignite.viewer.config.NamesListGroup">
                <property name="context" value="/sql"/>
                <property name="names">
                  <value>sql</value>
                </property>
              </bean>
            </list>
          </property>
        </bean>
      </list>
    </property>
:::
::::

где `context` — произвольное имя, которое впоследствии будет указываться как часть URL для сбора метрик. Для выбора групп метрик используется одно из свойств — `names` или `regExp`:
-   `names` — точное имя реестра (подробная информация содержится в подразделе «Метрики New Metrics System»);
-   `regExp` — имя реестра, которое можно найти через регулярное выражение.

Каждое свойство `context` описывает конечный `endpoint` публикуемых метрик, а свойства `regExp` и `names` описывают искомый реестр. Доступ к метрикам осуществляется по адресу: `http://ip:port/context`, где:

-   `ip` — ip-адрес узла DataGrid;
-   `port` — порт для `ignite-http-metrics-exporter`;
-   `context` — настроенный `context` для метрик.

**Свойства `labels` и `globalLabels`**

У классов `org.apache.ignite.viewer.config.RegExpGroup` и `org.apache.ignite.viewer.config.NamesListGroup`, указанных в конфигурации выше, есть свойство `labels` для генерации имен метрик с пользовательскими метками.

::::{admonition} Пример конфигурации свойства `labels`
:class: hint

:::{code-block} xml
:caption: XML
<bean class="org.apache.ignite.viewer.config.RegExpGroup">
      <property name="context" value="/all"/>
      <property name="regExp" value=".*"/>
      <property name="labels">
        <list>
          <bean class="org.apache.ignite.viewer.config.Label">
            <constructor-arg index="0" value="groupLabel" />
            <constructor-arg index="1" value="value" />
          </bean>
        </list>
      </property>
</bean>
:::
::::

При указании данного свойства в именах каждой метрики для данного `context` будет проставляться пользовательская метка.

У класса `org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi` есть свойство `globalLabels` для генерации имен метрик с пользовательскими метками.

::::{admonition} Пример конфигурации свойства `globalLabels`
:class: hint

:::{code-block} xml
:caption: XML
<property name="metricExporterSpi">
  <list>
    <bean class="org.apache.ignite.spi.metric.jmx.JmxMetricExporterSpi"/>
    <bean class="org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi">
      <property name="port" value="8081"/>
      <property name="globalLabels">
        <list>
          <bean class="org.apache.ignite.viewer.config.Label">
            <constructor-arg index="0" value="globalLabel" />
            <constructor-arg index="1" value="123"/>
          </bean>
        </list>
      </property>
    </bean>
  </list>
</property>
:::
::::

При указании данного свойства в именах каждой метрики для каждого `context` будет проставляться пользовательская метка.

Примеры метрик:

1. Со свойством `globalLabels`: `sys_ThreadCount{globalLabel="value"} 50`.
2. Со свойствами `globalLabels` и `labels`: `sys_ThreadCount{globalLabel="value", groupLabel="value"} 50`.

Данные свойства не исключают, а дополняют друг друга.

#### Фильтр метрик 

С помощью свойства `exportFilter` можно задать фильтр регистров метрик, которые будут экспортироваться. 

В поставку входит реализация фильтра на основе регулярного выражения — `RegexpMetricFilter`. Он позволяет экспортировать только те регистры метрик, которые удовлетворяют и соответствуют заданному регулярному выражению.

Для включения фильтрации добавьте в Spring XML конфигурацию экспортера метрик следующий блок:

:::{code-block} xml
:caption: XML
<property name="exportFilter">
  <bean class="org.apache.ignite.spi.metric.RegexpMetricFilter">
    <constructor-arg name="regNameRegex" value="<reg-exp>"/>
  </bean>
</property>
:::

где `<constructor-arg name="regNameRegex" value="<reg-exp>"/>` — параметр задания регулярного выражения для фильтрации регистров метрик; регулярное выражение указывается вместо `<reg-exp>`.

::::{admonition} Пример включения фильтрации метрик, начинающихся с `other`,  для экспортера `LogExporterSpi`
:class: hint

:::{code-block} xml
:caption: XML
<property name="metricExporterSpi">
  <bean class="org.apache.ignite.spi.metric.log.LogExporterSpi">
    <property name="exportFilter">
      <bean class="org.apache.ignite.spi.metric.RegexpMetricFilter">
        <constructor-arg name="regNameRegex" value="other.*"/>
      </bean>
    </property>
    <property name="period">
      <util:constant static-field="org.apache.ignite.internal.metric.AbstractExporterSpiTest.EXPORT_TIMEOUT"/>
    </property>
  </bean>
</property>
:::
::::

## Метрики в DataGrid

Базовые задачи мониторинга в DataGrid включают в себя метрики. Для доступа к метрикам существует несколько подходов:

-   использование New Metrics System;
-   доступ к метрикам из кода;
-   использование [Системных представлений](#системные-представления).

## Виды метрик в DataGrid

Метрики в DataGrid бывают двух видов:

-   глобальные;
-   относящиеся к определенному узлу;
-   относящиеся к кешам.

## Глобальные метрики

Глобальные метрики предоставляют общую информацию о кластере, например о количестве узлов и состоянии кластера.

Данная информация доступна на любом из узлов кластера.

## Метрики, относящиеся к определенному узлу

Данный вид метрик предоставляет информацию о конкретном узле кластера, на котором администратор запрашивает метрики. К примеру, такие метрики предоставляют информацию, касающуюся:

-   потребления памяти;
-   региона данных;
-   размера WAL-журнала;
-   размера очереди и т. д.

## Метрики, относящиеся к кешам

Метрики, относящиеся к кешам, могут быть как глобальными, так и относиться к определенному узлу.

:::{admonition} Пример
:class: hint

Общее количество записей — это глобальная метрика, и получить ее можно на любом узле.

Также можно получить количество записей в кеше определенного узла, но в этом случае метрика будет относиться к определенному узлу.
:::

### Включение метрик в DataGrid

:::{admonition} Внимание
:class: danger

Сбор метрик — затратная операция, которая может привести к снижению производительности приложения. По этой причине некоторые метрики по умолчанию отключены.
:::

Для доступа к метрикам по JMX включите возможность использования удаленного подключения к JVM:

```text
-Dcom.sun.management.jmxremote
-Dcom.sun.management.jmxremote.port=1098
-Dcom.sun.management.jmxremote.authenticate=false
-Dcom.sun.management.jmxremote.ssl=false
```

Также рекомендуется отключать отображение `CLASS LOADER ID` в MBean-путях:

```text
-DIGNITE_MBEAN_APPEND_CLASS_LOADER_ID=false`
```

:::{admonition} Внимание
:class: danger

Если в рамках одной JVM происходит запуск нескольких экземпляров DataGrid, отключать отображение `CLASS LOADER ID` не рекомендуется.
:::

#### Включение кеш-метрик

Для включения кеш-метрик необходимо использовать любой из указанных ниже методов для каждого кеша, для которого необходим мониторинг:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<property name="cacheConfiguration">
    <list>
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="mycache"/>
            <!-- Включение статистики для кеша. -->
            <property name="statisticsEnabled" value="true"/>
        </bean>
    </list>
</property>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

CacheConfiguration cacheCfg = new CacheConfiguration("test-cache");

// Включение статистики для кеша.
cacheCfg.setStatisticsEnabled(true);

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
        new CacheConfiguration("my-cache")
        {
            EnableStatistics = true
        }
    }
};

var ignite = Ignition.Start(cfg);
```
:::
::::

Для каждого кеша на узле DataGrid создает два JMX Bean:

1.   Bean, содержащий информацию о кеше на определенном узле.
2.   Bean, содержащий общую информацию о кешах всех узлов кластера.

#### Включение метрик для регионов данных

Метрики регионов данных отражают информацию о регионах данных и включают в себя информацию об объеме памяти и размере хранилища в регионе.

Для включения метрики региона измените [конфигурацию региона данных](https://ignite.apache.org/docs/latest/memory-configuration/data-regions). Пример включения метрик для одного региона данных по умолчанию и одного дополнительного региона данных:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="dataStorageConfiguration">
        <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
            <property name="defaultDataRegionConfiguration">
                <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                    <!-- Включение метрик для региона данных по умолчанию. -->
                    <property name="metricsEnabled" value="true"/>
                    <!-- Прочие свойства. -->
                </bean>
            </property>
            <property name="dataRegionConfigurations">
                <list>
                    <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                        <!-- Пользовательское название региона данных. -->
                        <property name="name" value="myDataRegion"/>
                        <!-- Включение метрик для конкретного региона данных.  -->
                        <property name="metricsEnabled" value="true"/>

                        <property name="persistenceEnabled" value="true"/>
                        <!-- Прочие свойства. -->
                    </bean>
                </list>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

DataStorageConfiguration storageCfg = new DataStorageConfiguration();

DataRegionConfiguration defaultRegion = new DataRegionConfiguration();
defaultRegion.setMetricsEnabled(true);

storageCfg.setDefaultDataRegionConfiguration(defaultRegion);

// Создание нового региона данных.
DataRegionConfiguration regionCfg = new DataRegionConfiguration();

// Имя региона данных.
regionCfg.setName("myDataRegion");

// Включение метрик для конкретного региона данных.
regionCfg.setMetricsEnabled(true);

// Конфигурация региона данных.
storageCfg.setDataRegionConfigurations(regionCfg);

// Прочие свойства.

// Применение новой конфигурации.
cfg.setDataStorageConfiguration(storageCfg);

Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        DefaultDataRegionConfiguration = new DataRegionConfiguration
        {
            Name = DataStorageConfiguration.DefaultDataRegionName,
            MetricsEnabled = true
        },
        DataRegionConfigurations = new[]
        {
            new DataRegionConfiguration
            {
                Name = "myDataRegion",
                MetricsEnabled = true
            }
        }
    }
};

var ignite = Ignition.Start(cfg);
```
:::
::::

#### Включение метрик, относящихся к Native Persistence

Метрики, относящиеся к Native Persistence, также можно включить или отключить двумя способами:

1.  В конфигурации хранилища:

    ::::{md-tab-set}
    :::{md-tab-item} XML
    ```xml
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="dataStorageConfiguration">
        <bean class="org.apache.ignite.configuration.DataStorageConfiguration">

            <!-- Метрики Persistence-хранилища данных. -->
            <property name="metricsEnabled" value="true"/>

            <property name="defaultDataRegionConfiguration">
                <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                    <property name="persistenceEnabled" value="true"/>

                    <!-- Включение метрик для региона данных по умолчанию. -->
                    <!-- property name="metricsEnabled" value="true"/ -->
                    <!-- Прочие свойства. -->
                </bean>
            </property>
        </bean>
    </property>
    </bean>
    ```
    :::

    :::{md-tab-item} Java
    ```java
    IgniteConfiguration cfg = new IgniteConfiguration();

    DataStorageConfiguration storageCfg = new DataStorageConfiguration();
    storageCfg.setMetricsEnabled(true);

    // Применение новой конфигурации.
    cfg.setDataStorageConfiguration(storageCfg);

    Ignite ignite = Ignition.start(cfg);
    ```
    :::

    :::{md-tab-item} C\#/.NET
    ```c#
    var cfg = new IgniteConfiguration
    {
        DataStorageConfiguration = new DataStorageConfiguration
        {
            MetricsEnabled = true
        }
    };

    var ignite = Ignition.Start(cfg);
    ```
    :::
    ::::

2. Используя следующий MXBean (во время работы приложения):

    :::{code-block} java
    :caption: Java
    org.apache:group="Persistent Store",name=DataStorageMetrics
    :::

    | Операция | Описание |
    |---|---|
    | `EnableMetrics` | Включение метрик Persistence-хранилища данных |
    | `DisableMetrics` | Отключить сбор метрик для конкретного региона данных |

### Метрики Legacy

#### Использование оперативной памяти

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `PagesFillFactor` | float | Средний размер данных в страницах в качестве множителя размера страницы. Когда режим Native Persistence включен, данная метрика применяется только для Persistence-хранилища (страниц, хранящихся на диске) | Узел |
| `TotalUsedPages` | long | Число используемых в текущий момент страниц с данными. Когда режим Native Persistence включен, данная метрика применяется только для Persistence-хранилища (страниц, хранящихся на диске) | Узел |
| `PhysicalMemoryPages` | long | Число страниц, размещенных в ОЗУ | Узел |
| `PhysicalMemorySize`  | long   | Место, занятое в ОЗУ в байтах | Узел |

#### Размер хранилища

Когда включен режим Native Persistence, сохраняются все данные приложения на диске. Общее количество данных, которые каждый узел содержит на диске, состоит из Persistence-хранилища (данные приложений), файлов WAL-журнала, а также файлов архива WAL-журнала.

##### Размер Persistence-хранилища

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `TotalAllocatedSize` | long | Место, занятое на диске для всего хранилища данных в байтах. Когда режим Native Persistence отключен, метрика показывает общий размер занятого пространства в ОЗУ | Узел |
| `WalTotalSize` | long | Общий размер WAL-файлов в байтах, включая файлы архива WAL-журнала | Узел |
| `WalArchiveSegments` | int | Число сегментов WAL-журнала в архиве | Узел |

##### Размер региона данных

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `TotalAllocatedSize` | long | Место, занятое для конкретного региона данных в байтах. Когда режим Native Persistence отключен, метрика показывает общий размер занятого пространства в ОЗУ | Узел |
| `PagesFillFactor` | float | Среднее количество данных в страницах в качестве множителя размера страницы | Узел |
| `TotalUsedPages` | long | Число используемых в настоящий момент страниц с данными | Узел |
| `PhysicalMemoryPages` | long | Число страниц с данными в конкретном регионе данных, содержащееся в ОЗУ | Узел |
| `PhysicalMemorySize` | long | Занятое место в ОЗУ в байтах | Узел |

##### Размер кеш-группы

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `TotalAllocatedSize` | long | Место, занятое на конкретном узле для кеш-группы | Узел |

#### Операции создания контрольных точек

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `DirtyPages` | long | Число страниц в памяти, которые были изменены, но еще не были синхронизированы с диском. Такие страницы будут записаны на диск при создании следующей контрольной точки | Узел |
| `LastCheckpointDuration` | long | Время, за которое была создана последняя контрольная точка (в миллисекундах) | Узел |
| `CheckpointBufferSize` | long | Размер буфера контрольной точки | Глобально |

#### Ребалансировка

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `RebalancingStartTime` | long | Показывает время начала ребалансировки локальных партиций для кеша. Если локальные партиции не участвуют в ребалансировке, данная метрика возвращает 0. Время возвращается в миллисекундах | Узел |
| `EstimatedRebalancingFinishTime` | long | Ожидаемое время завершения процесса ребалансировки | Узел |
| `KeysToRebalanceLeft` | long | Число ключей на узле, которые необходимо ребалансировать. Данную метрику можно отслеживать, чтобы понимать, когда заканчивается процесс ребалансировки | Узел |

#### Топология

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `TotalServerNodes` | long | Число серверных узлов в кластере | Глобально |
| `TotalClientNodes` | long   | Число клиентских узлов в кластере | Глобально |
| `TotalBaselineNodes` | long | Число узлов, зарегистрированных в базовой топологии. При отключении узла он остается зарегистрированным в базовой топологии, и удалять его необходимо вручную | Глобально |
| `ActiveBaselineNodes` | long | Число активных узлов в базовой топологии | Глобально |

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `Coordinator` | String | ID текущего узла координатора | Глобально |
| `CoordinatorNodeFormatted` | String | Подробная информация об узле-координаторе. Пример: `TcpDiscoveryNode [id=e07ad289-ff5b-4a73-b3d4-d323a661b6d4, consistentId=fa65ff2b-e7e2-4367-96d9-fd0915529c25, addrs=[0:0:0:0:0:0:0:1%lo, xxx.x.x.x, xxx.xx.x.xxx], sockAddrs=[mymachine.local/xxx.xx.x.xxx:47500, /0:0:0:0:0:0:0:1%lo:47500, /xxx.x.x.x:47500], discPort=47500, order=2, intOrder=2, lastExchangeTime=1568187777249, loc=false, ver=8.7.5#20190520-sha1:d159cd7a, isClient=false]` | |

#### Кеши

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `CacheSize` | long | Общее количество записей в кеше по всем узлам в кластере | Глобально |
| `CacheSize` | long | Число записей кеша, сохраненных на локальном узле | Узел |

#### Транзакции

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `LockedKeysNumber` | long | Число ключей, заблокированных на узле | Узел |
| `TransactionsCommittedNumber` | long | Число транзакций, зафиксированных на узле | Узел |
| `TransactionsRolledBackNumber` | long | Число транзакций, которые «откатились» | Узел |
| `OwnerTransactionsNumber` | long | Число транзакций, инициированных в узле | Узел |
| `TransactionsHoldingLockNumber` | long | Число открытых транзакций, которые имеют блокировку как минимум на один ключ на узле | Узел |

#### Клиентские подключения

| Имя | Тип | Описание |
|---|---|---|
| Connections | `java.util.List<String>` | Список строк. Каждая строка содержит информацию о подключении: `JdbcClient [id=4294967297, user=<anonymous>, rmtAddr=xxx.x.x.x:39264, locAddr=xxx.x.x.x:10800]` |

| Операция | Описание |
|---|---|
| `dropConnection (id)` | Отключить определенного клиента |
| `dropAllConnections` | Отключить всех клиентов |

#### Очереди сообщений

Когда очереди в пулах потоков растут, это означает, что узел не справляется с нагрузкой либо что при обработке сообщений в очереди произошла ошибка. Постоянное увеличение очереди может привести к возникновению ошибки ООМ (`OutOfMemoryError`).

##### Очередь communication-сообщений

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `OutboundMessagesQueueSize` | int | Размер очереди исходящих communication-сообщений | Узел |

##### Очередь discovery-сообщений

| Имя | Тип | Описание | Покрытие |
|---|---|---|---|
| `MessageWorkerQueueSize` | int | Размер очереди discovery-сообщений, ожидающих отправки на другие узлы | Узел |
| `AvgMessageProcessingTime` | long | Среднее время обработки сообщений | Узел |

### Метрики New Metrics System

#### Система

Имя реестра: `sys`

| Имя | Тип | Описание |
|---|---|---|
| `CpuLoad` | double | Нагрузка на процессор |
| `CurrentThreadCpuTime` | long | `ThreadMXBean.getCurrentThreadCpuTime()` |
| `CurrentThreadUserTime`| long | `ThreadMXBean.getCurrentThreadUserTime()` |
| `DaemonThreadCount` | integer | `ThreadMXBean.getDaemonThreadCount()` |
| `GcCpuLoad` | double | Нагрузка на процессор при сборке мусора |
| `PeakThreadCount` | integer| `ThreadMXBean.getPeakThreadCount` |
| `SystemLoadAverage` | java.lang.Double | `OperatingSystemMXBean.getSystemLoadAverage()` |
| `ThreadCount` | integer | `ThreadMXBean.getThreadCount` |
| `TotalExecutedTasks` | long | Общее количество выполненных задач |
| `TotalStartedThreadCount` | long | `ThreadMXBean.getTotalStartedThreadCount` |
| `UpTime` | long | `RuntimeMxBean.getUptime()` |
| `memory.heap.committed` | long | `MemoryUsage.getHeapMemoryUsage().getCommitted()` |
| `memory.heap.init` | long | `MemoryUsage.getHeapMemoryUsage().getInit()` |
| `memory.heap.used` | long | `MemoryUsage.getHeapMemoryUsage().getUsed()` |
| `memory.nonheap.committed` | long | `MemoryUsage.getNonHeapMemoryUsage().getCommitted()` |
| `memory.nonheap.init` | long | `MemoryUsage.getNonHeapMemoryUsage().getInit()` |
| `memory.nonheap.max` | long | `MemoryUsage.getNonHeapMemoryUsage().getMax()` |
| `memory.nonheap.used` | long | `MemoryUsage.getNonHeapMemoryUsage().getUsed()` |

#### Кеши

Имя реестра: `cache.{cache_name}.{near}`

| Имя | Тип | Описание |
|---|---|---|
| `CacheEvictions` | long | Общее число вытеснений из кеша |
| `CacheGets` | long | Общее число `get`-запросов к кешу |
| `CacheHits` | long | Число выполненных кешем `get`-запросов |
| `CacheMisses` | long | «Промах» (miss) – это невыполненный `get`-запрос |
| `CachePuts` | long | Общее число `put`-запросов к кешу |
| `CacheRemovals` | long | Общее число удалений из кеша |
| `CacheTxCommits` | long | Общее число фиксаций транзакций |
| `CacheTxRollbacks` | long | Общее число откатов транзакций |
| `CacheSize` | long | Размер локального кеша |
| `CommitTime` | histogram | Время фиксирования в наносекундах |
| `CommitTimeTotal` | long | Общее время фиксирования в наносекундах |
| `ConflictResolverAcceptedCount` | long | Количество записей, которые приняли в результате решения конфликта |
| `ConflictResolverRejectedCount` | long | Количество записей, которые отклонили в результате решения конфликта |
| `ConflictResolverMergedCount` | long | Количество записей, которые объединили в результате решения конфликта |
| `EntryProcessorHits` | long | Общее количество вызовов ключей, существующих в кеше |
| `EntryProcessorInvokeTimeNanos` | long | Общее время вызова кеша в наносекундах |
| `EntryProcessorMaxInvocationTime` | long | Максимальное время, требуемое для исполнения вызовов кеша |
| `EntryProcessorMinInvocationTime` | long | Минимальное время, требуемое для исполнения вызовов кеша |
| `EntryProcessorMisses` | long | Общее количество вызовов на ключи, которых нет в кеше |
| `EntryProcessorPuts` | long | Общее количество вызовов кеша, обусловленных обновлением |
| `EntryProcessorReadOnlyInvocations` | long | Общее количество вызовов кеша, обусловленных отсутствием обновлений |
| `EntryProcessorRemovals` | long | Общее количество вызовов кеша, обусловленных удалениями |
| `EstimatedRebalancingKeys` | long | Число ключей, которые необходимо ребалансировать |
| `EvictingPartitionsLeft` | long | Количество партиций, запланированных для процедуры вымещения (ниспадающий счетчик) |
| `GetAllTime` | histogram | Время выполнения `GetAll`-запроса, для которого узел является инициатором, в наносекундах |
| `GetTime` | histogram | Время `get`-запроса в наносекундах |
| `GetTimeTotal` | long | Общее количество `get`-запросов в кеше в наносекундах |
| `HeapEntriesCount` | long | Число записей в heap-памяти |
| `IndexRebuildKeysProcessed` | long | Число ключей с rebuilt-индексами |
| `IsIndexRebuildInProgress` | boolean | `True`, если выполняется сборка или пересборка индекса |
| `OffHeapBackupEntriesCount` | long | Число backup-записей в offheap-памяти |
| `OffHeapEntriesCount` | long | Количество записей в offheap-памяти |
| `OffHeapEvictions` | long | Общее количество вытеснений из offheap-памяти |
| `OffHeapGets` | long | Общее количество `get`-запросов offheap-памяти |
| `OffHeapHits` | long | Число `get`-запросов, выполненных heap-памятью |
| `OffHeapMisses` | long | Пропуск (miss) – `get`-запрос, невыполненный offheap-памятью |
| `OffHeapPrimaryEntriesCount` | long | Число первичных записей в offheap-памяти |
| `OffHeapPuts` | long | Общее число `put`-запросов к offheap-памяти |
| `OffHeapRemovals` | long | Общее количество удалений из offheap-памяти |
| `PutAllConflictTime` | histogram | Время выполнения `PutAllConflict`-запроса, для которого узел является инициатором, в наносекундах |
| `PutAllTime` | histogram | Время выполнения `PutAll`-запроса, для которого узел является инициатором, в наносекундах |
| `PutTime` | histogram | Время `put`-запроса в наносекундах |
| `PutTimeTotal` | long | Общее время `cache put`-запросов в наносекундах |
| `QueryCompleted` | long | Число завершенных запросов |
| `QueryExecuted` | long | Число выполненных запросов |
| `QueryFailed` | long | Число запросов, незавершенных из-за сбоя |
| `QueryMaximumTime` | long | Максимальное время исполнения запроса |
| `QueryMinimalTime` | long | Минимальное время исполнения запроса |
| `QuerySumTime` | long | Суммарное время запроса |
| `RebalanceClearingPartitionsLeft` | long | Число партиций, которые необходимо очистить перед началом ребалансировки |
| `RebalanceStartTime` | long | Время начала ребалансировки |
| `RebalancedKeys` | long | Число уже ребалансированных ключей |
| `RebalancingBytesRate` | long | Расчетная скорость ребалансировки в байтах |
| `RebalancingKeysRate` | long | Расчетная скорость ребалансировки в ключах |
| `RemoveAllConflictTime` | histogram | Время выполнения `RemoveAllConflict`-запроса, для которого узел является инициатором, в наносекундах |
| `RemoveAllTime` | histogram | Время выполнения `RemoveAll`-запроса, для которого узел является инициатором, в наносекундах |
| `RemoveTime` | histogram | Время `remove`-запроса в наносекундах |
| `RemoveTimeTotal` | long | Общее время `cache remove`-запроса в наносекундах |
| `RollbackTime` | histogram | Время отката в наносекундах |
| `RollbackTimeTotal` | long | Общее время отката в наносекундах |
| `TotalRebalancedBytes` | long | Число уже ребалансированных байт |
| `TxKeyCollisions` | String | Ключи и размер очереди коллизий. Из-за транзакционной нагрузки некоторые ключи становятся «горячими». К таким ключам идут частые и параллельные обращения, из-за чего и появляются коллизии |

#### Группы кешей

Имя реестра: `cacheGroups.{group_name}`

| Имя | Тип | Описание |
|---|---|---|
| `AffinityPartitionsAssignmentMap` | java.util.Map | Карта назначения affinity-партиций |
| `Caches` | java.util.ArrayList | Список кешей |
| `IndexBuildCountPartitionsLeft` | long | Число обработанных партиций, необходимое для завершения создания индексов или их создания, или их реорганизации |
| `InitializedLocalPartitionsNumber` | long | Число локальных партиций, инициализированных на текущем узле |
| `InMemoryIndexPages` | long | Число индексных страниц, загруженных в память |
| `LocalNodeMovingPartitionsCount` | integer | Число партиций в состоянии `MOVING` для конкретной кеш-группы на конкретном узле |
| `LocalNodeOwningPartitionsCount` | integer | Число партиций в состоянии `OWNING` для конкретной кеш-группы на конкретном узле |
| `LocalNodeRentingEntriesCount` | long | Число записей, которые осталось выместить в `RENTING`-партиции для кеш-группы на конкретном узле |
| `LocalNodeRentingPartitionsCount` | integer | Число партиций в состоянии `RENTING` для конкретной кеш-группы на конкретном узле |
| `MaximumNumberOfPartitionCopies` | integer | Максимальное число копий всех партиций конкретной кеш-группы |
| `MinimumNumberOfPartitionCopies` | integer | Минимальное число копий всех для партиций конкретной кеш-группы |
| `MovingPartitionsAllocationMap` | java.util.Map | Карта распределения партиций со статусом `MOVING` в кластере |
| `OwningPartitionsAllocationMap` | java.util.Map | Карта распределения партиций со статусом `OWNING` в кластере |
| `PartitionIds` | java.util.ArrayList | ID локальных партиций |
| `RebalancingEndTime` | long | Время окончания ребалансировки для данной группы кешей |
| `RebalancingFullReceivedBytes` | java.util.Map | Число байт, полученных для полной ребалансировки |
| `RebalancingStartTime` | long | Время начала ребалансировки для данной группы кешей |
| `RebalancingHistReceivedKeys` | java.util.Map | Количество полученных ключей, необходимых для исторической ребалансировки |
| `RebalancingReceivedBytes` | long | Количество отребалансированных байт для данной группы кешей |
| `RebalancingPartitionsTotal` | int | Общее количество партиций, подлежащих ребалансировке для данной группы кешей |
| `RebalancingReceivedKeys` | long | Текущее количество отребалансированных ключей для данной группы кешей |
| `RebalancingLastCancelledTime` | long | Время отмены ребалансировки или ее завершения с ошибкой |
| `RebalancingFullReceivedKeys` | java.util.Map | Количество полученных ключей для полной ребалансировки группы кешей |
| `SparseStorageSize` | long | Пространство в хранилище, настроенное на возможную низкую плотность данных в байтах |
| `StorageSize` | long | Пространство в хранилище, предназначенное для группы кешей в байтах |
| `TotalAllocatedPages` | long | Общее количество страниц, размещенных в кеш-группе |
| `TotalAllocatedSize` | long | Общий размер памяти, выделенной для кеш-группы в байтах |
| `ReencryptionBytesLeft` | long | Число байт, которые осталось перешифровать |
| `ReencryptionFinished` | boolean | Имя, обозначающее окончание перешифрования |

#### Транзакции

Имя реестра: `tx`

| Имя | Тип | Описание |
|---|---|---|
| `AllOwnerTransactions` | java.util.HashMap | Карта транзакций в статусе `OWNING` на локальном узле |
| `LockedKeysNumber` | long | Число ключей, заблокированных на узле |
| `OwnerTransactionsNumber` | long | Число активных транзакций, для которых узел является инициатором |
| `TransactionsHoldingLockNumber` | long | Число активных транзакций как минимум с одной блокировкой по ключу |
| `commitTime` | long | Время последнего коммита |
| `nodeSystemTimeHistogram` | histogram | Системное время транзакций на узле в виде гистограммы |
| `nodeUserTimeHistogram` | histogram | Пользовательское время транзакций в виде гистограммы |
| `rollbackTime` | long | Время последнего отката |
| `totalNodeSystemTime` | long | Общее системное время транзакций на узле |
| `totalNodeUserTime` | long | Общее пользовательское время транзакций на узле |
| `txCommits` | integer | Число фиксаций транзакций |
| `txRollbacks` | integer | Число откатов транзакций |

#### Обмен картами партиций (Partition Map Exchange (PME))

Имя реестра: `pme`

| Имя | Тип | Описание |
|---|---|---|
| `CacheOperationsBlockedDuration` | long | Продолжительность заблокированных текущих операций PME на кешах в миллисекундах |
| `CacheOperationsBlockedDurationHistogram` | histogram | Гистограмма продолжительности операций PME на кешах в миллисекундах |
| `Duration` | long | Продолжительность текущего PME в миллисекундах |
| `DurationHistogram` | histogram | Гистограмма продолжительности PME в миллисекундах |

#### Compute Jobs

Имя реестра: `compute.jobs`

| Имя | Тип | Описание |
|---|---|---|
| `compute.jobs.Active` | long | Число активных подзадач, исполняемых в настоящий момент |
| `compute.jobs.Canceled` | long | Число отмененных подзадач, которые все еще запущены |
| `compute.jobs.ExecutionTime` | long | Общее время исполнения подзадач |
| `compute.jobs.Finished` | long | Число завершенных подзадач |
| `compute.jobs.Rejected` | long | Число подзадач, отклоненных после самой свежей операции по устранению конфликтов |
| `compute.jobs.Started` | long | Число запущенных подзадач |
| `compute.jobs.Waiting` | long | Число подзадач в очереди на исполнение |
| `compute.jobs.WaitingTime` | long | Общее время, в течение которого подзадачи находились в очереди |

#### Пулы потоков

Имя реестра: `threadPools.{thread_pool_name}`

| Имя | Тип | Описание |
|---|---|---|
| `ActiveCount` | long | Приблизительное число потоков, активно исполняющих задачи |
| `CompletedTaskCount` | long | Приблизительное общее количество выполненных задач |
| `CorePoolSize` | long | Базовое число потоков |
| `KeepAliveTime` | long | Keep-alive-время потока. Это время, в течение которого потоки, выходящие за рамки базового размера пула потоков, могут находиться в состоянии ожидания до завершения их работы |
| LargestPoolSize | long | Самое большое число потоков, одновременно присутствовавших в пуле |
| `MaximumPoolSize` | long | Максимально допустимое число потоков |
| `PoolSize` | long | Текущее число потоков в пуле |
| `QueueSize` | long | Текущий размер очереди на исполнение |
| `RejectedExecutionHandlerClass` | string | Имя класса для текущего обработчика отклонения выполнения |
| `Shutdown` | boolean | Верно, если текущий исполнитель отключен |
| `TaskCount` | long | Примерное общее число задач на исполнение |
| `TaskExecutionTime` | histogram | Время исполнения задачи в миллисекундах |
| `Terminated` | boolean | Верно, если все задачи завершены с последующим отключением |
| `Terminating` | long | Верно, если завершается, но еще не завершено |
| `ThreadFactoryClass` | string | Имя класса для фабрики потоков, используемой для создания новых потоков |

#### I/O группы кешей

Имя реестра: `io.statistics.cacheGroups.{group_name}`

| Имя | Тип | Описание |
|---|---|---|
| `LOGICAL_READS` | long | Количество логических операций `read` |
| `PHYSICAL_READS` | long | Число физических операций `read` |
| `grpId` | integer | ID группы Group id |
| `name` | string | Имя индекса |
| `startTime` | long | Время начала сбора статистики |

#### I/O-статистика по отсортированным индексам

Имя реестра: `io.statistics.sortedIndexes.{cache_name}.{index_name}`

| Имя | Тип | Описание |
|---|---|---|
| `LOGICAL_READS_INNER` | long | Число логических `read`-операций для узла во внутреннем дереве |
| `LOGICAL_READS_LEAF` | long | Число логических `read`-операций для узла в дереве конечных объектов |
| `PHYSICAL_READS_INNER` | long | Число физических `read`-операций для узла во внутреннем дереве |
| `PHYSICAL_READS_LEAF` | long | Число физических `read`-операций для узла в дереве конечных объектов |
| `indexName` | string | Имя индекса |
| `name` | string | Имя кеша |
| `startTime` | long | Время начала сбора статистики |

#### Операции с отсортированными индексами

Содержит метрики низкоуровневых операций (таких как `Insert`, `Search` и так далее) на страницах отсортированных вторичных индексов.

Имя регистра: `index.{schema_name}.{table_name}.{index_name}`

| Имя | Тип | Описание |
|---|---|---|
| `{opType}Count` | long | Количество операций `{opType}` над индексом |
| `{opType}Time` | long | Общая продолжительность операций`{opType}` над индексом (в наносекундах) |


#### I/O-статистика по хеш-индексам

Имя реестра: `io.statistics.hashIndexes.{cache_name}.{index_name}`

| Имя | Тип | Описание |
|---|---|---|
| `LOGICAL_READS_INNER` | long | Число логических `read`-операций для узла во внутреннем дереве |
| `LOGICAL_READS_LEAF` | long | Число логических `read`-операций для узла в дереве конечных объектов |
| `PHYSICAL_READS_INNER` | long | Число физических `read`-операций для узла во внутреннем дереве |
| `PHYSICAL_READS_LEAF` | long | Число физических `read`-операций для узла в дереве конечных объектов |
| `indexName` | string | Имя индекса |
| `name` | string | Имя кеша |
| `startTime` | long | Время начала сбора статистики |

#### Communication I/O

Имя реестра: `io.communication`

| Имя | Тип | Описание |
|---|---|---|
| `ActiveSessionsCount` | integer | Число активных TCP-сессий |
| `OutboundMessagesQueueSize` | integer | Размер очереди исходящих сообщений |
| `SentMessagesCount` | integer | Число отправленных сообщений |
| `SentBytesCount` | long | Число отправленных байт |
| `ReceivedBytesCount` | long | Число полученных байт |
| `ReceivedMessagesCount` | integer | Число полученных сообщений |
| `RejectedSslSessionsCount` | integer | Число TCP-сессий, отклоненных из-за ошибок SSL (метрика экспортируется только при включенном SSL) |
| `SslEnabled` | boolean | Метрика показывает, включен ли SSL |
| `SslHandshakeDurationHistogram` | histogram | Гистограмма продолжительности SSL handshake в миллисекундах (метрика экспортируется только при включенном SSL) |

#### Коннектор тонкого клиента DataGrid

Имя реестра: `client.connector`

| Имя | Тип | Описание |
|---|---|---|
| `ActiveSessionsCount` | integer | Число активных TCP-сессий |
| `jdbc.AcceptedSessions` | integer | Количество успешно установленных сессий (соединений) |
| `jdbc.ActiveSessions` | integer | Количество активных сессий на данный момент |
| `odbc.AcceptedSessions` | integer | Количество успешно установленных сессий (соединений) |
| `odbc.ActiveSessions` | integer | Количество активных сессий на данный момент |
| `outboundMessagesQueueSize` | integer | Количество сообщений, ожидающих отправки |
| `receivedBytes` | long | Число полученных байт |
| `RejectedSslSessionsCount` | integer | Число TCP-сессий, отклоненных из-за ошибок SSL (метрика экспортируется только при включенном SSL) |
| `RejectedSessionsTimeout` | integer | Число TCP-сессий, отклоненных из-за тайм-аута handshake |
| `RejectedSessionsAuthenticationFailed` | integer | Число TCP-сессий, отклоненных из-за неудачной аутентификации |
| `RejectedSessionsTotal` | integer | Общее число отклоненных TCP-соединений |
| `{clientType}.AcceptedSessions` | integer | Количество успешно установленных соединений для клиента |
| `{clientType}.ActiveSessions` | integer | Число активных сессий для клиента |
| `sentBytes` | long | Число отправленных байт |
| `SslEnabled` | boolean | Метрика, показывающая, включен ли SSL |
| `SslHandshakeDurationHistogram` | histogram | Гистограмма продолжительности SSL handshake в миллисекундах (метрика экспортируется только при включенном SSL) |

#### Коннектор REST-клиента DataGrid

Имя реестра: `rest.client`

| Имя | Тип | Описание |
|---|---|---|
| `ActiveSessionsCount` | integer | Число активных TCP-сессий |
| `outboundMessagesQueueSize` | long | Количество сообщений, ожидающих отправки |
| `receivedBytes` | long | Число полученных байт |
| `RejectedSslSessionsCount` | integer | Число TCP-сессий, отклоненных из-за ошибок SSL (метрика экспортируется только при включенном SSL) |
| `sentBytes` | long | Число отправленных байт |
| `SslEnabled` | boolean | Метрика, показывающая, включен ли SSL |
| `SslHandshakeDurationHistogram` | histogram | Гистограмма продолжительности SSL handshake в миллисекундах (метрика экспортируется только при включенном SSL) |

#### Discovery I/O

Имя реестра: `io.discovery`

| Имя | Тип | Описание |
|---|---|---|
| `CoordinatorSince` | long | Временная отметка, после которой локальный узел стал узлом-координатором (метрика экспортируется только с серверных узлов) |
| `Coordinator` | UUID | ID координатора (метрика экспортируется только с серверных узлов) |
| `CurrentTopologyVersion` | long | Текущая версия топологии |
| `FailedNodes` | integer | Количество узлов, вышедших из топологии в результате какой-либо ошибки |
| `JoinedNodes` | integer | Число присоединившихся к топологии узлов |
| `LeftNodes` | integer | Число покинувших топологию узлов |
| `MessageWorkerQueueSize` | integer | Текущий размер очереди обработчика сообщений |
| `PendingMessagesRegistered` | integer | Число ожидающих зарегистрированных сообщений |
| `RejectedSslConnectionsCount` | integer | Число соединений TCP discovery, отклоненных из-за ошибок SSL |
| `SslEnabled` | boolean | Метрика, показывающая, включен ли SSL |
| `TotalProcessedMessages` | integer | Общее число обработанных сообщений |
| `TotalReceivedMessages` | integer | Общее число полученных сообщений |

#### I/O региона данных

Имя реестра: `io.dataregion.{data_region_name}`

| Имя | Тип | Описание |
|---|---|---|
| `AllocationRate` | hitrate | Соотношение распределения (страниц в секунду) в среднем по `rateTimeInterval` |
| `CheckpointBufferSize` | long | Размер буфера контрольных точек в байтах |
| `DirtyPages` | long | Число страниц в памяти, которые еще не были синхронизированы с Persistence-хранилищем |
| `EmptyDataPages` | long | Метрика, подсчитывающая число пустых страниц с данными для конкретного региона данных. Метрика подсчитывает только свободные страницы, которые могут быть использованы повторно (например, страницы, содержащиеся в хранилище страниц для повторного использования) |
| `EvictionRate` | hitrate | Уровень замещений (страниц в секунду) |
| `InitialSize` | long | Изначальный размер региона данных в байтах |
| `InMemoryIndexPages` | long | Количество индексных страниц, загруженных в память |
| `LargeEntriesPagesCount` | long | Количество страниц, занятых большими записями, размер которых превышает размер страницы |
| `MaxSize` | long | Максимальный размер региона данных в байтах |
| `OffHeapSize` | long | Размер offheap-памяти в байтах |
| `OffheapUsedSize` | long | Размер использованной offheap-памяти в байтах |
| `PagesFillFactor` | double | Процент использованного пространства |
| `PagesRead` | long | Число страниц, прочитанных с момента последнего перезапуска |
| `PagesReadTime` | long | Общее время чтения страниц в наносекундах с момента последнего перезапуска |
| `PagesReplaceAge` | hitrate | Средний возраст страниц в памяти, по наступлении которого они замещаются страницами из Persistence-хранилища (в миллисекундах) |
| `PagesReplaceRate` | hitrate | Норма, при которой страницы в памяти замещаются страницами из Persistence-хранилища (страниц в секунду) |
| `PagesReplaced` | long | Число страниц, замещенных с момента последнего перезапуска |
| `PagesReplaceTime` | long | Общее время на замещение страниц с момента последнего перезапуска |
| `PagesWritten` | long | Число страниц, записанных после последнего перезапуска |
| `PhysicalMemoryPages` | long | Число страниц, находящихся в физической оперативной памяти |
| `PhysicalMemorySize` | long | Собирает общий размер страниц, загруженных в ОЗУ в байтах |
| `TotalAllocatedPages` | long | Общее число размещенных страниц |
| `TotalAllocatedSize` | long | Собирает общий размер памяти в регионе данных в байтах |
| `TotalThrottlingTime` | long | Общее время зависания потоков в миллисекундах. Ignite тормозит потоки, создающие «грязные» страницы в ходе процесса создания контрольной точки |
| `UsedCheckpointBufferSize` | long | Собирает размер использованного пространства в буфере контрольной точки в байтах |

#### Хранилище данных

Имя реестра: `io.datastorage`

| Имя | Тип | Описание |
|---|---|---|
| `CheckpointBeforeLockHistogram` | histogram | Гистограмма действия по созданию контрольной точки до получения блокировки на запись в миллисекундах |
| `CheckpointFsyncHistogram` | histogram | Гистограмма продолжительности `fsync` контрольной точки в миллисекундах |
| `CheckpointHistogram` | histogram | Гистограмма продолжительности создания контрольной точки в миллисекундах |
| `CheckpointListenersExecuteHistogram` | histogram | Гистограмма продолжительности работы слушателей исполнения контрольной точки в миллисекундах |
| `CheckpointLockHoldHistogram` | histogram | Гистограмма длительности удержания блокировки контрольной точки в миллисекундах |
| `CheckpointLockWaitHistogram` | histogram | Гистограмма длительности ожидания блокировки контрольной точки в миллисекундах |
| `CheckpointMarkHistogram` | histogram | Гистограмма продолжительности маркирования контрольной точки в миллисекундах |
| `CheckpointPagesWriteHistogram` | histogram | Гистограмма продолжительности `write`-операции над страницами контрольной точки в миллисекундах |
| `CheckpointSplitAndSortPagesHistogram` | histogram | Гистограмма продолжительности разделения и сортировки страниц контрольной точки в миллисекундах |
| `CheckpointTotalTime` | long | Общая продолжительность контрольной точки |
| `CheckpointWalRecordFsyncHistogram` | histogram | Гистограмма продолжительности `fsync` WAL-журнала после появления в логах `TotalNodesCheckpointRecord` в начале контрольной точки в миллисекундах |
| `CheckpointWriteEntryHistogram` | histogram | Гистограмма продолжительности записи в файл входного буфера в миллисекундах |
| `LastArchivedSegment` | long | Индекс последнего заархивированного сегмента |
| `LastCheckpointBeforeLockDuration` | long | Продолжительность действия контрольной точки до получения блокировки на запись в миллисекундах |
| `LastCheckpointCopiedOnWritePagesNumber` | long | Количество страниц, скопированных во временный буфер контрольной точки во время создания последней контрольной точки |
| `LastCheckpointDataPagesNumber` | long | Общее число страниц с данными, записанных во время создания последней контрольной точки |
| `LastCheckpointDuration` | long | Продолжительность создания последней контрольной точки в миллисекундах |
| `LastCheckpointFsyncDuration` | long | Продолжительность фазы синхронизации последней контрольной точки в миллисекундах |
| `LastCheckpointListenersExecuteDuration` | long | Продолжительность работы слушателей исполнения контрольной точки при блокировке на запись в миллисекундах |
| `LastCheckpointLockHoldDuration` | long | Продолжительность удержания блокировки контрольной точки в миллисекундах |
| `LastCheckpointLockWaitDuration` | long | Продолжительность ожидания блокировки контрольной точки в миллисекундах |
| `LastCheckpointMarkDuration` | long | Продолжительность маркировки контрольной точки в миллисекундах |
| `LastCheckpointPagesWriteDuration` | long | Продолжительность `write`-операции над страницами контрольной точки в миллисекундах |
| `LastCheckpointTotalPagesNumber` | long | Общее число страниц, записанных во время создания последней контрольной точки |
| `LastCheckpointSplitAndSortPagesDuration` | long | Продолжительность разделения и сортировки страниц последней контрольной точки в миллисекундах |
| `LastCheckpointStart` | long | Временная метка начала последней контрольной точки |
| `LastCheckpointWalRecordFsyncDuration` | long | Продолжительность `fsync` WAL-журнала после появления в логах `CheckpointRecord` в начале последней контрольной точки в миллисекундах |
| `LastCheckpointWriteEntryDuration` | long | Продолжительность записи входного буфера в файл последней контрольной точки в миллисекундах |
| `SparseStorageSize` | long | Пространство в хранилище, настроенное под возможную низкую плотность данных в байтах |
| `StorageSize` | long | Пространство в хранилище в байтах |
| `WalArchiveSegments` | integer | Текущее число сегментов WAL-журнала в архиве WAL-журнала |
| `WalBuffPollSpinsRate` | hitrate | Число повторов опроса буфера WAL-журнала за последний временной интервал |
| `WalFsyncTimeDuration` | hitrate | Общая продолжительность `fsync` |
| `WalFsyncTimeNum` | hitrate | Общее число операций `fsync` |
| `WalLastRollOverTime` | long | Время последней выгрузки сегмента WAL-журнала |
| `WalLoggingRate` | hitrate | Среднее число записей WAL-журнале в секунду, созданных за последний временной интервал |
| `WalTotalSize` | long | Общий размер пространства для хранения файлов WAL-журнала в байтах |
| `WalWritingRate` | hitrate | Средняя скорость записи за последний временной интервал (байт/сек) |

#### Кластер

Имя реестра: `cluster`

| Имя | Тип | Описание |
|---|---|---|
| `ActiveBaselineNodes` | integer | Количество активных узлов в базовой топологии (baseline) |
| `Rebalanced` | boolean | Верно, если кластер полностью ребалансирован. Если кластер неактивен, данная метрика всегда имеет значение `false`, независимо от реального статуса партиций |
| `TotalBaselineNodes` | integer | Общее количество узлов в базовой топологии (baseline) |
| `TotalClientNodes` | integer | Число клиентских узлов |
| `TotalServerNodes` | integer | Количество серверных узлов |

#### Кеш-процессор

Имя реестра: `cache`

| Имя | Тип | Описание |
|---|---|---|
| `LastDataVer` | long | Последняя версия данных на узле |
| `DataVersionClusterId` | integer | ID кластера версии данных |

#### Безопасность

Имя реестра: `security`

| Имя | Тип | Описание |
|---|---|---|
| `DistinguishedName` | String | DName, содержащийся в сертификате (DN записи) |
| `ExpirationDate` | String | Дата окончания жизненного цикла сертификата в человекочитаемом формате |
| `ExpirationTimestamp` | long | Дата окончания жизненного цикла сертификата в UNIX-формате |
| `Fingerprint` | String | Fingerprint сертификата |

#### Кеш SQL-парсера

Имя реестра: `sql."parser.cache"`

| `hits` | long | Количество SQL-запросов, которые были найдены в кеше парсера (не требуют разбора и планирования перед выполнением) |
| `misses` | long | Количество SQL-запросов, которые были разобраны и спланированы |

#### Пользовательские SQL-запросы

Имя реестра: `sql."queries.user"`

| Имя | Тип | Описание |
|---|---|---|
| `success` | long | Число успешно выполненных запросов, запущенных на узле |
| `canceled` | long | Число отмененных запросов, запущенных на узле. Число, отображаемое данной метрикой, включено в общую метрику `failed` |
| `failed` | long | Общее число запросов, запущенных на узле и невыполненных по какой-либо причине (например, по причине отмены) |

#### Снепшоты

Имя реестра: `snapshot`

| Имя | Тип | Описание |
|---|---|---|
| `LastSnapshotName` | java.lang.String | Имя последнего запущенного на данном узле запроса на создание снепшота кластера |
| `LastSnapshotErrorMessage` | java.lang.String | Сообщение об ошибке последнего запущенного на данном узле запроса на создание снепшота кластера, завершившегося ошибкой. Значение будет пустым, если последний запрос на создание снепшота завершился успешно |
| `CurrentSnapshotProcessedSize` | java.lang.Long | Размер обработанного снепшота текущей версии кластера на данном узле в байтах |
| `LocalSnapshotNames` | java.util.List | Список имен всех снепшотов, сохраненных на данный момент на локальном узле с привязкой к рабочему пути снепшота, сконфигурированному при помощи класса `IgniteConfiguration` |
| `CurrentSnapshotTotalSize` | java.lang.Long | Рассчитанный размер снепшота текущей версии кластера на данном узле в байтах. Значение может увеличиваться во время создания снепшота |
| `LastSnapshotEndTime` | java.lang.Long | Системное время окончания последнего запроса на создание снепшота кластера |
| `LastSnapshotStartTime` | java.lang.Long | Системное время начала последнего запроса на создание снепшота кластера |

#### Восстановление из снепшота

Имя реестра: `snapshot-restore`

| Имя | Тип | Описание |
|---|---|---|
| `processedPartitions` | java.lang.Integer | Число партиций, обработанных на данном узле |
| `requestId` | java.lang.String | ID запроса последней запущенной операции по восстановлению из снепшота на данном узле |
| `totalPartitions` | java.lang.Integer | Общее количество партиций, подлежащих восстановлению на данном узле |
| `snapshotName` | java.lang.String | Имя снепшота последней запущенной операции восстановления из снепшота на данном узле |
| `startTime` | java.lang.Long | Системное время начала операции восстановления кластера из снепшота на данном узле |
| `endTime` | java.lang.Long | Системное время окончания операции восстановления кластера из снепшота на данном узле |
| `Error` | java.lang.String | Сообщение об ошибке последней запущенной операции восстановления кластера из снепшота на данном узле |

## Конфигурирование метрик

С помощью команды `metrics` можно конфигурировать:

-   интервалы (buckets) для метрик-гистограмм;
-   временной интервал для метрик типа hitrate.

:::{admonition} Пример команды
:class: hint

```bash
control.(sh|bat) --metric --configure-histogram <histogram-metric-name> 1,2,3
control.(sh|bat) --metric --configure-hitrate <hitrate-metric-name> 1000
```

где:

-   `<histogram-metric-name>` — имя метрики-гистограммы;
-   `1,2,3` — интервалы (buckets) гистограммы;
-   `<hitrate-metric-name>` — имя метрики типа hitrate;
-   `1000` — время в мс, за которое будут представлены данные в hitrate-метрике.
:::

:::{admonition} Внимание
:class: danger

При использовании команды `metric` к имени метрики необходимо в качестве префикса добавить имя реестра в формате: `<register-name>.<metric-name>`. Например, для метрики `WalLoggingRate` необходимо указать имя `io.datastorage.WalLoggingRate`.
:::

## Пользовательские метрики

:::{admonition} Важно

Это экспериментальная функциональность. Она может измениться в будущих версиях.
:::

DataGrid предоставляет различные внутренние метрики, но их может оказаться недостаточно. Пользователи могут разрабатывать и публиковать собственные метрики, которые основаны на [New Metrics System](#new-metrics-system).

:::{admonition} Примечание
:class: note

Пользовательские метрики являются локальными и привязаны исключительно к локальному узлу.
:::

### Создание пользовательских метрик

Перед регистрацией пользовательской метрики нужно добавить новый реестр. После этого в него можно будет добавить новые метрики.

#### Реестр пользовательских метрик

Реестры пользовательских метрик можно создавать с помощью интерфейса `IgniteMetrics`, который доступен через метод `Ignite.metrics()`. Методы интерфейса `IgniteMetrics`:

- `MetricRegistry getOrCreate(String registryName)` возвращает существующий или создает новый реестр пользовательских метрик.
- `void remove(String registryName)` удаляет весь реестр пользовательских метрик.

#### Создание пользовательской метрики

Для регистрации новой пользовательской метрики используйте интерфейс `MetricRegistry`, который получен с помощью метода `IgniteMetrics.getOrCreate(...)`. Интерфейс `MetricRegistry` включает несколько методов для добавления или удаления метрик, например:

- `void register(String metricName, IntSupplier valueSupplier, @Nullable String description);` регистрирует целочисленную метрику (тип integer).
- `void register(String metricName, DoubleSupplier valueSupplier, @Nullable String description);` регистрирует метрику типа double.
- `void remove(String name);` удаляет метрику.

### Имена пользовательских метрик

Имена пользовательских метрик (и их реестров) аналогичны именам внутренних метрик. Имя может состоять из нескольких частей, которые разделены точкой, например: `process.status.suspended`.

Префикс `custom.` автоматически добавляется перед именем пользовательского реестра в интерфейсе `IgniteMetrics`. Например, если передано имя реестра `process.status.suspended`, оно автоматически расширяется до `custom.process.status.suspended`.

### Ограничения пользовательских метрик

**Список ограничений:**

- Пользовательские метрики не влияют на работу внутренних метрик DataGrid.
- Пользовательские метрики регистрируются по требованию и не являются персистентными. После каждого перезапуска узла их необходимо регистрировать заново.
- Конфигурирование пользовательских метрик (например, изменение границ гистограмм) не поддерживается.
- Имена пользовательских метрик не могут быть пустыми, содержать пробелы или пустые части, которые разделены точками.

## Системные представления

DataGrid имеет ряд встроенных SQL-представлений, которые содержат информацию о процессах, протекающих внутри DataGrid. Доступ к метрикам осуществляется через SYS-схему.

:::{admonition} Примечание
:class: note

Для доступа к данным можно воспользоваться утилитой SQLLine:

```bash
./sqlline.sh -u jdbc:ignite:thin://xxx.x.x.x/SYS
```
:::

::::{admonition} Пример запроса данных по узлам
:class: hint

:::{code-block} sql
:caption: SQL
`select * from NODES;`
:::
::::

В системных представлениях доступно следующее дерево групп метрик:

| Имя представления | Описание |
|---|---|
| `CACHES` | Информация по кешам |
| `CACHE_GROUPS` | Информация по кеш-группам |
| `TASKS` | Информация о вычислительных задачах (`TASKS`) |
| `JOBS` | Информация о вычислительных подзадачах(`JOBS`) в рамках задач (`TASKS`) |
| `SERVICES` | Информация о сервисах |
| `TRANSACTIONS` | Информация о транзакциях |
| `NODES` | Информация об узлах |
| `NODE_ATTRIBUTES` | Информация об атрибутах узла |
| `BASELINE_NODES` | Информация о базовой топологии (baseline) |
| `BASELINE_NODE_ATTRIBUTES` | Информация об атрибутах узла, исправленных на момент установки текущей версии базовой топологии (baseline) |
| `CLIENT_CONNECTIONS` | Информация о подключенных тонких клиентах |
| `STRIPED_THREADPOOL_QUEUE` | Информация о задачах в рамках распределенного пула потоков (`striped thread pool`) |
| `DATASTREAM_THREADPOOL_QUEUE` | Информация о задачах в рамках распределенных потоков (`data streamer stripped thread pool`) |
| `SCAN_QUERIES` | Информация о запущенных запросах сканирования |
| `CONTINUOUS_QUERIES` | Информация о выполняемых в данный момент непрерывных запросах |
| `SQL_QUERIES` | Информация о запущенных SQL-запросах |
| `SQL_QUERIES_HISTORY` | Информация об истории выполнения SQL-запросов |
| `SCHEMAS` | Информация об SQL–схемах |
| `NODE_METRICS` | Информация о метриках узла |
| `TABLES` | Информация об SQL–таблицах |
| `TABLE_COLUMNS` | Информация о столбцах SQL–таблицы |
| `VIEWS` | Информация об SQL–представлениях |
| `VIEW_COLUMNS` | Информация о столбцах SQL–представлений |
| `INDEXES` | Информация об SQL–индексах |
| `CACHE_GROUP_PAGE_LISTS` | Информация о `PAGE LISTS` кеш-групп |
| `DATA_REGION_PAGE_LISTS` | Информация о `PAGE LISTS` в регионе данных (Data Region) |
| `PARTITION_STATES` | Информация о состоянии партиций |
| `BINARY_METADATA` | Информация о существующих бинарных типах |
| `METASTORAGE` | Информация о хранилище метаданных (`metastorage cache`) |
| `DS_QUEUES` | Список `IgniteQueue`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_SETS` | Список `IgniteSet`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_ATOMICSEQUENCES` | Список `IgniteAtomicSequence`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_ATOMICLONGS` | Список `IgniteAtomicLong`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_ATOMICREFERENCES` | Список `IgniteAtomicReference`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_ATOMICSTAMPED` | Список `IgniteAtomicStamped`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_COUNTDOWNLATCHES` | Список `IgniteCountDownLatch`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_SEMAPHORES` | Список `IgniteSemaphores`. Отображается не на родительском узле только после первого использования на этом узле |
| `DS_REENTRANTLOCKS` | Содержание `IgniteLock`. Отображается не на родительском узле только после первого использования на этом узле |
| `SQL_PLANS_HISTORY` | Список планов ранее выполненных SQL-запросов |
| `STATISTICS_CONFIGURATION` | Информация о конфигурации SQL-статистики |
| `STATISTICS_LOCAL_DATA` | SQL-статистика для данных, хранящихся или управляемых локально. Это отображение специфично для узла, поэтому на каждом узле содержится экземпляр отображения, содержащий информацию о статистике локальных данных |
| `STATISTICS_PARTITION_DATA` | Информация об SQL-статистике в каждой партиции данных, хранящейся на локальном узле |
| `SNAPSHOT` | Информация о локальных снепшотах |

### Описание системных представлений

#### `CACHES`

Системное представление содержит информацию о кешах.

| Имя | Тип | Описание |
|---|---|---|
| `AFFINITY` | string | `toString`-представление affinity-функции |
| `AFFINITY_MAPPER` | string | `toString`-представление affinity-преобразователя |
| `ATOMICITY_MODE` | string | Атомарный режим |
| `BACKUPS` | int | Число резервных копий |
| `CACHE_GROUP_ID` | int | ID группы кешей |
| `CACHE_GROUP_NAME` | string | Имя группы кешей |
| `CACHE_ID` | int | ID кеша |
| `CACHE_LOADER_FACTORY` | string | `toString`-представление фабрики загрузчика кеша |
| `CACHE_MODE` | string | Режим работы кеша |
| `CACHE_NAME` | string | Имя кеша |
| `CACHE_STORE_FACTORY` | string | `toString`-представление фабрики хранилища кеша |
| `CACHE_TYPE` | string | Тип кеша |
| `CACHE_WRITER_FACTORY` | string | `toString`-представление фабрики записи в кеш |
| `CONFLICT_RESOLVER` | string | `toString`-представление средства разрешения конфликтов кеша |
| `DATA_REGION_NAME` | string | Имя региона данных |
| `DEFAULT_LOCK_TIMEOUT` | long | тайм-аут блокировки в миллисекундах |
| `EVICTION_FILTER` | string | `toString`-представление фильтра замещения |
| `EVICTION_POLICY_FACTORY` | string | `toString`-представление фабрики политики замещения |
| `EXPIRY_POLICY_FACTORY` | string | `toString`-представление фабрики политики истечения срока хранения |
| `HAS_EXPIRING_ENTRIES` | string | Указывает, есть ли записи с истекающим временем жизни. Если определить невозможно, принимает значение `Unknown` |
| `INTERCEPTOR` | string | `toString`-представление сборщика данных |
| `IS_COPY_ON_READ` | boolean | Атрибут, который обозначает сохранение значения в on-heap-кеше |
| `IS_EAGER_TTL` | boolean | Атрибут, который обозначает немедленное удаление записей из кеша |
| `IS_ENCRYPTION_ENABLED` | boolean | Верно, если данные в кеше зашифрованы |
| `IS_EVENTS_DISABLED` | boolean | Верно, если события для данного кеша отключены |
| `IS_INVALIDATE` | boolean | Верно, если значения станут недействительными при фиксации в near-кеше |
| `IS_LOAD_PREVIOUS_VALUE` | boolean | Верно, если значение загружается из хранилища и не находится в кеше |
| `IS_MANAGEMENT_ENABLED` | boolean | Верно, если управление в кеше включено |
| `IS_NEAR_CACHE_ENABLED` | boolean | Верно, если кеш включен |
| `IS_ONHEAP_CACHE_ENABLED` | boolean | Верно, если heap-кеш включен |
| `IS_READ_FROM_BACKUP` | boolean | Верно, если чтение должно производиться из резервного узла |
| `IS_READ_THROUGH` | boolean | Верно, если включено чтение из стороннего хранилища |
| `IS_SQL_ESCAPE_ALL` | boolean | Если верно, то все имена SQL-таблиц и полей будут экранироваться двойными кавычками |
| `IS_SQL_ONHEAP_CACHE_ENABLED` | boolean | Верно, когда включен SQL on-heap-кеш. Когда он включен, DataGrid будет кешировать SQL-строки по мере доступа к ним системы обработки запросов. Строки обнуляются и вытесняются из кеша при изменении или вытеснении из кеша соответствующей записи |
| `IS_STATISTICS_ENABLED` | boolean | Верно, если включена статистика по кешам |
| `IS_STORE_KEEP_BINARY` | boolean | Атрибут, который указывает на то, что реализация `CacheStore` работает с бинарными объектами вместо Java-объектов |
| `IS_WRITE_BEHIND_ENABLED` | boolean | Атрибут, указывающий на то, что DataGrid должен использовать для хранилища кешей стратегию `write-behind` |
| `IS_WRITE_THROUGH` | boolean | Верно, если включена запись в стороннее хранилище |
| `MAX_CONCURRENT_ASYNC_OPERATIONS` | int | Максимальное число разрешенных параллельных асинхронных операций. Если возвращаемое значение равно «0», то число таких операций неограниченно |
| `MAX_QUERY_ITERATORS_COUNT` | int | Максимальное число сохраняемых итераторов запроса. Итераторы сохраняются для поддержки разбиения запроса на страницы, когда каждая страница данных отправляется на узел пользователя только при необходимости |
| `NEAR_CACHE_EVICTION_POLICY_FACTORY` | string | `toString`-представление фабрики политики вытеснения из near-кеша |
| `NEAR_CACHE_START_SIZE` | int | Изначальный размер near-кеша, который будет использоваться для создания черновика внутренней хеш-таблицы после запуска |
| `NODE_FILTER` | string | `toString`-представление фильтра узла |
| `PARTITION_LOSS_POLICY` | string | `toString`-представление политики потери партиции |
| `QUERY_DETAIL_METRICS_SIZE` | int | Размер подробных метрик запросов, которые сохраняются в памяти для целей мониторинга. Если значение равно «0», статистика собираться не будет |
| `QUERY_PARALLELISM` | int | Указание на систему исполнения запросов при необходимой степени параллелизма внутри одного узла |
| `REBALANCE_BATCH_SIZE` | int | Размер данных, загружаемых внутри одного сообщения ребалансировки (в байтах) |
| `REBALANCE_BATCHES_PREFETCH_COUNT` | int | Число пакетов, созданных питающим узлом при начале процесса ребалансировки |
| `REBALANCE_DELAY` | long | Задержка ребалансировки в миллисекундах |
| `REBALANCE_MODE` | string | Режим ребалансировки |
| `REBALANCE_ORDER` | int | Порядок ребалансировки |
| `REBALANCE_THROTTLE` | long | Время ожидания между сообщениями ребалансировки для избежания перегрузки процессора или сети |
| `REBALANCE_TIMEOUT` | long | тайм-аут ребалансировки в миллисекундах |
| `SQL_INDEX_MAX_INLINE_SIZE` | int | Размер подстановки индекса в байтах |
| `SQL_ONHEAP_CACHE_MAX_SIZE` | int | Максимальный размер SQL on-heap-кеша, измеряется в количестве строк. При достижении максимального числа строк самые старые из них вымещаются из кеша |
| `SQL_SCHEMA` | string | Имя схемы |
| `TOPOLOGY_VALIDATOR` | string | `toString`-представление валидатора топологии |
| `WRITE_BEHIND_BATCH_SIZE` | int | Максимальный размер пакета для write-behind-операций хранилища кешей |
| `WRITE_BEHIND_COALESCING` | boolean | Объединяющий атрибут записи для write-behind-операций хранилища кешей. Операции хранения (`get` или `remove`) с одним и тем же ключом комбинируются или объединяются в одну конечную операцию для уменьшения нагрузки на соответствующее хранилище кешей |
| `WRITE_BEHIND_FLUSH_FREQUENCY` | long | Частота, с которой write-behind-кеш перемещается в хранилище кешей (в миллисекундах) |
| `WRITE_BEHIND_FLUSH_SIZE` | int | Максимальный размер write-behind-кеша. Если размер кеша превышает значение этой метрики, все содержимое кеша перемещается в хранилище кешей, а кеш записи очищается |
| `WRITE_BEHIND_FLUSH_THREAD_COUNT` | int | Количество потоков, которые будут производить перемещение кеша |
| `WRITE_SYNCHRONIZATION_MODE` | string | Получает данные о режиме синхронизации write-операций |

#### `CACHE_GROUPS`

Системное представление содержит информацию о группах кеша.

| Имя | Тип данных | Описание |
|---|---|---|
| `AFFINITY` | VARCHAR | Строковая репрезентация (возвращаемая методом `toString()`) affinity-функции, определенная для группы кешей |
| `ATOMICITY_MODE` | VARCHAR | Атомарный режим работы кеш-группы |
| `BACKUPS` | INT | Число резервных партиций, сконфигурированных для группы кешей |
| `CACHE_COUNT` | INT | Количество кешей в группе |
| `CACHE_GROUP_ID` | INT | ID группы кешей |
| `CACHE_GROUP_NAME` | VARCHAR | Имя кеш-группы |
| `CACHE_MODE` | VARCHAR | Режим работы кеша |
| `DATA_REGION_NAME` | VARCHAR | Имя региона данных |
| `IS_SHARED` | BOOLEAN | Если конкретная группа кешей содержит больше одного кеша |
| `NODE_FILTER` | VARCHAR | Строковая репрезентация (возвращаемая методом `toString()`) фильтра узла, определенная для группы кешей |
| `PARTITION_LOSS_POLICY` | VARCHAR | Политика потери партиций |
| `PARTITIONS_COUNT` | INT | Число партиций |
| `REBALANCE_DELAY` | LONG | Задержка ребалансировки |
| `REBALANCE_MODE` | VARCHAR | Режим ребалансировки |
| `REBALANCE_ORDER` | INT | Порядок ребалансировки |
| `TOPOLOGY_VALIDATOR` | VARCHAR | Строковая репрезентация (возвращаемая методом `toString()`) валидатора топологии, определенная для группы кешей |

#### `TASKS`

Системное представление отражает информацию о запущенных на узле вычислительных задачах (compute task), выполняемых в данный момент времени. В качестве примера рассмотрим ситуацию, когда приложение запустило вычислительную задачу с использованием толстого клиента, и эта задача была выполнена на одном из серверных узлов. В этом случае толстый клиент будет сообщать статистику по задаче с помощью представления `TASKS`, в то время как серверный узел будет передавать на толстый клиент подробности выполнения задачи.

| Имя | Тип | Описание |
|---|---|---|
| `ID` | UUID | ID задачи |
| `SESSION_ID` | UUID | ID сессии |
| `TASK_NODE_ID` | UUID | ID узла, происходящий от задачи |
| `TASK_NAME` | string | Имя задачи |
| `TASK_CLASS_NAME` | string | Имя класса задачи |
| `AFFINITY_PARTITION_ID` | int | ID партиции кеша |
| `AFFINITY_CACHE_NAME` | string | Имя кеша |
| `START_TIME` | long | Время начала |
| `END_TIME` | long | Время окончания |
| `EXEC_NAME` | string | Имя пула потоков, исполняющего задачу |
| `INTERNAL` | boolean | Верно, если задача является внутренней |
| `USER_VERSION` | string | Версия пользователя задачи |

#### `JOBS`

Системное представление отражает список вычислительных заданий (compute jobs), начатых узлом как часть вычислительной задачи (compute task). Для просмотра статуса задачи необходимо обратиться к представлению `TASKS`.

:::{list-table}
:header-rows: 1
 
+   *   Имя
    *    Тип
    *    Описание
+   *   `ID`
    *    UUID
    *    Идентификатор подзадачи
+   *   `SESSION_ID`
    *    UUID
    *    Идентификатор сессии подзадачи. Для подзадач, которые принадлежат определенной задаче, метрика `SESSION_ID` равна `TASKS.SESSION_ID`
+   *   `ORIGIN_NODE_ID`
    *    UUID
    *    Идентификатор узла, который начал подзадачу
+   *   `TASK_NAME`
    *    string
    *    Название задачи
+   *   `TASK_CLASSNAME`
    *    string
    *    Название класса задачи
+   *   `AFFINITY_CACHE_IDS`
    *    string
    *    Идентификатор одного или нескольких кешей, если подзадача исполняется посредством одного из методов `IgniteCompute.affinity..`. Параметр остается без значения при использовании API `IgniteCompute`, которые не нацелены на использование строго определенных кешей
+   *   `AFFINITY_PARTITION_ID`
    *    int
    *    Идентификатор одной или нескольких партиций, если подзадача исполняется посредством одного из методов `IgniteCompute.affinity..`. Параметр остается без значения при использовании API `IgniteCompute`, которые не нацелены на использование строго определенных партиций
+   *   `CREATE_TIME`
    *    long
    *    Время создания подзадачи
+   *   `START_TIME`
    *    long
    *    Время начала подзадачи
+   *   `FINISH_TIME`
    *    long
    *    Время окончания подзадачи
+   *   `EXECUTOR_NAME`
    *    string
    *    Имя исполнителя задачи
+   *   `IS_FINISHING`
    *    boolean
    *    Верно, если подзадача завершается
+   *   `IS_INTERNAL`
    *    boolean
    *    Верно, если подзадача является внутренней
+   *   `IS_STARTED`
    *    boolean
    *    Верно, если подзадача началась
+   *   `IS_TIMEDOUT`
    *    boolean
    *    Верно, если время на выполнение подзадачи вышло до ее завершения
+   *   `STATE`
    *    string
    *    Возможные значения:
         - `ACTIVE` — подзадача исполняется.
         - `PASSIVE` — подзадача добавлена в очередь на исполнение. Для получения дополнительной информации необходимо обратиться к документации интерфейса `CollisionSPI`.
         - `CANCELED` — подзадача отменена
:::

#### `SERVICES`

Системное представление содержит информацию о сервисах.

| Имя | Тип | Описание |
|---|---|---|
| `AFFINITY_KEY` | string | Значение affinity-ключа для сервиса |
| `CACHE_NAME` | string | Имя кеша |
| `MAX_PER_NODE_COUNT` | int | Максимальное количество экземпляров сервиса на один узел |
| `NAME` | string | Имя сервиса |
| `NODE_FILTER ` | string | `toString`-представление фильтра узла |
| `ORIGIN_NODE_ID` | UUID | ID начального узла |
| `SERVICE_CLASS` | string | Имя класса сервиса |
| `SERVICE_ID` | UUID | ID сервиса |
| `STATICALLY_CONFIGURED` | boolean | Верно, если сервис сконфигурирован статически |
| `TOTAL_COUNT` | int | Общее число экземпляров сервиса |

#### `TRANSACTIONS`

Системное представление содержит информацию о текущих транзакциях.

| Имя | Тип | Описание |
|---|---|---|
| `ORIGINATING_NODE_ID` | UUID | |
| `STATE` | string | |
| `XID` | UUID | |
| `LABEL` | string | |
| `START_TIME` | long | |
| `ISOLATION` | string | |
| `CONCURRENCY` | string | |
| `KEYS_COUNT` | int | |
| `CACHE_IDS` | string | |
| `COLOCATED` | boolean | |
| `DHT` | boolean | |
| `DURATION` | long | |
| `IMPLICIT` | boolean | |
| `IMPLICIT_SINGLE` | boolean | |
| `INTERNAL` | boolean | |
| `LOCAL` | boolean | |
| `LOCAL_NODE_ID` | UUID | |
| `NEAR` | boolean | |
| `ONE_PHASE_COMMIT` | boolean | |
| `OTHER_NODE_ID` | UUID | |
| `SUBJECT_ID` | UUID | |
| `SYSTEM` | boolean | |
| `THREAD_ID` | long | |
| `TIMEOUT` | long | |
| `TOP_VER` | string | |


#### `NODES`

Системное представление содержит информацию об узлах кластера.

| Имя | Тип данных | Описание |
|---|---|---|
| `IS_LOCAL` | BOOLEAN | Показывает тип узла — локальный или удаленный |
| `ADDRESSES` | VARCHAR | Отображает адреса узла |
| `CONSISTENT_ID` | VARCHAR | Согласованный идентификатор (consistent ID) узла |
| `HOSTNAMES` | VARCHAR | Имена хостов узла |
| `IS_CLIENT` | BOOLEAN | Показывает, является ли узел клиентом |
| `IS_DAEMON` | BOOLEAN | Показывает, работает ли узел в `daemon`-режиме |
| `NODE_ID` | UUID | ID узла |
| `NODE_ORDER` | INT | Порядок расположения узлов в топологии |
| `VERSION` | VARCHAR | Версия узла |

#### `NODE_ATTRIBUTES`

Системное представление содержит атрибуты всех узлов.

| Имя | Тип данных | Описание |
|---|---|---|
| `NODE_ID` | UUID | ID узла |
| `NAME` | VARCHAR | Имя атрибута |

#### `CONFIGURATION`

Системное представление содержит свойства конфигурации узла.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | VARCHAR | Имя свойства конфигурации |
| `VALUE` | VARCHAR | Значение свойства конфигурации |

#### `BASELINE_NODES`

Системное представление содержит информацию об узлах, которые являются частью текущей базовой топологии.

| Имя | Тип данных | Описание |
|---|---|---|
| `CONSISTENT_ID` | VARCHAR | Согласованный идентификатор (consistent ID) узла |
| `ONLINE` | BOOLEAN | Показывает доступность и активность узла |

#### `BASELINE_NODE_ATTRIBUTES`

Системное представление отображает атрибуты узла, зафиксированные в момент установки текущей базовой топологии.

| Имя | Тип данных | Описание |
|---|---|---|
| `NODE_CONSISTENT_ID` | VARCHAR | Согласованный идентификатор узла |
| `NAME` | VARCHAR | Имя атрибута узла |
| `VALUE` | VARCHAR | Значение атрибута |

#### `CLIENT_CONNECTIONS`

Системное представление содержит информацию об открытых в данный момент клиентских подключениях: JDBC, ODBC, тонких клиентах.

| Имя | Тип | Описание |
|---|---|---|
| `CONNECTION_ID` | long | ID соединения |
| `LOCAL_ADDRESS` | IP | IP-адрес локального узла |
| `REMOTE_ADDRESS` | IP | IP-адрес удаленного узла |
| `TYPE` | string | Тип соединения |
| `USER` | string | Имя пользователя |
| `VERSION` | string | Версия протокола |

#### `STRIPED_THREADPOOL_QUEUE`

Системное представление содержит информацию о задачах, ожидающих выполнения в системном пуле разделенных потоков (`striped thread pool`).

| Имя | Тип | Описание |
|---|---|---|
| `DESCRIPTION` | string | `toString`-представление задачи |
| `STRIPE_INDEX` | int | Индекс части потока |
| `TASK_NAME` | string | Имя класса задачи |
| `THREAD_NAME` | string | Имя части потока |

#### `DATASTREAM_THREADPOOL_QUEUE`

Системное представление содержит информацию о задачах, ожидающих выполнения в пуле распределенных потоков `data streamer` (`data streamer stripped thread pool`).

| Имя | Тип | Описание |
|---|---|---|
| `DESCRIPTION` | string | `toString`-представление задачи |
| `STRIPE_INDEX` | int | Индекс части потока |
| `TASK_NAME` | string | Имя класса задачи |
| `THREAD_NAME` | string | Имя части потока |

#### `SCAN_QUERIES`

Системное представление содержит информацию о выполняемых в данный момент запросах сканирования.

| Имя | Тип | Описание |
|---|---|---|
| `CACHE_GROUP_ID` | int | ID группы кешей |
| `CACHE_GROUP_NAME` | string | Имя группы кешей |
| `CACHE_ID` | int | ID кеша |
| `CACHE_NAME` | string | Имя кеша |
| `CANCELED` | boolean | Верно, если запрос отменен |
| `DURATION` | long | Продолжительность запроса |
| `FILTER` | string | `toString`-представление фильтра |
| `KEEP_BINARY` | boolean | Верно при включенном `keepBinary` |
| `LOCAL` | boolean | Верно, если запрос только локальный |
| `ORIGIN_NODE_ID` | UUID | ID узла, инициировавшего запрос |
| `PAGE_SIZE` | int | Размер страницы |
| `PARTITION` | int | ID партиции запроса |
| `QUERY_ID` | long | ID запроса |
| `START_TIME` | long | Время начала запроса |
| `SUBJECT_ID` | UUID | ID пользователя, инициировавшего запрос |
| `TASK_NAME` | string | Имя класса задачи |
| `TOPOLOGY` | string | Версия топологии |
| `TRANSFORMER` | string | `toString`-представление модификатора |

#### `CONTINUOUS_QUERIES`

Системное представление содержит информацию о выполняемых в данный момент непрерывных запросах.

| Имя | Тип | Описание |
|---|---|---|
| `AUTO_UNSUBSCRIBE` | boolean | Верно, если запрос должен быть прекращен при отключении узла или выходе из топологии узла, инициировавшего запрос |
| `BUFFER_SIZE` | int | Размер буфера пакета события |
| `CACHE_NAME` | string | Имя кеша |
| `DELAYED_REGISTER` | boolean | Верно, если запрос инициируется при запуске соответствующего кеша |
| `INTERVAL` | long | Интервал уведомлений |
| `IS_EVENTS` | boolean | Верно, если используется для подписки на удаленные события |
| `IS_MESSAGING` | boolean | Верно, если используется для подписки на сообщения |
| `IS_QUERY` | boolean | Верно, если пользователь инициировал продолжительный запрос (continuous query) |
| `KEEP_BINARY` | boolean | Верно при включенном `keepBinary` |
| `LAST_SEND_TIME` | long | Показывает, когда в последний раз пакет события отсылался на узел, инициировавший запрос |
| `LOCAL_LISTENER` | string | `toString`-представление локального слушателя |
| `LOCAL_TRANSFORMED_LISTENER` | string | `toString`-представление преобразованного локального слушателя |
| `NODE_ID` | UUID | ID узла, инициировавшего запрос |
| `NOTIFY_EXISTING` | boolean | Верно, если слушателя необходимо уведомить о существующих записях |
| `OLD_VALUE_REQUIRED` | boolean | Верно, если старое значение записи должно быть включено в событие |
| `REMOTE_FILTER` | string | `toString`-представление удаленного фильтра |
| `REMOTE_TRANSFORMER` | string | `toString`-представление удаленного преобразователя |
| `ROUTINE_ID` | UUID | ID запроса |
| `TOPIC` | string | Имя топика запроса |

#### `SQL_QUERIES`

Системное представление содержит информацию о выполняемых в данный момент SQL-запросах.

| Имя | Тип | Описание |
|---|---|---|
| `QUERY_ID` | UUID | ID запроса |
| `SQL` | string | Текст запроса |
| `ORIGIN_NODE_ID` | UUID | Узел, инициировавший запрос |
| `START_TIME` | date | Время начала запроса |
| `DURATION` | long | Продолжительность исполнения запроса |
| `INITIATOR_ID` | string | Определяемый пользователем ID инициатора запроса |
| `LOCAL` | boolean | Верно, если запрос только локальный |
| `SCHEMA_NAME` | string | Имя запроса |
| `SUBJECT_ID` | UUID | ID субъекта, инициировавшего запрос |

#### `SQL_QUERIES_HISTORY`

Системное представление содержит информацию об истории SQL-запросов.

| Имя | Тип | Описание |
|---|---|---|
| `SCHEMA_NAME` | string | Имя схемы |
| `SQL` | string | Текст запроса |
| `LOCAL` | boolean | Верно, если запрос только локальный |
| `EXECUTIONS` | long | Количество исполнений запроса |
| `FAILURES` | long | Число сбоев |
| `DURATION_MIN` | long | Минимальная продолжительность исполнения запроса |
| `DURATION_MAX` | long | Максимальная продолжительность исполнения запроса |
| `LAST_START_TIME` | date | Дата последнего исполнения запроса |

#### `SCHEMAS`

Системное представление содержит информацию об SQL-схемах.

| Имя | Тип | Описание |
|---|---|---|
| `NAME` | string | Имя схемы |
| `PREDEFINED` | boolean | Если верно, то схема определена заранее |

#### `NODE_METRICS`

Системное представление содержит различные показатели о состоянии узлов и потреблении ресурсов.

| Имя | Тип данных | Описание |
|---|---|---|
| `NODE_ID` | UUID | ID узла |
| `LAST_UPDATE_TIME` | TIMESTAMP | Последнее обновление метрик |
| `MAX_ACTIVE_JOBS` | INT | Максимальное число одновременно выполняющихся подзадач за все время работы узла |
| `CUR_ACTIVE_JOBS` | INT | Количество активных в настоящий момент подзадач на узле |
| `AVG_ACTIVE_JOBS` | FLOAT | Среднее число активных подзадач, параллельно исполняющихся на узле |
| `MAX_WAITING_JOBS` | INT | Максимальное количество подзадач, находящихся в ожидании, когда-либо существовали на конкретном узле в один момент времени |
| `CUR_WAITING_JOBS` | INT | Количество подзадач в очереди на выполнение на данный момент |
| `AVG_WAITING_JOBS` | FLOAT | Среднее число подзадач, находившихся в очереди за все время работы узла |
| `MAX_REJECTED_JOBS` | INT | Максимальное количество подзадач во время выполнения отдельной операции по разрешению конфликтов |
| `CUR_REJECTED_JOBS` | INT | Количество подзадач, которые были отклонены в результате выполнения последней операции по разрешению конфликтов |
| `AVG_REJECTED_JOBS` | FLOAT | Среднее количество подзадач, отклоненных текущим узлом в результате выполнения операций по разрешению конфликтов |
| `TOTAL_REJECTED_JOBS` | INT | Общее количество подзадач, отклоненных текущим узлом в результате выполнения операций по разрешению конфликтов с момента запуска узла |
| `MAX_CANCELED_JOBS` | INT | Максимальное количество отмененных подзадач, когда-либо выполнявшихся на узле параллельно |
| `CUR_CANCELED_JOBS` | INT | Количество отмененных, но все еще запущенных подзадач |
| `AVG_CANCELED_JOBS` | FLOAT | Среднее количество отмененных подзадач, когда-либо выполнявшихся на текущем узле параллельно |
| `TOTAL_CANCELED_JOBS` | INT | Общее количество подзадач, отмененных с момента запуска узла |
| `MAX_JOBS_WAIT_TIME` | TIME | Максимальное время, в течение которого подзадача находилась в очереди на исполнение |
| `CUR_JOBS_WAIT_TIME` | TIME | Самое продолжительное время ожидания среди подзадач, в данный момент находящихся в очереди на исполнение |
| `AVG_JOBS_WAIT_TIME` | TIME | Среднее время, в течение которого подзадачи находятся в очереди на исполнение |
| `MAX_JOBS_EXECUTE_TIME` | TIME | Максимальное время исполнения подзадачи |
| `CUR_JOBS_EXECUTE_TIME` | TIME | Самое продолжительное время, в течение которого исполняется текущая подзадача |
| `AVG_JOBS_EXECUTE_TIME` | TIME | Среднее время исполнения подзадачи на текущем узле |
| `TOTAL_JOBS_EXECUTE_TIME` | TIME | Общее время исполнения завершенных подзадач на текущем узле с момента его запуска |
| `TOTAL_EXECUTED_JOBS` | INT | Общее число подзадач, обработанных узлом с момента его запуска |
| `TOTAL_EXECUTED_TASKS` | INT | Общее количество задач, обработанных узлом |
| `TOTAL_BUSY_TIME` | TIME | Общее время, в течение которого узел занимался выполнением задач |
| `TOTAL_IDLE_TIME` | TIME | Общее время простоя текущего узла (без выполнения подзадач) |
| `CUR_IDLE_TIME` | TIME | Время, в течение которого узел простаивал после выполнения последней подзадачи |
| `BUSY_TIME_PERCENTAGE` | FLOAT | Процентное соотношение времени выполнения подзадачи ко времени простоя |
| `IDLE_TIME_PERCENTAGE` | FLOAT | Процентное соотношение времени простоя ко времени выполнения задачи |
| `TOTAL_CPU` | INT | Количество ядер процессора, доступных для JVM |
| `CUR_CPU_LOAD` | DOUBLE | Процентное соотношение использования процессора, выраженное фракцией в диапазоне [0, 1] |
| `AVG_CPU_LOAD` | DOUBLE | Среднее соотношение использование процессора, выраженное фракцией в диапазоне [0, 1] |
| `CUR_GC_CPU_LOAD` | DOUBLE | Среднее время, потраченное на сборку мусора с момента последнего обновления метрик. По умолчанию метрики обновляются каждые 2 секунды |
| `HEAP_MEMORY_INIT` | LONG | Размер изначально запрашиваемой JVM у ОС heap-памяти для управления памятью. Если изначальный объем памяти не определен, значение метрики будет равно «–1» |
| `HEAP_MEMORY_USED` | LONG | Текущий размер heap-памяти, используемый для размещения объекта. `Heap` состоит из одного или нескольких пулов памяти. Это значение является суммой значений использованной heap-памяти во всех пулах heap-памяти |
| `HEAP_MEMORY_COMMITED` | LONG | Количество heap-памяти в байтах, выделенное для использования JVM. Heap состоит из одного или нескольких пулов памяти. Это значение является суммой значений выделенной heap-памяти во всех пулах heap-памяти |
| `HEAP_MEMORY_MAX` | LONG | Максимальный объем heap-памяти в байтах, используемый для управления памятью. Метрика отображает «–1», если максимальный объем памяти не задан |
| `HEAP_MEMORY_TOTAL` | LONG | Общий объем heap-памяти в байтах. Если общий объем памяти не задан, метрика отображает «–1» |
| `NONHEAP_MEMORY_INIT` | LONG | Объем изначально запрашиваемой JVM у ОС off-heap-памяти в байтах для управления памятью. Метрика отображает «–1», если изначальный объем памяти не задан |
| `NONHEAP_MEMORY_USED` | LONG | Текущий объем off-heap-памяти, используемый JVM. Off-heap-память состоит из одного или нескольких пулов памяти. Это значение является суммой значений использованной off-heap-памяти всех пулах памяти |
| `NONHEAP_MEMORY_COMMITED` | LONG | Объем off-heap-памяти, выделенной JVM для использования. Off-heap-память состоит из одного или нескольких пулов памяти. Это значение является суммой значений выделенного объема off-heap-памяти всех пулах памяти |
| `NONHEAP_MEMORY_MAX` | LONG | Возвращает максимальный объем off-heap-памяти, которая может использоваться для управления памятью в байтах. Метрика отображает «–1», если максимальный объем памяти не задан |
| `NONHEAP_MEMORY_TOTAL` | LONG | Общее количество off-heap-памяти, которая может быть использована для управления памятью. Метрика отображает «–1», если общий объем памяти не задан |
| `UPTIME` | TIME | Время работы JVM |
| `JVM_START_TIME` | TIMESTAMP | Время запуска JVM |
| `NODE_START_TIME` | TIMESTAMP | Время запуска узла |
| `LAST_DATA_VERSION` | LONG | IMDG присваивает всем кеш-операциям инкрементные версии. Эта метрика отображает последнюю версию данных на узле |
| `CUR_THREAD_COUNT` | INT | Число «живых» потоков, включая `daemon`- и `non-daemon`-потоки |
| `MAX_THREAD_COUNT` | INT | Максимальное количество «живых» потоков с момента запуска JVM или сброса пиковой нагрузки |
| `TOTAL_THREAD_COUNT` | LONG | Общее количество потоков, запущенных с момента запуска JVM |
| `CUR_DAEMON_THREAD_COUNT` | INT | Количество «живых» `daemon`-потоков |
| `SENT_MESSAGES_COUNT` | INT | Число communication-сообщений, отправленных узлом |
| `SENT_BYTES_COUNT` | LONG | Число отправленных байт |
| `RECEIVED_MESSAGES_COUNT` | INT | Число полученных узлом communication-сообщений |
| `RECEIVED_BYTES_COUNT` | LONG | Число полученных байт |
| `OUTBOUND_MESSAGES_QUEUE` | INT | Размер очереди исходящих сообщений |

#### TABLES

Системное представление содержит информацию об SQL-таблицах.

| Имя | Тип данных | Описание |
|---|---|---|
| `AFFINITY_KEY_COLUMN` | string | Имя колонки affinity–ключа |
| `CACHE_ID` | int | ID кеша для таблицы |
| `CACHE_NAME` | string | Имя кеша для таблицы |
| `IS_INDEX_REBUILD_IN_PROGRESS` | boolean | Верно, если производится перестройка индекса для конкретной таблицы |
| `KEY_ALIAS` | string | Псевдоним ключа |
| `KEY_TYPE_NAME` | string | Имя типа ключа |
| `SCHEMA_NAME` | string | Имя схемы таблицы |
| `TABLE_NAME` | string | Имя таблицы |
| `VALUE_ALIAS` | string | Псевдоним значения |
| `VALUE_TYPE_NAME` | string | Имя типа значения |

#### TABLE_COLUMNS

Системное представление содержит информацию о столбцах SQL–таблицы.

| Имя | Тип | Описание |
|---|---|---|
| `AFFINITY_COLUMN` | boolean | Верно, если это колонка affinity–ключа |
| `AUTO_INCREMENT` | boolean | Верно, если значение увеличивается автоматически |
| `COLUMN_NAME` | string | Имя колонки |
| `DEFAULT_VALUE` | string | Значение колонки по умолчанию |
| `NULLABLE` | boolean | Верно, если допустимо пустое значение |
| `PK` | boolean | Верно в случае первичного ключа (primary key) |
| `PRECISION` | int | Точность колонки |
| `SCALE` | int | Масштаб колонки |
| `SCHEMA_NAME` | string | Имя схемы |
| `TABLE_NAME` | string | Имя таблицы |
| `TYPE` | string | Тип таблицы |

#### VIEWS

Системное представление содержит информацию об SQL–представлениях.

| Имя | Тип | Описание |
|---|---|---|
| `NAME` | string | Имя |
| `SCHEMA` | string | Схема |
| `DESCRIPTION` | string | Описание |

#### VIEWS_COLUMNS

Системное представление содержит информацию о колонках SQL–представлений.

| Имя | Тип | Описание |
|---|---|---|
| `COLUMN_NAME` | string | Имя колонки |
| `DEFAULT_VALUE` | string | Значение колонки по умолчанию |
| `NULLABLE` | boolean | Верно, если значение колонки может быть пустым |
| `PRECISION` | int | Точность колонки |
| `SCALE` | int | Масштаб колонки |
| `SCHEMA_NAME` | string | Имя схемы |
| `TYPE` | string | Тип колонки |
| `VIEW_NAME` | string | Имя представления |

#### INDEXES

Системное представление содержит информацию об SQL индексах.

| Имя | Тип данных | Описание |
|---|---|---|
| `INDEX_NAME` | string | Имя индекса |
| `INDEX_TYPE` | string | Тип индекса |
| `COLUMNS` | string | Колонки, включенные в индекс |
| `SCHEMA_NAME` | string | Имя схемы |
| `TABLE_NAME` | string | Имя таблицы |
| `CACHE_NAME` | string | Имя кеша |
| `CACHE_ID` | int | ID кеша |
| `INLINE_SIZE` | int | Объем подстановки в байтах |
| `IS_PK` | boolean | Верно, если это индекс первичного ключа (primary key) |
| `IS_UNIQUE` | boolean | Верно, если индекс уникален |

#### PAGE_LISTS

Список страниц — это структура данных, использующаяся для хранения частично свободных страниц с данными (свободные списки) и полностью свободных выделенных страниц (списки страниц для повторного использования). Целью таких списков является быстрый поиск и локализация страницы с достаточным количеством места в ней для сохранения определенной записи, а также определение того, что такой страницы не существует и необходимо разместить в кеше новую. Списки страниц организуются в пакеты. Каждый такой пакет ссылается на страницы с примерно тем же объемом свободного места.

При включенном режиме Native Persistence списки страниц создаются для каждой партиции каждой группы кешей. Для просмотра таких списков необходимо использовать метрику `CACHE_GROUP_PAGE_LISTS`.

При отключенном режиме Native Persistence списки страниц создаются для каждого региона данных. В данном случае, необходимо использовать метрику `DATA_REGION_PAGE_LISTS`.

Системное представление содержит в себе информацию о каждом пакете каждого списка страниц. `PAGE_LISTS` полезно для понимания того, какой объем данных можно внести в кеш без размещения новых страниц. Также это системное представление помогает определить искажения в использовании списков страниц.

#### `CACHE_GROUP_PAGE_LISTS`

Системное представление содержит информацию о `PAGE LISTS` кеш-групп.

| Имя | Тип данных | Описание |
|---|---|---|
| `CACHE_GROUP_ID` | int | ID группы кешей |
| `PARTITION_ID` | int | ID партиции |
| `NAME` | string | Имя списка страниц |
| `BUCKET_NUMBER` | int | Номер контейнера |
| `BUCKET_SIZE` | long | Число страниц в контейнере |
| `STRIPES_COUNT` | int | Число дорожек, используемых контейнером. Дорожки используются для предотвращения возникновения конфликтов |
| `CACHED_PAGES_COUNT` | int | Число страниц в on-heap-кеше списка страниц конкретного контейнера |
| `PAGE_FREE_SPACE` | int | Свободное пространство (в байтах), доступное для использования для каждой страницы в этом контейнере |

#### `DATA_REGION_PAGE_LISTS`

Системное представление содержит информацию о `PAGE LISTS` в регионе данных (Data Region).

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя списка страниц |
| `BUCKET_NUMBER` | int | Номер контейнера |
| `BUCKET_SIZE` | long | Число страниц в контейнере |
| `STRIPES_COUNT` | int | Число дорожек, используемых контейнером. Дорожки используются для предотвращения возникновения конфликтов |
| `CACHED_PAGES_COUNT` | int | Число страниц в on-heap-кеше списка страниц конкретного контейнера |
| `PAGE_FREE_SPACE` | int | Свободное пространство (в байтах), доступное для использования для каждой страницы в этом контейнере |


#### `PARTITION_STATES`

Системное представление содержит информацию о распределении партиций группы кеша по узлам кластера.

:::{list-table}
:header-rows: 1
 
+   *   Имя
    *    Тип данных
    *    Описание
+   *   `CACHE_GROUP_ID`
    *    int
    *    Идентификатор группы кешей
+   *   `PARTITION_ID`
    *    int
    *    Идентификатор партиции
+   *   `NODE_ID`
    *    UUID
    *    Идентификатор узла
+   *   `STATE`
    *    string
    *    Состояние (статус) партиций. Партиция может иметь следующие состояния:
         - `MOVING` — партиция находится в процессе загрузки с одного узла на другой.
         - `OWNING` — узел является основным или резервным «держателем» партиции.
         - `RENTING` — узел не является ни основным, ни резервным «держателем» партиции (и в настоящий момент вымещается).
         - `EVICTED` — партиция вымещена;
         - `LOST` — некорректный статус партиции. Партицию нельзя использовать
+   *   `IS_PRIMARY`
    *    boolean
    *    Метка основной партиции
:::

#### `BINARY_METADATA`

Системное представление содержит информацию обо всех доступных бинарных типах.

| Имя | Тип данных | Описание |
|---|---|---|
| `TYPE_ID` | int | ID типа |
| `TYPE_NAME` | string | Имя типа |
| `AFF_KEY_FIELD_NAME` | string | Имя поля affinity-ключа |
| `FIELDS_COUNT` | int | Число полей |
| `FIELDS` | string | Записанные поля объектов |
| `SCHEMAS_IDS` | string | ID схем, зарегистрированные для конкретного типа |
| `IS_ENUM` | boolean | Метрика показывает, является ли тип перечисляемым (enum) |

#### `METASTORAGE`

Системное представление дает доступ к кешу хранилища метаданных (`metastorage cache`).

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя |
| `VALUE` | string | Строковое или простое бинарное (в случае невозможности десериализации данных) представление элемента |

#### `DISTRIBUTED_METASTORAGE`

Системное представление дает доступ к кешу распределенного хранилища метаданных (`distributed metastorage cache`).

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя |
| `VALUE` | string | Строковое или простое бинарное (в случае невозможности десериализации данных) представление элемента |

#### `DS_QUEUES`

Системное представление отображает список `IgniteQueue`. Обратите внимание: очередь будет отображаться не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `ID` | UUID | ID |
| `NAME` | string | Имя структуры данных |
| `CAPACITY` | int | Пропускная способность |
| `SIZE` | int | Текущий размер |
| `BOUNDED` | boolean | `True`, когда пропускная способность очереди ограничена |
| `COLLOCATED` | boolean | `True`, если совмещено |
| `GROUP_NAME` | string | Имя группы кешей для сохранения структуры данных |
| `GROUP_ID` | int | ID группы кешей для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_SETS`

Системное представление отображает список `Ignite Set`. Обратите внимание: данные будут показаны не на родительском узле только после первоначального использования на текущем узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `ID` | UUID | ID |
| `NAME` | string | Имя структуры данных |
| `SIZE` | int | Текущий размер |
| `COLLOCATED` | boolean | `True`, если совмещено |
| `GROUP_NAME` | string | Имя группы кешей для хранения структуры данных |
| `GROUP_ID` | int | ID группы кешей для хранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_ATOMICSEQUENCES`

Системное представление отображает список `IgniteAtomicSequence`. Обратите внимание: `IgniteAtomicSequence` будет показан не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `VALUE` | long | Текущее значение последовательности |
| `BATCH_SIZE` | long | Размер локального пакета |
| `GROUP_NAME` | string | Имя группы кешей для хранения структуры данных |
| `GROUP_ID` | int | ID группы кешей, используемой для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_ATOMICLONGS`

Системное представление отображает список `IgniteAtomicLong`. Обратите внимание: `IgniteAtomicLong` будет показан не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `VALUE` | long | Текущее значение последовательности |
| `GROUP_NAME` | string | Имя группы кешей для хранения структуры данных |
| `GROUP_ID` | int | ID группы кешей, используемой для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_ATOMICREFERENCES`

Системное представление отображает список `IgniteAtomicReference`. Обратите внимание: `IgniteAtomicReference` будет отображаться не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `VALUE` | long | Текущее значение последовательности |
| `GROUP_NAME` | string | Имя группы кешей для хранения структуры данных |
| `GROUP_ID` | int | ID группы кешей, используемой для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_ATOMICSTAMPED`

Системное представление отображает список `IgniteAtomicStamped`. Обратите внимание: `IgniteAtomicStamped` будет показан не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `VALUE` | long | Текущее значение последовательности |
| `STAMP` | string | Текущее значение метки |
| `GROUP_NAME` | string | Имя группы кешей для хранения структуры данных |
| `GROUP_ID` | int | ID группы кешей, используемой для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_COUNTDOWNLATCHES`

Системное представление отображает список `IgniteCountDownLatch`. Обратите внимание: `IgniteCountDownLatch` будет показан не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `COUNT` | int | Текущее число |
| `INITIAL_COUT` | int | Изначальное число |
| `AUTO_DELETE` | boolean | Для автоматического снятия блокировки с кеша, когда счетчик близится к нулю, должно быть установлено значение `true` |
| `GROUP_NAME` | string | Имя группы кешей для сохранения структуры данных |
| `GROUP_ID` | int | ID группы кешей для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_SEMAPHORES`

Системное представление отображает список `IgniteSemaphore`. Обратите внимание: `IgniteSemaphore` будет отображаться не на родительских узлах только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `AVAILABLE_PERMITS` | long | Количество доступных разрешений |
| `HAS_QUEUED_THREADS` | boolean | `True`, если есть другие потоки, ожидающие блокировки |
| `QUEUE_LENGTH` | int | Определенное число узлов, ожидающих блокировки |
| `FAILOVER_SAFE` | boolean | `True`, если восстановление после отказа безопасно |
| `BROKEN` | boolean | `True`, если узел вышел из строя на данном семафоре, и свойство `FAILOVER_SAFE` имело значение `false` |
| `GROUP_NAME` | string | Имя группы кешей для сохранения структуры данных |
| `GROUP_ID` | int | ID группы кешей для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### `DS_REENTRANTLOCKS`

Системное представление отображает содержимое `IgniteLock`. Обратите внимание: блокировка будет отображаться не на родительском узле только после первоначального использования на данном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | string | Имя структуры данных |
| `LOCKED` | boolean | `True`, если заблокировано |
| `HAS_QUEUED_THREADS` | boolean | `True`, если есть другие потоки, ожидающие блокировки |
| `FAILOVER_SAFE` | boolean | `True`, если восстановление после отказа безопасно |
| `FAIR` | boolean | `True`, если блокировка «честная» |
| `BROKEN` | boolean | `True`, если узел вышел из строя на данном семафоре, и свойство `FAILOVER_SAFE` имело значение `false` |
| `GROUP_NAME` | string | Имя группы кешей для сохранения структуры данных |
| `GROUP_ID` | int | ID группы кешей для сохранения структуры данных |
| `REMOVED` | boolean | `True`, если удалено |

#### SQL_PLANS_HISTORY

Системное представление содержит список планов ранее выполненных SQL-запросов.

| Имя | Тип | Описание |
|---|---|---|
| `SCHEMA_NAME` | string | Название схемы |
| `SQL` | string | Текст запроса |
| `PLAN` | string | Текст плана SQL-запроса |
| `LOCAL` | boolean | Флаг локального выполнения запроса. Если запрос выполняется локально, флаг принимает значение `true` |
| `ENGINE` | string | SQL-движок |
| `LAST_START_TIME` | date | Дата последнего выполнения |

##### Вопросы производительности

При использовании SQL-движка, который основан на H2, сбор планов выполненных SQL-запросов может привести к дополнительной нагрузке на производительность (при условии высокой интенсивности запросов). Дополнительная нагрузка влияет на задержку и пропускную способность. По этой причине сбор планов выполненных SQL-запросов по умолчанию отключен для движка, который основан на H2.

Чтобы включить сбор планов выполненных SQL-запросов, настройте размер истории планов выполненных SQL-запросов:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean id="grid.cfg" class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="sqlConfiguration">
        <bean class="org.apache.ignite.configuration.SqlConfiguration">
            <property name="sqlPlanHistorySize" value="1000"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setSqlConfiguration(new SqlConfiguration().setSqlPlanHistorySize(1000));
```
:::
::::

При использовании SQL-движка, который основан на Apache Calcite, сбор планов выполненных SQL-запросов не влияет на производительность, поэтому он включен по умолчанию. Размер истории планов выполненных SQL-запросов по умолчанию — 1000 записей.

#### `STATISTICS_CONFIGURATION`

Системное представление содержит информацию о конфигурации SQL–статистики.

| Имя | Тип данных | Описание |
|---|---|---|
| `SCHEMA` | VARCHAR | Имя схемы |
| `TYPE` | VARCHAR | Тип объекта |
| `NAME` | VARCHAR | Имя объекта |
| `COLUMN` | VARCHAR | Имя колонки |
| `MAX_PARTITION_OBSOLESCENCE_PERCENT` | TINYINT | Максимальный процент устаревающих строк в статистике |
| `MANUAL_NULLS` | BIGINT | Если не `null` — количество `null`-значений превышено |
| `MANUAL_DISTINCT` | BIGINT | Если не `null` — количество `distinct`-значений превышено |
| `MANUAL_TOTAL` | BIGINT | Если не `null` — превышено общее количество значений |
| `MANUAL_SIZE` | INT | Если не `null` — превышено количество не `null`-значений в колонке |
| `VERSION` | BIGINT | Версия конфигурации |

#### `STATISTICS_LOCAL_DATA`

Системное представление содержит SQL–статистику для локально управляемых (или сохраненных) данных. `STATISTICS_LOCAL_DATA` специфична для каждого конкретного узла, поэтому у каждого узла есть пример метрики, содержащий информацию со статистикой его локальных данных.

| Имя | Тип данных | Описание |
|---|---|---|
| `SCHEMA` | VARCHAR | Имя схемы |
| `TYPE` | VARCHAR | Тип объекта |
| `NAME` | VARCHAR | Имя объекта |
| `COLUMN` | VARCHAR | Имя колонки |
| `ROWS_COUNT` | BIGINT | Число строк в колонке |
| `DISTINCT` | BIGINT | Число уникальных не `null`-значений |
| `NULLS` | BIGINT | Число `null`-значений |
| `TOTAL` | BIGINT | Общее число значений в колонке |
| `SIZE` | INTEGER | Средний размер значения в байтах |
| `VERSION` | BIGINT | Версия статистики |
| `LAST_UPDATE_TIME` | VARCHAR | Максимальное время, в течение которого вся статистика по партициям использовалась для создания локальной статистики |

#### `STATISTICS_PARTITION_DATA`

Системное представление содержит информацию об SQL–статистике по каждой партиции данных, хранящейся на локальном узле.

| Имя | Тип данных | Описание |
|---|---|---|
| `SCHEMA` | VARCHAR | Имя схемы |
| `TYPE` | VARCHAR | Тип объекта |
| `NAME` | VARCHAR | Имя объекта |
| `COLUMN` | VARCHAR | Имя колонки |
| `PARTITION` | INTEGER | Номер партиции |
| `ROWS_COUNT` | BIGINT | Число строк в колонке |
| `UPDATE_COUNTER` | BIGINT | Обновление счетчика партиций после сбора статистики|
| `DISTINCT` | BIGINT | Число уникальных не `null`-значений |
| `NULLS` | BIGINT | Число `null`-значений |
| `TOTAL` | BIGINT | Общее число значений в колонке |
| `SIZE` | INTEGER | Средний размер значения в байтах |
| `VERSION` | BIGINT | Версия статистики |
| `LAST_UPDATE_TIME` | VARCHAR | Максимальное время, в течение которого вся статистика по партициям использовалась для создания локальной статистики |

#### `SNAPSHOT`

Системное представление содержит информацию о локальных снепшотах.

| Имя | Тип данных | Описание |
|---|---|---|
| `NAME` | VARCHAR | Имя снепшота |
| `CONSISTENT_ID` | VARCHAR | Последовательный идентификатор узла, к которому относятся данные снепшота |
| `BASELINE_NODES` | VARCHAR | Базовые узлы, на которые влияет снепшот |
| `CACHE_GROUPS` | VARCHAR | Имена групп кеша, включенных в снепшот |
| `SNAPSHOT_RECORD_SEGMENT` | BIGINT | Индекс сегмента WAL, содержащий записи WAL-снепшотов |
| `INCREMENT_INDEX` | INTEGER | Индекс инкрементального снепшота |
| `TYPE` | VARCHAR | Тип снепшота — полный или инкрементальный |
