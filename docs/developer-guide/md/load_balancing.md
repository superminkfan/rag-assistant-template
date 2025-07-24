# Балансировка нагрузки

DataGrid автоматически балансирует нагрузку по заданиям, которые запускаются вычислительными задачами, и по отдельным задачам, отправленным с помощью API распределенных вычислений. Отдельные задачи, которые отправляются с помощью `IgniteCompute.run(…​)` и других вычислительных методов, рассматриваются как задачи (task) с одним заданием (job).

По умолчанию DataGrid использует циклический (Round Robin) алгоритм `RoundRobinLoadBalancingSpi`, который в последовательном порядке распределяет задания по узлам, указанным для вычислительной задачи.

:::{admonition} Важно
:class: attention

Балансировка нагрузки не относится к коллоцированным вычислениям.
:::

Алгоритм балансировки нагрузки контролируется свойством `IgniteConfiguration.loadBalancingSpi`.

## Циклический алгоритм балансировки нагрузки

`RoundRobinLoadBalancingSpi` выполняет циклическую итерацию по доступным узлам и выбирает следующий в последовательности узел. Доступные узлы определяются при получении вычислительного экземпляра, с помощью которого выполняются задачи (подробнее о нем написано в разделе [«Распределенные вычисления»](distributed_computing.md)).

Циклическая балансировка нагрузки поддерживает два режима операций: по задачам и глобальный.

При настроенном режиме по задачам реализация выбирает случайный узел в начале выполнения каждой задачи и последовательно выполняет итерацию по всем узлам топологии, начиная с выбранного. Когда общее число частей задачи совпадает с количеством узлов, режим гарантирует, что в выполнении задания будут участвовать все узлы.

:::{admonition} Важно
:class: attention

Для режима по задачам нужно разрешить использование следующих типов событий: `EVT_TASK_FAILED`, `EVT_TASK_FINISHED` и  `EVT_JOB_MAPPED`.
:::

При настроенном глобальном режиме для всех задач поддерживается одна последовательная очередь узлов. Каждый раз выбирается следующий узел в очереди. Если в этом режиме общее число частей задачи совпадает с количеством узлов, при одновременном выполнении нескольких задач некоторые задания в рамках одной и той же задачи назначатся одному и тому же узлу.

По умолчанию используется глобальный режим.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:util="http://www.springframework.org/schema/util"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="         http://www.springframework.org/schema/beans
         http://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/util
         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="includeEventTypes">
            <list>
                <!-- Эти события нужны для работы в режиме по задачам. -->
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_TASK_FINISHED"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_TASK_FAILED"/>
                <util:constant static-field="org.apache.ignite.events.EventType.EVT_JOB_MAPPED"/>
            </list>
        </property>

        <property name="loadBalancingSpi">
            <bean class="org.apache.ignite.spi.loadbalancing.roundrobin.RoundRobinLoadBalancingSpi">
                <!-- Активируйте циклический режим по задачам. -->
                <property name="perTask" value="true"/>
            </bean>
        </property>

    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
RoundRobinLoadBalancingSpi spi = new RoundRobinLoadBalancingSpi();
spi.setPerTask(true);

IgniteConfiguration cfg = new IgniteConfiguration();
// Эти события нужны для работы в режиме по задачам.
cfg.setIncludeEventTypes(EventType.EVT_TASK_FINISHED, EventType.EVT_TASK_FAILED, EventType.EVT_JOB_MAPPED);

// Переопределите SPI балансировки нагрузки по умолчанию.
cfg.setLoadBalancingSpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

## Случайная и взвешенная балансировка нагрузки

`WeightedRandomLoadBalancingSpi` выбирает случайный узел из списка доступных. При желании можно назначать вес для узлов, чтобы на узлы с бóльшим весом направлялось больше заданий. Вес всех узлов по умолчанию — 10.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="loadBalancingSpi">
        <bean class="org.apache.ignite.spi.loadbalancing.weightedrandom.WeightedRandomLoadBalancingSpi">
            <property name="useWeights" value="true"/>
            <property name="nodeWeight" value="10"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
WeightedRandomLoadBalancingSpi spi = new WeightedRandomLoadBalancingSpi();

// Настройте SPI для использования алгоритма взвешенной балансировки нагрузки.
spi.setUseWeights(true);

// Установите вес для локального узла.
spi.setNodeWeight(10);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите SPI балансировки нагрузки по умолчанию.
cfg.setLoadBalancingSpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

## Перехват заданий (job stealing)

Довольно часто кластеры развертываются на нескольких машинах. Некоторые из них могут быть более мощными или менее используемыми, чем другие. Включение `JobStealingCollisionSpi` поможет избежать очередей заданий в перегруженном узле: их перехватит малоиспользуемый узел.

С помощью `JobStealingCollisionSpi` происходит перехват задач из перегруженных в малоиспользуемые узлы. SPI особенно полезен при наличии заданий, которые быстро завершаются, пока другие задания находятся в очереди на перегруженных узлах. В этом случае ожидающие задания перенесутся с более медленного узла на более быстрый/малоиспользуемый узел.

`JobStealingCollisionSpi` наследует так называемую «позднюю» балансировку нагрузки. Она позволяет переназначать задачу с узла A на узел B после того, как выполнение задачи уже было запланировано на узле A.

:::{admonition} Важно
:class: attention

Чтобы подключить перехват задач, настройте `JobStealingCollisionSpi` в качестве SPI отказоустойчивости. Подробнее об этом написано в разделе [«Отказоустойчивость»](fault_tolerance.md).
:::

Пример настройки `JobStealingCollisionSpi`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <!-- Включение требуемого SPI отказоустойчивости. -->
    <property name="failoverSpi">
        <bean class="org.apache.ignite.spi.failover.jobstealing.JobStealingFailoverSpi"/>
    </property>
    <!-- Включение `JobStealingCollisionSpi` для поздней балансировки нагрузки. -->
    <property name="collisionSpi">
        <bean class="org.apache.ignite.spi.collision.jobstealing.JobStealingCollisionSpi">
            <property name="activeJobsThreshold" value="50"/>
            <property name="waitJobsThreshold" value="0"/>
            <property name="messageExpireTime" value="1000"/>
            <property name="maximumStealingAttempts" value="10"/>
            <property name="stealingEnabled" value="true"/>
            <property name="stealingAttributes">
                <map>
                    <entry key="node.segment" value="foobar"/>
                </map>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
JobStealingCollisionSpi spi = new JobStealingCollisionSpi();

// Настройте количество ожидающих заданий
// в очереди для перехвата.
spi.setWaitJobsThreshold(10);

// Настройте время истечения срока действия сообщения (в мс).
spi.setMessageExpireTime(1000);

// Настройте количество попыток перехвата.
spi.setMaximumStealingAttempts(10);

// Настройте количество активных заданий, которые можно выполнять
// одновременно. Это число должно совпадать с количеством
// потоков в пуле (по умолчанию — 100).
spi.setActiveJobsThreshold(50);

// Подключите перехват заданий.
spi.setStealingEnabled(true);

// Установите атрибут перехвата, чтобы перехватывать задания с/на узлы, в которых есть этот атрибут.
spi.setStealingAttributes(Collections.singletonMap("node.segment", "foobar"));

// Подключите `JobStealingFailoverSpi`.
JobStealingFailoverSpi failoverSpi = new JobStealingFailoverSpi();

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Collision SPI по умолчанию.
cfg.setCollisionSpi(spi);

cfg.setFailoverSpi(failoverSpi);
```
:::
::::