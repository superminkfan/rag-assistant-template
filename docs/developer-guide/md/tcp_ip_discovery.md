# TCP/IP Discovery

В DataGrid узлы могут обнаруживать друг друга с помощью механизма `DiscoverySpi`. Его реализация по умолчанию — объект `TcpDiscoverySpi`, который использует протокол TCP/IP для поиска узлов. Discovery SPI можно настроить для обнаружения узлов на основе протокола Multicast и фиксированного списка IP-адресов.

## Поиск узлов с помощью Multicast IP Finder

Для обнаружения узлов с помощью Multicast укажите `TcpDiscoveryMulticastIpFinder` в настройках `TcpDiscoverySpi`. В DataGrid этот способ используется по умолчанию.

Пример настройки `TcpDiscoveryMulticastIpFinder`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.multicast.TcpDiscoveryMulticastIpFinder">
                    <property name="multicastGroup" value="xxx.xx.xx.xxx"/>
                </bean>
            </property>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
TcpDiscoverySpi spi = new TcpDiscoverySpi();

TcpDiscoveryMulticastIpFinder ipFinder = new TcpDiscoveryMulticastIpFinder();

ipFinder.setMulticastGroup("xxx.xx.xx.xxx");

spi.setIpFinder(ipFinder);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DiscoverySpi = new TcpDiscoverySpi
    {
        IpFinder = new TcpDiscoveryMulticastIpFinder
        {
            MulticastGroup = "xxx.xx.xx.xxx"
        }
    }
};
Ignition.Start(cfg);
```
:::
::::

## Поиск узлов по фиксированному списку IP-адресов

`TcpDiscoveryVmIpFinder` — другая реализация механизма обнаружения. Она обеспечивает поиск узлов DataGrid на основании указанного в конфигурации списка IP-адресов или их названий (host name).

Для начала поиска нужно указать как минимум один адрес удаленного узла (желательно указать адреса всех узлов кластера). Когда установится соединение с любым из указанных IP-адресов, DataGrid автоматически обнаружит все остальные узлы.

:::{admonition} Важно
:class: attention

IP-адреса можно указывать не только в конфигурации, но и в переменной среды `IGNITE_TCP_DISCOVERY_ADDRESSES` или одноименном системном параметре JVM. Адреса нужно разделять запятыми, в них можно дополнительно прописать диапазон портов.
:::

:::{admonition} Примечание
:class: note

По умолчанию `TcpDiscoveryVmIpFinder` используется в режиме `non-shared`. Чтобы запустить серверный узел в этом режиме, в списке адресов дополнительно укажите адрес локального узла. Это позволит ему стать первым узлом кластера и не ждать присоединения других серверных узлов.
:::

Настроить фиксированный список IP-адресов можно с помощью XML или программно.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder">
                    <property name="addresses">
                        <list>
                            <!--
                              Для запуска и нормальной работы локального узла укажите его адрес, даже если в кластере больше нет узлов.
                              Можно дополнительно указать отдельный порт или диапазон портов.
                              -->
                            <value>x.x.x.x</value>
                            <!--
                              IP-адрес и дополнительный диапазон портов для удаленного узла.
                              Можно также указать отдельный порт.
                              -->
                            <value>x.x.x.x:47500..47509</value>
                        </list>
                    </property>
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
TcpDiscoverySpi spi = new TcpDiscoverySpi();

TcpDiscoveryVmIpFinder ipFinder = new TcpDiscoveryVmIpFinder();

// Установите исходные IP-адреса.
// Можно дополнительно указать порт или диапазон портов.
ipFinder.setAddresses(Arrays.asList("x.x.x.x", "x.x.x.x:47500..47509"));

spi.setIpFinder(ipFinder);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DiscoverySpi = new TcpDiscoverySpi
    {
        IpFinder = new TcpDiscoveryStaticIpFinder
        {
            Endpoints = new[] {"x.x.x.x", "x.x.x.x:47500..47509" }
        }
    }
};
```
:::

:::{md-tab-item} Shell-скрипт
```shell
# В конфигурации нужно использовать `TcpDiscoveryVmIpFinder` без указания адресов.
IGNITE_TCP_DISCOVERY_ADDRESSES=x.x.x.x,x.x.x.x:47500..47509
bin/ignite.sh -v config/default-config.xml
```
:::
::::

:::{admonition} Внимание
:class: danger

Указывать нужно только адреса, по которым располагаются узлы кластера. Если указать много недоступных адресов, время запуска узла увеличится, так как он будет пытаться подключиться по всем указанным адресам.
:::

## Поиск узлов с помощью протокола Multicast и фиксированного списка IP-адресов

`TCPDiscoveryMulticastIpFinder` позволяет искать узлы одновременно по фиксированному списку IP-адресов и с помощью протокола Multicast.

Пример настройки:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.multicast.TcpDiscoveryMulticastIpFinder">
                    <property name="multicastGroup" value="xxx.xx.xx.xxx"/>
                    <!-- Фиксированный список IP-адресов. -->
                    <property name="addresses">
                        <list>
                            <value>x.x.x.x</value>
                            <!--
                              IP-адрес и дополнительный диапазон портов.
                              Можно также указать отдельный порт.
                             -->
                            <value>x.x.x.x:47500..47509</value>
                        </list>
                    </property>
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
TcpDiscoverySpi spi = new TcpDiscoverySpi();

TcpDiscoveryMulticastIpFinder ipFinder = new TcpDiscoveryMulticastIpFinder();

// Установите группу Multicast.
ipFinder.setMulticastGroup("xxx.xx.xx.xxx");

// Установите исходные IP-адреса.
// Можно дополнительно указать порт или диапазон портов.
ipFinder.setAddresses(Arrays.asList("x.x.x.x", "x.x.x.x:47500..47509"));

spi.setIpFinder(ipFinder);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C++
```c++
var cfg = new IgniteConfiguration
{
    DiscoverySpi = new TcpDiscoverySpi
    {
        IpFinder = new TcpDiscoveryMulticastIpFinder
        {
            MulticastGroup = "xxx.xx.xx.xxx",
            Endpoints = new[] {"x.x.x.x", "x.x.x.x:47500..47509" }
        }
    }
};
Ignition.Start(cfg);
```
:::
::::

## Изолированные кластеры на одном наборе машин

В DataGrid можно запустить два изолированных кластера на одном и том же наборе машин, если узлы из разных кластеров используют разные диапазоны локальных портов для `TCPDiscoverySpi` и `TCPCommunicationSpi`.

Ниже пример, как запустить два изолированных кластера для тестирования на одной машине.

Пример конфигурации `TCPDiscoverySpi` и `TCPCommunicationSpi` для узлов первого кластера:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <!--
    Настройте TCP Discovery SPI для узлов первого кластера.
    -->
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <!-- Исходный локальный порт. -->
            <property name="localPort" value="48500"/>

            <!-- Опциональное изменение диапазона локальных портов. -->
            <property name="localPortRange" value="20"/>

            <!-- Установите IP Finder для текущего кластера. -->
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder">
                    <property name="addresses">
                        <list>
                            <!--
                            IP-адреса и диапазон портов узлов первого кластера.
                            xxx.x.x.x замените актуальными IP-адресами или хостами.
                            Диапазон портов указывать не обязательно.
                            -->
                            <value>xxx.x.x.x:48500..48520</value>
                        </list>
                    </property>
                </bean>
            </property>
        </bean>
    </property>

    <!--
    Настройте порт TCP Communication SPI для узлов первого кластера.
    -->
    <property name="communicationSpi">
        <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
            <property name="localPort" value="48100"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration firstCfg = new IgniteConfiguration();

firstCfg.setIgniteInstanceName("first");

// Настройте TCP Discovery SPI для узлов первого кластера.
TcpDiscoverySpi firstDiscoverySpi = new TcpDiscoverySpi();

// Исходный локальный порт.
firstDiscoverySpi.setLocalPort(48500);

// Можно дополнительно изменить диапазон локальных портов.
firstDiscoverySpi.setLocalPortRange(20);

TcpDiscoveryVmIpFinder firstIpFinder = new TcpDiscoveryVmIpFinder();

// IP-адреса и диапазон портов узлов первого кластера.
// xxx.x.x.x замените актуальными IP-адресами или портами.
// Диапазон портов указывать не обязательно.
firstIpFinder.setAddresses(Collections.singletonList("xxx.x.x.x:48500..48520"));

// Переопределите IP Finder.
firstDiscoverySpi.setIpFinder(firstIpFinder);

// Настройте порт TCP Communication SPI для узлов первого кластера.
TcpCommunicationSpi firstCommSpi = new TcpCommunicationSpi();

firstCommSpi.setLocalPort(48100);

// Переопределите Discovery SPI.
firstCfg.setDiscoverySpi(firstDiscoverySpi);

// Переопределите Communication SPI.
firstCfg.setCommunicationSpi(firstCommSpi);

// Запустите узел.
Ignition.start(firstCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var firstCfg = new IgniteConfiguration
{
    IgniteInstanceName = "first",
    DiscoverySpi = new TcpDiscoverySpi
    {
        LocalPort = 48500,
        LocalPortRange = 20,
        IpFinder = new TcpDiscoveryStaticIpFinder
        {
            Endpoints = new[]
            {
                "xxx.x.x.x:48500..48520"
            }
        }
    },
    CommunicationSpi = new TcpCommunicationSpi
    {
        LocalPort = 48100
    }
};
Ignition.Start(firstCfg);
```
:::
::::

Пример конфигурации `TCPDiscoverySpi` и `TCPCommunicationSpi` для узлов второго кластера:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean id="ignite.cfg" class="org.apache.ignite.configuration.IgniteConfiguration">
    <!--
    Настройте TCP Discovery SPI для узлов второго кластера.
    -->
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <!-- Исходный локальный порт. -->
            <property name="localPort" value="49500"/>

            <!-- Опциональное изменение диапазона локальных портов. -->
            <property name="localPortRange" value="20"/>

            <!-- Установите IP Finder для текущего кластера. -->
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder">
                    <property name="addresses">
                        <list>
                            <!--
                            IP-адреса и диапазон портов узлов второго кластера.
                            xxx.x.x.x замените актуальными IP-адресами или хостами. Диапазон портов опционален.
                            -->
                            <value>xxx.x.x.x:49500..49520</value>
                        </list>
                    </property>
                </bean>
            </property>
        </bean>
    </property>

    <!--     
     Настройте порт TCP Communication SPI для узлов второго кластера.
    -->
    <property name="communicationSpi">
        <bean class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
            <property name="localPort" value="49100"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration secondCfg = new IgniteConfiguration();

secondCfg.setIgniteInstanceName("second");

// Настройте TCP Discovery SPI для узлов второго кластера.
TcpDiscoverySpi secondDiscoverySpi = new TcpDiscoverySpi();

// Исходный локальный порт.
secondDiscoverySpi.setLocalPort(49500);

// Можно дополнительно изменить диапазон локальных портов. 
secondDiscoverySpi.setLocalPortRange(20);

TcpDiscoveryVmIpFinder secondIpFinder = new TcpDiscoveryVmIpFinder();

// IP-адреса и диапазон портов узлов второго кластера.
// xxx.x.x.x замените актуальными IP-адресами или хостами.
// Диапазон портов указывать не обязательно.
secondIpFinder.setAddresses(Collections.singletonList("xxx.x.x.x:49500..49520"));

// Переопределите IP Finder.
secondDiscoverySpi.setIpFinder(secondIpFinder);

// Настройте порт TCP Сommunication SPI для узлов второго кластера.
TcpCommunicationSpi secondCommSpi = new TcpCommunicationSpi();

secondCommSpi.setLocalPort(49100);

// Переопределите Discovery SPI.
secondCfg.setDiscoverySpi(secondDiscoverySpi);

// Переопределите Communication SPI.
secondCfg.setCommunicationSpi(secondCommSpi);

// Запустите узел.
Ignition.start(secondCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var secondCfg = new IgniteConfiguration
{
    IgniteInstanceName = "second",
    DiscoverySpi = new TcpDiscoverySpi
    {
        LocalPort = 49500,
        LocalPortRange = 20,
        IpFinder = new TcpDiscoveryStaticIpFinder
        {
            Endpoints = new[]
            {
                "xxx.x.x.x:49500..49520"
            }
        }
    },
    CommunicationSpi = new TcpCommunicationSpi
    {
        LocalPort = 49100
    }
};
Ignition.Start(secondCfg);
```
:::
::::

Конфигурации узлов отличаются только номерами портов для SPI и IP Finder.

:::{admonition} Примечание
:class: note

Чтобы узлы из разных кластеров могли обнаружить друг друга с помощью протокола Multicast, замените `TCPDiscoveryVmIpFinder` на `TCPDiscoveryMulticastIpFinder` и установите уникальный `TCPDiscoveryMulticastIpFinder.multicastGroups` в обеих конфигурациях.
:::

:::{admonition} Внимание
:class: danger

Если в изолированных кластерах есть персистентные регионы данных, в каждом кластере персистентные файлы должны располагаться по разным путям в файловой системе. Подробнее об изменениях каталогов персистентных файлов написано в подразделе [«Персистентность DataGrid»](datagrid_persistence.md) раздела «Настройка Persistence».
:::

## IP Finder на основе JDBC

:::{admonition} Примечание
:class: note

Не поддерживается на языках .NET, C# и C++.
:::

База данных может использоваться как общее хранилище исходных IP-адресов. При запуске узлы будут отправлять базе данных свои IP-адреса через `TcpDiscoveryJdbcIpFinder`.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

  <property name="discoverySpi">
    <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
      <property name="ipFinder">
        <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.jdbc.TcpDiscoveryJdbcIpFinder">
          <property name="dataSource" ref="ds"/>
        </bean>
      </property>
    </bean>
  </property>
</bean>

<!-- Настроенный экземпляр Data Source. -->
<bean id="ds" class="some.Datasource">

</bean>
```
:::

:::{md-tab-item} Java
```java
TcpDiscoverySpi spi = new TcpDiscoverySpi();

// Настройте Data Source.
DataSource someDs = new MySampleDataSource();

TcpDiscoveryJdbcIpFinder ipFinder = new TcpDiscoveryJdbcIpFinder();

ipFinder.setDataSource(someDs);

spi.setIpFinder(ipFinder);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

## IP Finder на основе общей папки в файловой системе

:::{admonition} Примечание
:class: note

Не поддерживается на языках .NET, C# и C++.
:::

Общая папка в файловой системе может использоваться как хранилище IP-адресов узлов. При запуске узлы будут отправлять в папку файловой системы свои IP-адреса через `TCPDiscoverySharedFsIpFinder`.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.sharedfs.TcpDiscoverySharedFsIpFinder">
                  <property name="path" value="/var/ignite/addresses"/>
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
// Настройте Discovery SPI.
TcpDiscoverySpi spi = new TcpDiscoverySpi();

// Настройте IP Finder.
TcpDiscoverySharedFsIpFinder ipFinder = new TcpDiscoverySharedFsIpFinder();

ipFinder.setPath("/var/ignite/addresses");

spi.setIpFinder(ipFinder);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

## ZooKeeper IP Finder

:::{admonition} Примечание
:class: note

Не поддерживается на языках .NET и C#.
:::

Модуль ZooKeeper IP Finder предоставляет TCP Discovery IP Finder, который использует каталог ZooKeeper, чтобы искать узлы DataGrid для подключения. Не следует путать модуль ZooKeeper IP Finder и механизм обнаружения ZooKeeper Discovery SPI.

### Установка

В поставке DataGrid нет модуля ZooKeeper IP Finder. Для установки соберите модуль из [GitHub Apache Ignite](https://github.com/apache/ignite-extensions/tree/master/modules/zookeeper-ip-finder-ext).

После сборки модуль можно установить одним из способов:

- переместите `ignite-zookeeper-ip-finder-ext` в каталог `lib` перед запуском узла;
- добавьте библиотеки из `ignite-zookeeper-ip-finder-ext` в classpath приложения;
- добавьте модуль в качестве зависимости Maven в проект.

### Настройка

Для настройки ZooKeeper IP Finder укажите `TcpDiscoveryZookeeperIpFinder` в конфигурации `TcpDiscoverySpi`.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="discoverySpi">
        <bean class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
            <property name="ipFinder">
                <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.zk.TcpDiscoveryZookeeperIpFinder">
                    <property name="zkConnectionString" value="xxx.x.x.x:2181"/>
                </bean>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
TcpDiscoverySpi spi = new TcpDiscoverySpi();
 
TcpDiscoveryZookeeperIpFinder ipFinder = new TcpDiscoveryZookeeperIpFinder();
 
// Укажите строку подключения ZooKeeper.
ipFinder.setZkConnectionString("xxx.x.x.x:2181");
 
spi.setIpFinder(ipFinder);
 
IgniteConfiguration cfg = new IgniteConfiguration();
 
// Переопределите Discovery SPI по умолчанию.
cfg.setDiscoverySpi(spi);
 
// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

Модуль зависит от сторонних библиотек, которые используют фасад `SLF4J` для логирования. Фреймворк логирования можно настроить самостоятельно.