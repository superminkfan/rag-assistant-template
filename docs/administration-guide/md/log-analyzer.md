# Утилита DataGrid Log Analyzer

Log Analyzer — скрипт для автоматического анализа логов кластера DataGrid, который работает в режиме [сканирования логов](#режим-log-scanner) по определенным параметрам и записывает результаты в текстовые файлы.

:::{info} Будущие обновления

В будущих версиях планируется расширить режимы работы скрипта.
:::

## Режим Log Scanner

### Настройка

#### Основной конфигурационный файл

Имя по умолчанию: `run_conf.yml`.

Можно создать пользовательский файл: нет.

Путь: должен находиться в директории скрипта запуска — `$IGNITE-LOG-ANALYZER/utils/ignite-log-analyzer/bin/log-analyzer.sh`.

**Параметры:**

| Название | Обязательность | Тип поля | Описание | Шаблон значения | Значение по умолчанию |
|---|---|---|---|---|---|
| `logs_directory_path` | Да | String | Путь к директории с логами, которые необходимо просканировать | `/opt/logdir/` | — |
| `output_directory_path` | Нет | String | Путь к директории с результатами сканирования | `/opt/resultdir/` | Директория с логами |
| `output_directory_name` | Да | String | Имя директории с результатами сканирования | `resultscan` | — |
| `search_conf_path` | Нет | String | Путь к директории с файлом конфигурации сканирования | `configdir/` | `$IGNITE-LOG-ANALYZER/resources/search_conf.yml` |
| `search_conf_name` | Нет | String | Имя файла конфигурации сканирования | `custom_search_conf.yml` | `search_conf.yml` |
| `is_debug_enabled` | Нет | Boolean | Флаг включения `DEBUG`-режима в логгере | `TRUE` | `FALSE` |
| `threads_count` | Нет | Integer | Количество потоков для работы скрипта | `2` | `Количество ядер процессора * 1,25` |

#### Файл конфигурации сканирования

Имя по умолчанию: `search_conf.yml`.

Можно создать пользовательский файл: да, подробнее о создании пользовательского файла написано в таблице выше (параметр `search_conf_name`).

Путь: определяется параметром `search_conf_path` (подробнее о нем написано в таблице выше). По умолчанию — директория скрипта запуска (`$IGNITE-LOG-ANALYZER/utils/ignite-log-analyzer/bin/log-analyzer.sh`).

:::{code-block} yaml
:caption: Формат файла

name: assertion_error
log: ignite
level:
include: AssertionError
exclude:
time: YYYY-MM-DD 00:0[0-1]
---
name: warnings_no_big_results_no_unknown_plugin
log: ignite
level: WARN
include:
exclude: Query produced big result set & Received discovery data for unknown plugin
time: 
---
name: safepoint_pauses
log: safepoint
level:
include: 'Total time for which application threads were stopped: [1-9]+.[0-9]+'
exclude:
time:
:::

Каждая проверка состоит из следующих полей:

| Название | Обязательность | Описание |
|---|---|---|
| `name` | Да | Название проверки, которое также используется в качестве имени текстового файла, куда записываются результаты данной проверки |
| `log` | Да | Логи, в которых необходимо производить данную проверку. Указывать полное имя лога необязательно, можно указать только его начало — `ignite`, `gc`, `safepoint` и так далее |
| `level` | Нет | Необходимый уровень логирования. Если его не указать, будут проверяться все записи |
| `include` | Нет | Конкретная ошибка или событие, которые необходимо найти. В одной проверке можно задать сразу несколько событий, разделив их символом `&` |
| `exclude` | Нет | Ошибка или событие, которые нужно исключить из проверки. Например, нужно получить все записи уровня логирования `WARN`, но при этом исключить из данной выборки ошибки `Query produced big result set` и `Received discovery data for unknown plugin` (подробнее указано в примере выше) |
| `time` | Нет | Временной отрезок, внутри которого необходимо производить данную проверку. Задается в виде регулярного выражения (подробнее указано в примере выше) |

Поля `name` и `log` являются обязательными. Также для работы скрипта должно быть заполнено одно из следующих полей: `level`, `include`, `exclude`. Если требование по заполнению обязательный полей проверки не выполняется, она исключается из процедуры сканирования.

Параметры `level`, `include`, `exclude` и `time` могут сочетаться друг другом. В одной проверке можно установить уровень логирования, события для включения в выборку, события для исключения из выборки и временной промежуток сканирования. По правилам синтаксиса YAML проверки в конфигурационном файле отделяются друг от друга разделителем `---`.

В полях `include`, `exclude` и `time` используются регулярные выражения.

:::{admonition} Важно
:class: attention

Регулярные выражения, которые используются в полях `include`, `exclude` и `time`, должны оформляться соответствующим образом. Это подразумевает необходимость экранировать специальные символы. 

Например, выражение вида:

```yaml
Log message (additional information)
```

которое поместили в поле `include`, не будет использоваться для поиска соответствующих строк в логах, так как в нем имеются незаэкранированные символы `(` и `)`. Чтобы поиск по данному выражению сработал, экранируйте указанные символы следующим образом:

```yaml
Log message \(additional information\)
```
:::

Пользователь может добавлять в конфигурационный файл собственные проверки, для этого нужно заполнить указанные выше параметры по своему усмотрению. Если какие-либо проверки не нужны, их можно убрать с помощью комментария (символ `#`). Также можно подготовить для работы несколько конфигурационных файлов с разными наборами проверок и при необходимости указывать нужный в основном файле.

### Запуск скрипта

Для работы скрипта в одной директории должны находиться следующие файлы:

- JAR-файл (например, `ignite-log-analyzer-1.0.0-shaded.jar`);
- скрипт запуска (`log-analyer.sh` или `log-analyer.bat`);
- основной конфигурационный файл `run_conf.yml`;
- файл конфигурации сканирования `search_conf.yml`.

Чтобы запустить скрипт из командной строки, используйте команду с параметром `--scan`:

```yaml
$log-analyer.sh --scan
```

Скрипт выполнит анализ логов, используя параметры из заполненного файла `search_conf.yml`.

Для получения информации о скрипте запустите его с параметром `--help`:

```yaml
$log-analyer.sh --help
```

### Варианты работы скрипта

Скрипт может сканировать логи одного узла и всего кластера. Для сканирования логов всего кластера в параметре `logs_directory_path` укажите путь к директории, в которой находятся поддиректории с логами всех узлов кластера. В данном варианте имена поддиректорий будут использоваться в качестве названий узлов (то есть дополнительно к имени лога добавится путь, по которому он находится относительно заданного пути для сканирования). 

### Результат работы скрипта

В директории, которая задана параметрами `output_directory_path` и `output_directory_name`, будут созданы файлы с результами соответствующей проверки. Имя файла определяется параметром `name` из файла конфигурации сканирования для конкретной проверки. Если поиск по какой-либо проверке не дал результатов, соответствующий файл не создается.

:::{admonition} Пример вывода результатов работы скрипта в режиме сканирования логов кластера (файл `PME_started.txt`)
:class: hint
:collapsible:

```yaml
NODE HOST_01

/host_01/ignite.log: YYYY-MM-DD 03:04:19.849 [INFO ][exchange-worker-#74][org.apache.ignite.internal.exchange.time] Started exchange init [...]

NODE HOST_02

/host_02/ignite.log: YYYY-MM-DD 03:03:22.318 [INFO ][exchange-worker-#76][org.apache.ignite.internal.exchange.time] Started exchange init [...]
/host_02/ignite.log: YYYY-MM-DD 12:20:30.714 [INFO ][exchange-worker-#76][org.apache.ignite.internal.exchange.time] Started exchange init [...]

NODE HOST_03

/host_03/ignite.log: YYYY-MM-DD 03:03:22.323 [INFO ][exchange-worker-#76][org.apache.ignite.internal.exchange.time] Started exchange init [...]
/host_03/ignite.log: YYYY-MM-DD 12:20:30.724 [INFO ][exchange-worker-#76][org.apache.ignite.internal.exchange.time] Started exchange init [...]
```
:::

Формат записи результирующего файла:

- Название узла заглавными буквами.
- Все записи, найденные согласно текущей проверке на данном узле. Каждая запись состоит из: 
   - относительного пути к логу, в котором была найдена данная строка;
   - самой строки, отделенной от пути двоеточием и пробелом.

### Логирование

Логгер скрипта не записывает лог в виде отдельного текстового файла, но выводит в консоль информацию вида:

:::{admonition} Пример
:class: hint 
:collapsible:

```yaml
# Сообщение о запуске скрипта.
15:14:34.560 [INFO] Log scanner started. 

# Вывод параметров, заданный в файле `run_conf.yml`.
15:14:34.626 [INFO] Logs directory path: /home/usr/NEWLOGS 

# Вывод параметров, заданный в файле `run_conf.yml`.
15:14:34.631 [INFO] Search configuration path: /home/usr/test/search_conf.yml

# Вывод параметров, заданный в файле `run_conf.yml`.
15:14:34.631 [INFO] Output directory path: /home/usr/NEWLOGS/scan_results

# Вывод параметров, заданный в файле `run_conf.yml`.
15:14:34.631 [INFO] Is debug enabled: true

# Вывод параметров, заданный в файле `run_conf.yml`.
15:14:34.631 [INFO] Threads count: 15

# Сообщение об ошибке в конфигурации той или иной проверки.
15:14:34.652 [WARN] Search configuration for check "assertion_error" is invalid. Check cancelled.

# Сообщение о начале процедуры сканирования с указанием количества запланированных проверок.
15:14:34.680 [INFO] Scan procedure initiated (41 checks scheduled)...
...
# Сообщение о начале конкретной проверки.
15:14:34.692 [INFO] Processing check "start_in_maintenance_mode"...
...
# Сообщение об отсутствии в заданной директории поиска указанных в проверке типов лог-файлов.
15:14:34.693 [WARN] No files found for the "gc_pauses_gt_01s" check. Check cancelled.
...
# Сообщение о начале обработки конкретного файла в рамках проверки (только в `DEBUG`-режиме).
15:14:34.715 [DEBUG] >>> Check "failed_to_send_class_loading" >>> Searching file /home/usr/NEWLOGS/node01/ignite.log
...
# Сообщение об окончании обработки конкретного файла в рамках проверки (только в `DEBUG`-режиме).
15:14:36.346 [DEBUG] <<< Check "errors" <<< File searched: /home/usr/NEWLOGS/node01/ignite.log
...
# Сообщение об окончании процесса сканирования по определенной проверке с отсутствием результата.
15:14:37.654 [INFO] Check "rebalance_started" completed, no occurrences found.
...
# Сообщение об окончании процесса сканирования по определенной проверке с наличием результата.
15:14:42.208 [INFO] Check "PME_started" completed, results written to file.
...
# Сообщение о завершении процедуры сканирования с указанием ее длительности.
15:14:53.857 [INFO] Scan procedure finished, total time: 19 seconds
```
:::

Если в процессе работы скрипта происходит ошибка, выводится соответствующее сообщение. Например, если в основном конфигурационном файле есть ошибка заполнения параметров, при запуске скрипта выведется подобное сообщение:

```yaml
09:16:56.347 [INFO] Log scanner started.
09:02:26.903 [INFO] Logs directory path: /home/usr/NEWLOGS_WRONG
09:02:26.908 [INFO] Search configuration path: /home/usr/test/search_conf.yml
09:02:26.908 [INFO] Output directory path: /home/usr/NEWLOGS_WRONG/scan_results
09:16:56.426 [ERROR] Logs directory doesn't exist: "/home/usr/NEWLOGS_WRONG"
```

Возможные ошибки:

- `Logs directory doesn't exist` — директория с логами не найдена.
- `Logs directory is not a directory` — путь ведет не к директории.
- `Logs directory is empty` — указаный путь к логам ведет к пустой директории.
- `Failed to create output directory` — не удается создать директорию для отчета.
- `Search configuration for check search_conf.yml is invalid. Check cancelled` — некоректная конфигурация файла со списком проверок.
- `No checks found in the search config file` — файл со списком проверок пуст.