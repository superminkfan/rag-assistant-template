# Основные способы настройки

В разделе описаны форматы конфигурации, которые поддерживает DataGrid.

:::{admonition} Настройка для .NET, Python, Node.js и других языков программирования
:class: note

Подробно о настройке на основе .NET написано в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/thin-clients/getting-started-with-thin-clients).

Для настройки на основе Python, Node.js и других языков программирования используйте:
- данный раздел, чтобы настроить кластер DatGrid на базе Java;
- раздел [«Тонкие клиенты»](thin_clients.md), чтобы настроить приложения, которые будут работать с кластером, для конкретного языка.
:::

Чтобы запустить узел DataGrid, укажите экземпляр класса `IgniteConfiguration`. Его можно инициализировать программно или с помощью Spring XML-конфигурации.

Запуск узла DataGrid выполняется:

- Из кода — режим Embedded в составе пользовательского приложения.
- При помощи скрипта `ignite.sh|bat`, который входит в дистрибутив — режим Standalone отдельно от пользовательского приложения. Для этого способа нужно сформировать Spring XML-конфигурацию.

Обычно для запуска используется режим Standalone. Его также применяют при автоматизированном развертывании кластеров DataGrid с помощи Ansible-роли — подробнее об этом написано в разделе [«Установка DataGrid с помощью Ansible »](../../installation-guide/md/ansible-role-datagrid.md) документа «Руководство по установке».

## Spring XML-конфигурация

XML-конфигурация — файл определения bean Spring, в который включен bean `IgniteConfiguration`.

Запуск из командной строки:

```bash
ignite.sh|bat ignite-config.xml
```

Если конфигурационный файл не задан, скрипт использует файл `{IGNITE_HOME}/config/default-config.xml`.

При запуске из кода укажите путь к файлу с XML-конфигурацией:

```bash
Ignition.start("my-config-folder/my-ignite-configuration.xml");
```

Конфигурация указывается в формате Spring XML. Подробнее об этом написано в [официальной документации Spring](https://docs.spring.io/spring-framework/docs/4.2.x/spring-framework-reference/html/xsd-configuration.html).

В примере ниже показана настройка параметра `workDirectory` и статической конфигурации партицированного кеша. Подробноее о нем написано в подразделе [«Партиционирование данных»](data_partitioning.md) раздела «Моделирование данных».

:::{code-block} xml
:caption: XML
<?xml version="1.0" encoding="UTF-8"?>

<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
        http://www.springframework.org/schema/beans
        http://www.springframework.org/schema/beans/spring-beans.xsd">

    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="workDirectory" value="/path/to/work/directory"/>

        <property name="cacheConfiguration">
            <bean class="org.apache.ignite.configuration.CacheConfiguration">
                <!-- Установите имя кеша. -->
                <property name="name" value="myCache"/>
                <!-- Установите режим кеша. -->
                <property name="cacheMode" value="PARTITIONED"/>
                <!-- Другие параметры кеша. -->
            </bean>
        </property>
    </bean>
</beans>
:::

## Конфигурация через программный код

Создайте экземпляр класса `IgniteConfiguration` и установите необходимые параметры:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteConfiguration igniteCfg = new IgniteConfiguration();
// Настройка рабочего каталога.
igniteCfg.setWorkDirectory("/path/to/work/directory");

// Определение партицированного кеша.
CacheConfiguration cacheCfg = new CacheConfiguration("myCache");
cacheCfg.setCacheMode(CacheMode.PARTITIONED);

igniteCfg.setCacheConfiguration(cacheCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var igniteCfg = new IgniteConfiguration
{
    WorkDirectory = "/path/to/work/directory",
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "myCache",
            CacheMode = CacheMode.Partitioned
        }
    }
};
```
:::
::::

## Настройка дополнительных модулей из поставки DataGrid

В поставку DataGrid включены модули, которые обеспечивают дополнительную функциональность.

Все модули есть в дистрибутиве, но по умолчанию они отключены (за исключением `ignite-core`, `ignite-spring` и `ignite-indexing`). Модули находятся в каталоге `lib/optional` — каждый в отдельной поддиректории. Их можно подключать отдельно по мере необходимости. Список модулей указан в разделе [«Состав дистрибутива»](../../installation-guide/md/distrib-content.md) документа «Руководство по установке».

В зависимости от предполагаемого использования DataGrid модули можно подключить одним из следующих способов:

- Переместите каталог `lib/optional/{module-dir}` в папку `lib` перед запуском узла.
- Добавьте библиотеки из `lib/optional/{module-dir}` в classpath приложения.
- Добавьте модуль в качестве зависимости Maven в проект.

:::{admonition} Пример включения модуля логирования в состав Maven-проекта
:class: hint

```bash
<dependency>
<groupId>com.sbt.ignite</groupId>
<artifactId>ignite-log4j2</artifactId>
<version>${ignite.version}</version>
</dependency>
```
:::

## Дополнительные настройки (IgniteSystemProperties)

В DataGrid есть класс `IgniteSystemProperties`, который содержит перечень расширенных настроек. Список `IgniteSystemProperties` указан в [официальной документации Apache Ignite](https://ignite.apache.org/releases/latest/javadoc/org/apache/ignite/IgniteSystemProperties.html).

Дополнительные настройки можно указывать с помощью параметров JVM (переменных окружения) или API Java — `System#setProperty`.