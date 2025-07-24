# Настройка Persistence

В разделе собраны оптимальные методики настройки персистентности DataGrid. Если для обеспечения постоянного хранения данных используется внешнее (стороннее) хранилище, обратитесь к руководствам по производительности поставщика.

## Настройка размера страницы

Значение параметра `DataStorageConfiguration.pageSize` не должно быть ниже минимального из значений размеров страницы носителя (SSD, Flash, HDD и так далее) и страницы кеша операционной системы. Значение по умолчанию — 4 Кб. Размер страницы кеша операционной системы можно проверить с помощью системных инструментов и параметров.

Размер страницы устройства хранения данных, например SSD-накопителя, обычно указан в спецификации устройства. Если производитель не раскрывает информацию, запустите тесты SSD, чтобы выяснить это число. Многим производителям приходится адаптировать свои драйверы для рабочих нагрузок произвольной записи размером 4 Кб, так как различные стандартные тесты производительности по умолчанию используют это значение.

Ниже пример, как настроить размер страницы в конфигурации кластера.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">

                <!-- Установите размер страницы 8 Кб. -->
                <property name="pageSize" value="#{8 * 1024}"/>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Надежная конфигурация памяти.
DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Изменение размера страницы на 8 Кб.
storageCfg.setPageSize(8192);

cfg.setDataStorageConfiguration(storageCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        // Изменение размера страницы на 4 Кб.
        PageSize = 4096
    }
};
```
:::
::::

## Хранение WAL отдельно

Рекомендуется рассмотреть возможность использовать отдельные диски для файлов данных и WAL-журнала. DataGrid активно записывает и данные, и WAL-файлы.

Ниже пример, как настроить отдельные пути для хранилища данных, WAL и WAL-архива.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">

                <!--
                    Устанавливает путь к корневому каталогу, где хранятся данные и индексы.
                    Предполагается, что каталог находится на отдельном SSD-накопителе.
                -->
                <property name="storagePath" value="/opt/persistence"/>
                <property name="walPath" value="/opt/wal"/>
                <property name="walArchivePath" value="/opt/wal-archive"/>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Настройка Native Persistence.
DataStorageConfiguration storeCfg = new DataStorageConfiguration();

// Устанавливает путь к каталогу, где хранятся данные и индексы.
// Предполагается, что каталог находится на отдельном SSD-накопителе.
storeCfg.setStoragePath("/ssd/storage");

// Устанавливает путь к каталогу, где хранится WAL.
// Предполагается, что каталог находится на отдельном HDD-накопителе.
storeCfg.setWalPath("/wal");

// Устанавливает путь к каталогу, где хранится WAL-архив.
// Каталог находится на том же HDD-накопителе, что и WAL.
storeCfg.setWalArchivePath("/wal/archive");

cfg.setDataStorageConfiguration(storeCfg);

// Запуск узла.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        // Устанавливает путь к корневому каталогу, где хранятся данные и индексы.
        // Предполагается, что каталог находится на отдельном SSD-накопителе.
        StoragePath = "/ssd/storage",

        // Устанавливает путь к каталогу, где хранится WAL.
        // Предполагается, что каталог находится на отдельном HDD-накопителе.
        WalPath = "/wal",

        // Устанавливает путь к каталогу, где хранится WAL-архив.
        // Каталог находится на том же HDD-накопителе, что и WAL.
        WalArchivePath = "/wal/archive"
    }
};
```
:::
::::

## Увеличение размера сегмента WAL

Размер сегмента WAL по умолчанию (64 Мб) может быть неэффективным для сценариев с высокой нагрузкой. WAL будет слишком часто переключаться между сегментами, а переключение (ротация) — дорогостоящая операция. Установка большего размера сегмента (до 2 Гб) может помочь уменьшить количество операций переключения. Это увеличит общий объем WAL-журнала.

Подробнее об этом написано в подразделе «Изменение размера WAL-сегмента» раздела [«Персистентность DataGrid»](datagrid_persistence.md).

## Изменение режима WAL

Рекомендуется рассмотреть другие режимы WAL в качестве альтернативы режиму по умолчанию. Каждый режим дает разную степень надежности в случае выпадения узла, и эта степень обратно пропорциональна скорости. То есть чем надежнее режим WAL, тем он медленнее. Если использование WAL не требует высокой надежности, можно переключиться на менее надежный (более быстрый) режим.

Подробнее об этом написано в подразделе «Режимы WAL» раздела [«Персистентность DataGrid»](datagrid_persistence.md).

## Отключение WAL

Иногда отключение WAL может повысить эффективность. Подробнее об этом написано в подразделе «Отключение WAL» раздела [«Персистентность DataGrid»](datagrid_persistence.md).

## Регулирование записи страниц (throttling)

DataGrid периодически запускает процесс checkpoint (контрольные точки), который переносит «грязные» страницы из памяти на диск. «Грязная» страница — страница, которая обновилась в оперативной памяти, но не записалась в соответствующий файл партиций (обновление было добавлено только в WAL). Данный процесс происходит в фоновом режиме, не затрагивая логику приложения.

Если «грязная» страница, которая запланирована для проверки checkpoint, обновится перед записью на диск, ее предыдущее состояние скопируется в специальную область — checkpoint-буфер (буфер контрольных точек). Если буфер переполнится, DataGrid остановит обработку всех обновлений до тех пор, пока не закончится Сheckpoint. Пока не завершится цикл checkpoint, производительность записи может упасть до нуля.

Такая же ситуация произойдет, если порог «грязных» страниц будет достигнут во время выполнения checkpoint. DataGrid запланирует еще одно выполнение checkpoint и остановит все операции обновления до тех пор, пока не завершится первый процесс.

Обе ситуации обычно возникают, когда дисковое устройство работает медленно или скорость обновления слишком высокая. Чтобы смягчить и предотвратить снижение производительности, включите алгоритм регулирования записи страниц. Он снижает производительность операций обновления до скорости дискового устройства, когда checkpoint-буфер заполняется слишком быстро или процент «грязных» страниц резко возрастает.

Ниже пример, как включить регулирование записи страниц.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">

                <property name="writeThrottlingEnabled" value="true"/>

            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Настройка Native Persistence.
DataStorageConfiguration storeCfg = new DataStorageConfiguration();

// Подключение регулирования (throttling) записи страниц.
storeCfg.setWriteThrottlingEnabled(true);

cfg.setDataStorageConfiguration(storeCfg);

// Запуск узла.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        WriteThrottlingEnabled = true
    }
};
```
:::
::::

## Настройка размера Checkpoint-буфера

Размер буфера контрольных точек (Checkpoint-буфер) — одна из причин запуска процесса Checkpoint.

Размер буфера по умолчанию рассчитывается в зависимости от размера региона данных:

| Размер региона данных | Размер Checkpoint-буфера по умолчанию |
|---|---|
| Меньше 1 Гб | `MIN` (256 Мб, `Data_Region_Size`) |
| От 1 до 8 Гб | `Data_Region_Size / 4` |
| Больше 8 Гб | 2 Гб |

Подробнее о регионах данных написано в подразделе [«Конфигурация регионов данных»](configuration_of_data_regions.md) раздела «Настройка памяти».

Размер буфера по умолчанию может быть неоптимальным для рабочих нагрузок с интенсивным объемом записи. Алгоритм регулирования записи страниц замедляет запись каждый раз, когда размер достигает критической отметки. Чтобы поддерживать желаемую скорость записи во время процесса Checkpoint, увеличьте `DataRegionConfiguration.checkpointPageBufferSize`. Чтобы предотвратить снижение производительности, включите регулирования записи страниц.

В примере ниже размер Checkpoint-буфера региона данных по умолчанию составляет 1 Гб.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="dataStorageConfiguration">
            <bean class="org.apache.ignite.configuration.DataStorageConfiguration">

                <property name="writeThrottlingEnabled" value="true"/>

                <property name="defaultDataRegionConfiguration">
                    <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                        <!-- Включение режима Persistence. -->
                        <property name="persistenceEnabled" value="true"/>
                        <!-- Увеличение размера буфера до 1 Гб. -->
                        <property name="checkpointPageBufferSize" value="#{1024L * 1024 * 1024}"/>
                    </bean>
                </property>

            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

// Настройка Native Persistence.
DataStorageConfiguration storeCfg = new DataStorageConfiguration();

// Включение регулирования (throttling) записи страниц.
storeCfg.setWriteThrottlingEnabled(true);

// Увеличение размера буфера до 1 Гб.
storeCfg.getDefaultDataRegionConfiguration().setCheckpointPageBufferSize(1024L * 1024 * 1024);

cfg.setDataStorageConfiguration(storeCfg);

// Запуск узла.
Ignite ignite = Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        WriteThrottlingEnabled = true,
        DefaultDataRegionConfiguration = new DataRegionConfiguration
        {
            Name = DataStorageConfiguration.DefaultDataRegionName,
            PersistenceEnabled = true,

            // Увеличение размера буфера до 1 Гб.
            CheckpointPageBufferSize = 1024L * 1024 * 1024
        }
    }
};
```
:::
::::

## Включение прямого ввода-вывода

Обычно когда приложение считывает данные с диска, сначала операционная система получает данные и помещает их в файловый буферный кеш. Аналогично для каждой операции записи система сначала записывает данные в кеш, а затем переносит их на диск. Чтобы исключить этот процесс, включите прямой ввод-вывод (Direct I/O): данные будут считываться и записываться непосредственно с диска и на диск, минуя файловый буферный кеш.

Модуль прямого ввода-вывода используется в DataGrid для ускорения процесса создания контрольной точки (checkpoint), который записывает «грязные» страницы из оперативной памяти на диск. Рекомендуется рассмотреть возможность использования плагина прямого ввода-вывода для рабочих нагрузок с интенсивной записью.

:::{admonition} Прямой ввод-вывод и WAL
:class: hint

Прямой ввод-вывод нельзя включить специально для файлов WAL. Включение модуля Direct I/O даст небольшое преимущество в отношении файлов WAL: данные WAL не будут храниться в буферном кеше операционной системы слишком долго. Буферный кеш сбросится (в зависимости от режима WAL) при следующем сканировании кеша страницы и удалится из него.
:::

Чтобы включить прямой ввод-вывод, переместите папку `{IGNITE_HOME}/libs/optional/ignite-direct-io` в папку верхнего уровня `libs/optional/ignite-direct-io` в дистрибутиве DataGrid или в качестве зависимости Maven. 

Чтобы включить или отключить плагин во время выполнения, используйте системное свойство `IGNITE_DIRECT_IO_ENABLED`.

## Использование SSD-накопителя производственного уровня

Производительность DataGrid Native Persistence может упасть после нескольких часов интенсивной записи из-за особенностей конструкции и работы SSD-накопителя. Быстрые SSD-накопители производственного уровня нужны для поддержания высокой производительности. Можно переключиться на устройства энергонезависимой памяти, например Intel Optane Persistent Memory.

## Гарантированное выделение SSD-накопителя

Из-за гарантированного выделения ресурсов SSD производительность случайной записи на диске, который заполнен на 50%, намного выше производительности накопителя, который заполнен на 90%.

Рекомендуется рассмотреть использование SSD-накопителя с более высоким уровнем гарантированного выделения ресурсов. Убедитесь, что производитель предоставляет инструменты для настройки SSD.