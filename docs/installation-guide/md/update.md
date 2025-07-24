# Обновление

Обновление производится с помощью находящейся в дистрибутиве ansible-роли.  Подробнее процесс обновления описан в [разделе «Установка DataGrid с помощью Ansible»](./ansible-role-datagrid.md) текущего документа.

## Обновление ролевой модели

### Обновление ролевой модели на версию 15.0

В версии DataGrid 15.0 добавлено новое право `ADMIN_CLUSTER_STATE`, которое позволяет управлять состоянием кластера. Подробнее в разделе [«Ролевая модель в DataGrid»](../../administration-guide/md/role-model.md) документа «Руководство по системному администрированию».

При обновлении DataGrid на версию 15.0:

- для миграции in-memory-кластеров — добавьте право `ADMIN_CLUSTER_STATE` в конфигурационный файл `default-security-data.json` согласно ролевой модели;
- для миграции Persistence-кластеров — перед активацией загрузите новую ролевую модель с помощью команды:

    ```bash
    ise-user-control.(sh|bat) load-security-model --file-path <путь к JSON-файлу с новой ролевой моделью>
    ```

  Подробнее об утилите `ise-user-control` в документе [«Руководство по системному администрированию», раздел «Утилита ise-user-control для управления пользователями»](../../administration-guide/md/user-control.md).

## Обновление зависимостей

### Обновление зависимостей на версию 15.0

В версии DataGrid 15.0 в связи с исключением зависимости `ignite-indexing` из модуля `ignite-spring`при условии использовании SQL и получении зависимости через maven необходимо проверить, что в pom-файле явно присутствует зависимость на один из SQL-движков (`ignite-indexing` или `ignite-calcite`).

## Обновление с версий 4.2130 и более ранних

В DataGrid до версии 14.0 значение `CompactFooter` для тонкого клиента по умолчанию — `false`. Начиная с версии 14.0 значение по умолчанию берется из конфигурации серверного узла. Поэтому перед обновлением на версию 14.0 и выше с предыдущих версий необходимо проверить, какое значения установлено для параметра `CompactFooter` на серверных узлах (СУ) и на тонких клиентах.

:::{admonition} Внимание
:class: danger

Данный раздел актуален при соблюдении условий:

- кластер до обновления настроен на работу с PDS, после обновления не планируется повторная загрузка данных;
- с кластером работают тонкие клиенты разных версий — до версии 4.2131 и начиная с 4.2131.
:::

Если значения `CompactFooter`:

-   для СУ – `true` и для тонкого клиента – `true` *(рекомендуемые значения)*, то никаких действий предпринимать не требуется;
-   для СУ – `true` и для тонкого клиента – `false`, то необходимо на стороне тонкого клиента установить `ClientConfiguration#setAutoBinaryConfigurationEnabled(false)`. Рекомендуется изменить значение `CompactFooter` для тонкого клиента на `true`;
-   для CУ – `false` и для тонкого клиента – `true`, то необходимо на стороне тонкого клиента установить `ClientConfiguration#setAutoBinaryConfigurationEnabled(false)`. Рекомендуется изменить значение `CompactFooter` для СУ на `true`;
-   для CУ – `false` и для тонкого клиента – `false`, то никаких действий предпринимать не требуется. Рекомендуется изменить значение `CompactFooter` для СУ и тонкого клиента на `true`.

При одновременной работе разных версий клиента с одним кластером нужно добиться того, чтобы версия `CompactFooter` на тонких клиентах была одной и той же, с учетом того, что значение по умолчанию может измениться после обновления на версию 13.1 и выше.

## Обновление персистентных кластеров с версии Ignite SE 3.280 в случае использования плагина безопасности

Плагин безопасности в Ignite SE 3.280 использует `ignite-sys-cache` для сохранения учетных данных пользователей. При обновлении данный кеш требуется удалить во избежание аварийных ситуаций из-за ошибок несовместимости.

Причина проблемы: при миграции со старого плагина безопасности системный кеш не был очищен.

Без очистки `ignite-sys-cache` возможно появление ошибки `B+Tree is corrupted` с `Failed to find class with given class loader for unmarshalling (make sure same versions of all classes are available on all nodes or enable peer-class-loading)`:

```text
YYYY-MM-DD 09:26:06.937 [ERROR][rebalance-striped-#189][] Critical system error detected. Will be handled accordingly to configured handler [hnd=StopNodeFailureHandler [super=AbstractFailureHandler [ignoredFailureTypes=UnmodifiableSet []]], failureCtx=FailureContext [type=CRITICAL_ERROR, err=class o.a.i.i.processors.cache.persistence.tree.CorruptedTreeException: B+Tree is corrupted [groupId=-2100569601, pageIds=[], msg=Runtime failure on bounds: [lower=null, upper=null]]]]
org.apache.ignite.internal.processors.cache.persistence.tree.CorruptedTreeException: B+Tree is corrupted [groupId=-2100569601, pageIds=[], msg=Runtime failure on bounds: [lower=null, upper=null]]
...
Caused by: org.apache.ignite.internal.processors.cache.persistence.tree.BPlusTreeRuntimeException: class org.apache.ignite.IgniteException: Failed to unmarshal object with optimized marshaller
...
Caused by: org.apache.ignite.internal.marshaller.optimized.OptimizedMarshallerInaccessibleClassException: Failed to find class with given class loader for unmarshalling (make sure same versions of all classes are available on all nodes or enable peer-class-loading) [clsLdr=jdk.internal.loader.ClassLoaders$AppClassLoader@2c13da15, cls=Failed to resolve class name [platformId=0, platform=Java, typeId=-201039783]]
...
Caused by: java.lang.ClassNotFoundException: Failed to resolve class name [platformId=0, platform=Java, typeId=-201039783]
...
```

В примере выше `groupId=-2100569601` соответствует системному кешу `ignite-sys-cache`.