# Запуск клиентских узлов за пределами NAT

При развертывании клиентских узлов за пределами NAT серверные узлы не смогут установить связь с клиентскими из-за ограничений протокола коммуникации. К таким случаям в том числе относится развертывание клиентских узлов в виртуальных сетях, например в Kubernetes, а серверных узлов — в другом месте.

Примеры, как настроить режим коммуникаций между узлами в таком случае:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="clientMode" value="true"/>
    <property name="communicationSpi">
        <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
            <property name="forceClientToServerConnections" value="true"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setClientMode(true);

cfg.setCommunicationSpi(new TcpCommunicationSpi().setForceClientToServerConnections(true));
```
:::
::::

Ограничения:

- Такой режим коммуникаций нельзя использовать при `TCPCommunicationspi.usepairedConnections = true` на серверных и клиентских узлах.
- Свойство `TCPCommunicationspi.usepairedConnections = true` можно использовать только для клиентских узлов.
- Функциональность Peer Class Loading не работает для запросов типа `ContinuousQuery` (трансформаторы и фильтры), если они начинаются с клиентского узла `ForceClientToServerConnections = true`. Добавьте соответствующие классы в classpath каждого серверного узла. Подробнее о функциональности написано в подразделе [Peer Class Loading](peer_class_loading.md) раздела «Развертывание кода».