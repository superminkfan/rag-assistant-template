# Конфигурация регионов данных

## Введение

DataGrid использует концепцию регионов данных для управления объемом оперативной памяти, которая доступна кешу или кеш-группе. Регион данных — логическая расширяемая область в оперативной памяти, в которой хранятся кешированные данные. Начальный и максимальный размеры региона данных можно настраивать. Также можно контролировать настройки персистентности для кешей — подробнее об этом написано в подразделе [«Персистентность DataGrid»](datagrid_persistence.md) раздела «Настройка Persistence».

По умолчанию при запуске DataGrid создается один регион данных с автоматически заданными начальным и максимальным размерами. Начальный размер составляет 256 Мб, максимальный — 20% от всей доступной узлу оперативной памяти. Все создаваемые кеши хранятся в этом регионе. Пользователи могут настраивать начальный и максимальный размеры автоматически созданного региона данных по своему усмотрению. Количество регионов данных для создания не ограничено. Ситуации, в которых стоит рассмотреть добавление дополнительных регионов:

- Настройка объема памяти, доступной кешу или кеш-группе, которые используют один регион данных.
- Конфигурация способа хранения данных — только в памяти (In-memory) или в памяти и на диске (Persistence). Способ хранения конфигурируется на уровне настроек региона данных, поэтому этот способ является единым для всех кешей, которые используют один регион данных. В этом случае настройте два и более региона с разными persistence-параметрами: один для in-memory-кешей, другой — для persistence-кешей. По умолчанию данные кешей не записываются на диск и хранятся только в оперативной памяти.
- Настройка политики хранения, например политики вытеснения данных — подробнее написано в разделе [«Политика вытеснения данных из кеша (Eviction Policies)»](eviction_policies.md). Политики хранения данных настраиваются отдельно для каждого региона.

Ниже описывается, как изменить параметры региона данных по умолчанию и настроить несколько регионов.

## Настройка региона данных по умолчанию

Новый кеш добавляется в регион данных, который указан по умолчанию. Изменить свойства региона данных по умолчанию можно с помощью конфигурации хранения данных.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
                <!--
                Область памяти, к которой привязаны все кеши, если в их конфигурации не указан другой регион.
                -->
                <property name="defaultDataRegionConfiguration">
                    <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                        <property name="name" value="Default_Region"/>
                        <!-- Область памяти объемом 100 Мб с отключенным вытеснением. -->
                        <property name="initialSize" value="#{100 * 1024 * 1024}"/>
                    </bean>
                </property>
            </bean>
        </property>
        <!-- Другие свойства. -->
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
public class DataRegionConfigurationExample {

    public static void main(String[] args) {

        DataStorageConfiguration storageCfg = new DataStorageConfiguration();

        DataRegionConfiguration defaultRegion = new DataRegionConfiguration();
        defaultRegion.setName("Default_Region");
        defaultRegion.setInitialSize(100 * 1024 * 1024);

        storageCfg.setDefaultDataRegionConfiguration(defaultRegion);

        IgniteConfiguration cfg = new IgniteConfiguration();

        cfg.setDataStorageConfiguration(storageCfg);

        // Запустите узел.
        Ignite ignite = Ignition.start(cfg);

        ignite.close();
    }
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        DefaultDataRegionConfiguration = new DataRegionConfiguration
        {
            Name = "Default_Region",
            InitialSize = 100 * 1024 * 1024
        }
    }
};

// Запустите узел.
var ignite = Ignition.Start(cfg);
```
:::
::::

## Добавление пользовательских регионов данных

Кроме региона данных, который доступен по умолчанию, можно добавить дополнительные области с пользовательскими настройками. В примере ниже настраивается область данных, которая может занимать до 40 Мб и использовать политику вытеснения данных Random-2-LRU — подробнее о ней написано в разделе [«Политика вытеснения данных из кеша (Eviction Policies)»](eviction_policies.md). В конфигурации создается кеш, который находится в новой области данных.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
                <!--
                Область памяти, к которой привязаны все кеши, если в их конфигурации не указан другой регион.
                -->
                <property name="defaultDataRegionConfiguration">
                    <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                        <property name="name" value="Default_Region"/>
                        <!-- Область памяти объемом 100 Мб с отключенным вытеснением. -->
                        <property name="initialSize" value="#{100 * 1024 * 1024}"/>
                    </bean>
                </property>
                <property name="dataRegionConfigurations">
                    <list>
                        <!--
                        Область памяти объемом 40 Мб с включенным вытеснением.
                        -->
                        <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                            <property name="name" value="40MB_Region_Eviction"/>
                            <!-- Область памяти с начальным размером 20 Мб. -->
                            <property name="initialSize" value="#{20 * 1024 * 1024}"/>
                            <!-- Максимальный размер — 40 Мб. -->
                            <property name="maxSize" value="#{40 * 1024 * 1024}"/>
                            <!-- Включение вытеснения для этой области памяти. -->
                            <property name="pageEvictionMode" value="RANDOM_2_LRU"/>
                        </bean>
                    </list>
                </property>
            </bean>
        </property>
        <property name="cacheConfiguration">
            <list>
                <!-- Кеш, который сопоставлен с определенной областью данных. -->
                <bean class="org.apache.ignite.configuration.CacheConfiguration">

                    <property name="name" value="SampleCache"/>
                    <!--
                    Присвоение кешу региона `40MB_Region_Eviction`.
                    -->
                    <property name="dataRegionName" value="40MB_Region_Eviction"/>
                </bean>
            </list>
        </property>
        <!-- Другие свойства. -->
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
DataStorageConfiguration storageCfg = new DataStorageConfiguration();

DataRegionConfiguration defaultRegion = new DataRegionConfiguration();
defaultRegion.setName("Default_Region");
defaultRegion.setInitialSize(100 * 1024 * 1024);

storageCfg.setDefaultDataRegionConfiguration(defaultRegion);
// Область памяти объемом 40 Мб с включенным вытеснением.
DataRegionConfiguration regionWithEviction = new DataRegionConfiguration();
regionWithEviction.setName("40MB_Region_Eviction");
regionWithEviction.setInitialSize(20 * 1024 * 1024);
regionWithEviction.setMaxSize(40 * 1024 * 1024);
regionWithEviction.setPageEvictionMode(DataPageEvictionMode.RANDOM_2_LRU);

storageCfg.setDataRegionConfigurations(regionWithEviction);

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setDataStorageConfiguration(storageCfg);

CacheConfiguration cache1 = new CacheConfiguration("SampleCache");
// Данный кеш будет находиться в регионе данных `40MB_Region_Eviction`.
cache1.setDataRegionName("40MB_Region_Eviction");

cfg.setCacheConfiguration(cache1);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        DefaultDataRegionConfiguration = new DataRegionConfiguration
        {
            Name = "Default_Region",
            InitialSize = 100 * 1024 * 1024
        },
        DataRegionConfigurations = new[]
        {
            new DataRegionConfiguration
            {
                Name = "40MB_Region_Eviction",
                InitialSize = 20 * 1024 * 1024,
                MaxSize = 40 * 1024 * 1024,
                PageEvictionMode = DataPageEvictionMode.Random2Lru
            },
            new DataRegionConfiguration
            {
                Name = "30MB_Region_Swapping",
                InitialSize = 15 * 1024 * 1024,
                MaxSize = 30 * 1024 * 1024,
                SwapPath = "/path/to/swap/file"
            }
        }
    }
};
Ignition.Start(cfg);
```
:::
::::

## Стратегия предварительного прогрева кешей

DataGrid не требует предварительного прогрева памяти с диска при перезапуске. Как только кластер соединился с приложением, оно может запускать запросы и вычисления. Функция предварительного прогрева памяти предназначена для приложений с низким временем задержки (low-latency) — им требуется загрузка данных в память перед выполнением запросов.

Сейчас стратегия предварительного прогрева DataGrid предполагает загрузку данных во все или в конкретные регионы данных, начиная с индексов, пока не закончится свободное место на диске. Память можно настроить для всех областей данных (по умолчанию) и отдельно для каждой области.

Чтобы настроить прогрев всех регионов данных, передайте параметр конфигурации `LoadAllWarmUpStrategy` в `DataStorageConfiguration#setDefaultWarmUpConfiguration`.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="dataStorageConfiguration">
        <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
            <property name="defaultWarmUpConfiguration">
                <bean class="org.apache.ignite.configuration.LoadAllWarmUpConfiguration"/>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Изменение стратегии прогрева по умолчанию для всех регионов данных.
storageCfg.setDefaultWarmUpConfiguration(new LoadAllWarmUpConfiguration());

cfg.setDataStorageConfiguration(storageCfg);
```
:::
::::

Чтобы настроить прогрев определенного региона данных, передайте параметр конфигурации `LoadAllWarmUpStrategy` в `DataStorageConfiguration#setWarmUpConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
<property name="dataStorageConfiguration">
    <property name="dataRegionConfigurations">
        <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
            <property name="name" value="NewDataRegion"/>
            <property name="initialSize" value="#{100 * 1024 * 1024}"/>
            <property name="persistenceEnabled" value="true"/>
            <property name="warmUpConfiguration">
                <bean class="org.apache.ignite.configuration.LoadAllWarmUpConfiguration"/>
            </property>
        </bean>
    </property>
</property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Установите другую стратегию прогрева для пользовательского региона данных.
DataRegionConfiguration myNewDataRegion = new DataRegionConfiguration();

myNewDataRegion.setName("NewDataRegion");

// Можно настроить начальный размер и другие параметры.
myNewDataRegion.setInitialSize(100 * 1024 * 1024);

// Выполнение загрузки данных с диска в DRAM при перезапуске.
myNewDataRegion.setWarmUpConfiguration(new LoadAllWarmUpConfiguration());

// Подключение персистентности регионов данных. DataGrid считывает данные с диска при запросе таблиц/кешей из этого региона.
myNewDataRegion.setPersistenceEnabled(true);

// Применение настроек.
storageCfg.setDataRegionConfigurations(myNewDataRegion);

cfg.setDataStorageConfiguration(storageCfg);
```
:::
::::

Чтобы отключить прогрев кешей для всех регионов данных, передайте конфигурационный параметр `NoOpWarmUpConfiguration` в `DataStorageConfiguration#setDefaultWarmUpConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
<property name="dataStorageConfiguration">
    <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
        <property name="defaultWarmUpConfiguration">
            <bean class="org.apache.ignite.configuration.NoOpWarmUpConfiguration"/>
        </property>
    </bean>
</property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

DataStorageConfiguration storageCfg = new DataStorageConfiguration();

storageCfg.setDefaultWarmUpConfiguration(new NoOpWarmUpConfiguration());

cfg.setDataStorageConfiguration(storageCfg);
```
:::
::::

Чтобы отключить прогрев кешей для определенного региона данных, передайте конфигурационный параметр `NoOpWarmUpStrategy` в `DataStorageConfiguration#setWarmUpConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
<property name="dataStorageConfiguration">
    <property name="dataRegionConfigurations">
        <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
            <property name="name" value="NewDataRegion"/>
            <property name="initialSize" value="#{100 * 1024 * 1024}"/>
            <property name="persistenceEnabled" value="true"/>
            <property name="warmUpConfiguration">
                <bean class="org.apache.ignite.configuration.NoOpWarmUpConfiguration"/>
            </property>
        </bean>
    </property>
</property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Установите другую стратегию прогрева для пользовательского региона данных.
DataRegionConfiguration myNewDataRegion = new DataRegionConfiguration();

myNewDataRegion.setName("NewDataRegion");

// Можно настроить начальный размер и другие параметры.
myNewDataRegion.setInitialSize(100 * 1024 * 1024);

// Выполнение загрузки данных с диска в DRAM при перезапуске.
myNewDataRegion.setWarmUpConfiguration(new NoOpWarmUpConfiguration());

// Подключение персистентности регионов данных. DataGrid считывает данные с диска при запросе таблиц/кешей из этого региона.
myNewDataRegion.setPersistenceEnabled(true);

// Применение настроек.
storageCfg.setDataRegionConfigurations(myNewDataRegion);

cfg.setDataStorageConfiguration(storageCfg);
```
:::
::::

Прогрев региона данных можно остановить через утилиту `control.sh` или JMX.

Пример, как выполнить остановку прогрева через утилиту `control.sh`:

```bash
control.sh --warm-up --stop --yes
```

Пример, как выполнить остановку прогрева через JMX:

```bash
org.apache.ignite.mxbean.WarmUpMXBean#stopWarmUp
```