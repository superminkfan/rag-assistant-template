# Настройка сети

## IPv4 и IPv6

DataGrid поддерживает одновременно IPv4 и IPv6. Это может привести к проблемам, из-за которых узлы кластера утрачивают сетевую связанность. Чтобы избежать подобных проблем, ограничьте DataGrid на использование только IPv4 — для этого нужно установить JVM-параметр `-[Djava.net](http://djava.net/).preferIPv4Stack=true`.

## Обнаружение узлов кластера

В разделе описаны сетевые параметры механизма Discovery по умолчанию, в котором используется протокол TCP/IP для обмена сообщениями. Механизм реализован в классе `TcpDiscoverySpi`.

Пример, как изменить свойства механизма Discovery:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="discoverySpi">
            <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
                <property name="localPort" value="8300"/>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

TcpDiscoverySpi discoverySpi = new TcpDiscoverySpi().setLocalPort(8300);

cfg.setDiscoverySpi(discoverySpi);
Ignite ignite = Ignition.start(cfg);
```
:::
::::

Важные свойства `TcpDiscoverySpi`:

:::{admonition} Внимание
:class: danger

Инициализируйте параметр `IgniteConfiguration.localHost` или `TcpDiscoverySpi.localAddress` с помощью адреса сетевого интерфейса, который будет использоваться для межузлового взаимодействия. По умолчанию узел слушает все доступные IP-адреса среды, в которой он запущен. Это может увеличить время обнаружения сбоев узла, если некоторые из его адресов недоступны для других узлов кластера.
:::

| Свойство | Описание | Значение по умолчанию |
|---|---|---|
| `localAddress` | Локальный IP-адрес хоста, который используется для обнаружения. При установке переопределяет параметр `IgniteConfiguration.localHost` | По умолчанию узел связывается со всеми доступными сетевыми адресами. Если доступен не замыкающийся адрес (non-loopback address), используется значение `java.net.InetAddress.getLocalHost()`, которое получили с помощью метода `getLocalHost()` |
| `localPort` | Локальный порт, к которому привязан узел. Если значение установлено не по умолчанию, другие узлы кластера должны знать этот порт, чтобы иметь возможность обнаружить узел | `47100` |
| `localPortRange` | Диапазон портов, с которыми узлы связываются, пока не найдут свободный.<br><br>Свойство устанавливает количество портов, к которым узел будет пытаться присоединиться, если `localPort` занят. Узел увеличивает значение `localPort` по умолчанию на `1`, пока не найдется свободный порт | `100` |
| `soLinger` | Задает время задержки при закрытии сокетов TCP, которые используются Discovery SPI. Подробности по настройке этого параметра можно посмотреть в Java `Socket.setSoLinger` API. В DataGrid по умолчанию установлено неотрицательное значение тайм-аута, чтобы предотвратить потенциальные блокировки с соединениями SSL. Это может увеличить время обнаружения сбоев в узлах кластера. Можно обновить JRE до той версии, в которой исправлена проблема с SSL, и настроить свойство после этого | `0` |
| `reconnectCount` | Количество попыток узла установить или восстановить соединение с другим узлом | `10` |
| `networkTimeout` | Максимальное время ожидания для сетевых операций, мс | `5000` |
| `socketTimeout` | Тайм-аут операций сокета. Используется для ограничения времени соединения и записи данных в сокет | `5000` |
| `ackTimeout` | Тайм-аут определяет время для подтверждения сообщений об обнаружении. Если в течение этого времени подтверждение не получено, Discovery SPI пытается отправить сообщение повторно | `5000` |
| `joinTimeout` | Тайм-аут определяет время, в течение которого узел ждет присоединения к кластеру. Если используется несовместимый IP Finder и узел не может подключиться ни к одному адресу из него, узел продолжает попытки до окончания тайм-аута. Если все адреса не отвечают, генерируется исключение и узел отключается. `0` означает неограниченное время ожидания | `0` |
| `statisticsPrintFrequency` | Определяет, как часто узел выводит статистику обнаружения в файлы журнала (logs). `0` означает отсутствие вывода. Если значение больше нуля и настроен вывод в файлы журнала, статистика выводится на уровне `INFO` один раз в период | `0` |

## Обмен сообщениями между узлами

Когда узлы обнаружили друг друга и сформировали кластер, они обмениваются сообщениями с помощью Communication SPI. Сообщения реализуют распределенные операции кластера, например выполнение задач, запросы, операции по изменению данных и так далее. Реализация Communication SPI по умолчанию использует протокол TCP/IP для обмена сообщениями (`TcpCommunicationSpi`).

Каждый узел открывает локальный порт для подключения и адрес, с которым соединяются и отправляют сообщения другие узлы. При запуске узел пытается связаться с указанным портом для подключения (значение по умолчанию — 47100). Если порт уже используется, узел увеличивает номер порта, пока не найдет свободный. Количество попыток связи устанавливается свойством `localPortRange` (значение по умолчанию — 100).

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">

        <property name="communicationSpi">
            <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
                <property name="localPort" value="4321"/>
            </bean>
        </property>

    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
TcpCommunicationSpi commSpi = new TcpCommunicationSpi();

// Установите локальный порт.
commSpi.setLocalPort(4321);

IgniteConfiguration cfg = new IgniteConfiguration();
cfg.setCommunicationSpi(commSpi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} С#/.NET
```c#
 var cfg = new IgniteConfiguration
 {
     CommunicationSpi = new TcpCommunicationSpi
     {
         LocalPort = 1234
     }
 };
Ignition.Start(cfg);
```
:::
::::

В таблице ниже описаны некоторые важные свойства `TcpCommunicationSpi`. Полный список есть в [официальной документации Apache Ignite](https://ignite.apache.org/releases/2.16.0/javadoc/org/apache/ignite/spi/communication/tcp/TcpCommunicationSpi.html).

| Свойство | Описание | Значение по умолчанию |
|---|---|---|
| `localAddress` | Локальный адрес, с которым связывается Communication SPI. При установке переопределяет параметр `IgniteConfiguration.localHost` | — |
| `localPort` | Локальный порт, который узел использует для коммуникации | `47100` |
| `localPortRange` | Диапазон портов, с которыми узлы пытаются последовательно связаться, пока не найдут свободный | `100` |
| `tcpNoDelay` | Устанавливает значение для опции сокета `TCP_NODELAY`. Каждый принятый или созданный сокет будет использовать установленное значение. <br><br>По умолчанию установлено значение `true`, чтобы уменьшить время запроса и ответа во время взаимодействия по протоколу TCP.<br><br>В большинстве случаев не рекомендуется менять значение по умолчанию | `true` |
| `idleConnectionTimeout` | Максимальное время простоя соединения, после которого оно закрывается, мс | `600000` |
| `usePairedConnections` | Определяет необходимость принудительной установки двухсокетного соединения между узлами. Если задано значение `true`, между связанными узлами будет установлено два отдельных соединения: одно для исходящих сообщений и одно для входящих. Если задано значение `false`, для обоих направлений будет использоваться одно TCP-соединение.<br><br>Этот флаг будет полезен для некоторых операционных систем, в которых доставка сообщений занимает слишком много времени | `false` |
| `directBuffer` | Указывает, что вместо буфера heap-распределения NIO нужно выделить буфер прямого распределения NIO. Хотя у буферов прямого распределения лучше показатели по производительности, в некоторых случаях (особенно на Windows) они могут вызывать сбои JVM. Если в среде есть такая проблема, установите значение свойства `false` | `true` |
| `directSendBuffer` | Указывает, что при отправке сообщений вместо буфера heap-распределения NIO нужно использовать буфер прямого распределения NIO | `false` |
| `socketReceiveBuffer` | Размер буфера приема для сокетов, которые создал или принял Communication SPI.<br><br>Если установлено `0`, используется значение операционной системы по умолчанию | `0` |
| `socketSendBuffer` | Размер буфера отправки для сокетов, которые создал или принял Communication SPI.<br><br>Если установлено `0`, используется значение операционной системы по умолчанию | `0` |

## Тайм-ауты подключения

Свойства, которые определяют тайм-ауты подключения:

| Свойство | Описание | Значение по умолчанию |
|---|---|---|
| `IgniteConfiguration.failureDetectionTimeout` | Тайм-аут для основных сетевых операций серверных узлов, мс | `10000` |
| `IgniteConfiguration.clientFailureDetectionTimeout` | Тайм-аут для основных сетевых операций клиентских узлов, мс | `30000` |

В примере ниже показано, как установить тайм-аут обнаружения сбоев в конфигурации узла. Значения по умолчанию обеспечивают надежную работу механизма Discovery SPI в большинстве развертываний в локальных системах и контейнерах. В стабильных сетях с низкими показателями задержки можно установить значение параметра на примерно 200 мс, чтобы быстрее обнаруживать сбои и реагировать на них.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">

        <property name="failureDetectionTimeout" value="5000"/>

        <property name="clientFailureDetectionTimeout" value="10000"/>

    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setFailureDetectionTimeout(5_000);

cfg.setClientFailureDetectionTimeout(10_000);
```
:::
::::