# Плагин для работы с кеш-дампами

:::{admonition} Внимание
:class: danger

Функциональность находится в статусе Alpha. Она может содержать ошибки, которые не обнаружили во время синтетического тестирования. В процессе эксплуатации могут возникать проблемы в работе. Эта версия может содержать не все запланированные функции и возможности. Разработчики могут добавлять новые функции или улучшать существующие в следующих релизах.
:::

## Введение

Кеш-дамп (далее — дамп) — консистентная копия данных кеша, которая записана в файлах на диске. Структура файла дампа — список. В файле друг за другом записаны каждая пара «ключ-значение» соответствующей партиции.

Чтобы защитить данные, при хранении для каждой пары «ключ-значение» вычисляется циклический избыточный код (CRC).

Дампы компактнее, чем полные снепшоты. Это связано с тем, что полные снепшоты сохраняют физическую структуру Page memory, поэтому сохраняются и все накладные расходы на организацию эффективного файлового хранилища.

Кроме данных, дамп содержит всю необходимую для обработки информацию:

-   данные кеша;
-   конфигурация кеша;
-   файлы метаданных бинарного типа (`binary metadata`);
-   файлы `marshaller`;
-   метаданные дампа.

Ключевые отличия дампа от полного снепшота:

-   дамп можно формировать для in-memory кешей;
-   в дампе не хранятся индексы;
-   размер дампа существенно меньше, чем PDS;
-   есть утилита и API для оффлайн-обработки сохраненных в дампе данных.

Совпадающие с полными снепшотами свойства дампов:

-   В начале снятия происходит PME.
-   Есть потеря производительности во время снятия.
-   Повышенный расход Java heap во время снятия.
-   Не нужно останавливать пользовательскую нагрузку. Дамп можно снимать одновременно с пользовательскими операциями.

## Работа с дампами

Функциональность дампов состоит из двух модулей:

-   Снятие дампа — выполняется на кластере DataGrid с помощью команды `control.sh --dump`. Для запуска команды снятия дампа нужны права `ADMIN_SNAPSHOT`.
-   Восстановление (чтение) дампа — выполняется с помощью утилиты `ignite-dump-reader.sh`. Утилита восстановления соединяется с кластером с помощью указанной в опциях конфигурации. Нужны права на создание кеша и вставку в него данных.

### Снятие и проверка дампа

Команды снятия и проверки дампа интегрированы в `control.sh`.

**Синтаксис команды снятия дампа:**

```bash
control.(sh|bat) --dump create --name name [--dest path] [--only-primary] [[--groups group1[,group2,....,groupN]]|[--in-memory-only]] [--compress]  [--encrypt]
```

**Опции:**

| Имя | Значение по умолчанию | Описание |
|---|---|---|
| `--name` | - | Имя дампа |
| `--dest` | `null` | Каталог для хранения дампа. Если не указан, дамп будет записан в каталог для хранения снепшотов |
| `--only-primary` | `false` | Создавать дамп только primary-партиций кеша |
| `--groups` | `null` | Имена кеш-групп, которые должны быть включены в дамп (через запятую) |
| `--in-memory-only` | `false` | Включить в дамп только in-memory кеши |
| `--compress` | `false` | Включить сжатие файлов дампа партиций в формате `zip` |
| `--encrypt` | `false` | Шифровать данные перед записью на диск |

:::{admonition} Ограничения
:class: hint

- Следует задавать только одну из опций — `--in-memory-only` или `--groups`.
- Если обе опции `--in-memory-only` и `--groups` заданы одновременно, возникнет ошибка.
- Если обе опции `--in-memory-only` и `--groups` не заданы, в дамп попадут все кеши, в том числе persistent-кеши.
:::

**Синтаксис команды проверки дампа:**

```bash
control.(sh|bat) --dump check --name name [--src path]
```

**Опции:**

| Имя | Значение по умолчанию | Описание |
|---|---|---|
| `--name` | - | Имя дампа |
| `--src path` | `null` | Каталог, где расположены файлы дампа. Если не указан, будет использован каталог хранения снепшотов по умолчанию |

#### Ограничение скорости при снятии дампа

Для ограничения скорости снятия дампа используйте свойство `snapshotTransferRate`, которое задает ограничение в байт/с.

Конфигурация и использование аналогичны ограничителю скорости при снятии снепшота. Подробнее — в подразделе «Работа со снепшотами» раздела [«Утилита control»](./control-sh.md).

### Восстановление дампа

Восстановление дампа производится с помощью `ignite-dump-reader.sh`.

**Опции:**

| Имя | Значение по умолчанию | Описание |
|---|---|---|
| `--dump` | - | Полный путь к директории с дампом |
| `--restore` | `false` | Флаг восстановления кешей. Если флаг указан, данные дампа будут вставлены в кластер |
| `--thin` | `null` | URL для соединения тонкого клиента с кластером |
| `--thin-config` | `null` | Путь к XML-файлу с конфигурационным файлом Spring. Ожидается наличие bean `ClientConfiguration`. Он будет использован для соединения тонкого клиента с кластером |
| `--client-node-config` | `null` | Путь к XML-файлу с конфигурационным файлом Spring. Ожидается наличие bean `IgniteConfiguration`. Он будет использован для соединения клиентского узла с кластером |
| `--no-cache-create` | `false` | Не создавать кеши |
| `--ignore-expire-time` | `false` | Игнорировать сохраненное в дампе значение `expireTime` |
| `--threads` | `1` | Количество потоков, которые обрабатывают дамп. Каждый поток одновременно обрабатывает `1` файл партиции. Увеличение числа потоков ускоряет обработку дампа |
| `--cache-group-names` | `null` | Имена кеш-групп из дампа, которые нужно обработать |
| `--skip-copies` | `false` | Если каталог с дампом содержит данные с нескольких узлов и значение опции — `true`, копии партиций будут пропущены. Каждая партиция будет обработана один раз. Включение опции ускоряет обработку дампа |
| `--batch-size` | `1` | Если больше `1`, для вставки данных будут использоваться операции `putAll` и batch соответствующего размера. Включение опции ускоряет обработку дампа.<br><br>Если `--batch-size` больше `1`, одновременный запуск нескольких экземпляров утилиты может вызывать взаимоблокировку (deadlock) |
| `--use-data-streamer` | `false` | Если установлено `true`, для вставки будет использован [IgniteDataStreamer](https://ignite.apache.org/docs/latest/data-streaming). Включение опции ускоряет обработку дампа |
| `--allow-overwrite` | `false` | [Флаг `IgniteDataStreamer`](https://ignite.apache.org/docs/latest/data-streaming#overwritting)  |
| `--per-node-buffer-size` | `null` |  Настройка `IgniteDataStreamer` |
| `--per-node-parallel-operations` | `null` | Настройка `IgniteDataStreamer` |
| `--per-thread-buffer-size` | `null` | Настройка `IgniteDataStreamer` |
| `--timeout` | `null` | Настройка `IgniteDataStreamer` |
| `--auto-flush-frequency` | `null` | Настройка `IgniteDataStreamer` |
| `--for-cdc` | `null` | Вставлять данные с использованием сохраненной версии и вызовов `putConflict`. Данный режим вставляет данные так же, как это делает `ignite-cdc.sh` во время репликации. Позволяет восстанавливать состояние репликации после сбоев без снятия нагрузки и остановки репликации |
| `--consumer` | `null` | Имя класса, который реализует интерфейс `DumpConsumer` |

#### Восстановления дампа на кластере с включенным плагином безопасности через толстого клиента

При запуске восстановления дампа на кластере с включенным плагином безопасности через толстого клиента нужно указать дополнительные JVM-опции для клиента:

-   `DIGNITE_CLUSTER_NAME`;
-   `DIGNITE_CLUSTER_TYPE`.

При использовании Cipher Suites `TLS_RSA_WITH_NULL_SHA256` для серверных узлов и толстых клиентов нужно дополнительно разрешить их использование в `java.security`. Если изменения невозможно внести локально, используйте собственный файл `java.security` с исправленными опциями через JVM-опцию  `-Djava.security.properties=/opt/ignite/server/config/java.security` с путем к каталогу, где хранится файл конфигурации.

Также нужно следить за размером heap: при больших объемах данных требуется большой размер heap. Например, при использовании синтетических данных потребовалось 16 Гб данных на дамп размером 140 Гб. Задается через JVM-опции `-Xmx16g -Xms16g`. Размер heap и настройку GC нужно подбирать исходя из испытаний на стендах для нагрузочного тестирования.

:::{admonition} Пример команды для экспорта JVM-опций
:class: hint

```bash
export CONTROL_JVM_OPTS="-DIGNITE_CLUSTER_NAME=ise -DIGNITE_CLUSTER_TYPE=dev -Djava.security.properties=/opt/ignite/server/config/java.security -Xmx16g -Xms16g"
```
:::

:::{admonition} Внимание
:class: danger

Кеши, которые создали через клиентские узлы (thick clients) или серверные узлы, должны восстанавливаться с использованием клиентского узла (`--client-node-config`). Восстановление через тонкий клиент возможно, но часть конфигурации кеша может быть утеряна.
:::

### Шифрование дампов

Для защиты конфиденциальных данных, которые содержатся в дампе, он может быть зашифрован стандартными средствами шифрования DataGrid — `EncryptionSPI`.

#### Снятие зашифрованного дампа

Порядок снятия зашифрованного дампа:

1. В начале снятия на каждом узле создается новый ключ шифрования — `EncryptionSPI#create()`.
2. С помощью этого ключа шифруется каждая пара «ключ-значение», которая записывается на диск.
3. Данные записываются на диск в зашифрованном виде. Незашифрованных данных на диске нет.
4. Ключ шифрования шифруется с помощью мастер-ключа — `EncryptionSPI#getMasterKeyName()` — и в зашифрованном виде сохраняется в метафайле дампа.
5. Цифровая подпись мастер-ключа `EncryptionSPI#masterKeyDigest()` сохраняется в метафайле дампа.

Чтобы создать зашифрованный дамп:

1. Настройте `EncryptionSPI` для серверных узлов (например через конфигурацию Spring XML).

   :::{code-block} xml
   :caption: XML
   <bean id="grid.cfg" class="org.apache.ignite.configuration.IgniteConfiguration">
   ...
       <property name="encryptionSpi">
           <bean class="org.apache.ignite.spi.encryption.keystore.KeystoreEncryptionSpi">
               <property name="keyStorePath" value="/path/to/key_storage.jks" />
               <property name="keyStorePassword" value="key_storage_password" />
           </bean>
       </property>
   ...
   </bean>
   :::

Проверка для зашифрованного дампа производится так же, как для незашифрованного, с помощью команды: 

```bash
control.(sh|bat) --dump check --name name [--src path]
```

2.  Создайте дамп с опцией `--encrypt`.

#### Восстановление зашифрованного дампа

Алгоритм восстановления зашифрованного дампа:

1. Проверяется соответствие мастер-ключа при чтении и снятии. Затем сравнивается подпись из метафайла дампа и то, что вернет `EncryptionSPI#masterKeyDigest()` при чтении. При несовпадении выдается ошибка.
2. Расшифровывается ключ шифрования, который сохранен в метафайле дампа — `EncryptionSPI#decryptKey`.
3. Расшифровывается каждая запись в памяти. Незашифрованные данные не записываются на диск и существуют только в памяти.
4. Внутри каждой записи хранится CRC (его значение хранится в зашифрованном виде). После расшифровки проверяется CRC открытых данных. При несовпадении выдается ошибка.

Чтобы восстановить зашифрованный дамп:

1. Настройте `EncryptionSPI` в конфигурационном файле.

    ::::{admonition} Пример конфигурации для тонкого клиента
    :class: hint 
    :collapsible:

    :::{code-block} xml
    :caption: XML
    <beans xmlns="http://www.springframework.org/schema/beans"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">
        <bean id="client.cfg" class="org.apache.ignite.configuration.ClientConfiguration">
            <property name="addresses">
                <list>
                    <value>localhost:10800</value>
                </list>
            </property>
        </bean>

        <bean id="encSpi" class="org.apache.ignite.spi.encryption.keystore.KeystoreEncryptionSpi">
            <property name="keyStorePath" value="/path/to/key_storage.jks" />
            <property name="keyStorePassword" value="key_storage_password" />
        </bean>
    </beans>
    :::
    ::::

2.  Восстановите дамп командой:
    
    ```bash
    ./bin/ignite-dump-reader.sh --dump <path-to-dump> --restore --thin-config <path-to-thin-client-config.xml>
    ```

    или

    ```bash
    ./bin/ignite-dump-reader.sh --dump <path-to-dump> --restore --client-node-config <path-to-client-node-config.xml>
    ```

    где

    - `path-to-thin-client-config.xml` — путь к файлу конфигурации тонкого клиента;
    - `path-to-client-node-config.xml` — путь к файлу конфигурации клиентского узла.

### Логирование

#### Логирование при снятии

Логирование при снятии дампов происходит аналогично логированию при снятии снепшотов.

#### Логирование при восстановлении

При работе утилиты восстановления дампов `ignite-dump-reader.sh` события записываются в отдельный log-файл. Путь к этому log-файлу выводится в терминале при запуске `ignite-dump-reader.sh`.

:::{admonition} Пример  вывода `ignite-dump-reader.sh`
:class: hint

```text
...
[18:27:25] Quiet mode.
[18:27:25]   ^— Logging to file '/opt/ignite/server/logs/dump-reader-85bcc08d.log'
[18:27:25]   ^— Logging by 'Log4J2Logger [quiet=true, config=null]'
[18:27:25]   ^— To see *FULL* console log here add -DIGNITE_QUIET=false or "-v" to ignite.{sh|bat}
...
```
:::

где `/opt/ignite/server/logs/dump-reader-85bcc08d.log` — путь к log-файлу утилиты восстановления дампов.

## Сценарий работы

Рекомендуемый сценарий работы с дампами:

1. По расписанию или перед работами администратор снимает дамп.

    :::{admonition} Примечание
    :class: note

    Целостность данных можно проверить с помощью утилиты `control` с опциями `--dump check`.
    :::

2. Данные дампа хранятся на каждом узле. Локально сохраняются партиции, которые расположены на узле в момент снятия дампа. 
3. Для уменьшения объема хранения и увеличения скорости восстановления используйте режим `--only-primary`.
4. Для восстановления после потери всех серверов кластера данные дампа нужно скопировать во внешнее хранилище.
5. Чтобы восстановить дамп, запустите утилиту восстановления на каждом узле, где хранятся данные дампа.

    :::{admonition} Примечание
    :class: note

    Утилита обрабатывает только локальные данные.
    :::

6. Если данные дампа аккумулированы во внешнем хранилище, достаточно запустить один экземпляр утилиты. Она обработает данные со всех узлов, которые есть внутри локального дампа.

:::{admonition} Внимание
:class: danger

Проверка дампа оказывает существенное влияние на производительность узла, поэтому не рекомендуется выполнять проверку под нагрузкой.
:::

### Режим восстановления --for-cdc

Режим предназначен для реплицированного восстановления данных с помощью кеша CDC.

При указании флага данные из дампа будут вставлены в кеш с помощью вызовов `putConflict` с указанием сохраненной версии пары «ключ-значение».

В этом режиме будет использоваться `conflictResolver` — это позволяет отбросить из дампа те пары «ключ-значения», которые уже есть в кеше в более «новом» состоянии.

Предполагаемый сценарий восстановления после сбоя межкластерной репликации:

1. Репликация была запущена, затем остановлена.
2. Включите репликацию в обычном режиме.
3. Снимите дамп на активном кластере.

    :::{admonition} Внимание
    :class: danger

    В случае репликации в режиме Active-Active дампы нужно снять на обоих кластерах.
    :::

4. Сделайте восстановление (restore) дампа на кластере с опцией `--for-cdc`:

    - При вставке из дампа каждой пары «ключ-значение» будет известны ее значение и версия на активном кластере. Будет использоваться `conflictResolver`.
    - Те пары «ключ-значение», которые к моменту восстановления дампа уже были реплицированы CDC, останутся без изменений.
    - Те пары «ключ-значение», которых еще нет на кластере в момент восстановления, будут загружены из дампа.

## Пример использования

1. Снимите дамп командой:

    ```bash
    ./control.sh --dump create --name first_dump
    Control utility [ver. 2.16.0-SNAPSHOT#20231113-sha1:fd8757e4]
    2023 Copyright(C) Apache Software Foundation
    User: user
    Time: YYYY-MM-DDT18:39:15.985
    Command [DUMP] started
    Arguments: --dump create --name first_dump
    --------------------------------------------------------------------------------
    Dump "first_dump" was created.
    Command [DUMP] finished with code: 0
    Control utility has completed execution at: YYYY-MM-DDT18:39:18.436
    Execution time: 2451 ms
    ...
    ```

    В log узла будет выведена информация:

    ```text
    [18:39:16,187][INFO][pub-#126][IgniteSnapshotManager] Cluster-wide snapshot operation started [snpName=first_dump, grps=[cache-1, cache-2], incremental=true, incrementIndex=-1]
    ...
    [18:39:16,204][INFO][exchange-worker-#75][CreateDumpFutureTask] Start cache dump [name=first_dump, grps=[540204198, 540204199]]
    [18:39:16,208][INFO][exchange-worker-#75][CreateDumpFutureTask] Start group dump [name=cache-1, id=540204198]
    [18:39:16,216][INFO][exchange-worker-#75][CreateDumpFutureTask] Start group dump [name=cache-2, id=540204199]
    ...
    [18:39:18,231][INFO][snapshot-runner-#133][CreateDumpFutureTask] Finish group dump [name=cache-1, id=540204198, time=2023, iterEntriesCnt=1000000, writtenIterEntriesCnt=1000000, changedEntriesCnt=0]
    [18:39:18,328][INFO][snapshot-runner-#134][CreateDumpFutureTask] Finish group dump [name=cache-2, id=540204199, time=2112, iterEntriesCnt=10000, writtenIterEntriesCnt=10000, changedEntriesCnt=0]
    [18:39:18,333][INFO][snapshot-runner-#133][IgniteSnapshotManager] Snapshot metafile has been created: /Users/user/bin/apache-ignite-2.16.0-SNAPSHOT-bin/work/snapshots/first_dump/0_0_0_0_0_0_0_1_lo0_10_8_148_42_127_0_0_1_47500.smf
    ...
    [18:39:18,418][INFO][disco-notifier-worker-#68][IgniteSnapshotManager] Cluster-wide snapshot operation finished successfully: SnapshotOperationRequest [reqId=7708da52-0e7d-4f96-b4a8-f5ede66070d3, snpName=first_dump, snpPath=null, nodes=HashSet [a2940478-4601-4117-a081-edae464acd9a], grps=ArrayList [cache-1, cache-2], opNodeId=a2940478-4601-4117-a081-edae464acd9a, err=null, startStageEnded=true, startTime=1700149156184, incremental=false, incIdx=-1, onlyPrimary=false, dump=true]
    ```

2. Удалите кеши командой:

    ```bash
    ./control.sh --cache destroy --destroy-all-caches
    ```

    Вывод команды:

    ```text
    Warning! The command will destroy 2 caches: cache-1, cache-2.
    If you continue, the cache data will be impossible to recover.
    Press 'y' to continue . . . y
    Control utility [ver. 2.16.0-SNAPSHOT#20231113-sha1:fd8757e4]
    2023 Copyright(C) Apache Software Foundation
    User: user
    Time: YYYY-MM-DDT18:44:13.634
    Command [CACHE] started
    Arguments: --cache destroy --destroy-all-caches
    --------------------------------------------------------------------------------
    The following caches have been stopped: cache-1, cache-2.
    Command [CACHE] finished with code: 0
    Control utility has completed execution at: YYYY-MM-DDT18:44:16.955
    Execution time: 3321 ms
    ```

3. Восстановите дамп командой:

    ```bash
    ./bin/ignite-dump-reader.sh --dump <path-to-dump> --restore --thin localhost:10800
    ```

    Вывод команды:

    ```text
    [18:49:25,611][INFO][main][DumpReader] 

    >>>    __________  ________________  ___  __  ____  ______    ___  _______   ___  _______
    >>>   /  _/ ___/ |/ /  _/_  __/ __/ / _ \/ / / /  |/  / _ \  / _ \/ __/ _ | / _ \/ __/ _ \
    >>>  _/ // (_ /    // /  / / / _/  / // / /_/ / /|_/ / ___/ / , _/ _// __ |/ // / _// , _/
    >>> /___/\___/_/|_/___/ /_/ /___/ /____/\____/_/  /_/_/    /_/|_/___/_/ |_/____/___/_/|_|
    >>> 
    >>> ver. 2.16.0-SNAPSHOT#20231113-sha1:fd8757e4
    >>> 2023 Copyright(C) Apache Software Foundation
    >>> 
    >>> Ignite documentation: http://ignite.apache.org
    >>> ConsistentId: /Users/user/bin/apache-ignite-2.16.0-SNAPSHOT-bin/work/snapshots/first_dump
    >>> Consumer: RestoreThinClientDumpConsumer [cfg=ClientConfiguration [addrFinder=null, tcpNoDelay=true, timeout=0, sndBufSize=32768, rcvBufSize=32768, binaryCfg=null, sslMode=DISABLED, sslClientCertKeyStorePath=null, sslClientCertKeyStorePwd=null, sslTrustCertKeyStorePath=null, sslTrustCertKeyStorePwd=null, sslClientCertKeyStoreType=null, sslTrustCertKeyStoreType=null, sslKeyAlgorithm=null, sslTrustAll=false, sslProto=TLS, sslCtxFactory=null, userName=null, userPwd=null, txCfg=ClientTransactionConfiguration [dfltIsolation=REPEATABLE_READ, dfltConcurrency=PESSIMISTIC, dfltTxTimeout=0], partitionAwarenessEnabled=true, partitionAwarenessMapperFactory=null, clusterDiscoveryEnabled=true, reconnectThrottlingPeriod=30000, reconnectThrottlingRetries=3, retryLimit=0, retryPolicy=org.apache.ignite.client.ClientRetryAllPolicy@45c8e616, asyncContinuationExecutor=null, heartbeatEnabled=false, heartbeatInterval=30000, autoBinaryConfigurationEnabled=true]]
    [18:49:25,797][INFO][main][DumpReader] Resolved directory for serialized binary metadata: /Users/user/bin/apache-ignite-2.16.0-SNAPSHOT-bin/work/snapshots/first_dump/db/binary_meta/0_0_0_0_0_0_0_1_lo0_10_8_148_42_127_0_0_1_47500
    [18:49:25,859][INFO][main][DumpReaderStartupLog] Thin Client Dump Consumer [cfg=ClientConfiguration [addrFinder=null, tcpNoDelay=true, timeout=0, sndBufSize=32768, rcvBufSize=32768, binaryCfg=null, sslMode=DISABLED, sslClientCertKeyStorePath=null, sslClientCertKeyStorePwd=null, sslTrustCertKeyStorePath=null, sslTrustCertKeyStorePwd=null, sslClientCertKeyStoreType=null, sslTrustCertKeyStoreType=null, sslKeyAlgorithm=null, sslTrustAll=false, sslProto=TLS, sslCtxFactory=null, userName=null, userPwd=null, txCfg=ClientTransactionConfiguration [dfltIsolation=REPEATABLE_READ, dfltConcurrency=PESSIMISTIC, dfltTxTimeout=0], partitionAwarenessEnabled=true, partitionAwarenessMapperFactory=null, clusterDiscoveryEnabled=true, reconnectThrottlingPeriod=30000, reconnectThrottlingRetries=3, retryLimit=0, retryPolicy=org.apache.ignite.client.ClientRetryAllPolicy@45c8e616, asyncContinuationExecutor=null, heartbeatEnabled=false, heartbeatInterval=30000, autoBinaryConfigurationEnabled=true]]
    [18:49:25,957][INFO][main][DumpReaderStartupLog] Restoring type mappings
    [18:49:25,959][INFO][main][DumpReaderStartupLog] Restoring binary types
    [18:49:25,992][INFO][main][DumpReaderStartupLog] Creating cache [cfg=CacheConfiguration [name=cache-1, grpName=null, memPlcName=null, storeConcurrentLoadAllThreshold=5, rebalancePoolSize=4, rebalanceTimeout=10000, evictPlc=null, evictPlcFactory=null, onheapCache=false, sqlOnheapCache=false, sqlOnheapCacheMaxSize=0, evictFilter=null, eagerTtl=true, dfltLockTimeout=0, nearCfg=null, platformCfg=null, writeSync=PRIMARY_SYNC, storeFactory=null, storeKeepBinary=false, loadPrevVal=false, aff=RendezvousAffinityFunction [parts=1024, mask=1023, exclNeighbors=false, exclNeighborsWarn=false, backupFilter=null, affinityBackupFilter=null], cacheMode=PARTITIONED, atomicityMode=ATOMIC, backups=0, invalidate=false, tmLookupClsName=null, rebalanceMode=ASYNC, rebalanceOrder=0, rebalanceBatchSize=524288, rebalanceBatchesPrefetchCnt=3, maxConcurrentAsyncOps=500, sqlIdxMaxInlineSize=-1, writeBehindEnabled=false, writeBehindFlushSize=10240, writeBehindFlushFreq=5000, writeBehindFlushThreadCnt=1, writeBehindBatchSize=512, writeBehindCoalescing=true, maxQryIterCnt=1024, affMapper=org.apache.ignite.internal.processors.cache.CacheDefaultBinaryAffinityKeyMapper@2f54a33d, rebalanceDelay=0, rebalanceThrottle=0, interceptor=null, longQryWarnTimeout=3000, qryDetailMetricsSz=0, readFromBackup=true, nodeFilter=IgniteAllNodesPredicate [], sqlSchema=null, sqlEscapeAll=false, cpOnRead=true, topValidator=null, partLossPlc=IGNORE, qryParallelism=1, evtsDisabled=false, encryptionEnabled=false, diskPageCompression=DISABLED, diskPageCompressionLevel=null]]
    [18:49:26,040][INFO][main][DumpReaderStartupLog] Creating cache [cfg=CacheConfiguration [name=cache-2, grpName=null, memPlcName=null, storeConcurrentLoadAllThreshold=5, rebalancePoolSize=4, rebalanceTimeout=10000, evictPlc=null, evictPlcFactory=null, onheapCache=false, sqlOnheapCache=false, sqlOnheapCacheMaxSize=0, evictFilter=null, eagerTtl=true, dfltLockTimeout=0, nearCfg=null, platformCfg=null, writeSync=PRIMARY_SYNC, storeFactory=null, storeKeepBinary=false, loadPrevVal=false, aff=RendezvousAffinityFunction [parts=1024, mask=1023, exclNeighbors=false, exclNeighborsWarn=false, backupFilter=null, affinityBackupFilter=null], cacheMode=PARTITIONED, atomicityMode=ATOMIC, backups=0, invalidate=false, tmLookupClsName=null, rebalanceMode=ASYNC, rebalanceOrder=0, rebalanceBatchSize=524288, rebalanceBatchesPrefetchCnt=3, maxConcurrentAsyncOps=500, sqlIdxMaxInlineSize=-1, writeBehindEnabled=false, writeBehindFlushSize=10240, writeBehindFlushFreq=5000, writeBehindFlushThreadCnt=1, writeBehindBatchSize=512, writeBehindCoalescing=true, maxQryIterCnt=1024, affMapper=org.apache.ignite.internal.processors.cache.CacheDefaultBinaryAffinityKeyMapper@3315d2d7, rebalanceDelay=0, rebalanceThrottle=0, interceptor=null, longQryWarnTimeout=3000, qryDetailMetricsSz=0, readFromBackup=true, nodeFilter=IgniteAllNodesPredicate [], sqlSchema=null, sqlEscapeAll=false, cpOnRead=true, topValidator=null, partLossPlc=IGNORE, qryParallelism=1, evtsDisabled=false, encryptionEnabled=false, diskPageCompression=DISABLED, diskPageCompressionLevel=null]]
    [18:49:26,107][INFO][main][DumpReaderStartupLog] Streaming entries [grp=540204198, part=907, cnt=0]
    [18:49:26,383][INFO][main][DumpReaderStartupLog] Partition consumed [grp=540204198, part=907, cnt=976]
    ....
    [18:49:27,002][INFO][main][DumpReaderStartupLog] Partition consumed [grp=540204198, part=268, cnt=977]
    ```

4. Проверьте, что данные присутствуют в кеше, с помощью команды:

    ```bash
    ./bin/control.sh --cache scan cache-1
    ```

    Вывод команды:

    ```text
    Control utility [ver. 2.16.0-SNAPSHOT#20231113-sha1:fd8757e4]
    2023 Copyright(C) Apache Software Foundation
    User: user
    Time: YYYY-MM-DDT18:53:57.979
    Command [CACHE] started
    Arguments: --cache scan cache-1
    --------------------------------------------------------------------------------
    Key Class         Key       Value Class       Value
    java.lang.Long    0         java.lang.Long    0
    java.lang.Long    1024      java.lang.Long    1024
    ...
    java.lang.Long    7168      java.lang.Long    7168

    ```