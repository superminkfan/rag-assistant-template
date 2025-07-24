# Плагин для работы CDC в реальном времени

:::{admonition} Внимание
:class: danger

Данная функциональность находится в статусе Alpha. Это означает, что она может содержать ошибки, которые не были обнаружены во время синтетического тестирования. В процессе эксплуатации могут возникать проблемы в работе. Эта версия может содержать не все запланированные функции и возможности. Разработчики могут добавлять новые функции или улучшать существующие в следующих релизах.
:::

## Описание

Плагин `cdc-manager-plugin` позволяет сократить задержку репликации CDC, обрабатывая события и доставляя их до `CdcConsumer` внутри узла DataGrid.

Плагин предоставляет собой реализацию интерфейса `CdcManager`. Его задача — перехватывать `DataRecords`, записываемые в WAL-журнал, и сохранять их во внутреннем буфере в виде массива байт. Поток `cdc-worker` последовательно считывает данные из буфера и преобразует их в `CdcEvents` для передачи в `CdcConsumer`.

:::{admonition} Внимание
:class: danger

Ограничение размера буфера — 2 Гб.
:::

Плагин также отслеживает изменения в `BinaryMeta`, `CacheConfiguration`. Эти изменения также передаются в соответствующие методы `CdcConsumer`.

Обратите внимание, что `CdcConsumer` работает внутри узла. Учитывайте это при его реализации. Если `CdcConsumer` долго обрабатывает данные, то возникает риск переполнения буфера. В случае переполнения буфера работа `CdcManager` остановится, и за работу CDC снова будет отвечать утилита `ignite-cdc`.

## Конфигурация

Для активации плагина дополните `IgniteConfiguration` один из приведенных способов:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteConfiguration cfg = ...;

CdcManagerPluginConfiguration plgCfg = new CdcManagerPluginConfiguration();

cfg.setPluginProviders(new CdcMangerPluginProvider(plgCfg));
```

Конфигурация `CdcManagerPluginConfiguration` имеет следующие опции:

- `setBuffSize` — размер внутреннего буфера, который хранит `DataRecords` из WAL-журнала;
- `setConsumer` — реализация `CdcConsumer`;
- `setKeepBinary` — если `true`, то данные передаются в `CdcConsumer` в бинарном виде.
:::

:::{md-tab-item} XML
```xml
<property name="pluginProviders">
    <list>
        <ref bean="server_securityPlugin"/>
        <bean class = "com.sbt.ignite.cdc.CdcManagerPluginProvider">
            <constructor-arg ref="cdcManager"/>
        </bean>          
    </list>
</property>
...
<bean id = "cdcManager" class = "com.sbt.ignite.cdc.CdcManagerPluginConfiguration">
    <property name="bufferSize" value="1073741824"/>
    <property name="consumer"   ref="cdcStreamer"/>
    <property name="keepBinary" value="true"/>
</bean>
```

Добавьте в файл конфигурации `customIgniteConfiguration.xml` в класс `IgniteConfiguration`.
:::
::::

Утилита `ignite-cdc` должна быть запущена вместе с узлом DataGrid и сконфигурирована аналогичным образом.

## Режимы работы CDC

CDC может работать в двух режимах:

-   `IGNITE_NODE_ACTIVE` — плагин обрабатывает события и поставляет данные в `CdcConsumer` внутри узла DataGrid;
-   `CDC_UTILITY_ACTIVE` — утилита `ignite-cdc` обрабатывает архивные сегменты WAL и поставляет данные в `CdcConsumer`.

Режим CDC по умолчанию — `IGNITE_NODE_ACTIVE`. В случае ошибки в `CdcConsumer` или в случае переполнения буфера, режим CDC переключается в `CDC_UTILITY_ACTIVE`. Утилита `ignite-cdc` автоматически перехватывает управление процессом CDC.

Для переключения режима CDC обратно в `IGNITE_NODE_ACTIVE`:

1. Остановите узел DataGrid.
2. Дождитесь, пока утилита `ignite-cdc` завершит обработку всех WAL сегментов в директории `сdcWalPath`.
3. Остановите утилиту `ignite-cdc`.
4. Удалите файл `сdcWalPath/state/cdc-mode.bin` и `сdcWalPath/000000000000***.wal` (единственный wal-файл в каталоге) 
5. Запустите узел DataGrid.
6. Запустите утилиту `ignite-cdc`.

## Логирование

Рекомендуется настроить логирование процесса `onlinecdc` в отдельный log-файл. Для этого добавьте запись классов `com.sbt.ignite.cdc` и `org.apache.ignite.cdc` в уже используемую конфигурацию log4j2.

::::{admonition} Пример конфигурации log4j2
:class: hint

:::{code-block} xml
:caption: XML
<Logger name="com.sbt.ignite.cdc" level="INFO" additivity="false">
    <AppenderRef ref="ONLINECDC"/>
</Logger>        
<Logger name="org.apache.ignite.cdc" level="INFO" additivity="false">
    <AppenderRef ref="ONLINECDC"/>
</Logger>
</Routing>
    <Routing name="ONLINECDC">
    <Routes pattern="$${sys:nodeId}">
        <Route>
            <RollingFile name="Rolling-${sys:nodeId}" fileName="/opt/ignite/server/logs/ONLINECDC-${sys:appId}.log"
                    filePattern="/opt/ignite/server/logs/ONLINECDC-${sys:appId}-${sys:nodeId}-%i-%d{yyyy-MM-dd}.log.gz">
                <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss.SSS} [%-5level][%t][%logger{36}] %msg%n"/>
            <Policies>
                <TimeBasedTriggeringPolicy interval="1" modulate="true" />
                    </Policies>
                </RollingFile>
        </Route>
    </Routes>
</Routing>
:::
::::

## Метрики

Плагин предоставляет следующие метрики для мониторинга процесса CDC в рамках узла DataGrid:

-   `CdcManagerMode` — текущий режим работы CDC (`IGNITE_NODE_ACTIVE` или `CDC_UTILITY_ACTIVE`);
-   `BufferSize` — сконфигурированный размер CDC буфера (в байтах);
-   `BufferUsedSize` — текущий размер данных, накопленных в буфере (в байтах);
-   `BufferMaxUsedSize` — максимальный размер данных, хранившихся в буффере (в байтах);
-   `LastCollectedSegmentIndex` — индекс сегмента последней обработанной записи;
-   `LastCollectedSegmentOffset` — позиция в сегменте последней обработанной записи;
-   `CommittedSegmentIndex` — индекс сегмента последней подтвержденной записи;
-   `CommittedSegmentOffset` — позиция в сегменте последней подтвержденной записи;
-   `EventsConsumptionTime` — время, затраченное на обработку пачки событий в `CdcConsumer` (в миллисекундах);
-   `LastConsumptionTime` — временная метка последней обработки пачки событий в `CdcConsumer`;
-   `MetadataUpdateTime` — время, затраченное на обработку метаданных в `CdcConsumer` (в миллисекундах).

Также в узле DataGrid доступны метрики реализации `CdcConsumer`.