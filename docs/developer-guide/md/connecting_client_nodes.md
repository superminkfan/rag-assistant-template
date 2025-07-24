# Подключение клиентских узлов

## Повторное подключение клиентского узла

Клиентский узел может отключиться от кластера по нескольким причинам:

- Не удалось восстановить соединение с серверным узлом из-за проблем с сетью.
- Соединение с серверным узлом было разорвано на некоторое время. Клиентский узел может восстановить соединение с кластером, но серверный узел уже разорвал соединение с клиентским, так как не получил от него heartbeat-сообщение.
- Медленная работа клиентских узлов.

Когда клиентский узел определяет, что соединение с кластером разорвано, он пытается повторно подключиться к кластеру под новым идентификатором узла (`nodeId`).

:::{admonition} Внимание
:class: danger

В случае повторного соединения клиента меняется идентификатор локального `ClusterNode`. Это может затронуть логику приложения, которая зависит от идентификатора.
:::

Повторное соединение клиента можно отключить в конфигурации узла.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="clientMode" value="true"/>

    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <!-- Предотвратите повторное подключение этого клиента при потере соединения. -->
            <property name="clientReconnectDisabled" value="true"/>
            <property name="ipFinder">

                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder">
                    <property name="addresses">
                        <list>
                            <value>xxx.x.x.x:47500..47509</value>
                        </list>
                    </property>
                </bean>
            </property>
        </bean>
    </property>
    <property name="communicationSpi">
        <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
            <property name="slowClientQueueLimit" value="1000"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

TcpDiscoverySpi discoverySpi = new TcpDiscoverySpi();
discoverySpi.setClientReconnectDisabled(true);

cfg.setDiscoverySpi(discoverySpi);
```
:::
::::

Пока клиентский узел отключен от кластера и пытается восстановить соединение, Ignite API генерирует исключение `IgniteClientDisconnectedException`. Оно содержит операцию повторного соединения `future`. Ее можно использовать, чтобы дождаться восстановления подключения.

:::{code-block} java
:caption: Java
IgniteCache cache = ignite.getOrCreateCache(new CacheConfiguration<>("myCache"));

try {
    cache.put(1, "value");
} catch (IgniteClientDisconnectedException e) {
    if (e.getCause() instanceof IgniteClientDisconnectedException) {
        IgniteClientDisconnectedException cause = (IgniteClientDisconnectedException) e.getCause();

        cause.reconnectFuture().get(); // Ожидайте переподключения клиентского узла. 
        // Продолжайте.
    }
}
:::

## События клиентского отключения от кластера или повторного подключения к нему

Когда клиентский узел отключается от кластера или повторно подключается к нему, запускаются события:

- `EVT_CLIENT_NODE_DISCONNECTED`;
- `EVT_CLIENT_NODE_RECONNECTED`.

Можно прослушать эти события и выполнить пользовательские действия в ответ. Подробности и примеры описаны в разделе [«Работа с событиями»](working_with_events.md).

## Работа с медленными клиентскими узлами

Во многих развертываниях клиентские узлы запускаются на более медленных машинах с более низкой пропускной способностью сети, чем серверные узлы. Это приводит к тому, что серверы могут генерировать нагрузку, с которой не справляются клиентские узлы. Проблемы с сетью могут привести к росту очереди исходящих сообщений на серверах — это может заблокировать работу всего кластера или вызвать нехватку памяти на сервере.

Чтобы справиться с такими ситуациями, настройте максимальное количество исходящих сообщений для клиентских узлов. Если размер исходящей очереди превысит максимальное значение, узел отключится от кластера.

Примеры, как настроить ограничение размера очереди исходящих сообщений для медленных клиентских узлов:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="clientMode" value="true"/>
        <property name="communicationSpi">
            <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
                <property name="slowClientQueueLimit" value="1000"/>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();
cfg.setClientMode(true);

TcpCommunicationSpi commSpi = new TcpCommunicationSpi();
commSpi.setSlowClientQueueLimit(1000);

cfg.setCommunicationSpi(commSpi);
```
:::
::::