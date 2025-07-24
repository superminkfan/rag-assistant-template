# Сжатие диска

Сжатие диска — процесс сжатия страниц данных, который работает при условии записи страниц на диск. Сжатие позволяет уменьшить размер дискового хранилища. Страницы хранятся в памяти в несжатом виде, но при сбросе данных на диск они сжимаются с использованием настроенного алгоритма. Это применимо только к страницам данных, которые находятся в постоянном хранилище; индексы или записи WAL не сжимаются. Сжатие записей WAL можно включить отдельно — подробнее об этом написано в разделе [«Персистентность DataGrid»](datagrid_persistence.md).

Сжатие страниц диска можно включить для каждого кеша в его конфигурации. Для этого кеш должен находиться в персистентном регионе данных. Сейчас включить глобальное сжатие страниц на диске нельзя. Перед сжатием выполните действия:

1. Установите значение свойства `pageSize` в конфигурации хранилища данных как минимум в 2 раза больше размера страницы файловой системы. Размер страницы должен быть 8 Кб или 16 Кб.
2. Включите модуль `ignite-compress`.

Чтобы включить сжатие страниц диска для кеша, укажите в его конфигурации один из доступных алгоритмов:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="dataStorageConfiguration">
        <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
            <property name="pageSize" value="#{4096 * 2}"/>
            <property name="defaultDataRegionConfiguration">
                <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                    <property name="persistenceEnabled" value="true"/>
                </bean>
            </property>
        </bean>
    </property>
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="myCache"/>
            <!-- Включите сжатие страниц на диске для данного кеша. -->
            <property name="diskPageCompression" value="LZ4"/>
            <!-- Опционально: установите уровень сжатия страниц. -->
            <property name="diskPageCompressionLevel" value="10"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
DataStorageConfiguration dsCfg = new DataStorageConfiguration();

// Установите размер страницы данных в 2 раза больше размера страницы на диске.
dsCfg.setPageSize(4096 * 2);

// Включите постоянное хранение на диске для региона данных.
dsCfg.setDefaultDataRegionConfiguration(new DataRegionConfiguration().setPersistenceEnabled(true));

IgniteConfiguration cfg = new IgniteConfiguration();
cfg.setDataStorageConfiguration(dsCfg);

CacheConfiguration cacheCfg = new CacheConfiguration("myCache");
// Включите сжатие страниц на диске для данного кеша.
cacheCfg.setDiskPageCompression(DiskPageCompression.LZ4);
// Опционально: установите уровень сжатия страниц.
cacheCfg.setDiskPageCompressionLevel(10);

cfg.setCacheConfiguration(cacheCfg);

Ignite ignite = Ignition.start(cfg);
```
:::
::::

## Поддерживаемые алгоритмы сжатия

Поддерживаются следующие алгоритмы сжатия страниц данных:

- `ZSTD` — поддерживает уровни сжатия от -131072 до 22 (по умолчанию — 3).
- `LZ4` — поддерживает уровни сжатия от 0 до 17 (по умолчанию — 0).
- `SNAPPY` — алгоритм Snappy.
- `SKIP_GARBAGE` — извлекает полезные данные только из наполовину заполненных страниц и не сжимает данные.