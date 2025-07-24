# Первичный анализ логов

Работу с DataGrid можно представить в виде следующих уровней:

-   Уровень приложения, отправляющего запросы в DataGrid.
-   Уровень DataGrid.
-   Уровень JVM, в которой работает DataGrid.
-   Уровень ОС, на которой работает JVM. Является прослойкой между аппаратными ресурсами и JVM.
-   Уровень аппаратных ресурсов (CPU, RAM, SSD/HDD, Network).

На каждом из уровней могут возникнуть ошибки. У каждого из уровней есть свои диагностические утилиты и своя фактура для анализа.

Возможные причины проблем в работе DataGrid на каждом уровне:

| Уровень | Анализ фактуры | Возможные причины проблем |
|---|---|---|
| Приложение, отправляющее запросы в DataGrid | ignite.log, jmx, Grafana, Zabbix, nmon | Некорректная настройка, некорректное использование API, некорректный код бизнес-логики, ошибки в технических компонентах, например, в конфигураторе |
| DataGrid | JMX, логи DataGrid: ignite.log, control-utility.log, idle_verify-[].txt | Неполнота документации, ошибки кода, некорректная конфигурация |
| JVM, в котором работает DataGrid | JFR, jvm crush dump, heapdump, log-файл GC, log-файл Safepoint | Дефекты, некорректная конфигурация |
| ОС | dmesg, messages, nmon, sar, sysstat | Дефекты, некорректная конфигурация
| Аппаратные ресурсы (CPU, RAM, SSD/HDD, Network) | ignite.log, Zabbix, Grafana, messages & dmesg | Проблемы с аппаратными ресурсами, ошибки работы сети |

Если источник проблемы неизвестен до начала анализа, изучите информацию по следующим пунктам:

-   Соответствие значений параметров стенда рекомендуемым — комплексная проверка, отвечающая за соответствие окружения условиям, при которых возможна эксплуатация с требуемыми характеристиками.

    Рекомендуемые значения параметров расположены в виде `yml`-файлов в дистрибутиве DataGrid в каталоге `Ignite-SE-[version]/Ignite-SE-ansibleRole-[version]/defaults/main`:

    -   `0.checklist.yml` — параметры ОС;
    -   `2.jvm.yml` — JVM-опции;
    -   `3.config.yml` — параметры DataGrid.

-   Дашборды Grafana — проверка метрик на наличие аномалий, отклонений от ожидаемых значений и крайних состояний метрик.
-   Логи DataGrid (`ignite.log`, `control-utility.log`, `idle_verify-[дата].txt`) — поиск сообщений в интервале возникновения проблемы, поиск по *WARN*, *ERROR*, проверка содержимого *INFO* для определения состояния DataGrid.
-   GC, Safepoint — поиск проблем, связанных с особенностями JVM, долгой или частой сборкой мусора, высокой утилизацией Heap.
-   messages, dmesg — проверка состояния операционной системы на момент воспроизведения проблемы и до него.
-   nmon, sar — поиск степени утилизации аппаратных ресурсов на момент воспроизведения проблемы.
-   JFR — проверка аспектов работы JVM, кода внутри JVM в зависимости от настроек.

Используя команды `grep`, `less` вместе с регулярными выражениями, стоит сформировать запрос на поиск *WARN*, *ERROR*, *INFO* сообщений и восстановить последовательность событий, которые привели к проблеме в работе DataGrid.

При обнаружении сообщений об ошибке на одном узле, проверьте наличие таких же сообщений на узле-координаторе и на других узлах.

Узел-координатор собирает информацию по всем узлам, поэтому факт наличия повторяющейся информации и в остальных узлах (а также изучение сообщений с узла-координатора) может дополнить информацию по возникшей проблеме. Например, узел-координатор может содержать сообщения об успешном завершении PME. При формировании хронологии событий обращайте внимание на изменение топологии по следующим строкам — `Added new node to topology`, `Node left topology`, `Topology snapshot` — анализируйте, какие изменения происходят с серверными и клиентскими узлами по отдельности.

Возможно, будет необходимо дополнительно собрать логи с клиентского узла.

## Основные события в логах DataGrid

-   Вход нового узла в топологию:

    ```text
    YYYY-MM-DD 17:43:43.595 [INFO ][disco-event-worker-#56][org.apache.ignite.internal.managers.discovery.GridDiscoveryManager] Added new node to topology: TcpDiscoveryNode [id=2d2103cb-c6d0-46ee-ad44-9a4010da765d, consistentId=xx.xx.xxx.xxx,xxx.x.x.x:47500, addrs=ArrayList [xx.xx.xxx.xxx, xxx.x.x.x], sockAddrs=HashSet [<hostname>, /xxx.x.x.x:47500], discPort=47500, order=2, intOrder=2, lastExchangeTime=1601995423434, loc=false, ver=2.8.1#20200914-sha1:602ccc45, isClient=false]
    ```

-   Выход узла из топологии:

    ```text
    YYYY-MM-DD 11:58:38.589 [INFO ][disco-event-worker-#245][org.apache.ignite.internal.managers.discovery.GridDiscoveryManager] Node left topology: TcpDiscoveryNode [id=ea0d97c0-1ae7-4b65-811a-17d0384de6f7, consistentId=<hostname>, addrs=ArrayList [<hostname>, xxx.x.x.x], sockAddrs=HashSet [/xxx.x.x.x:47500, grid2151/<hostname>:47500], discPort=47500, order=1, intOrder=1, lastExchangeTime=1666327737233, loc=false, ver=2.13.0#20220815-sha1:efa5ba4e, isClient=false]
    ```

-   Снепшот топологии:

    ```text
    [13:39:58,266][INFO][disco-event-worker-#78][GridDiscoveryManager] Topology snapshot [ver=3, locNode=5236a343, servers=1, clients=0, state=INACTIVE, CPUs=12, offheap=3.2GB, heap=4.0GB, aliveNodes=[TcpDiscoveryNode [id=5236a343-1072-4351-bfb5-8acf32452492, consistentId=67625aad-3b87-4bf0-9ba4-89b9800fe0fb, isClient=false, ver=2.15.0#20221201-sha1:27ef026b]]]
    ```

-   Активация кластера:

    ```text
    YYYY-MM-DD 11:23:37.269 [INFO ][disco-notifier-worker-#238][org.apache.ignite.internal.processors.cluster.GridClusterStateProcessor] Cluster state was changed from INACTIVE to ACTIVE
    ```

-   Деактивация кластера:

    ```text
    YYYY-MM-DD 11:23:37.269 [INFO ][disco-notifier-worker-#238][org.apache.ignite.internal.processors.cluster.GridClusterStateProcessor] Cluster state was changed from ACTIVE TO INACTIVE
    ```

-   PME:

    -   PME начался:

        ```text
        YYYY-MM-DD 11:51:31.921 [INFO ][exchange-worker-#245][org.apache.ignite.internal.exchange.time] Started exchange init [topVer=AffinityTopologyVersion [topVer=40, minorTopVer=3], crd=false, evt=DISCOVERY_CUSTOM_EVT, evtNode=e09def93-780c-4e9b-ae25-48c1e63ef8d3, customEvt=ChangeGlobalStateMessage [id=7ed05e8f381-e3b71132-ffa1-4ca0-af58-330a33d1e20c, reqId=12745afb-dc55-45de-9807-6bd81e9b8333, initiatingNodeId=e09def93-780c-4e9b-ae25-48c1e63ef8d3, state=INACTIVE, baselineTopology=null, forceChangeBaselineTopology=false, timestamp=1666342291899, forceDeactivation=false], allowMerge=false, exchangeFreeSwitch=false]
        ```

    -   Не дождался PME:

        ```text
        YYYY-MM-DD 11:51:42.162 [WARN ][exchange-worker-#242][org.apache.ignite.internal.diagnostic] Failed to wait for partition map exchange [topVer=AffinityTopologyVersion [topVer=40, minorTopVer=3], node=ea0d97c0-1ae7-4b65-811a-17d0384de6f7]. Dumping pending objects that might be the cause:
        ```

        :::{admonition} Примечание
        :class: note

        Возможные причины: зависшие блокировки, незавершенные транзакции, выпадение узла и, как результат, долгое ожидание кластера перед удалением узла из топологии.
        :::

    -   PME закончился:

        ```text
        YYYY-MM-DD 11:56:18.202 [INFO ][sys-#2211][org.apache.ignite.internal.processors.cache.distributed.dht.preloader.GridDhtPartitionsExchangeFuture] Exchange longest local stages [startVer=AffinityTopologyVersion [topVer=40, minorTopVer=3], resVer=AffinityTopologyVersion [topVer=40, minorTopVer=3]]
        ```

-   Ребалансировка:

    -   Процедура ребалансировки началась:

        ```text
        YYYY-MM-DD 19:58:07.049 [INFO ][sys-#64][org.apache.ignite.internal.processors.cache.distributed.dht.preloader.GridDhtPartitionDemander] Starting rebalance routine [ignite-sys-cache, topVer=AffinityTopologyVersion [topVer=5, minorTopVer=0], supplier=0aa67196-7cd2-4121-ad59-86a125c791db, fullPartitions=[0-99], histPartitions=[]]
        ```

    -   Процедура ребалансировки закончилась:

        ```text
        YYYY-MM-DD 19:58:07.074 [INFO ][rebalance-#69][org.apache.ignite.internal.processors.cache.distributed.dht.preloader.GridDhtPartitionDemander] Completed rebalance future: RebalanceFuture [grp=CacheGroupContext [grp=ignite-sys-cache], topVer=AffinityTopologyVersion [topVer=5, minorTopVer=0], rebalanceId=1, routines=1, receivedBytes=1200, receivedKeys=0, partitionsLeft=0, startTime=1602176287046, endTime=-1, lastCancelledTime=-1]
        ```

-   LRT:

    ```text
    YYYY-MM-DD 03:18:48.650 [WARN ]sys-#665674[org.apache.ignite.internal.diagnostic] First 10 long running transactions [total=20]
    ```

-   Сегментирование узлов:

    ```text
    YYYY-MM-DD 03:18:40.869 [WARN ]disco-event-worker-#244[org.apache.ignite.internal.managers.discovery.GridDiscoveryManager] Local node SEGMENTED: TcpDiscoveryNode [id=072e1f27-d2c3-4efb-bfbc-eeae108a4a48, consistentId=<hostmane>, addrs=ArrayList [xx.xx.xxx.x, xxx.x.x.x], sockAddrs=HashSet [/xxx.x.x.x:47500, <hostname>], discPort=47500, order=20, intOrder=20, lastExchangeTime=1666311510321, loc=true, ver=2.13.0#20220815-sha1:efa5ba4e, isClient=false]
    ```

-   Deadlock:

    ```text
    ...
    Deadlock detected:
    K1: TX1 holds lock, TX2 waits lock.
    K2: TX2 holds lock, TX1 waits lock.
    Transactions:
    TX1 [txId=GridCacheVersion [topVer=245981357, order=1637828217886, nodeOrder=418], nodeId=1d0a56c0-cc47-4369-b9c5-c5fe1fffe7bf, threadId=1176]
    TX2 [txId=GridCacheVersion [topVer=245981357, order=1637828217919, nodeOrder=410], nodeId=68ca22f4-38be-4027-8c81-94b0ea81559e, threadId=12957]
    Keys:
    K1 [key=d6oDXoRGCvEAAAF8x+CxoMaIDaIpVm6K, cache=tw.transactions_bundle]
    K2 [key=d6oDXoRGCvEAAAF8x+CxoMaIDaIpVm6K, cache=tw.transactions]
        at org.apache.ignite.internal.processors.cache.distributed.dht.colocated.GridDhtColocatedLockFuture$LockTimeoutObject$1.apply(GridDhtColocatedLockFuture.java:1539)
        at org.apache.ignite.internal.processors.cache.distributed.dht.colocated.GridDhtColocatedLockFuture$LockTimeoutObject$1.apply(GridDhtColocatedLockFuture.java:1532)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.notifyListener(GridFutureAdapter.java:399)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.unblock(GridFutureAdapter.java:347)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.unblockAll(GridFutureAdapter.java:335)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.onDone(GridFutureAdapter.java:511)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.onDone(GridFutureAdapter.java:490)
        at org.apache.ignite.internal.processors.cache.transactions.TxDeadlockDetection$TxDeadlockFuture.onDone(TxDeadlockDetection.java:538)
        at org.apache.ignite.internal.processors.cache.transactions.TxDeadlockDetection$TxDeadlockFuture.onDone(TxDeadlockDetection.java:163)
        at org.apache.ignite.internal.util.future.GridFutureAdapter.onDone(GridFutureAdapter.java:467)
        at org.apache.ignite.internal.processors.cache.transactions.TxDeadlockDetection$TxDeadlockFuture.detect(TxDeadlockDetection.java:314)
        at org.apache.ignite.internal.processors.cache.transactions.TxDeadlockDetection$TxDeadlockFuture.onResult(TxDeadlockDetection.java:514)
        at org.apache.ignite.internal.processors.cache.transactions.IgniteTxManager$DeadlockDetectionListener.onMessage(IgniteTxManager.java:3593)
        at org.apache.ignite.internal.managers.communication.GridIoManager.invokeListener(GridIoManager.java:1908)
        at org.apache.ignite.internal.managers.communication.GridIoManager.processRegularMessage0(GridIoManager.java:1529)
        at org.apache.ignite.internal.managers.communication.GridIoManager.access$5300(GridIoManager.java:242)
        at org.apache.ignite.internal.managers.communication.GridIoManager$9.execute(GridIoManager.java:1422)
        at org.apache.ignite.internal.managers.communication.TraceRunnable.run(TraceRunnable.java:55)
        at org.apache.ignite.internal.util.StripedExecutor$Stripe.body(StripedExecutor.java:569)
        at org.apache.ignite.internal.util.worker.GridWorker.run(GridWorker.java:120)
        ... 1 more
    ```

-   Найдены потерянные партиции:

    ```text
    YYYY-MM-DD 15:55:42.284 - 15:55:52.662 [WARN ][exchange-worker-#388][org.apache.ignite.internal.processors.cache.distributed.dht.topology.GridDhtPartitionTopologyImpl] Detected lost partitions
    ```

-   `idle_verify` вывод в `control-utility.log`:

    ```text
    Control utility [ver. 2.13.0-p4#20220815-sha1:efa5ba4e]
    2022 Copyright(C) Apache Software Foundation
    Time: YYYY-MM-DDT11:30:59.948
    Command [CACHE] finished with code: 0
    Control utility has completed execution at: YYYY-MM-DDT11:40:25.869
    Execution time: 565921 ms
    ```

    Результат выполнения `idle_verify` можно проверить по числу в строке `command [CACHE] finished with code`:

    -   0: `idle_verify` команда завершилась без ошибок;
    -   1: `idle_verify` неверные аргументы;
    -   2: `idle_verify` ошибка соединения;
    -   3: `idle_verify` ошибка аутентификации;
    -   4: `idle_verify` неизвестная ошибка.

    Информацию по выполнению команды `--cache idle_verify` можно найти в логе `control-utility.log` и файле `idle_verify-[дата].txt`, которые находятся в каталоге `${IGNITE_HOME}/work/log`.

    Полный путь будет указан в результатах вывода запроса в командной строке `./bin/control.sh --cache idle_verify`, например:

    ```text
    See log for additional information. /.../work/log/idle_verify-YYYY-MM-DDT12-58-22_547.txt
    ```

**Примеры использования grep, less, find, sed, tee:**

-   `grep` — команда в терминале Linux, используемая для поиска строк, соответствующих строке в тексте или содержимому файлов. Команда находит строки по шаблону или по регулярным выражениям.
-   `less` — утилита командной строки в Linux, отображающая содержимое файла или вывод команды по одной странице за раз. Утилита выводит данные на отдельной странице терминала, что облегчает чтение.
-   `find` — команда в Linux по поиску файлов и каталогов на основе специальных условий, например, для поиска файлов по разрешениям, владельцам, группам, типу, размеру и прочим критериям.
-   `sed` — утилита или потоковый редактор текста, работающий по принципу замены. С помощью sed можно редактировать файлы, не открывая их.
-   `tee` — утилита в Linux, используется для записи вывода любой команды в один или несколько файлов.

Все указанные утилиты можно использовать в одной составной команде.

Часто используемые аргументы команды `grep`:

-   `-i` — игнорировать регистр при поиске;
-   `-w` — найти полное совпадение вместо частичного;
-   `-с` — найти количество успешных совпадений вместо фактического совпадения со строкой;
-   `-r` — поиск не только в текущем каталоге, но и в подкаталогах;
-   `-v` — найти что-то, не соответствующее заданному шаблону — инверсивный поиск;
-   `-n` — напечатать номера найденных строк, чтобы узнать их позицию в файле;
-   `-m[num]` — вывести фиксированное количество строк;
-   `-I` — напечатать только имена файлов, в которых найден шаблон;
-   `-x` — напечатать только строки, точно соответствующие заданному шаблону, а не какой-то его части;
-   `"^[string]"` — вывести только строки, которые начинаются со String — совпадение по началу строки;
-   `"[string]$"` — вывести только строки, которые заканчиваются String — совпадение по концу строки;
-   `-f` — найти строки, соответствующие данным из файла шаблонов, содержащие перечень часто используемых шаблонов (по одному шаблону на строку);
-   `-e` — найти строки, соответствующие хотя бы одному шаблону из перечня;
-   `-R` — рекурсивно прочитать файлы внутри директории, аргумент следует всем символическим ссылкам, в отличие от `-r`.
-   `-H` — напечатать названия файла для каждого совпадения. Это значение по умолчанию, когда нужно искать более одного файла.

:::{admonition} Внимание
:class: danger

Значения ключей могут отличаться от приведенного в документации. Проверяйте актуальные значения ключей в документации на утилиту `grep`.
:::

## Логи messages, dmesg

Команды для работы с messages, dmesg:

-   получить список уникальных сообщений в директории логов messages:

    ```bash
    grep -R * . | cut -d ' ' -f 6-12 | sort -u
    ```

-   исключить ненужные сообщения из директории логов messages:

    ```bash
    grep -RvE 'systemd: Started Session|systemd-logind: Removed session|systemd-logind: New session|systemd: Removed slice User Slice of wfadmin|systemd: Created slice User Slice of wfadmin|systemd: Removed slice User|systemd: Created slice User|rsyslogd: imjournal: journal reloaded|journal: Suppressed|python: ansible-ansible.legacy.command|python: ansible-command Invoked with|python: ansible' . | cut -d ' ' -f 6-12
    ```

## Логи DataGrid

Команды для работы с логами DataGrid:

-  Получить список уникальных сообщений с `ERROR`:

    ```bash
    grep "\[ERROR\]" ~/.../ignite.log | cut -d ' ' -f 3-8 | sort -u
    ```

    где:

    - `cut -d ' ' -f 3-8` — команда `cut` вырезает часть текста;
    - `-d` — устанавливает разделитель вместо стандартного TAB в `''`;
    - `-f` указывает перечень полей для вырезания текста с учетом разделителя;
    - `sort -u` — составляет уникальный сортированный список на основании команды, выполненной до нее.

    :::{admonition} Пример
    :class: hint

    ```bash
    grep -E 'ERROR|WARN' ~/.../ignite.log | cut -d ' ' -f 3-8 | sort -u
    ```

    где:

    - поиск идет одновременно по *ERROR* и *WARN*;
    - текст вывода обрезан и отсортирован по уникальности сообщений.
    :::

-   Исключить ненужные сообщения:

    ```bash
    grep -E "\[WARN \]|\["ERROR\]"" ~/.../ignite.log | grep -vE "Authentication failed|Inline sizes on local nod|Received discovery data for unknown plugin" | cut -d ' ' -f 3-20 | sort -u
    ```

    где:

    -   `-E` — передает команде в качестве шаблона расширенное регулярное выражение, что равноценно использованию `egrep`;
    -   `-v` — осуществляет инверсивный поиск — находит то, что не соответствует заданному шаблону.

-   Убрать уникальность и ограничение по выводу, смотреть полные сообщения:

    ```bash
    grep -E "\[WARN \]|\["ERROR\]"" ~/.../ignite.log | grep -vE "Authentication failed|Inline sizes on local nod|Received discovery data for unknown plugin"
    ```

-   Оставить транзакции, которые не в `state=ACTIVE`, так как у некоторых из них превышен timeout:

    ```bash
    grep -E "\[WARN \]|\["ERROR\]"" ~/.../ignite.log | grep "state=" | grep -v "state=ACTIVE"
    ```

-   Найти сообщения об узле `<node-name>`:

    ```bash
    grep <node-name> ~/.../ignite.log
    ```

    где `<node-name>` — имя узла.

-   Исключить сообщения о транзакции из сообщений об узле `<node-name>`:

    ```bash
    grep <node-name> ~/.../ignite.log | grep -v ">>> Transaction"
    ```

    где `<node-name`> — имя узла.

-   Включить временное ограничение по выводу:

    ```bash
    grep 'YYYY-MM-DD 16:0[0-4]' ~/.../ignite.log | less
    ```

    Будет выведена информация за YYYY-MM-DD с 16:00:00 по 16:04:00.

-   Выполнить множественный поиск в log-файле с временным ограничением:

    ```bash
    grep 'YYYY-MM-DD 03:1[5-9]' ~/.../ignite.log | grep 'ERROR' | cut -d ' ' -f 3-8 | sort -u | less
    ```

    В less будет выведен сокращенный уникальный список ERROR за период с YYYY-MM-DD 03:15 - 03:19.

-   Включить дополнительные строчки ниже или выше для понимания контекста:

    ```bash
    grep -С[num] <node-name> ~/.../ignite.log | grep -v ">>> Transaction"
    ```

    где `<node-name>` — имя узла.

    Опции включаются через `-A`, `-B`, `-С`, где:

    -   `-A[num]` — включение строки ниже, или `--after-context`;
    -   `-B[num]` — включение строки выше, или `--before-context`;
    -   `-C[num]` — включить обе строки (ниже и выше), или `--context`;
    -   `[num]` — отвечает за количество строк, включаемых в контекст к основному выводу.

-   Выполнить поиск не в конкретном файле, а внутри директории, включая все поддиректории:

    ```bash
    grep -RIi "Failed to update partition counter" . | less
    ```

    где:

    -   `-R` — отвечает за поиск нужной информации внутри директории вместо конкретного файла, что может быть полезно при анализе данных со многих узлов одновременно. Следует указать путь до директории, а не конкретного файла;
    -   `-I` — печатает только имена файлов, в которых найден шаблон;
    -   `-i` — игнорирует регистр при поиске.

    В результате команда переведет вывод на отдельную страницу терминала less и выведет список названий файлов и информацию по ошибке *"Failed to update partition counter"*.

-   Выполнить поиск файлов по имени в текущей папке:

    ```bash
    find . -name '*.log' -exec grep -IHi "Failed to update partition counter" {} \; | less
    ```

    где:

    - `-H` печатает имя файла для каждого совпадения, когда нужно искать больше одного файла;
    - Параметр `-exec` работает в связке с программой find, отвечающей за поиск файлов по имени через `-name`. Правила синтаксиса для find подразумевают окончание команды через `{} \;`.

-   Выполнить поиск нужной информации в текущей папке с указанием временного ограничения и переводом вывода в файл в формате `csv`:

    ```bash
    find . -name '*.log' -exec grep -IHi "Failed to update partition counter" {} \; | sed -En 's/^\.\/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).+(YYYY-MM-DD [0-9]+:[0-9]+:[0-9]+.[0-9]+).+grpName=(.+), partId=([0-9]+).+$/\1;\2;\3;\4/p' | tee ../failed_to_update_partition_counter.csv
    ```

    Команда состоит из трех частей, разделенных знаком `|`:

    -   Найти строки в log-файлах директории:

        ```bash
        find . -name '*.log' -exec grep -IHi "Failed to update partition counter" {} \;
        ```

        :::{admonition} Примечание
        :class: note

        Описание команды — смотри описание команды «Выполнить поиск файлов по имени в текущей папке» выше.
        :::

    -   Отредактировать поток данных через регулярные выражения:

        ```bash
        sed -En 's/^\.\/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).+(YYYY-MM-DD [0-9]+:[0-9]+:[0-9]+.[0-9]+).+grpName=(.+), partId=([0-9]+).+$/\1;\2;\3;\4/p'
        ```

        :::{admonition} Пример
        :class: hint 
        :collapsible:

        **Входящий поток данных:**

        ```
        ./IP-address.ignite.log:YYYY-MM-DD 15:37:52.811 [ERROR][sys-#371][org.apache.ignite.internal.processors.cache.persistence.GridCacheOffheapManager] Failed to update partition counter. Most probably a node with most actual data is out of topology or data streamer is used in preload mode (allowOverride=false) concurrently with cache transactions [grpName=TmGr3, partId=6313]
        ```

        **Вывод команды `sed`:**

        ```
        IP-address;YYYY-MM-DD 15:37:52.862;TmGr3;15559
        ```

        **Анализ регулярного выражения:**

        -   Выражение представлено в формате: `'s/образец/замена/'`;
        -   Образец: `^\.\/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).+(YYYY-MM-DD [0-9]+:[0-9]+:[0-9]+.[0-9]+).+grpName=(.+), partId=([0-9]+).+$;`
        -   Замена: `\1;\2;\3;\4`

        **Образец:**

        -   `^` — символ начала строки;
        -   `.\` — равен `.`;
        -   `\/` — равен `/`;
        -   группа №1: `([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)`;
        -   `.+` — связь между группами;
        -   группа №2: `(YYYY-MM-DD [0-9]+:[0-9]+:[0-9]+.[0-9]+)`;
        -   группа №3: `(.+)`;
        -   `, ` — деление между группами 3 и 4 в оригинальном тексте;
        -   группа №4: `([0-9]+)`;
        -   `$` — символ конца строки.

        **Замена:**

        -   числа 1–4 — отсылка к номерам групп;
        -   `;` — деление при выводе данных.
        :::

    -   Направить вывод в новый автоматически созданный файл:

        ```bash
        tee ../failed_to_update_partition_counter.csv
        ```

        Направляет вывод команды в новый автоматически созданный файл. `tee` принимает данные из `find` и `sed`, создает файл `failed_to_update_partition_counter.csv` и сохраняет в него полученную информацию.

### Логи при работе CDC

В разделе приведены примеры сообщений в log-файлах при работе CDC.

Типичные проблемы при работе CDC и их решения описаны в документе [«Часто встречающиеся проблемы и пути их устранения»](../../troubleshooting-and-performance/md/faq.md).

#### Записываемые логи

Сообщения сохраняются в следующие файлы:

-   `ignite.log` — для серверного узла;
-   `ignite-cdc.log` — для приложения `ignite-cdc.sh`;
-   `kafka-ignite-streamer.log` — для приложения `kafka-to-ignite.sh`.

Кроме того, стандартный вывод и вывод ошибок могут дополнительно переводится в соответствующие `.out` и `.err` файлы (зависит от используемых скриптов).

Далее приведены примеры сообщений, которые записываются в log-файл при определенных условиях.

#### Серверный узел

##### Старт узла

1. Вывод конфигурации регионов данных с включенным CDC.

   :::{admonition} Пример сообщения
   :class: hint

   ```text
   YYYY-MM-DDT18:56:22,418 [INFO ][main][IgniteKernal%cluster_node] IgniteConfiguration
   ...
   DataRegionConfiguration [name=default,
   ...
   cdcEnabled=true]
   ```
   :::

2. Вывод информации о старте плагина.

   :::{admonition} Пример сообщения
   :class: hint

   ```text
   YYYY-MM-DDT17:03:51,124 [INFO ][main][IgnitePluginProcessor]   ^-- Cache version conflict resolver [clusterId=2, conflictResolveField=modificationDate, caches=[PersonCache]] 1.0.0-SNAPSHOT
   YYYY-MM-DDT17:03:51,124 [INFO ][main][IgnitePluginProcessor]   ^-- Apache Software Foundation
   ```
   :::

3. Вывод информации о длительности запуска плагина.

   :::{admonition} Пример сообщения
   :class: hint

   ```text
   YYYY-MM-DDT16:04:36,540 [INFO ][main][G] Node started :
   ...
   stage="Start 'Cache version conflict resolver [clusterId=1, conflictResolveField=modificationDate, caches=[PersonCache]]' plugin" (0 ms),
   ...
   ```
   :::

##### Старт кешей с ConflictResolver

При старте кешей (в том числе во время старта узлов) с настроенным ConflictResolver выводятся сообщения:

```text
YYYY-MM-DDT16:05:53,811 [INFO ][exchange-worker-#77%cluster_node%][CacheVersionConflictResolverPluginProvider] ConflictResolver provider set for cache [cacheName=PersonCache]
YYYY-MM-DDT16:05:53,817 [INFO ][exchange-worker-#77%cluster_node%][CacheConflictResolutionManagerImpl] <PersonCache> Conflict resolver created [rslvr=CacheVersionConflictResolverImpl [clusterId=1, conflictResolveField=modificationDate, conflictResolveFieldEnabled=true]]
```

Для кешей, которые ConflictResolver не обрабатывает:

```text
YYYY-MM-DDT14:57:03,894 [INFO ][main][CacheVersionConflictResolverPluginProvider] Skip ConflictResolver provider for cache [cacheName=ignite-sys-cache]
```

##### Ротация WAL

Ротация при наличии меняющей данные нагрузки должна происходить с интервалом, близким к walForceArchiveTimeout. При этом выводятся сообщения, указывающие номер старого и нового сегмента:

```text
YYYY-MM-DDT16:11:37,036 [INFO ][grid-timeout-worker-#30%cluster_node%][FileWriteAheadLogManager] Rollover segment [18 to 19], recordType=null
YYYY-MM-DDT16:11:47,044 [INFO ][grid-timeout-worker-#30%cluster_node%][FileWriteAheadLogManager] Rollover segment [19 to 20], recordType=null
```

##### Сообщения ConfilctResovler

:::{admonition} Примечание
:class: note

Ошибки разрешения конфликтов рассмотрены в документе [«Часто встречающиеся проблемы и пути их устранения»](../../troubleshooting-and-performance/md/faq.md).
:::

При любых изменениях в кешах, для которых настроен ConflictResolver, на уровне `DEBUG` выводятся сообщения о применении или отказе в применении изменений.

Список полей в сообщении:

-   `start` — `true`, если происходит вставка с новым (отсутствующим в кеше) ключом;
-   `oldVer` — внутренняя версия текущей записи в кластере, содержит поля:

    -   `dataCenterId` — соответствует значению `clusterId` из конфигурации ConflictResolver того кластера, в котором была выполнена вставка записи данной версии;
    -   `nodeOrder`— порядковый номер узла в кольце Discovery. Соответствует значению `order` из вывода команды `--baseline`;

-   `newVer` — внутренняя версия новой записи; содержит те же поля, что и `oldVer`.
-   `old` — значение conflictResolvableField для старой версии записи;
-   `new` — значение conflictResolvableField для новой версии записи;
-   `res` — результат разрешения конфликта:

    -   `res=true` для успешного применения новой версии;
    -   `res=false` если значение не применено.

:::{admonition} Пример сообщения при успешном применении изменений
:class: hint

```text
YYYY-MM-DDT21:14:24,500 [DEBUG][sys-stripe-9-#10%cluster_node%][CacheVersionConflictResolverImpl] <PersonCache> isUseNew[start=false, oldVer=GridCacheVersion [topVer=300146712, order=1688666709873, nodeOrder=1, dataCenterId=1], newVer=GridCacheVersion [topVer=300146712, order=1688666709875, nodeOrder=1, dataCenterId=1], old=YYYY-MM-DD 21:14:03.528, new=YYYY-MM-DD 21:14:23.464, res=true]
```
:::

В примере выше `dataCenterId` одинаковый. Такое может быть как на удаленном кластере, так и на локальном, так как любое изменение кешей, обрабатываемых ConflictResolver, проверяется на конфликтность.

:::{admonition} Пример сообщения при отказе применения изменений
:class: hint

```text
YYYY-MM-DDT21:19:04,494 [DEBUG][sys-stripe-11-#12%cluster_node%][CacheVersionConflictResolverImpl] <PersonCache> isUseNew[start=false, oldVer=GridCacheVersion [topVer=300146718, order=1688666742208, nodeOrder=1, dataCenterId=2], newVer=GridCacheVersion [topVer=300146712, order=1688666709877, nodeOrder=1, dataCenterId=1], old=YYYY-MM-DD 21:18:56.494, new=YYYY-MM-DD 21:18:53.797, res=false]
```
:::

#### Приложение ignite-cdc.sh

Приложение `ignite-cdc.sh` запускает CdcConsumer, который читает журнал репликации, то есть последовательно обрабатывает WAL-сегменты. В зависимости от типа и настроек будут запускаться следующие CdcConsumer:

-   прямая репликация DataGrid + клиентский узел: `IgniteToIgniteCdcStreamer`;
-   прямая репликация DataGrid + тонкий клиент: `IgniteToIgniteClientCdcStreamer`;
-   репликация через Kafka: `IgniteToKafkaCdcStreamer`.

##### Старт

1.  Вывод информации о директориях, используемых в работе `ignite-cdc.sh`.

    Директории, используемые в работе `ignite-cdc.sh`, должны совпадать с серверными директориями.

    :::{admonition} Пример сообщения
    :class: hint

    ```text
    YYYY-MM-DDT16:29:37,491 [INFO ][Thread-1][] Change Data Capture [dir=/ignite/db/wal/cdc/cluster_node]
    YYYY-MM-DDT16:29:37,492 [INFO ][Thread-1][] Ignite node Binary meta [dir=/ignite/db/binary_meta/cluster_node]
    YYYY-MM-DDT16:29:37,492 [INFO ][Thread-1][] Ignite node Marshaller [dir=/ignite/db/marshaller]
    YYYY-MM-DDT16:29:37,551 [INFO ][Thread-1][] Resolved directory for serialized binary metadata: /ignite/db/binary_meta/cluster_node
    ```
    :::

2.  Вывод информации о загруженном состоянии. В сообщении выводятся указатель WAL, состояние обработки типов и кешей.

    :::{admonition} Пример сообщения
    :class: hint

    ```text
    YYYY-MM-DDT16:29:37,632 [INFO ][Thread-1][CdcConsumerState] Initial WAL state loaded [ptr=WALPointer [idx=19, fileOff=1501, len=0], idx=0]
    YYYY-MM-DDT16:29:37,637 [INFO ][Thread-1][CdcConsumerState] Initial types state loaded [typesCnt=2]
    YYYY-MM-DDT16:29:37,640 [INFO ][Thread-1][CdcConsumerState] Initial mappings state loaded [mappingsCnt=2]
    YYYY-MM-DDT16:29:37,641 [INFO ][Thread-1][CdcConsumerState] Initial caches state loaded [cachesCnt=1]
    ```
    :::

3.  Вывод типа CdcConsumer.

    После загрузки состояния выводится тип CdcConsumer и его основные параметры конфигурации:

    -   прямая репликация DataGrid + клиентский узел:

        ```text
        YYYY-MM-DDT16:29:37,642 [INFO ][Thread-1][IgniteToIgniteClientCdcStreamer] Ignite To Ignite Client Streamer [cacheIds=[1215863053]]
        ```

    -   прямая репликация DataGrid + клиентский узел:

        ```text
        YYYY-MM-DDT16:59:49,594 [INFO ][Thread-1][IgniteToIgniteCdcStreamer] Ignite To Ignite Streamer [cacheIds=[1215863053]]
        ```

    -   репликация через Kafka:

        ```text
        YYYY-MM-DDT22:20:17,001 [INFO ][Thread-1][IgniteToKafkaCdcStreamer] CDC Ignite To Kafka started [topic=dc1_to_dc2, metadataTopic = metadata_from_dc1, onlyPrimary=false, cacheIds=[1215863053]]
        ```

##### Репликация типов (метаданные бинарного типа, маршалинг)

При вставке значений новых типов приложением `ignite-cdc.sh` будут реплицироваться зарегистрированные в кластере-источнике метаданные новых типов: `type / marshaller mapping` и `binary metadata`.

###### Репликация типов в CDC Ignite2Ignite

-   прямая репликация DataGrid + клиентский узел — регистрация `TypeMapping` в удаленном кластере:

    ```text
    YYYY-MM-DDT21:06:29,535 [INFO ][Thread-1][IgniteToIgniteCdcStreamer] Mapping [mapping=TypeMappingImpl [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, platform=JAVA]]
    ```

-   прямая репликация DataGrid + тонкий клиент — регистрация `BinaryMetadata` в удаленном кластере:

    ```text
    YYYY-MM-DDT16:28:35,419 [INFO ][Thread-1][IgniteToIgniteClientCdcStreamer] BinaryMeta [meta=BinaryMetadata [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, fields=LinkedHashMap {keyId=BinaryFieldMetadata [fieldId=101945274, typeId=3], stringId=BinaryFieldMetadata [fieldId=1795009772, typeId=9]}, affKeyFieldName=null, schemas=SingletonSet [BinarySchema [schemaId=-1145041288, idToOrderMask=0, id0=101945274, id1=1795009772, id2=0, id3=0, ids=[101945274, 1795009772], names=[null, null], idToOrderData=null]], isEnum=false]]
    ```

###### Репликация типов при репликации через Kafka/Corax

1.  Отправка `TypeMapping` в Kafka/Corax (уровень DEBUG):

    ```text
    YYYY-MM-DDT22:51:05,239 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=TypeMappingImpl [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, platform=JAVA]]
    ```

    Отправка `BinaryMetadata` в Kafka (уровень DEBUG):

    ```text
    YYYY-MM-DDT22:51:05,311 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=BinaryTypeImpl [meta=BinaryMetadata [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, fields=LinkedHashMap {keyId=BinaryFieldMetadata [fieldId=101945274, typeId=3], stringId=BinaryFieldMetadata [fieldId=1795009772, typeId=9]}, affKeyFieldName=null, schemas=SingletonSet [BinarySchema [schemaId=-1145041288, idToOrderMask=0, id0=101945274, id1=1795009772, id2=0, id3=0, ids=[101945274, 1795009772], names=[null, null], idToOrderData=null]], isEnum=false]]]
    ```

2.  После каждой обработки набора метаданных типов (`mappings` или `binary meta`) выводится общее количество обработанных событий (отправленных сообщений) с момента старта. Каждый тип отправляется в отдельном сообщении:

    ```text
    YYYY-MM-DDT22:51:05,272 [INFO ][Thread-1][IgniteToKafkaCdcStreamer] Items processed [count=10]
    ```

3.  После отправки метаданных типов (`mappings` или `binary meta`) отправляются служебные маркеры (нужны для синхронного обновления типов на удаленном кластере) и выводится общее число отправленных сообщений с момента старта. При каждом обнаружении нового набора метаданных типов отправляется маркер в каждую партицию топика событий (отдельное сообщение на каждый маркер). В примере ниже отправлено 16 маркеров, так как 16 партиций в топике событий CDC (уровни DEBUG + INFO):

    ```text
    YYYY-MM-DDT22:51:05,274 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=0]
    YYYY-MM-DDT22:51:05,276 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=1]
    ...
    YYYY-MM-DDT22:51:05,281 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=15]
    YYYY-MM-DDT22:51:05,286 [INFO ][Thread-1][IgniteToKafkaCdcStreamer] Items processed [count=16]
    YYYY-MM-DDT22:51:05,287 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Meta update markers sent.
    ```

##### Обработка WAL-сегментов

1.  Вывод обработанного WAL-сегмента и директории с метаданными:

    ```text
    YYYY-MM-DDT21:26:24,048 [INFO ][Thread-1][] Processing WAL segment [segment=/Users/17840611/Work/dev/workspace/works/dc-1/db/wal/cdc/ignite_2029_server/xxxxxxxxxxxxxxx.wal]
    YYYY-MM-DDT21:26:24,057 [INFO ][Thread-1][] Resolved directory for serialized binary metadata: /Users/17840611/Work/dev/workspace/works/dc-1/db/binary_meta/ignite_2029_server
    ```

2.  На уровне логирования DEBUG выводится описание каждого полученного события из WAL (описание полей CdcEvent приведено в разделе «Описание CDC API» инструкции по системному администрированию):

    -   Прямая репликация DataGrid:

        ```text
        YYYY-MM-DDT21:26:24,061 [DEBUG][Thread-1][CdcEventsIgniteApplier] Event received [evt=CdcEventImpl [primary=true, part=83, ord=GridCacheVersion [topVer=300146712, order=1688666709881, nodeOrder=1, dataCenterId=1], cacheId=1215863053]]
        ```

    -   Репликация через Kafka/Corax:

        ```text
        YYYY-MM-DDT22:26:34,898 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Event received [evt=CdcEventImpl [primary=true, part=83, ord=GridCacheVersion [topVer=300150464, order=1688670462056, nodeOrder=1, dataCenterId=1], cacheId=1215863053]]
        ```

3.  На уровне логирования DEBUG на каждое изменение выводится сообщение об отправке в удаленный приемник (DataGrid или Kafka/Corax).

     При прямой репликации DataGrid события на удаленный кластер сразу же:

    -   Клиентский узел + put:

        ```text
        YYYY-MM-DDT21:26:24,061 [DEBUG][Thread-1][CdcEventsIgniteApplier] Applying put batch [cacheId=1215863053]
        ```

    -   Тонкий клиент + remove:

        ```text
        YYYY-MM-DDT21:45:34,972 [DEBUG][Thread-1][CdcEventsIgniteClientApplier] Applying remove batch [cacheId=1215863053]
        ```

    CDC through Kafka сообщает об отправке сообщения в Kafka:

    ```text
    YYYY-MM-DDT22:26:34,898 [DEBUG][Thread-1][IgniteToKafkaCdcStreamer] Sent asynchronously [item=CdcEventImpl [primary=true, part=83, ord=GridCacheVersion [topVer=300150464, order=1688670462056, nodeOrder=1, dataCenterId=1], cacheId=1215863053]]
    ```

4.  Отметка о числе обработанных событий с момента старта `ignite-cdc.sh` происходит после полной обработки WAL-сегментов, то есть когда CdcConsmuer доходит до конца журнала:

    -   прямая репликация DataGrid + клиентский узел:

        ```text
        YYYY-MM-DDT21:26:24,065 [INFO ][Thread-1][IgniteToIgniteCdcStreamer] Events applied [evtsApplied=21]
        ```

    -   прямая репликация DataGrid + тонкий клиент:

        ```text
        YYYY-MM-DDT21:38:34,550 [INFO ][Thread-1][IgniteToIgniteClientCdcStreamer] Events applied [evtsApplied=2]
        ```

    -   репликация через Kafka (уровень DEBUG):

        ```text
        YYYY-MM-DDT22:33:45,374 [INFO ][Thread-1][IgniteToKafkaCdcStreamer] Items processed [count=7]
        ```

#### Приложение kafka-to-ignite.sh

Приложение запускается на удаленном кластере только в случае использования репликации через Kafka. Для вставок в кластер-приемник используется клиентский узел либо тонкий клиент.

##### Старт

1.  Вывод информации о версии, названии топика событий и диапазоне партиций (пример сообщения):

    ```text
    >>> ver. 14.1.0#20221216-sha1:a01793d7
    >>> 2022 Copyright(C) Apache Software Foundation
    >>>
    >>> Ignite documentation: http://ignite.apache.org
    >>> Kafka topic: dc1_to_dc2
    >>> Kafka partitions: 0-16
    ```

2.  `KafkaConsumer` в составе приложения производят постоянный опрос топика событий, который говорит об успешной работе `kafka-to-ignite.sh`. Опрос может производиться в несколько потоков с интервалом `kafkaRequestTimeout`. При этом каждая запись содержит вычитанное при текущем запросе число событий и общее число вычитанных событий со времени старта `kafka-to-ignite.sh`:

    ```text
    YYYY-MM-DDT22:51:13,463 [INFO ][applier-thread-3][KafkaToIgniteCdcStreamerApplier] Polled from consumer [assignments=[dc1_to_dc2-12], cnt=22, rcvdEvts=1025]
    YYYY-MM-DDT22:51:15,465 [INFO ][applier-thread-2][KafkaToIgniteCdcStreamerApplier] Polled from consumer [assignments=[dc1_to_dc2-8], cnt=7, rcvdEvts=1032]
    ```

##### Регистрация типов в кластере-приемнике

При получении служебного маркера из топика событий производится чтение из топика метаданных, в котором хранятся метаданные типов с кластера-источника.

При чтении из топика метаданных выводится общее количество сообщений, вычитанных из топика метаданных с момента старта `kafka-to-ignite.sh`.

1.  Чтение из топика метаданных:

    ```text
    YYYY-MM-DDT22:51:05,404 [INFO ][applier-thread-2][KafkaToIgniteMetadataUpdater] Polled from meta topic [rcvdEvts=4]
    ```

2.  Вычитан `TypeMapping`:

        ```text
        YYYY-MM-DDT22:51:05,423 [INFO ][applier-thread-2][KafkaToIgniteMetadataUpdater] Mapping [mapping=TypeMappingImpl [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, platform=JAVA]]
        ```

    Вычитан `BinaryMetadata`:

        ```text
        YYYY-MM-DDT22:51:05,445 [INFO ][applier-thread-2][KafkaToIgniteMetadataUpdater] BinaryMeta [meta=BinaryMetadata [typeId=-544320117, typeName=com.sbt.ignite.springframework.examples.model.PersonKey, fields=HashMap {stringId=BinaryFieldMetadata [fieldId=1795009772, typeId=9], keyId=BinaryFieldMetadata [fieldId=101945274, typeId=3]}, affKeyFieldName=null, schemas=ArrayList [BinarySchema [schemaId=-1145041288, idToOrderMask=0, id0=101945274, id1=1795009772, id2=0, id3=0, ids=[101945274, 1795009772], names=[null, null], idToOrderData=null]], isEnum=false]]
        ```

##### Применение событий CDC

1.  При получении событий на изменение или удаление выводятся соответствующие записи в логе (уровень DEBUG):

    ```text
    YYYY-MM-DDT22:48:15,527 [DEBUG][applier-thread-0][CdcEventsIgniteClientApplier] Event received [evt=CdcEventImpl [primary=true, part=83, ord=GridCacheVersion [topVer=300150464, order=1688670462072, nodeOrder=1, dataCenterId=1], cacheId=1215863053]]
    ```

2.  `Kafka2Ignite` + тонкий клиент — применение put (уровень DEBUG):

    ```text
    YYYY-MM-DDT22:48:15,528 [DEBUG][applier-thread-0][CdcEventsIgniteClientApplier] Applying put batch [cacheId=1215863053]
    ```

    `Kafka2Ignite` + клиентский узел — применение remove (уровень DEBUG):

    ```text
    YYYY-MM-DDT19:28:21,748 [DEBUG][applier-thread-3][CdcEventsIgniteApplier] Applying remove batch [cacheId=1215863053]
    ```