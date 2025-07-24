# Быстрый старт

Руководство по первому запуску DataGrid.

:::{admonition} Примечание
:class: note

Информация по установке указана в документе [«Руководство по установке»](../../installation-guide/md/index.md).
:::

## Запуск узла

Запустить узел можно из командной строки с помощью конфигурации по умолчанию. Также можно добавить в директорию DataGrid пользовательский файл конфигурации.

Можно запускать несколько узлов сразу. Они автоматически обнаружат друг друга.

Для запуска узла:

1. Из командной строки перейдите в папку `bin` в установочной директории DataGrid. Примеры команды входа:

    ```bash
    cd {IGNITE_HOME}/bin/
    ```

2. Запустите узел. Передайте пользовательский файл конфигурации в `ignite.sh|bat` в качестве параметра, например:

    ```bash
    ./ignite.sh ../examples/config/example-ignite.xml `
    ```

    После запуска узла появится следующий вывод:

    ```bash
    [08:53:45] Ignite node started OK (id=7b30bc8e) [08:53:45] Topology snapshot [ver=1, locNode=7b30bc8e, servers=1, clients=0, state=ACTIVE, CPUs=4, offheap=1.6GB, heap=2.0GB]
    ```

3. Откройте новое окно командной строки и снова запустите команду из пункта 2 данной инструкции.
4. Проверьте, что в выводе есть строка `Topology snapshot`:

   ```text
   [08:54:34] Ignite node started OK (id=3a30b7a4) [08:54:34] Topology snapshot [ver=2, locNode=3a30b7a4, servers=2, clients=0, state=ACTIVE, CPUs=4, offheap=3.2GB, heap=4.0GB]
   ```

По умолчанию `ignite.sh|bat` запускает узел с помощью стандартного конфигурационного файла `config/default-config.xml`.

## Запуск первого приложения

После запуска кластера выполните шаги ниже, чтобы запустить пример `HelloWorld`.

### Шаг 1. Добавление зависимостей DataGrid

Добавить зависимости DataGrid можно двумя способами.

#### Maven

:::{admonition} Внимание
:class: danger

Этот способ будет работать, только если в локальном Sonatype Nexus или другом репозитории зависимостей уже добавлены библиотеки `com.sbt.ignite:ignite-core` и `com.sbt.ignite:ignite-spring`. В противном случае [добавьте зависимости вручную](#добавление-зависимостей-вручную).
:::

Самый простой способ начать работу с DataGrid на Java — использовать управление зависимостями через Maven.

Создайте новый проект Maven с помощью любой IDE и добавьте в файл `pom.xml` проекта следующие зависимости:

```bash
<properties>
    <ignite.se.version>18.0.0</ignite.se.version>
</properties>

<dependencies>
    <dependency>
        <groupId>com.sbt.ignite</groupId>
        <artifactId>ignite-core</artifactId>
        <version>${ignite.se.version}</version>
    </dependency>
    <dependency>
        <groupId>com.sbt.ignite</groupId>
        <artifactId>ignite-spring</artifactId>
        <version>${ignite.se.version}</version>
    </dependency>
</dependencies>
```

#### Добавление зависимостей вручную

Найдите в архиве с дистрибутивом DataGrid два файла: `libs/ignite-core-<версия_DataGrid>.jar` и `libs/ignite-spring/ignite-spring-<версия_DataGrid>.jar`. Распакуйте их в любую папку и добавьте путь к этим файлам в classpath при запуске примера из следующего шага.

### Шаг 2. HelloWorld.java

Ниже приведен пример файла `HelloWord.java`, который выводит запись `Hello World` и другие детали окружения на всех серверных узлах кластера. Пример показывает, как подготовить конфигурацию клиента DataGrid с помощью Java API, создать кеш с данными и выполнить пользовательскую Java-логику на серверных узлах кластера.

::::{admonition} Пример
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
public class HelloWorld {
    public static void main(String[] args) throws IgniteException {
        // Подготовка `IgniteConfiguration` с помощью Java APIs.
        IgniteConfiguration cfg = new IgniteConfiguration();

        // Узел запустится как клиентский.
        cfg.setClientMode(true);

        // Классы пользовательской Java-логики будут передаваться по сети из этого приложения.
        cfg.setPeerClassLoadingEnabled(true);

		// Настройка IP Finder (чтобы клиент мог найти серверные узлы).
		cfg.setDiscoverySpi(new TcpDiscoverySpi().setIpFinder(new TcpDiscoveryVmIpFinder()
				.setAddresses(Collections.singletonList("xxx.x.x.x:47500..47509"))));

        // Запуск узла.
        Ignite ignite = Ignition.start(cfg);

        // Создайте `IgniteCache` и поместите в него данные.
        IgniteCache<Integer, String> cache = ignite.getOrCreateCache("myCache");
        cache.put(1, "Hello");
        cache.put(2, "World!");

        System.out.println(">> Created the cache and add the values.");

        // Выполните пользовательские вычислительные задачи Java на серверных узлах.
        ignite.compute(ignite.cluster().forServers()).broadcast(new RemoteTask());

        System.out.println(">> Compute task is executed, check for output on the server nodes.");

        // Отключитесь от кластера.
        ignite.close();
    }

    /**
     * Вычислительные задачи, которые выводят идентификатор узла и некоторые сведения о его операционной системе и JRE (Java Runtime Environment).
     * Также в коде показано, как получить доступ к хранящимся в кеше данным из вычислительной задачи.
     */
    private static class RemoteTask implements IgniteRunnable {
        @IgniteInstanceResource
        Ignite ignite;

        @Override public void run() {
            System.out.println(">> Executing the compute task");

            System.out.println(
                "   Node ID: " + ignite.cluster().localNode().id() + "\n" +
                "   OS: " + System.getProperty("os.name") +
                "   JRE: " + System.getProperty("java.runtime.name"));

            IgniteCache<Integer, String> cache = ignite.cache("myCache");

            System.out.println(">> " + cache.get(1) + " " + cache.get(2));
        }
    }
}
:::
::::

## Настройка JVM

C релиза версии 16.0.0 DataGrid запускается только на Java 11 и новее.

Чтобы запустить DataGrid, установите переменную окружения `JAVA_HOME` и укажите в ней каталог установки Java.

DataGrid использует проприетарное Java SDK API, которое недоступно по умолчанию. Чтобы сделать его доступным, передайте указанные ниже флаги в JVM.

Если запускаете сценарий `ignite.sh|bat`, дополнительно ничего делать не нужно: в нем уже настроены флаги. В остальных случаях предоставьте следующие параметры для JVM приложения:

::::{md-tab-set}
:::{md-tab-item} Java 11
```java
--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED
--add-exports=java.base/sun.nio.ch=ALL-UNNAMED
--add-exports=java.management/com.sun.jmx.mbeanserver=ALL-UNNAMED
--add-exports=jdk.internal.jvmstat/sun.jvmstat.monitor=ALL-UNNAMED
--add-exports=java.base/sun.reflect.generics.reflectiveObjects=ALL-UNNAMED
--add-opens=jdk.management/com.sun.management.internal=ALL-UNNAMED
--illegal-access=permit
```
:::

:::{md-tab-item} Java 17
```java
--add-opens=java.base/jdk.internal.access=ALL-UNNAMED
--add-opens=java.base/jdk.internal.misc=ALL-UNNAMED
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED
--add-opens=java.base/sun.util.calendar=ALL-UNNAMED
--add-opens=java.management/com.sun.jmx.mbeanserver=ALL-UNNAMED
--add-opens=jdk.internal.jvmstat/sun.jvmstat.monitor=ALL-UNNAMED
--add-opens=java.base/sun.reflect.generics.reflectiveObjects=ALL-UNNAMED
--add-opens=jdk.management/com.sun.management.internal=ALL-UNNAMED
--add-opens=java.base/java.io=ALL-UNNAMED
--add-opens=java.base/java.nio=ALL-UNNAMED
--add-opens=java.base/java.net=ALL-UNNAMED
--add-opens=java.base/java.util=ALL-UNNAMED
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED
--add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED
--add-opens=java.base/java.lang=ALL-UNNAMED
--add-opens=java.base/java.lang.invoke=ALL-UNNAMED
--add-opens=java.base/java.math=ALL-UNNAMED
--add-opens=java.sql/java.sql=ALL-UNNAMED
--add-opens=java.base/java.lang.reflect=ALL-UNNAMED
--add-opens=java.base/java.time=ALL-UNNAMED
--add-opens=java.base/java.text=ALL-UNNAMED
--add-opens=java.management/sun.management=ALL-UNNAMED
--add-opens java.desktop/java.awt.font=ALL-UNNAMED
```
:::
::::

## SQL

Если требуется просто запустить кластер и добавить строки с данными без запуска Java и настройки IDE, можно использовать SQL.

Чтобы сделать это, используйте утилиту `sqlline.sh|bat`, которая находится в папке `bin` установочной директории DataGrid.

### Использование утилиты SQLline

Утилита `sqlline.sh|bat` позволяет подключиться к узлу и начать вводить строки данных:

1. Откройте новое окно командной строки и проверьте, что находитесь в директории `$IGNITE_HOME`. Если это не так, настройте переменную — выполните в терминале команду:

   ```bash
   export IGNITE_HOME=path/to/ignite
   ```

2. Подключитесь к кластеру с помощью утилиты SQLLine:

    ```bash
    ./bin/sqlline.sh -u "jdbc:ignite:thin://xxx.x.x.x/"
    ```

3. Введите название учетной записи клиента. Начальные учетные данные приводятся в подразделе «Начальные учетные данные» раздела [«Сценарии администрирования»](../../administration-guide/md/administration-scenarios.md) документа «Руководство по системному администрированию».

4. Создайте две таблицы. Для этого запустите две команды в утилите SQLLine.

    :::{code-block} sql
    :caption: SQL
    CREATE TABLE City (id LONG PRIMARY KEY, name VARCHAR) WITH "template=replicated";
    CREATE TABLE Person (id LONG, name VARCHAR, city_id LONG, PRIMARY KEY (id, city_id)) WITH "backups=1, affinityKey=city_id"; 
    :::

5. Cкопируйте и вставьте команды.

    :::{code-block} sql
    :caption: SQL
    INSERT INTO City (id, name) VALUES (1, 'Forest Hill');
    INSERT INTO City (id, name) VALUES (2, 'Denver');
    INSERT INTO City (id, name) VALUES (3, 'St. Petersburg');
    INSERT INTO Person (id, name, city_id) VALUES (1, 'John Doe', 3);
    INSERT INTO Person (id, name, city_id) VALUES (2, 'Jane Roe', 2);
    INSERT INTO Person (id, name, city_id) VALUES (3, 'Mary Major', 1);
    INSERT INTO Person (id, name, city_id) VALUES (4, 'Richard Miles', 2);
    :::

6. Запустите базовые запросы. 

    ::::{admonition} Пример запроса с выводом:
    :class: hint

    :::{code-block} sql
    :caption: SQL
    SELECT * FROM City;

    +--------------------------------+--------------------------------+
    |               ID               |              NAME              |
    +--------------------------------+--------------------------------+
    | 1                              | Forest Hill                    |
    | 2                              | Denver                         |
    | 3                              | St. Petersburg                 |
    +--------------------------------+--------------------------------+
    3 rows selected (0.05 seconds)
    :::
    ::::

    :::{admonition} Примечание
    :class: note

    Запрос `SELECT` проверяет, создана ли таблица.
    :::

7. Запустите запросы с распределенными `JOIN`.

    ::::{admonition} Пример запроса с выводом:
    :class: hint

    :::{code-block} sql
    :caption: SQL
    SELECT p.name, c.name FROM Person p, City c WHERE p.city_id = c.id;

    +--------------------------------+--------------------------------+
    |              NAME              |              NAME              |
    +--------------------------------+--------------------------------+
    | Mary Major                     | Forest Hill                    |
    | Jane Roe                       | Denver                         |
    | John Doe                       | St. Petersburg                 |
    | Richard Miles                  | Denver                         |
    +--------------------------------+--------------------------------+
    4 rows selected (0.011 seconds)
    :::
    ::::

    :::{admonition} Примечание
    :class: note

    При создании каждой новой таблицы для нее одновременно создается отдельный кеш. Таблица физически сохраняется на диске в отдельном каталоге с ее названием.
    :::