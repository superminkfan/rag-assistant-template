# Запуск и остановка узлов

Для управления узлами кластера используйте инструменты DevOps — подробнее о них написано в разделе [«Установка DataGrid с помощью Ansible»](../../installation-guide/md/ansible-role-datagrid.md) документа «Руководство по установке».

В главе описывается, как запускать и останавливать серверные и клиентские узлы. Это ознакомительная информация для разработчиков — она пригодится, например, для написания тестов.

Существует два типа узлов: серверные и клиентские. Клиентские узлы также называют толстыми клиентскими узлами, чтобы отличать их от тонких клиентов. Серверные узлы участвуют в кешировании, выполнении вычислений, потоковой обработке и так далее. Толстые клиенты дают возможность удаленно подключаться к серверам. Клиентские узлы не хранят данные, но предоставляют полный набор API с клиентской стороны: транзакции, вычисления, потоковую обработку, кеширование, сервисы и так далее.

По умолчанию все узлы DataGrid запускаются как серверные. Для работы в режиме клиентского узла его нужно явно [включить](#запуск-клиентского-узла).

## Запуск серверного узла

Пример запуска серверного узла:

::::{md-tab-set}
:::{md-tab-item} Shell
```shell
ignite.sh|bat path/to/configuration.xml
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();
Ignite ignite = Ignition.start(cfg);
```
:::
::::

`Ignite` — объект `AutoCloseable`. Чтобы закрыть его автоматически, используйте конструкцию `try-with-resource`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

try (Ignite ignite = Ignition.start(cfg)) {
    //
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration();
IIgnite ignite = Ignition.Start(cfg);
```
:::
::::

`Ignite` — объект `IDisposable`. Чтобы закрыть его автоматически, используйте оператор `using`:

:::{code-block} c#
:caption: C\#
var cfg = new IgniteConfiguration();
using (IIgnite ignite = Ignition.Start(cfg))
{
    //
}
:::

## Запуск клиентского узла

Чтобы запустить клиентский узел, включите режим клиента в конфигурации узла:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
	xmlns:util="http://www.springframework.org/schema/util"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="
    http://www.springframework.org/schema/beans
	http://www.springframework.org/schema/beans/spring-beans.xsd
	http://www.springframework.org/schema/util
	http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="clientMode" value="true"/>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Включите клиентский режим.
cfg.setClientMode(true);

// Запустите клиент.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    ClientMode = true
};
IIgnite ignite = Ignition.Start(cfg);
```
:::
::::

Для удобства также можно включать и отключать клиентский режим с помощью класса `Ignition`, чтобы клиенты и серверы могли повторно использовать одну и ту же конфигурацию.

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignition.setClientMode(true);

// Запустите узел в клиентском режиме.
Ignite ignite = Ignition.start();
```
:::

:::{md-tab-item} C\#/.NET
```c#
Ignition.ClientMode = true;
Ignition.Start();
```
:::
::::

В дистрибутиве DataGrid есть дополнительный скрипт `startServer.sh`, который запускает серверный узел с конфигурацией `customIgniteConfiguration.xml`.

## Остановка узла

Принудительная остановка узла может привести к несогласованности и потере данных или помешать перезагрузке узла. Принудительно останавливать узел стоит только в крайнем случае, если он не отвечает и нельзя выключить его другим способом.

Корректная остановка позволяет узлу закончить критические операции и правильно завершить жизненный цикл.

### Шаг 1. Остановите узел.

Узел можно корректно остановить через конструкцию `try-with-resources` или одним из способов:

- Вызвать `Ignite.close()`.
- Вызвать `System.exit()`.
- Отправить пользовательский сигнал прерывания. DataGrid использует JVM Shutdown Hook для выполнения пользовательской логики перед остановкой JVM. Если узел запускается с помощью скрипта `ignite.sh|bat` и не отсоединяется от терминала, для остановки можно нажать `Ctrl+C`.

В дистрибутиве DataGrid есть дополнительный скрипт `stopServer.sh`. Он отравляет пользовательский сигнал прерывания, после чего происходит проверка корректной остановки в течение 40 секунд. Если процесс не остановился, происходит принудительная остановка через `kill -9`.

Перед остановкой персистентных кластеров нужно обязательно деактивировать их.

:::{admonition} Внимание
:class: danger

При завершении работы через `kill -9` невозможно предотвратить потерю партиций, если их копии полностью недоступны.
:::

### Шаг 2. Удалите узел из базовой топологии.

Этот шаг может быть необязательным, если включена автоматическая настройка базовой топологии — подобнее о ней написано в подразделе [«Базовая топология»](baseline_topology.md) раздела «Кластеризация».

Удаление узла из базовой топологии запускает процесс ребалансировки на оставшихся узлах. Если вскоре после выключения узла планируется его перезапуск, ребалансировку можно не выполнять. В этом случае удалять узлы из базовой топологии не нужно.

## Жизненный цикл узла

Прослушивание событий жизненного цикла позволяет выполнить пользовательский код на различных этапах цикла узла DataGrid.

События жизненного цикла:

| Событие | Описание |
|---|---|
| `BEFORE_NODE_START` | Вызывается перед началом процедуры запуска узла |
| `AFTER_NODE_START` | Вызывается сразу после запуска узла |
| `BEFORE_NODE_STOP` | Вызывается перед началом процедуры остановки узла |
| `AFTER_NODE_STOP` | Вызывается сразу после остановки узла |

Чтобы добавить пользовательский слушатель событий жизненного цикла:

1.  Создайте пользовательский bean жизненного цикла узла. Для этого создайте собственный класс и реализуйте интерфейс `LifecycleBean`. Класс должен содержать пользовательскую логику, которую нужно выполнить на этапах жизненного цикла. В интерфейсе есть метод `onLifecycleEvent()`, который вызывается для любого события жизненного цикла:

    ```bash
    public class MyLifecycleBean implements LifecycleBean {
        @IgniteInstanceResource
        public Ignite ignite;

        @Override
        public void onLifecycleEvent(LifecycleEventType evt) {
            if (evt == LifecycleEventType.AFTER_NODE_START) {

                System.out.format("After the node (consistentId = %s) starts.\n", ignite.cluster().node().consistentId());

            }
        }
    }
    ```

2.  Добавьте реализацию интерфейса `LifecycleBean` в конфигурацию узла:

    ::::{md-tab-set}
    :::{md-tab-item} XML
    ```xml
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="lifecycleBeans">
            <list>
                <bean class="org.apache.ignite.snippets.MyLifecycleBean"/>
            </list>
        </property>
    </bean>
    ```
    :::

    :::{md-tab-item} Java
    ```java
    IgniteConfiguration cfg = new IgniteConfiguration();

    // Укажите компонент жизненного цикла в конфигурации узла.
    cfg.setLifecycleBeans(new MyLifecycleBean());

    // Запустите узел.
    Ignite ignite = Ignition.start(cfg);
    ```
    :::
    ::::