# Change Data Capture (CDC)

Change Data Capture (CDC) — механизм, который предназначен для асинхронной передачи измененных данных с целью дальнейшей обработки.

Подробнее о CDC написано в документе «Руководство по системному администрированию»:

- алгоритм работы механизма, конфигурация, метрики, логирование и жизненный цикл `ignite-cdc.sh` описаны в подразделе «Механизм Change Data Capture (CDC) и межкластерная репликация» раздела [«Сценарии администрирования»](../../administration-guide/md/administration-scenarios.md);
- конфигурация и режимы работы плагина `cdc-manager-plugin` описаны в разделе [«Плагин для работы CDC в реальном времени»](../../administration-guide/md/cdc-manager-plugin.md);
- команды администрирования CDC описаны в подразделе «Change Data Capture (CDC)» раздела [«Утилита control»](../../administration-guide/md/control-sh.md);
- режим восстановления `--for-cdc` описан в разделе [«Плагин для работы с кеш-дампами»](../../administration-guide/md/ignite-dump-reader.md);
- примеры сообщений в log-файлах при работе CDC описаны в подразделе «Логи при работе CDC» раздела [«Первичный анализ логов»](../../administration-guide/md/primary-analysis-of-logs.md);
- процесс контроля репликации кластера (CDC) описан в разделе [«Использование Zabbix и Grafana для мониторинга»](../../administration-guide/md/zabbix-and-grafana.md).

Типичные проблемы при работе CDC и их решения описаны в документе [«Часто встречающиеся проблемы и пути их устранения»](../../troubleshooting-and-performance/md/faq.md) в разделе «Проблемы при работе CDC».