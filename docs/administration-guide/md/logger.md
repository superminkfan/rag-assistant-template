# Логирование событий

Для логирования событий DataGrid поддерживает следующие библиотеки и фреймворки:

-   JUL (используется по умолчанию);
-   Log4j2;
-   JCL;
-   SLF4J.

При запуске узла он выводит в консоль начальную информацию, в том числе информацию о сконфигурированной библиотеке логирования. Каждая библиотека логирования имеет собственные параметры конфигурации и должна настраиваться согласно официальной документации этой библиотеки. Помимо собственных параметров конфигурации каждой отдельной библиотеки существуют следующие параметры, которые позволяют дополнительно настроить логирование:

:::{list-table}
:header-rows: 1
 
+   *   Системное свойство
    *   Описание
    *   Значение по умолчанию
+   *   `IGNITE_LOG_INSTANCE_NAME`
    *   Если данное свойство имеет значение `set`, DataGrid включает в логи название своего экземпляра
    *   Не задано
+   *   `IGNITE_QUIET`
    *   При значении `false` отключает "тихий" и включает расширенный (verbose) режим. В режиме verbose узел записывает в логи больше информации
    *   `true`
+   *   `IGNITE_LOG_DIR`
    *   Директория для записи log-файлов Datagrid
    *   `$IGNITE_HOME/ work/log`
+   *   `IGNITE_DUMP_THREADS_ON_FAILURE` 
    *   При значении `true` данное свойство выдает в логах дампы потоков при появлении критической ошибки
    *   `true`
+   *   `IGNITE_SENSITIVE_DATA_LOGGING`
    *   - `plain` (true) — выводит данные «как есть»;
        - `hash` — выводит хеш (примитивы выводятся «как есть»);
        - `none` — (false) не выводит ничего
    *   `hash`
:::

## Логирование по умолчанию (JUL)

По умолчанию DataGrid использует фреймворк `java.util.logging` (JUL). Если DataGrid запускается с использованием скрипта `ignite.sh|bat` из дистрибутива, то по умолчанию в качестве файла конфигурации используется `$IGNITE_HOME/config/java.util.logging.properties`, выдающий все сообщения в log-файлах в директории `$IGNITE_HOME/work/log`. Директория, используемая по умолчанию, может быть изменена при помощи системного свойства `IGNITE_LOG_DIR`.

При использовании DataGrid в приложении в качестве библиотеки, конфигурация логирования, используемая по умолчанию, включает в себя только обработчик консоли на уровне **INFO**. Собственный файл конфигурации можно использовать, изменив системное свойство `java.util.logging.config.file`.

## Log4j2

:::{admonition} Внимание
:class: danger

Чтобы использовать Log4j2, необходимо подключить модуль **ignite-log4j2**.
:::

Для включения Log4j2 сконфигурируйте свойство `gridLogger` класса `IgniteConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML (указывается в `$IGNITE_HOME/config/serverExampleConfig.xml`)
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="gridLogger">
        <bean class="org.apache.ignite.logger.log4j2.Log4J2Logger">
            <!-- Конфигурационный файл log4j2. -->
            <constructor-arg type="java.lang.String" value="ignite-log4j2.xml"/>
        </bean>
    </property>

    <!-- Прочие свойства. -->

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

IgniteLogger log = new Log4J2Logger("ignite-log4j2.xml");

cfg.setGridLogger(log);

// Запустите узел.
try (Ignite ignite = Ignition.start(cfg)) {
    ignite.log().info("Info Message Logged!");
}
```
:::
::::

где `ignite-log4j2.xml` — конфигурационный файл логера log4j2 (смотри [пример файла](./resources/ignite-log4j2.xml)).

Путь к `ignite-log4j2.xml` может быть как абсолютным, так и локальным относительным путем к META-INF в `classpath` или к `IGNITE_HOME`. Пример файла конфигурации log4j2 можно найти в дистрибутиве (`$IGNITE_HOME/config/ignite-log4j2.xml`).

:::{admonition} Примечание
:class: note

Настройку уровней логирования и других параметров логирования производит администратор ОС или DevOps-инженер.
:::

### Настройка уровней логирования

Уровни логирования настраиваются в конфигурационном файле логера `ignite-log4j2.xml` в блоке `<Loggers>`. 

Фрагмент конфигурационного файла логера с уровнями логирования:

:::{code-block} xml
:caption: XML
<Loggers>
    <Logger name="org.eclipse.jetty.util.log" level="ERROR"/>
    <Logger name="org.eclipse.jetty.util.component" level="ERROR"/>
    <Logger name="com.amazonaws" level="WARN"/>
    <Logger name="org.apache.ignite" level="INFO" additivity="false">
            <appender-ref ref="IGNITE"/>
    </Logger>
    ...
    <Logger name="com.sbt.ignite" level="INFO" additivity="false">
        <AppenderRef ref="IGNITE"/>
    </Logger>
    ...
    </Loggers>
:::

где 

-   `org.eclipse.jetty.util.log`, `org.eclipse.jetty.util.component`, `com.amazonaws`, `org.apache.ignite` – классы, для которых будут генерироваться события;
-   `INFO`, `WARN`, `ERROR` — уровни логирования событий.

### Настройка пути для хранения системного журнала (log-файла)

Путь к log-файлу указывается в конфигурационном файле логера в формате:

:::{code-block} xml
:caption: XML
<Routing name="IGNITE">
    <Routes pattern="$${sys:nodeId}">
        <Route>
            <RollingFile name="Rolling-${sys:nodeId}" fileName="/opt/ignite/server/logs/${sys:appId}.log" filePattern="/opt/ignite/server/logs/${sys:appId}-${sys:nodeId}-%i-%d{yyyy-MM-dd}.log.gz">
                <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss.SSS} [%-5level][%t][%logger{36}] %msg%n"/>
                <Policies>
                    <TimeBasedTriggeringPolicy interval="1" modulate="true" />
                </Policies>
            </RollingFile>
        </Route>
    </Routes>
</Routing>
:::

где `fileName` — путь к log-файлу.

:::{admonition} Примечание
:class: note

Log4j2 поддерживает изменение конфигурации в ходе работы. Таким образом, изменения в файле конфигурации применяются без необходимости перезапуска приложения.
:::

Подробную информацию по логеру log4j2 — см. [офицальную документацию log4j](https://logging.apache.org/log4j/).

## JCL

:::{admonition} Внимание
:class: danger

Чтобы использовать JCL, необходимо подключить модуль **ignite-jcl**.
:::

JCL лишь пересылает log-сообщения в соответствующую систему логирования, которая должна быть настроена должным образом. Например, для использования Log4j2 убедитесь, что необходимые библиотеки добавлены в свой classpath.

Более подробная информация приведена в [официальной документации JCL](https://commons.apache.org/proper/commons-logging/guide.html#Configuration).

Для включения JCL сконфигурируйте свойство `gridLogger` класса `IgniteConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML (указывается в `$IGNITE_HOME/config/serverExampleConfig.xml`)
```xml

<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="gridLogger">
        <bean class="org.apache.ignite.logger.jcl.JclLogger">
        </bean>
    </property>

    <!-- Прочие свойства. -->

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setGridLogger(new JclLogger());

// Запустите узел.
try (Ignite ignite = Ignition.start(cfg)) {
    ignite.log().info("Info Message Logged!");
}
```
:::
::::

## SLF4J

:::{admonition} Внимание
:class: danger

Чтобы использовать SLF4J, необходимо подключить модуль **ignite-slf4j**.
:::

Для включения SLF4J сконфигурируйте свойство `gridLogger` класса `IgniteConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML (указывается в `$IGNITE_HOME/config/serverExampleConfig.xml`)
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="gridLogger">
        <bean class="org.apache.ignite.logger.slf4j.Slf4jLogger">
        </bean>
    </property>

    <!-- Прочие свойства. -->

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setGridLogger(new Slf4jLogger());

// Запустите узел.
try (Ignite ignite = Ignition.start(cfg)) {
    ignite.log().info("Info Message Logged!");
}
```
:::
::::

Более подробная информация приведена в [официальной документации SLF4J](https://www.slf4j.org/docs.html).

## Скрытие конфиденциальной информации в log-файлах

В log-файлах может отражаться содержание кеш-записей, системных свойств, настроек запуска и прочая информация, которая в некоторых случаях может быть конфиденциальной. Отображение такой информации в log-файлах можно отключить, установив значение системного свойства `IGNITE_TO_STRING_INCLUDE_SENSITIVE = false`.

:::{admonition} Пример команды
:class: hint

```bash
./ignite.sh -J-DIGNITE_TO_STRING_INCLUDE_SENSITIVE=false`
```
:::

Более подробная информация приведена в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/starting-nodes#setting-jvm-options).

## Пример конфигурации логирования

Для конфигурации логирования:

1. Включите Log4j2, как описано в разделе [Log4j2](#log4j2).
2. При использовании стандартного файла конфигурации (`ignite-log4j2.xml`) раскомментируйте appender `CONSOLE`.
3. В файле конфигурации log4j2 укажите путь к log-файлу. По умолчанию log-файлы сохраняются в директорию `${IGNITE_HOME}/work/log/ignite.log`.
4. Запустите узлы в verbose-режиме:

    -   при использовании утилиты `ignite.sh` для запуска узлов — добавьте ключ `-v`;
    -   если запуск узлов производится из Java-кода — используйте системную переменную `IGNITE_QUIET=false`.
