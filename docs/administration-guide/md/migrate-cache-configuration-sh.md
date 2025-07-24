# Утилита migrate-cache-configuration.sh

В дистрибутив DataGrid входит консольная утилита, предназначенная для миграции конфигураций кешей на кластер DataGrid — Cache Configurations Migration Tool. Утилита сравнивает текущую конфигурацию кешей кластера с новой, создает недостающие кеши, индексы и поля.

Утилита Cache Configurations Migration Tool поддерживает Spring XML-конфигурацию кешей и предоставляет функциональности:

- создание новых кешей;
- создание новых таблиц;
- создание полей в таблицах;
- удаление полей в таблицах;
- создание новых индексов.

## Сборка утилиты

Выполните следующую команду для сборки утилиты:

`mvn clean install -Dmaven.test.skip=true`

Результат сборки — архив `target/ignite-migrate-cache-configuration.zip`.

## Конфигурация утилиты

Перед запуском конфигурации утилиты: 

1. Разместите скрипт `mirgate-cache-configuration.sh` в каталоге `IGNITE_HOME/bin/migrate-cache-configuration.sh`.
2. Убедитесь в том, что в `classpath` на всех узлах кластера присутствует каталог `libs/ignite-migrate-cache-configuration`.

Утилита использует `IgniteLogger` из конфигурации клиентского узла для логирования и логируется в отдельный файл как отдельное приложение `migrate-cache-configuration`.

### Конфигурирование JVM-опций

JVM-параметры можно задать:

- переменной окружения `MIGRATE_CACHE_CFG_JVM_OPTS`:

    ```bash
    export MIGRATE_CACHE_CFG_JVM_OPTS="-Dgroup.id=test_group_id -Dnode.id=test_node_id -Dmodule.id=igniteSE -Dconfig-store.disabled=False"
    ```

- при инициализации клиентского узла в XML-конфигурации (указывается в `serverExampleConfig.xml`):

    :::{code-block} xml
    :caption: XML
    <!-- Добавьте свойство 'depends-on' к beans, которые работают с системными переменными. -->
    <bean id="igniteConfigurator" class="com.sbt.core.commons.config_spring.PlatformPlaceholderConfigurer" depends-on="addSystemProperties">
       ...
    </bean>
    <!-- Конфигурирование системных переменных. -->
    <bean id="systemProperties" class="java.lang.System" factory-method="getProperties"/>

    <bean id="addSystemProperties" class="org.springframework.beans.factory.config.MethodInvokingFactoryBean">
        <property name="targetObject" ref="systemProperties" />
        <property name="targetMethod" value="putAll" />
        <property name="arguments">
            <util:map map-class="java.util.HashMap">
                <entry key="group.id" value="test_group_id"/>
                <entry key="node.id" value="test_node_id"/>
                <entry key="module.id" value="igniteSE"/>
                <entry key="config-store.disabled" value="False"/>
            </util:map>
        </property>
    </bean>
    :::

## Использование утилиты

Синтаксис команды:

`migrate-cache-configuration.sh <Путь к XML-конфигурации клиентского узла> <Путь к XML-конфигурации кешей> [--migrate] [--help]`

Запуск без ключей выводит информацию об изменениях режиме «read-only».

Описание параметров:

-   `Ignite Cfg Path` — путь к XML-конфигурации клиентского узла;
-   `Caches Cfg Path` — путь к XML-конфигурации кешей.

Описание ключей:

-   `--help` — вывод справочной информации;
-   `--migrate` — запуск для миграции конфигурации кешей на кластер DataGrid.

Вывод утилиты Cache Configurations Migrate Tool содержит информацию:

-   конфигурацию кластера до вызова утилиты;
-   вычисленные изменения;
-   произведенные действия;
-   конфигурацию кластера после вызова утилиты.

## Пример вывода утилиты

Вывод утилиты при выполнении команды миграции `migrate-cache-configuration.sh <Путь к XML-конфигурации клиентского узла> <Путь к XML-конфигурации кешей> [--migrate]`:

:::{code-block} xml
:caption: XML
...
Cluster info before migration:
...
Cache configurations changes:
New caches:
[cacheName=new-cache1]
[cacheName=new-cache2]
Table changes [cacheName=test-static-cache, tableName=test-static-cache]
Dropped fields:
[name=ORGID]
New fields:
[name=name, type=java.lang.String]
New indexes:
[indexName=PERSON_NAME_ASC_IDX]
[indexName=PERSON_ID_ASC_NAME_ASC_IDX]
...
New caches created [cacheNames=[new-cache1, new-cache2]]
Executed SQL [sql=ALTER TABLE PERSON DROP COLUMN IF EXISTS "ORGID"]
Executed SQL [sql=ALTER TABLE PERSON ADD COLUMN IF NOT EXISTS "NAME" VARCHAR]
Executed SQL [sql=CREATE INDEX IF NOT EXISTS PERSON_NAME_ASC_IDX ON PERSON ("name" ASC)]
Executed SQL [sql=CREATE INDEX IF NOT EXISTS PERSON_ID_ASC_NAME_ASC_IDX ON PERSON ("id" ASC, "name" ASC)]
...
Cluster info after migration:
...
:::

где:

-   `cacheName=new-cache1` — имя/имена новых кешей;
-   `tableName=test-static-cache` — имена новых таблиц;
-   `name=name, type=java.lang.String` — имена и типы новых полей в таблицах;
-   `indexName=PERSON_NAME_ASC_IDX` — имена новых новых индексов.