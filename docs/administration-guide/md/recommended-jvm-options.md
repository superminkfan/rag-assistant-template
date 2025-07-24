# Рекомендуемые JVM-опции для DataGrid

Ниже приведен минимальный рекомендуемый набор опций для корректной работы DataGrid. 

В случае сбоя применение указанных опций позволяет получить достаточную фактуру для анализа проблемы.

## JVM-опции, которые применяются к OpenJDK 11 и 17 

| Параметр | Описание |
|---|---|
| `-Xmx` | Максимальный размер Heap |
| `-Xms` | Начальный размер Heap (в общем случае выбирается равным `Xmx`) |
| `-ea` | Активация assertions |
| `-server` | Включение серверного режима в JVM |
| `-XX:+ScavengeBeforeFullGC` | Сборка в young-поколении перед Full GC |
| `-XX:+AlwaysPreTouch` | Инициализация памяти при аллокации Heap |
| `-XX:+UnlockDiagnosticVMOptions` | Включение возможности использования дополнительных отладочных опций |
| `-Djava.net.preferIPv4Stack` | Использование протокола IPv4 |
| `-Dnetworkaddress.cache.ttl` | Используется для указания политики кеширования, успешного резолвинга DNS. Значение указывается как целое число для последующего указания количества времени в секундах, которое необходимо для кеширования успешного поиска. `-1` означает «кешировать всегда» |
| `-XX:+ExitOnOutOfMemoryError` | Остановка JVM при событии `OutOfMemoryError` |
| `-XX:+HeapDumpOnOutOfMemoryError` | Снятие `HeapDump` при событии `OutOfMemoryError` |
| `-XX:HeapDumpPath` | Путь к `HeapDump` |
| `-XX:ErrorFile` | Путь к `JVM crush dump` |
| `-Djava.io.tmpdir` | Переопределение временной директории в JVM |
| `-Dcom.sun.management.jmxremote.port` | Указание порта для JMX |
| `-Dcom.sun.management.jmxremote.authenticate` | Включение аутентификации для подключения к JMX |
| `-Dcom.sun.management.jmxremote.ssl` | Включение SSL для JMX-соединений |
| `-Dcom.sun.management.config.file` | Путь к файлу конфигурации JMX |
| `-Dfile.encoding` | Задает кодировку по умолчанию |
| `-XX:+PerfDisableSharedMem` | Снижает вероятность возникновения GC-паузы при работе внутренних механизмов профилирования |
| `-XX:+UnlockExperimentalVMOptions` | Включение экспериментальных параметров JVM |
| `-XX:-OmitStackTraceInFastThrow` | Включение вывода трассировки стека для определенной группы исключительных ситуаций |
| `-XX:+LogVMOutput` | Включение логирования JVM |
| `-XX:+UseShenandoahGC` | Использование сборщика мусора Shenandoah |
| `-XX:PrintSafepointStatisticsCount` | Количество записей в последнем отчете safepoint |
| `-XX:StartFlightRecording` | Активирует JFR и определяет основные параметры его работы |
| `-XX:FlightRecorderOptions` | Задает дополнительные параметры работы JFR |
| `-Xlog:gc*` | Настройка log-файла GC, детализация, ротация |
| `-Xlog:safepoint` | Настройка log-файла safepoint, детализация |
| `-XX:G1NewSizePercent` | Задает размер young-поколения в процентах |
| `-XX:+PrintSafepointStatistics` | Выводит в log-файл статистику по safepoint-паузам |
| `-XX:+SafepointTimeout` | Выводит в log-файл информацию о потоках, у которых `time to safepoint` превысило предустановленный тайм-аут |
| `-XX:SafepointTimeoutDelay` | Если `time to safepoint` потока превысит этот тайм-аут и используется опция `-XX:+SafepointTimeout`, в log-файле выведется информация о данном потоке |
| `-XX:G1MaxNewSizePercent` | Устанавливает максимальный размер young-региона. Задается в процентах от размера Heap. Используется для настройки производительности в высоконагруженных проектах |
| `-XX:InitiatingHeapOccupancyPercent` | Устанавливает заполненность Heap в процентах, с которой начинается сборка мусора |
| `-XX:-G1UseAdaptiveIHOP` | Отключение Adaptive IHOP (автоматическое определение оптимального IHOP по процессу маркировки) |
| `-XX:G1HeapRegionSize` | Устанавливает размер региона для GC G1 |
| `-Dnode.id` | Вспомогательный идентификатор для различных интеграций |
| `-Dmodule.id` | Вспомогательный идентификатор для различных интеграций |
| `-Djava.security.properties` | Задает путь к файлу `security.properties`, который следует использовать при запуске JVM |
| `-Dgroup.id` | Вспомогательный идентификатор для различных интеграций |
| `-Dconfig-store.disabled` | Для интеграции с конфигуратором |
| `-Dplatform-config` | Для интеграции с конфигуратором |
| `-Djndi-store.disabled` | Для интеграции с конфигуратором |
| `-Dcom.sun.management.jmxremote` | Включение JMX |
| `-Dlog4j2.formatMsgNoLookups` | WA к уязвимости старых Log4j2 |

## JVM-опции, которые применяются к OpenJDK 11

| Параметр | Описание |
|---|---|
| `--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED` | Позволяет получать доступ к публичным полям и методам пакета в runtime |
| `--add-exports=java.base/sun.nio.ch=ALL-UNNAMED` | Позволяет получать доступ к публичным полям и методам пакета в runtime |
| `--add-exports=java.management/com.sun.jmx.mbeanserver=ALL-UNNAMED` | Позволяет получать доступ к публичным полям и методам пакета в runtime |
| `--add-exports=jdk.internal.jvmstat/sun.jvmstat.monitor=ALL-UNNAMED` | Позволяет получать доступ к публичным полям и методам пакета в runtime |
| `--add-exports=java.base/sun.reflect.generics.reflectiveObjects=ALL-UNNAMED` | Позволяет получать доступ к публичным полям и методам пакета в runtime |
| `--add-opens=jdk.management/com.sun.management.internal=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--illegal-access=permit` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `-XX:-UseBiasedLocking` | Отключение Biased Locking. Оптимизация неэффективная для сценариев с низкими задержками (low-latency) |

## JVM-опции, которые применяются к OpenJDK 17

| Параметр | Описание |
|---|---|
| `--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/sun.nio.ch=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.management/com.sun.jmx.mbeanserver=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=jdk.internal.jvmstat/sun.jvmstat.monitor=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/sun.reflect.generics.reflectiveObjects=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=jdk.management/com.sun.management.internal=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.io=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.nio=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.util=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.util.concurrent=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.lang=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.lang.invoke=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.math=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.sql/java.sql=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.lang.reflect=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.time=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.base/java.text=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens=java.management/sun.management=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |
| `--add-opens java.desktop/java.awt.font=ALL-UNNAMED` | Позволяет получать доступ ко всем (не только к публичным) полям и методам пакета в runtime |

**Только для клиентских узлов:**

| Параметр | Описание |
|---|---|
| `-DIGNITE_START_CACHES_ON_JOIN=true` | Включение инициализации прокси-кешей на клиентском узле во время его запуска |

## Вендорозависимые JVM-опции

### Openjdk

| Параметр | Описание |
|---|---|
| `-XX:StartFlightRecording=disk={{ ignite_se_jfr_disk }},settings={{ ignite_se_jfr_settings }},maxage={{ ignite_se_jfr_maxage }},maxsize={{ ignite_se_jfr_maxsize }},dumponexit={{ ignite_se_jfr_dumponexit }},{% if ignite_se_jfr_dumponexit == 'True' %}filename={{ ignite_se_diag_dir }}/dumpjfr.jfr{% endif %}` | При запуске JVM, JFR будут записываться на диск. Параметрами можно регулировать глубину хранения и детализацию JFR |
| `-XX:FlightRecorderOptions=repository={{ ignite_se_diag_dir }},maxchunksize={{ ignite_se_jfr_maxchunksize }}` | Указывает, куда помещать записанные JFR и задает размер chunk |

## Опции GC для Openjdk Java 11

| Параметр | Описание |
|---|---|
| `-Xlog:gc*=debug,gc+classhisto=trace:file={{ ignite_se_jvm_gc_log }}:time,uptime,tags:filecount=50,filesize=50M` | Настройка log-файла GC, детализация, ротация |
| `-Xlog:safepoint:file={{ ignite_se_jvm_safepoint_log }}:time,uptime,tags:filecount=50,filesize=50M` | Настройка log-файла safepoint, детализация, ротация |

## Настройка стабильной топологии (PROP_STABLE_TOPOLOGY)

В in-memory-кластерах смена паролей от учетных записей DataGrid с помощью `REST` возможна, только если настроена стабильная топология. Она задается с помощью JVM-опции.

:::{code-block} java
:caption: Java
-DPROP_STABLE_TOPOLOGY="consistID1,consistID2,...,consistIDN"
:::

где `consistID1,consistID2,...,consistIDN` — согласованные идентификаторы (`consistent ID`) узлов, которые составляют стабильную топологию.

:::{admonition} Важно
:class: attention

На всех узла кластера с помощью опции `PROP_STABLE_TOPOLOGY` должны передаваться одинаковые списки `consistent ID`. Узлы, на которых списки будут отличаться, не войдут в тополгию.
:::