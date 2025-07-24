# Настройка мониторинга

## Настройка кластера для сбора метрик транзакций и операций с кешами в формате Prometheus с помощью Zabbix

### Требования

-   Zabbix версия 6.0 LTS;
-   Zabbix-agent версия 6.0 LTS.

### Конфигурация узла DataGrid

Подробно процесс настройки узла под нужды мониторинга описан в «Руководстве по системному администрированию».

Ниже приведен пример конфигурационного файла для включения IgniteHttpMetricsExporterSpi для сбора метрик транзакций и операций с кешами шаблоном «SBT DataGrid Cache and Tx HttpMetricsExporter 1.0»:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
  <property name="metricExporterSpi">
    <list>
      <bean class="org.apache.ignite.viewer.IgniteHttpMetricsExporterSpi">
        <property name="port" value="yyyy"/>
        <property name="groups">
          <list>
            <bean class="org.apache.ignite.viewer.config.RegExpGroup">
              <property name="context" value="/cache"/>
              <property name="regExp" value="cache\..*"/>
            </bean>
            <bean class="org.apache.ignite.viewer.config.NamesListGroup">
              <property name="context" value="/tx"/>
              <property name="names">
                <value>tx</value>
              </property>
            </bean>
          </list>
        </property>
      </bean>
    </list>
  </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteHttpMetricsExporterSpi igniteHttpMetricsExporterSpi = new IgniteHttpMetricsExporterSpi();

igniteHttpMetricsExporterSpi.setPort(8084); // Порт для HTTP-экспортера.

// Для сбора метрик операций с кешами и транзакций:
RegExpGroup cacheGroup = new RegExpGroup();
cacheGroup.setRegExp("cache.*");
cacheGroup.setContext("/cache");

NamesListGroup txGroup = new NamesListGroup();
txGroup.setNames(Arrays.asList("tx"));
txGroup.setContext("/tx");

// Опционально можно включить экспорт всех метрик:
RegExpGroup allMetrics = new RegExpGroup();
allMetrics.setRegExp(".*");
allMetrics.setContext("/metrics");


igniteHttpMetricsExporterSpi.setGroups(Arrays.asList(cacheGroup, txGroup, allMetrics));

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setMetricExporterSpi(igniteHttpMetricsExporterSpi, new JmxMetricExporterSpi());

Ignition.start(cfg);
```
:::
::::

В результате применения указанных опций на узле DataGrid будут доступны следующие ресурсы:

-   `http://xxx.x.x.x:yyyy/cache/` — страница с метриками операций с кешами;
-   `http://xxx.x.x.x:yyyy/tx/` — страница с метриками транзакций;
-   `http://xxx.x.x.x:yyyy/metrics/` — страница со всеми метриками узла DataGrid;

  где `xxx.x.x.x` — локальный сетевой интерфейс клиентского узла DataGrid, `yyyy` — номер порта, указанный в `<property name="port" value="yyyy"/>`.

### Настройка Zabbix

1.  Импортируйте шаблон мониторинга SBT DataGrid Cache and Tx HttpMetricsExporter 1.0 на сервер Zabbix.
2.  Прикрепите шаблон к целевым хостам.
3.  На хостах настройте макросы:

    - `{$HTTP_PORT}` — номер порта должен совпадать с номером порта, указанным в настройке `<property name="port" value="yyyy"/>`;
    - `{$HTTP_CONTEXT_TX}` — название URI контекста для ресурса с метриками транзакций; должно совпадать с настройкой `<property name="context" value="/tx"/>`;
    - `{$HTTP_CONTEXT_CACHE}` — Название URI контекста для ресурса с метриками операций с кешами; должно совпадать с настройкой `<property name="context" value="/cache"/>`.

4.  Убедитесь, что метрики обнаружились, и данные поступают. Для этого в **Web UI Zabbix** перейдите в раздел **Мониторинг/Последние данные** и в настройках фильтра укажите целевые хосты и теги *Application: DataGrid TX* и *Application: DataGrid Cache*.

## Настройка мониторинга CDC-репликации DataGrid

Все CDC-узлы, участвующие в репликации, должны быть настроены на мониторинг как самостоятельные сущности. Для мониторинга таких узлов необходимо определить четыре постоянных порта (два JMX и два RMI) и зафиксировать эти номера портов у администраторов Zabbix через ЗНО.

### Вариант репликации Ignite to Ignite

#### Active–Passive репликация

1.  Для каждого клиентского узла (КУ), передающего данные с кластера-источника, создайте на zabbix-сервере хост для мониторинга данного КУ. Имя хоста должно совпадать с именем основного JMX-хоста серверного узла (СУ), на котором запущен процесс репликации, с добавлением суффикса `cdc-i2i`.

    :::{admonition} Внимание
    :class: danger

    Все хосты из шага 1 должны входить в отдельную хост-группу. Имя хост-группы должно совпадать с именем хост-группы кластера-источника и оканчиваться на `/i2i`.
    :::

2.  Ко всем хостам в хост-группе «i2i» прикрепите шаблон «SBT DataGrid CDC» актуальной версии.
3.  После создания хостов, указанных в шаге 1, в мастер-шаблоне для мониторига логов хост-группы СУ передающего кластера активируйте элемент данных «CDC port listen» и укажите в макросе `{$DATAGRID.CDC.CLIENT.PORT.HIGH}` актуальный JMX порт.

:::{admonition} Пример
:class: hint

- группа СУ хостов передающего кластера: `IGN ППРБ ПРОМ РБ/ISE`;
- имя СУ: `sylvanas10.ignite.jmx1098`;
- группа CDC хостов передающего кластера: `IGN ППРБ ПРОМ РБ/I2I`;
- имя КУ для репликации (CDC): `sylvanas10.cdc-i2i.jmx0000`;

  где `0000` — номер порта, согласованного с администраторами zabbix.
:::

#### Active–Active репликация

Все действия по созданию хостов и хост-группы должны быть зеркально повторены для противоположного кластера.

### Вариант репликации с использованием транспорта Kafka

#### Active–Passive репликация

1.  Для каждого процесса CDC, передающего данные с кластера-источника, создайте на zabbix-сервере хост для мониторинга данного процесса. Имя хоста должно совпадать с именем основного JMX-хоста серверного узла (СУ), на котором запущен процесс репликации, с добавлением суффикса `cdc-i2k`.

    :::{admonition} Внимание
    :class: danger

    Все хосты из шага 1 должны входить в отдельную хост-группу. Имя хост-группы должно совпадать с именем хост-группы кластера-источника и оканчиваться на `/i2k`.
    :::

2.  После создания хостов, указанных в шаге 1, в мастер-шаблоне для мониторинга логов хост-группы СУ передающего кластера активируйте элемент данных «CDC port listen» и укажите в макросе `{$DATAGRID.CDC.CLIENT.PORT.HIGH}` актуальный JMX порт.
3.  На принимающем кластере для КУ, выполняющих роль стримеров `kafka-to-ignite`, создайте zabbix-хосты. Имена хостов должны совпадать с именами основных хостов для мониторинга СУ с добавлением суффикса `cdc-k2i`.
4.  Все хосты из шага 3 должны входить в отдельную хост-группу. Имя хост-группы должно совпадать с именем хост-группы принимающего кластера и оканчиваться на `/k2i`.
5.  После создания хостов, указанных в шаге 3, в мастер-шаблоне для мониторига логов хост-группы СУ передающего кластера активируйте элемент данных «CDC port listen» и укажите в макросе `{$DATAGRID.CDC.CLIENT_KAFKA.PORT.HIGH}` актуальный JMX порт.

#### Active–Active репликация

Все действия по созданию хостов и хост-группы должны быть зеркально повторены для противоположного кластера.

:::{admonition} Пример
:class: hint

- группа СУ хостов передающего кластера: `IGN ППРБ ПРОМ РБ/ISE`;
- имя СУ: `sylvanas10.ignite.jmx1098`;
- группа CDC хостов передающего кластера: `IGN ППРБ ПРОМ РБ/I2K`;
- имя хоста для репликации (CDC): `sylvanas10.cdc-i2k.jmx0000`, где `0000` — номер порта, согласованного с администратором Zabbix;
- группа CDC хостов принимающего кластера: `IGN ППРБ ПРОМ РБ/K2I`;
- имя КУ для репликации (CDC): `sylvanas10.cdc-k2i.jmx0000`, где `0000` — номер порта, согласованного с администратором Zabbix.
:::

## Настройка мониторинга ячеек кластера (Backup Filter)

### Настройка экспортера метрик

В конфигурационный файл узла DataGrid поместите следующие строки:

:::{code-block} xml
:caption: XML
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
   <property name="metricExporterSpi">
        <list>
            <bean class="org.apache.ignite.spi.metric.jmx.JmxMetricExporterSpi"/>
            <bean class="org.apache.ignite.spi.metric.log.LogExporterSpi"/>
        </list>
    </property>
</bean>
:::

### Настройка записи метрик в отдельный log-файл (для log4j2)

Ниже приведен пример конфигурации log4j2 для записи метрик DataGrid в отдельный файл лога. Ротация происходит каждый час и сохраняет три последних архива.

:::{code-block} xml
:caption: XML
<Configuration monitorInterval="60">
    <Appenders>
        <Routing name="MONITORING">
            <Routes pattern="$${sys:nodeId}">
                <Route>
                    <RollingFile name="Rolling-${sys:nodeId}" fileName="${sys:IGNITE_HOME}/work/log/metrics-${sys:appId}.log" filePattern="${sys:IGNITE_HOME}/work/log/metrics-${sys:appId}-${sys:nodeId}-%d{yyyy-MM-dd-HH}.log.gz">
                        <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss.SSS} [%-5level][%t][%logger{36}] %msg%n"/>
                        <Policies>
                            <TimeBasedTriggeringPolicy interval="1" modulate="true" />
                        </Policies>
                        <DefaultRolloverStrategy>
                            <Delete basePath="${sys:IGNITE_HOME}/work/log/">
                                <IfFileName glob="metrics-*.log.gz" />
                                <IfAccumulatedFileCount exceeds="3" />
                            </Delete>
                        </DefaultRolloverStrategy>
                    </RollingFile>
                </Route>
            </Routes>
        </Routing>
    </Appenders>

    <Loggers>
        <Logger name="org.apache.ignite.spi.metric.log.LogExporterSpi" level="INFO" additivity="false">
            <AppenderRef ref="MONITORING"/>
        </Logger>
    </Loggers>
</Configuration>
:::

### Настройка Zabbix

Для настройки Zabbix:

1.  На все узлы скопируйте файлы `sbt_datagrid_compute_node_reserv.sh` и `userparameter_sbt_datagrid.conf` в директорию с пользовательскими параметрами zabbix-agent. Например, для Platform V SberLinux директория будет `/etc/zabbix/zabbix-agent.d/`. Для уточнения правильного пути для конкретной ОС обратитесь к документации Zabbix.
2.  Импортируйте шаблон мониторинга «SBT DataGrid Log» и прикрепите его ко всем хостам кластера.
3.  На всех хостах кластера укажите актуальные значения макросов:

-   `{$DATAGRID.METRICS_LOG.PATH}` - путь к файлу метрик DataGrid;
-   `{$DATAGRID.AFFINITI_BACKUP_FILTER.NAME}` - имя параметра, в котором задается название ячейки кластера.