# Утилита control

В комплект поставки DataGrid входит скрипт командной строки `control.(sh|bat)`, который может использоваться для мониторинга кластеров и управления ими. Скрипт находится в папке `/bin/` дистрибутива.

Пример синтаксиса `control.(sh|bat)`:

::::{md-tab-set}
:::{md-tab-item} Unix
```bash
control.sh <connection parameters> <command> <arguments>
```
:::

:::{md-tab-item} Windows
```bash
control.bat <connection parameters> <command> <arguments>
```

где:

- `<connection parameters>` — параметры для подключения к узлу кластера. Полный список параметров приведен в таблице «Список параметров для подключения».
- `<command>` — команда администрирования. Полный список команд описан ниже в разделе [«Команды администрирования»](#команды-администрирования).
- `<arguments>` — параметры команды администрирования.
:::
::::

:::{admonition} Важно
:class: attention

Версия `control.sh` должна совпадать с версией используемого DataGrid. Необходимо обновлять версию `control.sh` для работы с новыми версиями DataGrid, чтобы избежать возможных конфликтов.
:::

## Подключение к кластеру

:::{admonition} Примечание
:class: note

Начиная с DataGrid версии 17.0.0, утилита `control.sh` по умолчанию использует подключение через протокол тонкого клиента, который настроен на узле с помощью класса `org.apache.ignite.configuration.ClientConnectorConfiguration`. Подробнее об этом написано ниже в разделе «[](#миграция-на-протокол-тонкого-клиента)».
:::

При выполнении без параметров подключения скрипт `control.sh` пытается подключиться к узлу, который запущен на локальном хосте (`localhost:10800`).

:::{admonition} Пример команды подключения к кластеру
:class: hint

```bash
./control.sh
...
./control.sh [--host HOST_OR_IP] [--port PORT] [--user USER] [--password PASSWORD] [--ping-interval PING_INTERVAL] [--ping-timeout PING_TIMEOUT] [--verbose] [--ssl-protocol SSL_PROTOCOL[, SSL_PROTOCOL_2, ..., SSL_PROTOCOL_N]] [--ssl-cipher-suites SSL_CIPHER_1[, SSL_CIPHER_2, ..., SSL_CIPHER_N]] [--ssl-key-algorithm SSL_KEY_ALGORITHM] [--ssl-factory SSL_FACTORY_PATH] [--keystore-type KEYSTORE_TYPE] [--keystore KEYSTORE_PATH] [--keystore-password KEYSTORE_PASSWORD] [--truststore-type TRUSTSTORE_TYPE] [--truststore TRUSTSTORE_PATH] [--truststore-password TRUSTSTORE_PASSWORD] [--enable-experimental] [command] <command_parameters>
...
```
:::

:::{admonition} Важно
:class: attention

Указание имени пользователя и пароля в явном виде в качестве параметров при запуске скрипта `control.sh` может привести к их компрометации, так как они будут видны при отображении статуса соответствующего процесса (команда `ps`). Если запустить `control.sh` подобным образом, отобразится следующее предупреждение:

```
Control utility [ver. 16.1.0-beta1#20240423-sha1:c379b8bd]
2024 Copyright(C) Apache Software Foundation
User: ignite
Time: YYYY-MM-DDT13:29:06.386
Warning: --password is insecure. Whenever possible, use interactive prompt for password (just discard --password option).
Warning: --keystore-password is insecure. Whenever possible, use interactive prompt for password (just discard --keystore-password option).
Warning: --truststore-password is insecure. Whenever possible, use interactive prompt for password (just discard --truststore-password option).
```

Для работы с `control.sh` на удаленных серверах рекомендуется использовать более безопасные способы передачи чувствительных данных в качестве параметров. Например, можно хранить имена пользователей и пароли в переменных окружения и при запуске передавать эти переменные, а не сами значения. Важно помнить, что переменные окружения можно увидеть с помощью команды `cat /proc/[PID процесса]/environ`, которая выполнена в режиме `sudo`, root-пользователем или пользователем, который запустил процесс.
:::

**Список параметров для подключения:**

| Параметр | Описание | Значение по умолчанию|
|---|---|---|
| `--host <HOST_OR_IP>` | Имя хоста или IP-адрес узла | `xxx.x.x.x` |
| `--port <PORT>` | Порт, к которому нужно подключиться | `10800` |
| `--user <USER>` | Имя пользователя | — |
| `--password` | Перед подключением к кластеру введите пароль пользователя при помощи утилиты `control.sh`. Пароль можно ввести тремя способами.<br><br>Первый способ — явно указать значение для этого параметра, например `--password <PASSWORD>`. Использовать данный способ крайне не рекомендуется по соображениям безопасности, так как в этом случае отсутствует маскирование пароля.<br><br>Второй способ (рекомендуемый) — задать параметр `--password` без указания значения. В этом случае `control.sh` принудительно запросит пароль без предварительного подключения к кластеру.<br><br>Третий способ — не использовать параметр `--password`. В этом случае подключение к кластеру будет производиться с пустыми учетными данными. Утилита `control.sh` принудительно запросит пароль пользователя, если сервер требует аутентификацию по паролю. При этом утилита потратит одну попытку подключения, чтобы определить, нужен ли серверу пароль | — |
| `--ping-interval <PING_INTERVAL>` | Интервал между `ping` (в мс) | 5000 |
| `--ping-timeout <PING_TIMEOUT>` | Время ожидания `ping` (в мс) | 30 000 |
| `--ssl-protocol <PROTOCOL1, PROTOCOL2...>` | Список SSL-протоколов для подключения к кластеру (укажите через запятую) | `TLS` |
| `--ssl-cipher-suites <CIPHER1,CIPHER2...>` | Наборы SSL-шифров (укажите через запятую) | — |
| `--ssl-key-algorithm <ALG>` | Алгоритм SSL-ключей | `SunX509` |
| `--ssl-factory <SSL_FACTORY_PATH>` | Пользовательский путь к xml-файлу `Spring` SSL-фабрики. Пример конфигурационного файла предоставляется по запросу | — |
| `--keystore-type <KEYSTORE_TYPE>` | Тип хранилища сертификатов | `JKS` |
| `--keystore KEYSTORE_PATH` | Путь к хранилищу сертификатов | — |
| `--keystore-password` | Перед подключением к кластеру введите пароль от хранилища ключей (`keystore`) при помощи утилиты `control.sh`. Пароль можно ввести тремя способами.<br><br>Первый способ — явно указать значение для этого параметра, например `--keystore-password <KEYSTORE_PWD>`. Использовать данный способ крайне не рекомендуется по соображениям безопасности, так как в этом случае отсутствует маскирование пароля.<br><br>Второй способ (рекомендуемый) — задать параметр `--keystore-password` без указания значения. В этом случае `control.sh` принудительно запросит пароль без предварительного подключения к кластеру.<br><br>Третий способ — не использовать параметр `--keystore-password`. В этом случае подключение к кластеру будет производиться с пустыми учетными данными. Утилита `control.sh` принудительно запросит пароль от хранилища ключей перед подключением к кластеру (если указан аргумент `--keystore KEYSTORE_PATH`) | — |
| `--truststore-type <TRUSTSTORE_TYPE>` | Тип хранилища доверенных сертификатов | `JKS` |
| `--truststore <TRUSTSTORE_PATH>` | Путь к хранилищу доверенных сертификатов | — |
| `--truststore-password` | Перед подключением к кластеру введите пароль от хранилища доверенных сертификатов (`truststore`) при помощи утилиты `control.sh`. Пароль можно ввести тремя способами.<br><br>Первый способ — явно указать значение для этого параметра, например `--truststore-password <TRUSTSTORE_PWD>`. Использовать данный способ крайне не рекомендуется по соображениям безопасности, так как в этом случае отсутствует маскирование пароля.<br><br>Второй способ (рекомендуемый) — задать параметр `--truststore-password` без указания значения. В этом случае `control.sh` принудительно запросит пароль без предварительного подключения к кластеру.<br><br>Третий способ — не использовать параметр `--truststore-password`. В этом случае подключение к кластеру будет производиться с пустыми учетными данными. Утилита `control.sh` принудительно запросит пароль от хранилища доверенных сертификатов перед подключением к кластеру (если указан аргумент `--truststore TRUSTSTORE_PATH`) | — |

**Общие параметры:**

| Параметр | Описание |
|---|---|
| `-–verbose` | Включить подробный вывод |
| `--enable-experimental` | Разрешить использование experimental-функциональности; далее в описании эти команды будут отмечены экспериментальными |

**Коды возврата команд:**

-   «0» — успешно выполнено;
-   «1» — указаны неверные аргументы;
-   «2» — не удалось подключиться к кластеру;
-   «3» — неуспешная аутентификация;
-   «4» — возникла неожиданная ошибка.

Чтобы вывести справку по использованию `control.sh`, используйте команду `./control.sh --help`.

## Миграция на протокол тонкого клиента

С конфигурацией DataGrid по умолчанию никаких действий по миграции не требуется, дополнительная настройка коннектора не нужна.

При подключении к некорректному коннектору возникнет ошибка с сообщением:

```text
Make sure you are connecting to the client connector (configured on a node via 'org.apache.ignite.configuration.ClientConnectorConfiguration'). Connection to the REST connector was deprecated and will be removed for the control utility in future releases. Set up the 'IGNITE_CONTROL_UTILITY_USE_CONNECTOR_CONNECTION' system property to 'true' to forcefully connect to the REST connector (configured on a node via 'org.apache.ignite.configuration.ConnectorConfiguration').
```
:::{admonition} Перевод текста ошибки
:class: note
:collapsible:

```text
Убедитесь, что подключаетесь к коннектору клиента, который настроен на узле с помощью `org.apache.ignite.configuration.ClientConnectorConfiguration`. Подключение к REST-коннектору признано устаревшим и будет удалено для утилиты `control.sh` в будущих версиях. Чтобы принудительно подключиться к REST-коннектору, который настроен на узле с помощью `org.apache.ignite.configuration.ConnectorConfiguration`, установите значение `true` у системного свойства `IGNITE_CONTROL_UTILITY_USE_CONNECTOR_CONNECTION`.
```
:::

Для обеспечения обратной совместимости добавлено системное свойство `IGNITE_CONTROL_UTILITY_USE_CONNECTOR_CONNECTION`, оно обеспечивает предыдущее поведение:

```bash
export IGNITE_CONTROL_UTILITY_USE_CONNECTOR_CONNECTION=true;
control.sh --state --host x.x.x.x --port 11212
```

:::{admonition} Важно
:class: attention

Системное свойство `IGNITE_CONTROL_UTILITY_USE_CONNECTOR_CONNECTION` будет удалено в будущих релизах DataGrid.
:::

В некоторых случаях для миграции пользовательских скриптов, которые используют утилиту `control.sh`, могут потребоваться дополнительные действия.

**Случаи, в которых могут потребоваться дополнительные действия:**

1. **Случай:** указан пользовательский порт:

   ```bash
   control.sh --state --host x.x.x.x --port 11212
   ```

   **Действие:** укажите порт для коннектора тонкого клиента:
   
   ```bash
   control.sh --state --host x.x.x.x
   control.sh --state --host x.x.x.x --port 10801
   ```

2. **Случай:** для коннектора Binary REST указана пользовательская SSL-фабрика, которая отличается от SSL-фабрики коннектора тонкого клиента:
   
   ```bash
   control.sh --state --ssl-factory connector-ssl-factory.xml
   ```

   **Действие:** укажите SSL-фабрику для коннектора тонкого клиента:
      
   ```bash
   control.sh --state --ssl-factory ignite-ssl-factory.xml
   control.sh --state --ssl-factory client-connector-ssl-factory.xml
   ```

3. **Случай:** коннектор клиента отключен. 
   
   **Действие:** включите коннектор в конфигурации `IgniteConfiguration#setClientConnectorConfiguration`.

## Команды администрирования

### Изменение состояния кластера (--set-state)

Выполните команду `--set-state` для изменения состояния кластера:

```bash
./control.sh --set-state INACTIVE|ACTIVE|ACTIVE_READ_ONLY [--force] [--yes]
```

где:

-   `INACTIVE|ACTIVE|ACTIVE_READ_ONLY` — укажите один из вариантов, чтобы изменить состояние кластера:

    -   `INACTIVE` — не активирован, все операции запрещены.
    -   `ACTIVE` — активирован, нормальный режим работы кластера. Разрешено выполнение любых операций.
    -   `ACTIVE_READ_ONLY` — активирован в режиме только для чтения.

-   `--force ` — принудительная деактивация кластера. Используйте этот аргумент, если в кластере есть in-memory регионы данных.
-   `--yes` — деактивация без подтверждения выполнения команды.

Чтобы отобразить текущее состояние кластера, используйте команду `./control.sh --state`. В результате будет выведено одно из возможных состояний кластера (`INACTIVE`, `ACTIVE`, `ACTIVE_READ_ONLY`).

### Работа с базовой топологией (--baseline)

Выполните команду `--baseline` для получения списка узлов, которые входят в базовую топологию (`baseline topology`):

```bash
./control.sh|bat --baseline [--verbose]
```

где `--verbose` — параметр для отображения полного списка IP-адресов узлов.

Вывод команды содержит:

-   текущую версию топологии;
-   список идентификаторов узлов, которые включены в базовую топологию;
-   список узлов, которые соединялись с кластером, но не были добавлены в базовую топологию.

#### Добавление узлов в базовую топологию

:::{admonition} Важно
:class: attention

Перед добавлением нового узла в базовую топологию и выполнением команды `--baseline add` запустите узел и убедитесь, что узел подключился к кластеру и присутствует в топологии кластера.

После добавления нового узла начнется процесс ребалансировки для перераспределения данных по узлам базовой топологии.
:::

Используйте команду `--baseline add` для добавления узла/узлов в базовую топологию:

```bash
./control.sh|bat --baseline add consistentId1[,consistentId2,....,consistentIdN] [--verbose] [--yes]
```

где:

-   `consistentId1`, `consistentId2` — `consistency ID` узла/узлов (через запятую), которые нужно добавить в топологию;
-  `--verbose` — параметр для отображения полного списка IP-адресов узлов;
-   `--yes` — добавление узла/узлов без подтверждения выполнения операции. 

#### Удаление узлов из базовой топологии

Используйте команду `--baseline remove` для удаления узла/узлов из базовой топологии: 

```bash
./control.sh|bat -baseline remove consistentId1[,consistentId2,....,consistentIdN] [--verbose] [--yes]
```

где: 

-   `consistentId1`, `consistentId2` — `consistency ID` узла/узлов (через запятую), которые нужно исключить из топологии;
-  `--verbose` — параметр для отображения полного списка IP-адресов узлов;
-   `--yes` — удаление узла/узлов без подтверждения выполнения операции. 

:::{admonition} Примечание
:class: note

Только автономные узлы могут быть удалены из базовой топологии.

Отключите узел перед его исключением из базовой топологии и выполнением команды `--baseline remove`.

После удаления узла начнется процесс ребалансировки, в результате чего данные перераспределятся по узлам, которые остались в базовой топологии.
:::

#### Установка базовой топологии

Используйте команду `--baseline set` для установки списка всех `consistency ID` узлов в базовой топологии: 

```bash
./control.sh|bat --baseline set consistentId1[,consistentId2,....,consistentIdN] [--verbose] [--yes]
```

где:

-   `consistentId1`, `consistentId2` — `consistency ID` узла/узлов базовой топологии;
-   `--verbose` — параметр для отображения полного списка IP-адресов узлов;
-   `--yes` — установка базовой топологии без подтверждения выполнения операции. 

#### Установка версии базовой топологии

Используйте команду `--baseline version` для установки конкретной версии базовой топологии: 

```bash
./control.sh --baseline version topologyVersion [--verbose] [--yes]
```

где:

-   `topologyVersion` — номер требуемой версии базовой топологии;
-   `--verbose` — параметр для отображения полного списка IP-адресов узлов;
-   `--yes` — установка версии базовой топологии без подтверждения выполнения операции. 

#### Автоматическая настройка базовой топологии

:::{admonition} Примечание
:class: note

Функция автоматической настройки базовой топологии доступна в случае, если топология оставалась стабильной в течение заданного периода времени.
:::

Используйте команду `--baseline auto_adjust`, чтобы включить или выключить функции автонастройки для persistence-кластеров: 

```bash
./control.sh --baseline auto_adjust [--verbose] [DISABLE|ENABLE] [timeout <timeoutMillis>] [--yes]
```

где: 

-   `[DISABLE|ENABLE]` — параметр выключения/включения автонастройки базовой топологии;
-   `timeout <timeoutMillis>` — значение тайм-аута в миллисекундах. Базовая топология устанавливается на текущую топологию кластера по истечении заданного количества миллисекунд после последнего события `JOIN`, `LEFT`, или `FAIL`. Каждое новое событие `JOIN`, `LEFT`, или `FAIL` перезапускает обратный отсчет времени ожидания;
-   `--verbose` — параметр для отображения полного списка IP-адресов узлов;
-   `--yes` — автонастройка базовой топологии без подтверждения выполнения операции.

### Работа с транзакциями (--tx)

Используйте команду `--tx` для получения информации о транзакциях, выполняемых в кластере, и отмены конкретных транзакций: 

```bash
./control.sh -tx [--xid XID] [--min-duration SECONDS] [--min-size SIZE] [--label PATTERN_REGEX] [--limit NUMBER] [--order DURATION|SIZE|START_TIME] [--kill] [--servers|--clients|--nodes consistentId1[,consistentId2,....,consistentIdN]] [--yes]
```

где:

-   `--xid <XID>` — идентификатор транзакции;
-   `--min-duration <SECONDS>` — минимальная длительность транзакции (в секундах);
-   `--min-size <SIZE>` — минимальный размер транзакции;
-   `--label <LABEL>` — метка транзакции (можно присваивать регулярное выражение/ключевое слово, которое будет использоваться при поиске);
-   `--limit <NUMBER>` — ограничение числа строк при выводе запроса;
-   `--order <DURATION|SIZE|START_TIME>` — сортировка транзакций при выводе запроса (по продолжительности, размеру, времени старта транзакции, соответственно);
-   `--kill` — прерывание выполнения транзакции;
-   `--servers`, `--clients` — вывод запроса по конкретным серверным (`servers`) или клиентским (`clients`) узлам;
-   `--nodes <nodeId1,nodeId2…>` — cписок согласованных ID узлов, по которым нужно выполнить поиск транзакций;
-   `--yes` — вывод информации о транзакции без подтверждения выполнения операции.

Чтобы получить подробную информацию о конкретной транзакции, используйте команду:

```bash
./control.sh --tx --info txId
```

где `txId` — уникальный идентификатор транзакции в формате GridCacheVersion: `[topVer=..., order=..., nodeOrder=...]`.

### Работа с кешами (--cache)

Для выполнения операций с кешами используйте следующую команду: 

```bash
./control.sh --cache [subcommand] <subcommand arguments>
```

Чтобы получить подсказку по синтаксису команды, используйте команду `./control.sh --cache help`.

#### Проверка согласованности партиций

Используйте команду `--cache idle_verify` для проверки счетчиков, хеш-сумм и количества записей основных (primary) и резервных (backup) партиций:

```bash
./control.sh --cache idle_verify [--dump] [--skip-zeros] [--check-crc] [--exclude-caches cacheName1,...,cacheNameN] [--cache-filter DEFAULT|SYSTEM|PERSISTENT|NOT_PERSISTENT|USER|ALL] [cacheName1,...,cacheNameN]
```

где: 

-   `--dump` — перенаправление вывода результата работы в файл, расположенный в `$IGNITE_HOME/work/`. Формат имени файла: `idle-dump-YYYY-MM-DDTHH24-MI-SS_sss.txt`;
-   `--skip-zeros ` — пропуск партиций, в которых нет записей;
-   `--check-crc ` — проверка CRC-суммы страниц;
-   `--exclude-caches cacheName1,...,cacheNameN` — исключение кешей, по которым не нужно искать расхождения;
-   `--cache-filter` тип кешей, по которым нужно искать расхождения:

    -   `DEFAULT` — пользовательские кеши или все кеши, которые явно указаны;
    -   `SYSTEM` — системные кеши, которые DataGrid создает для своих нужд;
    -   `PERSISTENT` — персистируемые кеши, данные которых хранятся на диске;
    -   `NOT_PERSISTENT` — неперсистируемые кеши, данные которых хранятся только в оперативной памяти;
    -   `USER` — все пользовательские кеши, за исключением системных;
    -   `ALL` — все кеши, независимо от типа и места хранения их данных;

-   `cacheName1,...,cacheNameN` — имена кешей, в которых нужно искать расхождения.

Чтобы отменить запущенный процесс `idle_verify`, используйте аргумент `--cancel`:

```bash
control.sh --cache idle_verify --cancel
```

:::{admonition} Важно
:class: attention

Запускайте команду `control.sh --cache idle_verify` на кластере без нагрузки на изменение данных. В противном случае команда может показать расхождения по партициям, которые изменяются на момент работы данной утилиты.

При запуске утилиты `idle_verify` учитывайте, что CPU утилизируется примерно на 100%, что может блокировать другие процессы.
:::

#### Вывод информации о кешах

Используйте команду `--cache list` для вывода информации о кешах кластера:

```bash
./control.sh --cache list regexPattern [nodeId] [--config] [--output-format multi-line] [--groups|--seq]
```

где:

-   `--config` — включить в вывод конфигурации кешей;
-   `--output-format multi-line` — вывести параметры конфигурации в каждой строке.  Параметр действует только при использовании вместе с атрибутом `--config` и без атрибута `--groups|--seq]`;
-   `--groups` — вывести информацию о кеш-группах;
-   `--seq` — вывести информацию об атомарных кешах (`IgniteAtomicSequence`).

#### Создание кешей

Используйте команду `--cache create` для создания кешей из Spring XML-конфигурации:

```bash
./control.sh --cache create --springxmlconfig springXmlConfigPath --skip-existing
```

где:

- `--springxmlconfig springXmlConfigPath` — путь к [конфигурации Spring XML](../../administration-guide/md/resources/create-cache.xml), которая содержит компоненты `org.apache.ignite.configuration.CacheConfiguration` для создания кешей;
- `--skip-existing` — необязательный параметр, который исключает создание существующего кеша.

:::{admonition} Примечание
:class: note

Модуль `ignite-spring` должен быть включен.
:::

#### Удаление кешей

Используйте команду `--cache destroy` для удаления конкретных кешей:

```bash
./control.sh --cache destroy --caches cache1,...,cacheN|--destroy-all-caches
```

где:

-   `--caches cache1,...,cacheN` — имя кеша или список кешей через запятую;
-   `--destroy-all-caches` — удаление всех кешей.

#### Очистка кешей

Используйте команду `--cache clear` для очистки определенных кешей (при этом сами кеши не удаляются):

```bash
./control.sh --cache clear --caches cache1[,cache2,....,cacheN]
```

где `cache1,…​,cacheN` — имя кеша или список кешей (через запятую), которые нужно очистить.

#### Проверка индексов

Используйте команду `--cache validate_indexes` для проверки индексов указанных кешей/кеш-групп:

```bash
./control.sh --cache validate_indexes [cacheName1,...,cacheNameN] [nodeId] [--check-first N] [--check-through K] [--check-crc] [--check-sizes]
```

где:

-   `cacheName1,...,cacheNameN` — имя кеша или список кешей через запятую;
-   `nodeId` — идентификатор узла;
-   `--check-first N` — проверка только первых N ключей;
-   `--check-through K` — проверка каждого K-го ключа (например, каждого десятого ключа);
-   `--check-crc` — проверка CRC-суммы страниц, которые хранятся на диске;
-   `--check-sizes` — проверка, совпадают ли размер индекса и размер кеша.

#### Проверка размера встроенных SQL-индексов

Используйте команду `--cache check_index_inline_sizes` для проверки размера индексов кешей на всех узлах кластера:

```bash
./control.sh --cache check_index_inline_sizes
```

где `check_index_inline_sizes` — параметр проверки размера встроенных индексов (`inlinesize`) заданных кешей.

#### Проверка очереди транзакций

Используйте команду `--cache contention` для вывода ключей, за которые идет конкуренция в транзакциях:

```bash
./control.sh --cache contention minQueueSize [nodeId] [maxPrint]
```

где:

-   `minQueueSize` — минимальная длина очереди транзакций, которые хотят получить ключ;
-   `nodeId` — идентификатор узла;
-   `maxPrint` — максимальная длина вывода.

#### Вывод распределения партиций

Используйте команду `--cache distribution` для вывода информации о распределении партиций:

```bash
./control.sh --cache distribution nodeId|null [cacheName1,...,cacheNameN] [--user-attributes attrName1,...,attrNameN]
```

где:

-   `nodeId` - идентификатор узла;
-   `cacheName1,...,cacheNameN` - имя кеша или список кешей через запятую;
-   `--user-attributes attrName1,...,attrNameN` — названия атрибутов узлов.

#### Сброс состояния партиций

Используйте команду `--cache reset_lost_partitions` для сброса состояния потерянных партиций:

```bash
./control.sh --cache reset_lost_partitions cacheName1,...,cacheNameN
```

где `cacheName1,...,cacheNameN ` — имя кеша или список кешей через запятую.

#### Удаление мусора из кешей

Используйте команду `--cache find_garbage` для поиска и, при необходимости, удаления мусора из общих (shared) кеш-групп:

```bash
./control.sh --cache find_garbage [groupName1,...,groupNameN] [nodeId] [--delete]
```

где:

-   `nodeId` — идентификатор узла;
-   `cacheName1,...,cacheNameN` — имя кеша или список кешей через запятую;
-   `--delete` — команда удаления мусора.

#### Вывод списка индексов

Используйте команду `--cache indexes_list` для вывода списка всех индексов:

```bash
./control.sh --cache indexes_list [--node-id nodeId] [--group-name grpRegExp] [--cache-name cacheRegExp] [--index-name idxNameRegExp]
```

где:

-   `--node-id nodeId` — идентификатор узла, на котором будет происходить выполнение задачи. Если не указать идентификатор, по умолчанию будет выбран случайный узел;
-   `--group-name grpRegExp` — регулярное выражение для фильтрации по именам кеш-групп;
-   `--cache-name cacheRegExp` — регулярное выражение для фильтрации по именам кешей;
-   `--index-name idxNameRegExp` — регулярное выражение для фильтрации по именам индексов.

#### Вывод списка перестраиваемых индексов

Используйте команду `--cache indexes_rebuild_status` для вывода индексов, находящихся в процессе перестроения:

```bash
./control.sh --cache indexes_rebuild_status [--node-id nodeId]
```

где `--node-id <nodeId>` — идентификатор узла, на котором будет происходить выполнение задачи. Если не указать идентификатор, по умолчанию будет выбран случайный узел.

#### Перестройка индексов

Используйте команду `--cache indexes_force_rebuild`, чтобы перенастроить все индексы для указанных кешей/кеш-групп:

```bash
./control.sh --cache indexes_force_rebuild --node-id nodeId|--node-ids nodeId1,...nodeIdN|--all-nodes --cache-names cacheName1,...cacheNameN|--group-names groupName1,...groupNameN
```

где:

-   `--node-id nodeId` — идентификатор узла, на котором будет происходить перестроение индекса (не рекомендуемый вариант использования);
-   `--node-ids nodeId1,...nodeIdN` — идентификатор узла/узлов, где будет происходить перестроение индексов (рекомендуемый вариант использования);
-   `--all-nodes` — перестройка индексов на всех узлах (рекомендуемый вариант использования);
-   `--cache-names cacheName1,...cacheNameN` — список кешей, для которых будут перестроены индексы;
-   `--group-names groupName1,...groupNameN` — список кеш-групп, для которых будут перестроены индексы.

#### Сбор метрик кешей

Используйте команду `--cache metrics` для управления сбором метрик кешей:

```bash
./control.sh --cache metrics ENABLE|DISABLE|STATUS --caches cache1[,...,cacheN]|--all-caches
```

где:

-   `--cache metrics` — параметры метрики кеша:

    -   `ENABLE` — включить расчет метрик;
    -   `DISABLE` — выключить расчет метрик;
    -   `STATUS` — показать состояние метрик;

-   `--caches cache1[,...,cacheN]` — список кешей;
-   `--all-caches` — сбор метрик по всем кешам.

#### Перестройка индексов по расписанию

Используйте команду `--cache schedule_indexes_rebuild`, чтобы запустить перестройку всех индексов для указанных кешей или кеш-групп; указанные кеши или группы кешей должны находиться в Maintenance Mode:

```bash
./control.sh --cache schedule_indexes_rebuild [--node-id nodeId|--node-ids nodeId1,...nodeIdN|--all-nodes] --cache-names cacheName[index1,...indexN],cacheName2,cacheName3[index1] --group-names groupName1,groupName2,...groupNameN
```

где:

-   `--node-id nodeId` — идентификатор узла, на котором будет происходить перестроение индекса (не рекомендуемый вариант использования);
-   `--node-ids nodeId1,...nodeIdN` — идентификатор узла/узлов, где будет происходить перестроение индексов (рекомендуемый вариант использования);
-   `--all-nodes` — перестройка индексов на всех узлах (рекомендуемый вариант использования);
-   `--cache-names cacheName1,...cacheNameN` — список кешей, для которых будут перестроены индексы;
-   `--group-names groupName1,...groupNameN` — список кеш-групп, для которых будут перестроены индексы.

### Проверка состояний (--diagnostic)

Для проверки состояний процессов в кластере используйте команду:

```bash
./control.sh --diagnostic help
```

Чтобы получить подсказку по синтаксису команды, используйте `./control.sh --diagnostic help`.

#### Проверка состояний блокировки страниц (--diagnostic pagelocks)

Используйте команду `--diagnostic pagelocks` для отображения состояния блокировки страниц:

```bash
./control.sh --diagnostic pagelocks [DUMP|DUMP_LOG] [--path path] [--all|--nodes node_id1[,node_id2....node_idN]|consistend_id1[,consistent_id2,....,consistent_idN]]
```

где: 

-   `DUMP` — сохранение дампа в директории `IGNITE_HOME/work/diagnostic directory`;
-   `DUMP_LOG` — вывод дампа на консоль;
-   `--path` — путь к директории, где будет сохранен дамп;
-   `--all` — запуск проверки состояния блокировки страниц на всех узлах;
-   `--nodes node_id1[,node_id2....node_idN]|consistend_id1[,consistent_id2,....,consistent_idN]` — список узлов или `consistent ID` узлов.

#### Проверка состояний подключения узлов (--diagnostic connectivity)

Используйте команду `--diagnostic connectivity` для отображения состояния подключения всех узлов в кластере:

```bash
./control.sh --diagnostic connectivity
```

### Сканирование кешей (--cache scan)

Для просмотра содержимого кеша используйте команду: 

```bash
./control.sh --cache scan cacheName [--limit N]
```

где:

-   `cacheName` — имя кеша;
-   `--limit N` — лимит количества записей в выводе (по умолчанию составляет 1000).

После выполнения команды для каждой записи будут отображаться четыре параметра:

-   класс ключа (key class);
-   строковое представление ключа;
-   класс значения (value class);
-   строковое представление значения.

### Шифрование данных (--encryption)

#### Вывод мастер-ключа

Используйте команду `--encryption get_master_key_name` для вывода имени мастер-ключа:

```bash
./control.sh --encryption get_master_key_name
```

#### Смена мастер-ключа

Используйте команду `--encryption change_master_key` для смены мастер-ключа:

```bash
./control.sh --encryption change_master_key newMasterKeyName
```

где `newMasterKeyName` — имя нового мастер-ключа.

#### Смена ключа шифрования кеш-группы

Используйте команду `--encryption change_cache_key` для смены ключа шифрования кеш-группы:

```bash
./control.sh --encryption change_cache_key cacheGroupName
```

где `cacheGroupName` — имя кеш-группы.

#### Вывод ID ключа шифрования

Используйте команду `--encryption cache_key_ids`, чтобы отобразить идентификатор ключа шифрования:

```bash
./control.sh --encryption cache_key_ids cacheGroupName
```

где `cacheGroupName` — имя кеш-группы.

#### Вывод статуса повторного шифрования

Используйте команду `--encryption reencryption_status`, чтобы отобразить статус повторного шифрования:

```bash
./control.sh --encryption reencryption_status cacheGroupName
```

где `cacheGroupName` — имя кеш-группы.

#### Остановка повторного шифрования

Используйте команду `--encryption suspend_reencryption`, чтобы приостановить повторное шифрование кеш-группы:

```bash
./control.sh --encryption suspend_reencryption cacheGroupName
```

где `cacheGroupName` — имя кеш-группы.

#### Возобновление повторного шифрования

Используйте команду `--encryption resume_reencryption`, чтобы возобновить приостановленное ранее повторное шифрование кеш-группы:

```bash
./control.sh --encryption resume_reencryption cacheGroupName
```

где `cacheGroupName` — имя кеш-группы.

#### Изменение скорости повторного шифрования

Используйте команду `--encryption reencryption_rate_limit`, чтобы посмотреть/изменить скорость повторного шифрования:

```bash
./control.sh --encryption reencryption_rate_limit [new_limit]
```

где `new_limit` — десятичное значение для изменения ограничения скорости повторного шифрования (МБ/с).

### Команды прерывания (--kill)

Для прерывания выполнения операций используйте команду:

```bash
./control.sh --kill
```

#### Прерывание compute task

Используйте команду `--kill compute` для прерывания выполнения распределенных вычислений (compute tasks):

```bash
./control.sh --kill compute session_id
```

где `session_id` — идентификатор сессии.

#### Прерывание работы сервиса

Используйте команду `--kill service` для прерывания работы сервиса:

```bash
./control.sh --kill service name
```

где `name` — имя сервиса.

#### Прерывание транзакций

Используйте команду `--kill transaction` для прерывания выполнения транзакции:

```bash
./control.sh --kill transaction xid
```

где `xid` — идентификатор транзакции.

#### Прерывание запросов

Используйте команду `--kill sql` для прерывания выполнения SQL-запроса:

```bash
./control.sh --kill sql query_id
```

где `query_id` — идентификатор запроса.

#### Прерывание scan query

Используйте команду `--kill scan` для прерывания выполнения `scan query`-запроса:

```bash
./control.sh --kill scan origin_node_id cache_name query_id
```

где: 

-   `origin_node_id` — идентификатор узла, который инициировал запрос;
-   `cache_name` — имя кеша;
-   `query_id` — идентификатор `scan query`-запроса.

#### Прерывание continuous query

Используйте команду `--kill continuous` для прерывания выполнения `continuous query`-запроса:

```bash
./control.sh --kill continuous origin_node_id routine_id
```

где: 

-   `origin_node_id` — идентификатор узла, который инициировал запрос;
-   `routine_id` — идентификатор `continuous query`-запроса.

#### Прерывание клиентских подключений

Используйте команду `--kill client` для прерывания клиентских подключений:

```bash
./control.sh --kill client connection_id [--node-id node_id]
```

где: 

-   `connection_id` — идентификатор соединения. Если вместо `connection_id` указать значение `ALL`, будут прерваны все клиентские подключения;
-   ` --node-id node_id` — идентификатор узла, с которым нужно разорвать соединение.

#### Прерывание снятия снепшота

Используйте команду `--kill snapshot` для прерывания снятия снепшота:

```bash
./control.sh --kill snapshot request_id
```

где `request_id` — идентификатор задачи по снятию снепшота.

#### Прерывание проверки несогласованности

Используйте команду `--kill consistency` для прерывания операции по проверке и устранению несогласованности данных:

```bash
./control.sh --kill consistency
```

### Работа со снепшотами (--snapshot)

#### Снятие снепшотов

Используйте команду `--snapshot` для снятия снепшота:

```bash
./control.sh --snapshot create snapshot_name [--dest path] [--sync] [--incremental] [--only-primary]
```

где:

-   `snapshot_name` — имя снепшота. При снятии инкрементального снепшота (атрибут `--incremental`) укажите имя полного снепшота, с которого снимается инкрементальный снепшот;
-   `--dest path` — путь, по которому будет сохраняться снепшот. Если путь не указан, по умолчанию снепшот будет сохранен в директории `snapshots`;
-   `--sync` — синхронный запуск операции, управление вернется по окончании снятия снеппшота. Если не указывать атрибут `--sync`, управление вернется после начала снятия, а снепшот будет сниматься в фоновом режиме;
-   `--incremental` — снятие инкрементального снепшот. Полный снепшот должен быть доступен по пути `--dest` и имени `snapshot_name`;
-   `--only-primary` — включение в снепшот только primary-партиций.

#### Отмена снятия снепшота

Используйте команду `--snapshot cancel` для прерывания процесса снятия снепшота:

```bash
./control.sh --snapshot cancel [--id id]|[--name name]
```

где:

-   `--id <id>` — идентификатор запроса снятия снепшота;
-   `--name <name>` — имя снепшота.

#### Проверка снепшота

Используйте команду `--snapshot check`, чтобы провести проверку снепшота:

```bash
./control.sh --snapshot check snapshot_name [--src path] [--increment incrementIndex]
```

где: 

-   `snapshot_name` — имя снепшота;
-   `--src path` — путь к директории, где сохранен снепшот. Если путь не указан, снепшот считывается из директории по умолчанию;
-   `--increment incrementIndex` — индекс инкрементального снепшота. Проверка выполняется последовательно по всем частям инкрементального снепшота, от первого до указанного изменения.

#### Восстановление из снепшота

Используйте команду `--snapshot restore` для восстановления из снепшота:

```bash
./control.sh --snapshot restore snapshot_name [--increment incrementIndex] [--groups group1,...groupN] [--src path] [--sync] [--check] [--status|--cancel|--start]
```

где: 

-   `snapshot_name` — имя снепшота. При восстановлении из инкрементального снепшота (`--incremental`) укажите имя полного снепшота.
-   `--increment incrementIndex` — индекс инкрементального снепшота. После восстановления из полного снепшота инкрементальные изменения применяются последовательно, от первого до указанного.
-   `--groups group1,...groupN` — названия кеш-групп.
-   `--src path` — путь к каталогу, в котором расположены файлы снепшотов. Если путь не указан, будет использоваться каталог по умолчанию.
-   `--sync` — синхронный запуск операции, управление вернется по окончанию восстановления из снеппшота. Если не указывать атрибут `--sync`, управление вернется после начала снятия, а снепшот будет сниматься в фоновом режиме.
-   `--check` — проверка целостности снепшота перед восстановлением.
-   `--status` — статус операции восстановления (не рекомендуемый вариант; для вывода статуса используйте атрибут `—-snapshot status`).
-   `--cancel` — отмена операции восстановления (не рекомендуемый вариант; для отмены используйте атрибут `—-snapshot cancel`).
-   `--start` — запуск операции восстановления снепшота (действует по умолчанию).

#### Статус операции

Используйте команду `--snapshot status`, чтобы получить статус по процессу снятия снепшота:

```bash
./control.sh --snapshot status
```

### Установка ID кластера (--change-tag)

Используйте команду `--change-tag` для установки идентификатора кластера (cluster tag):

```bash
./control.sh --change-tag newTagValue [--yes]
```

где `yes` —  смена идентификатора без подтверждения выполнения команды.

### Работа с метаданными (--meta)

#### Вывод справки

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--meta help` для вывода справки:

```bash
./control.sh --meta help
```

#### Вывод метаданных бинарного типа

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--meta list` для вывода метаданных бинарного типа (`binary metadata`):

```bash
./control.sh --meta list
```

#### Вывод информации о Binary Type

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--meta details` для вывода детальной информации об определенном `BinaryType`:

```bash
./control.sh --meta details [--typeId <typeId>]|[--typeName <typeName>]
```

где:

-   `--typeId` — идентификатор `BinaryType`;
-   `--typeName` — имя `BinaryType`.

#### Удаление метаданных

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--meta remove` для удаления метаданных из кластера и сохранения их копии в файл с именем `<typeId>.bin`:

```bash
./control.sh --meta remove [--out <fileName>] [--typeId <typeId>]|[--typeName <typeName>]
```

#### Обновление метаданных

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--meta update` для обновления метаданных кластера из файла:

```bash
./control.sh --meta update --in <fileName>
```

где `--in <fileName>` — путь к файлу с метаданными.

### Политика отключения

Используйте команду `--shutdown-policy` для установки или отображения политики отключения:

```bash
./control.sh --shutdown-policy [IMMEDIATE|GRACEFUL]
```

где:

-   `IMMEDIATE` — остановка произойдет настолько быстро, насколько возможно;
-   `GRACEFUL` — остановка произойдет в том случае, если в кластере останется хотя бы одна копия партиции.

### Прерывание разогрева данных

Используйте команду `--warm-up` для прерывания разогрева данных:

```bash
./control.sh --warm-up --stop
```

### Вывод справки

Используйте команду `--property help` для вывода справки о команде:

```bash
./control.sh --property help
```

#### Вывод списка параметров

Используйте команду `--property list` для вывода списка всех доступных параметров:

```bash
./control.sh --property list [--info]
```

где `--info` — вывод детальной информации.

#### Вывод значения параметра

Используйте команду `--property get` для вывода значения параметра:

```bash
./control.sh --property get --name <property_name>
```

где `--name <property_name>` — название параметра.

#### Установка значения параметра

Используйте команду `--property set` для установки значения параметра:

```bash
./control.sh --property set --name <property_name> --val <property_value>
```

где:

-   `--name <property_name>` — название параметра;
-   `--val <property_value>` — значение параметра.

### Работа с системными представлениями

Используйте команду `--system-view` для отображения содержимого системного представления:

```bash
./control.sh --system-view system_view_name [--node-id node_id|--node-ids nodeId1,nodeId2,..|--all-nodes]
```

где:

-   `system_view_name` — название системного представления. Поддерживаются оба типа представления — SQL и Java;
-   `--node-id nodeId` — идентификатор узла, на котором будет происходить перестроение (не рекомендуемый вариант, используйте `--node-ids` или `--all-nodes`);
-   `--node-ids nodeId1,nodeId2,..` — идентификаторы узлов, с которых выводится содержимое системного представления. Если идентификаторы не установлены, будет выбран случайный узел;
-   `--all-nodes` — вывод системных представлений со всех узлов.

### Работа с метриками

#### Вывод метрики

Используйте команду `--metric` для вывода значения метрики:

```bash
./control.sh --metric name [--node-id node_id]
```

где:

-   `name` — название метрики;
-   `--node-id <node_id>` — идентификатор узла.

#### Вывод гистограммы

Используйте команду `--metric --configure-histogram` для конфигурирования гистограммы конкретной метрики:

```bash
./control.sh --metric --configure-histogram name newBounds [--node-id node_id]
```

где:

-   `name` — название метрики;
-   `newBounds` — список значений для конфигурирования гистограммы через запятую;
-   `--node-id <node_id>` — идентификатор узла.

#### Настройка метрики

Используйте команду `-metric --configure-hitrate` для настройки показателя частоты снятия метрики:

```bash
./control.sh --metric --configure-hitrate name newRateTimeInterval [--node-id node_id]
```

где:

-   `name` — название метрики;
-   `newRateTimeInterval` — временной интервал для снятия метрики;
-   `--node-id <node_id>` — идентификатор узла.

### Работа с persistence-данными

#### Вывод информации о поврежденных кешах

Используйте команду `--persistence info` для вывода информации о потенциально поврежденных кешах в локальном узле:

```bash
./control.sh --persistence info
```

#### Очистка от поврежденных кешей

Используйте команду `--persistence clean corrupted` для очистки каталогов кешей с поврежденными файлами данных:

```bash
./control.sh --persistence clean corrupted
```

#### Очистка от всех кешей

Используйте команду `--persistence clean all` для очистки каталогов от всех кешей:

```bash
./control.sh --persistence clean all
```

#### Очистка от конкретных кешей

Используйте команду `--persistence clean caches` для очистки каталогов от перечисленных кешей:

```bash
./control.sh --persistence clean caches cache1,cache2,cache3
```

где `cache1,cache2,cache3` — имена кешей через запятую.

#### Резервирование поврежденных файлов

Используйте команду `--persistence backup corrupted` для резервирования поврежденных файлов данных:

```bash
./control.sh --persistence backup corrupted
```

#### Резервирование файлов всех кешей

Используйте команду `--persistence backup all` для резервирования файлов данных всех кешей:

```bash
./control.sh --persistence backup all
```

#### Резервирование файлов конкретных кешей

Используйте команду `--persistence backup caches` для резервирования файлов данных перечисленных кешей:

```bash
./control.sh --persistence backup caches cache1,cache2,cache3
```

где `cache1,cache2,cache3` — имена кешей через запятую.

### Дефрагментация

#### Запуск дефрагментации по расписанию

Используйте команду `--defragmentation schedule`, чтобы запланировать дефрагментацию PDS (Persistent Data Store):

```bash
./control.sh --defragmentation schedule --nodes consistentId0,consistentId1 [--caches cache1,cache2,cache3]
```

#### Статус дефрагментации

Используйте команду `--defragmentation status` для вывода статуса запущенной дефрагментации:

```bash
./control.sh --defragmentation status
```

#### Отмена дефрагментации

Используйте команду `--defragmentation cancel` для отмены запланированной или активной дефрагментации PDS (Persistent Data Store):

```bash
./control.sh --defragmentation cancel
```

### Сбор статистики

#### Запуск сбора статистики

Используйте команду `--performance-statistics start` для запуска сбора статистики:

```bash
./control.sh --performance-statistics start
```

#### Остановка сбора статистики

Используйте команду `--performance-statistics stop` для остановки сбора статистики:

```bash
./control.sh --performance-statistics stop
```

#### Ротация сбора статистики

Используйте команду `--performance-statistics rotate` для ротации сбора статистики:

```bash
./control.sh --performance-statistics rotate
```

#### Статус сбора статистики

Используйте команду `--performance-statistics status` для вывода статуса сбора статистики:

```bash
./control.sh --performance-statistics status
```

### Проверка согласованности данных

#### Проверка согласованности кешей

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--consistency repair` для проверки/восстановления согласованности кеша методом Read Repair:

```bash
./control.sh --consistency repair --cache cache --partitions partition --strategy LWW|PRIMARY|RELATIVE_MAJORITY|REMOVE|CHECK_ONLY [--parallel]
```

где:

-   `--cache <cache>` — имя кеша;
-   `--partitions <partition>` — партиции кешей;
-   `--strategy <LWW|PRIMARY|RELATIVE_MAJORITY|REMOVE|CHECK_ONLY>` — стратегия восстановления:

    -   `LWW` (Last Write Wins) — побеждает последняя (самая новая) запись;
    -   `PRIMARY` — побеждает значение, которое было получено с основной копии партиции;
    -   `RELATIVE_MAJORITY` — побеждает относительное большинство (самое часто встречающееся значение);
    -   `REMOVE` — несогласованные значения будут удалены, а несогласованные данные — утеряны;
    -   `CHECK_ONLY` — будет проведена только проверка согласованности;

-   `--parallel` — проверка на всех узлах параллельно.

#### Статус согласованности кешей

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--consistency status` для вывода статуса операции проверки/восстановления согласованности кеша:

```bash
./control.sh --consistency status
```

#### Установка значений счетчиков

:::{admonition} Важно
:class: attention

Экспериментальная команда.
:::

Используйте команду `--consistency finalize` для пересчета и установки корректного значения счетчиков после устранения расхождений:

```bash
./control.sh --consistency finalize
```

### Change Data Capture (CDC)

#### Удаление ссылок на WAL-сегменты

Используйте команду `--cdc delete_lost_segment_links` для удаления ссылок на удаленные WAL-сегменты, которые не были обработаны CDC:

```bash
./control.sh --cdc delete_lost_segment_links [--node-id node_id] [--yes]
```

где:

- `--node-id <node_id>` — идентификатор узла. Если значение не установлено, удаление ссылок будет выполнено на всех узлах;
- `--yes` — удаление ссылок без подтверждения операции.

#### Запись данных в WAL

Используйте команду `--cdc resend` для выполнения итерации по кешам и записи первичных копий записей данных в WAL для их дальнейшей обработки с помощью CDC:

```bash
./control.sh --cdc resend --caches cache1,...,cacheN
```

где `--caches cache1,...,cacheN` — список кешей.

### Распределение партиций

Используйте команду `--distribution`, чтобы распечатать текущее распределение партиций или различий между распределениями на установленной базовой топологии:

```bash
./control.sh --distribution [--caches cache1[,cache2,....,cacheN]] [--baseline consistentId1[:{attr1:val1[,...,attrN:valN]}][,...,consistentIdN[...]]]
```

где:

- `--caches cache1[,cache2,....,cacheN]` — список кешей. Если список кешей не установлен, информация будет собрана по всем кешам;
- `--baseline consistentId1[:{attr1:val1[,...,attrN:valN]}][,...,consistentIdN[...]]` — целевая базовая топология (список `consistent id` узлов и их атрибутов). Атрибуты узла будут заполнены неявно, если узел с таким `consistent id` уже существует в кластере. Атрибуты, которые явно указаны в параметре, перезапишут атрибуты из кластера. Если указан `baseline`, будет выведена разница между целевым базовым уровнем и текущим базовым уровнем.

### Работа с дампами

#### Снятие дампа кеша

Используйте команду `--dump create` для снятия дампа кеша/кеш-группы:

```bash
./control.sh --dump create --name name [--dest path] [--only-primary] [--compress] [--encrypt] [[--groups group1[,group2,....,groupN]]|[--in-memory-only]]
```

где:

-   `--name <name>` — имя дампа;
-   `--dest <path>` — путь к каталогу, в который будут сохраняться файлы дампа. Если путь не указан, по умолчанию будет использоваться каталог со снепшотами;
-   `--only-primary` — включить в дамп только primary-партиции;
-   `--compress` — сжать дамп;
-   `--encrypt` — зашифровать дамп;
-   `--groups group1[,group2,....,groupN]` — кеш-группы через запятую;
-   `--in-memory-only` — включать в дамп только не persistence-кеш-группы.

#### Проверка дампа кеша

Используйте команду `--dump check` для проверки целостности дампа кеша/кеш-группы:

```bash
./control.sh --dump check --name name [--src path]
```

где:

- `--name <name>` — имя дампа;
- `--src <path>` — путь к каталогу, в котором находятся файлы дампа. Если путь не указан, по умолчанию будет использоваться каталог со снепшотами.

## Команды плагина безопасности

Подробнее о плагине безопасности написано в подразделе [«Плагин безопасности для DataGrid»](administration-scenarios.md#плагин-безопасности-для-datagrid) раздела «Сценарии администрирования».

### Вывести справку по командам плагина безопасности

```bash
control.(sh|bat) --security-plugin help
```

### Создать пользователя

```bash
control.(sh|bat) --security-plugin users create [--user-password user_password] [--key key] [--salt salt] [--temp-secret] --user-login user_login [--dn distinguished_name] --roles role1[,role2,....,roleN] [--realm realm]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--user-password user_password` | Пароль пользователя. Используйте аргумент для указания секрета пользователя в виде текстового пароля |
| `--key key` | Ключ. Используйте совместно с аргументом `salt`, чтобы задать секрет пользователя, который основан на алгоритме PBKDF |
| `--salt salt` | Соль. Используйте совместно с аргументом `key`, чтобы задать секрет пользователя, который основан на алгоритме PBKDF |
| `--temp-secret` | Флаг, который указывает, что секрет пользователя является временным |
| `--user-login user_login` | Имя пользователя |
| `--dn distinguished_name` | DN (distinguished name) пользователя |
| `--roles role1[,role2,....,roleN]` | Роли пользователя |
| `--realm realm` | Имя Realm, в который будет добавлен пользователь |

### Удалить пользователя

```bash
control.(sh|bat) --security-plugin users delete --user-login user_login
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--user-login user_login` | Имя пользователя |

### Вывести пользователей

```bash
control.(sh|bat) --security-plugin users list [--logins login1[,login2,....,loginN]] [--format DEFAULT|PRETTY_JSON]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--logins login1[,login2,....,loginN]` | Разделенный запятыми список имен пользователей, которые должны быть выведены. Если не указан, будут выведены все пользователи |
| `--format DEFAULT\|PRETTY_JSON` | Формат вывода. `DEFAULT` выводит результат выполнения команды в одной строке в JSON-формате без форматирования. `PRETTY_JSON` выводит результат выполнения команды в валидном JSON-формате с применением форматирования |

### Обновить данные пользователя

```bash
control.(sh|bat) --security-plugin users update [--temp-secret] --user-login user_login [--user-password user_password] [--key key] [--salt salt] [--dn distinguished_name] [--roles role1[,role2,....,roleN]] [--realm realm]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--temp-secret` | Флаг, который указывает, что секрет пользователя является временным |
| `--user-login user_login` | Имя пользователя |
| `--user-password user_password` | Пароль пользователя. Используйте аргумент для указания секрета пользователя в виде текстового пароля |
| `--key key` | Ключ. Используйте совместно с аргументом `salt`, чтобы задать секрет пользователя, который основан на алгоритме PBKDF |
| `--salt salt` | Соль. Используйте совместно с аргументом `key`, чтобы задать секрет пользователя, который основан на алгоритме PBKDF |
| `--dn distinguished_name` | DN (distinguished name) пользователя |
| `--roles role1[,role2,....,roleN]` | Роли пользователя |
| `--realm realm` | Имя Realm, в который будет добавлен пользователь |

### Изменить пароль текущего аутентифицированного пользователя

```bash
control.(sh|bat) --security-plugin users change_password --old-password old_password --new-password new_password
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--old-password old_password` | Текущий пароль пользователя |
| `--new-password new_password` | Новый пароль |

### Создать роль

```bash
control.(sh|bat) --security-plugin roles create [--permissions permission1[,permission2,....,permissionN]] [--conflict-permissions conflict_permission1[,conflict_permission2,....,conflict_permissionN]] [--name name]|[--json-input json_input]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--permissions permission1[,permission2,....,permissionN]` | Разрешения роли |
| `--conflict-permissions conflict_permission1[,conflict_permission2,....,conflict_permissionN]` | Разрешения, которые не могут быть даны пользователю с текущей ролью |
| `--name name` | Имя роли |
| `--json-input json_input` | Дескриптор роли в JSON-формате |

### Вывести список ролей

```bash
control.(sh|bat) --security-plugin roles list [--format DEFAULT|PRETTY_JSON] [--names name1[,name2,....,nameN]]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--format DEFAULT\|PRETTY_JSON` | Формат вывода. `DEFAULT` выводит результат выполнения команды в JSON-формате без форматирования. `PRETTY_JSON` выводит результат выполнения команды в валидном JSON-формате с применением форматирования |
| `--names name1[,name2,....,nameN]` | Разделенный запятыми список имен ролей, которые должны быть выведены. Если не указан, будут выведены все роли |

### Изменить роль

```bash
control.(sh|bat) --security-plugin roles update [--permissions permission1[,permission2,....,permissionN]] [--conflict-permissions conflict_permission1[,conflict_permission2,....,conflict_permissionN]] [--name name]|[--json-input json_input]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--permissions permission1[,permission2,....,permissionN]` | Разрешения роли |
| `--conflict-permissions conflict_permission1[,conflict_permission2,....,conflict_permissionN]` | Разрешения, которые не могут быть даны пользователю с текущей ролью |
| `--name name` | Имя роли |
| `--json-input json_input` | Дескриптор роли в JSON-формате |

### Удалить роль

```bash
control.(sh|bat) --security-plugin roles delete --name name
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--name name` | Имя роли |

### Вывести актуальные данные плагина безопасности

```bash
control.(sh|bat) --security-plugin storage export [--format DEFAULT|PRETTY_JSON]
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--format DEFAULT\|PRETTY_JSON` | Формат вывода. `DEFAULT` выводит результат выполнения команды в одной строке в JSON-формате без форматирования. `PRETTY_JSON` выводит результат выполнения команды в валидном JSON-формате с применением форматирования |

### Обновить данные плагина безопасности

```bash
control.(sh|bat) --security-plugin storage import --file-path file_path
```

**Параметры:**

| Параметр | Описание |
|---|---|
| `--file-path file_path` | Путь к файлу с данными в JSON-формате, которые предназначены для импорта в плагин безопасности |