# Кеширование в heap-памяти (On-Heap)

DataGrid использует память вне heap (Off-Heap) для выделения областей памяти вне Java Heap. Чтобы включить дополнительное кеширование в Java Heap, установите свойство `CacheConfiguration.setOnheapCacheEnabled(true)`.

Кеширование в heap-памяти пригодится при большом количестве операций чтения кеша на серверных узлах, которые работают с записями кеша в бинарном формате или вызывают их десериализацию. Например, кеширование в heap-памяти пригодится при распределенных вычислениях или получении данных от кеша для дальнейшей обработки.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="myCache"/>
            <property name="onheapCacheEnabled" value="true"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cfg = new CacheConfiguration();
cfg.setName("myCache");
cfg.setOnheapCacheEnabled(true);
```
:::

:::{md-tab-item} С#/.NET
```c#
var cfg = new CacheConfiguration
{
    Name = "myCache",
    OnheapCacheEnabled = true
};
```
:::
::::

## Настройка политики вытеснения

При включении кеширования в heap-памяти можно использовать одну из политик вытеснения (eviction policy), чтобы управлять растущим On-Heap-кешем.

Политики вытеснения контролируют максимальное количество элементов, которые можно хранить в памяти On-Heap-кеша. Когда достигнут максимальный размер, записи вытесняются из Java Heap.

:::{admonition} Внимание
:class: danger

Политики вытеснения для On-Heap-кешей удаляют записи из Java Heap. Это не затрагивает записи, которые хранятся в основной памяти (Off-Heap).
:::

Некоторые политики поддерживают вытеснение пакетами (batch) и вытеснение по ограничению объема памяти. Вытеснение записей пакетами начинается, когда размер кеша превысил максимальную величину `batchSize`. В этом случае записи вытесняются пакетами размером `batchSize`. Вытеснение по ограничению размера памяти начинается, когда размер On-Heap-кеша в байтах становится больше максимального.

:::{admonition} Важно
:class: attention

Вытеснение пакетами поддерживается, только если не установлен максимальный размер On-Heap-кеша.
:::

Политики вытеснения настраиваются с помощью интерфейса `EvictionPolicy`. Реализация политики вытеснения уведомляется о каждом изменении кеша и определяет алгоритм выбора записей для вытеснения из On-Heap-кеша.

### Политика вытеснения LRU

Политика вытеснения LRU основана на алгоритме Least Recently Used. Она гарантирует, что первой вытеснится наименее используемая запись (то есть запись, которая не была затронута в течение самого длительного времени).

:::{admonition} Примечание
:class: note

Политика вытеснения LRU подходит для большинства случаев использования кеширования в heap-памяти. Если есть сомнения в выборе политики вытеснения, используйте LRU.
:::

Политика LRU поддерживает вытеснение пакетами (batch) и вытеснение по ограничению объема памяти. LRU можно включить в конфигурации кеша.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.cache.CacheConfiguration">
  <property name="name" value="myCache"/>

  <!-- Включение кеширования в heap для распределенного кеша. -->
  <property name="onheapCacheEnabled" value="true"/>

  <property name="evictionPolicy">
    <!-- Политика вытеснения LRU. -->
    <bean class="org.apache.ignite.cache.eviction.lru.LruEvictionPolicy">
        <!-- Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000). -->
      <property name="maxSize" value="1000000"/>
    </bean>
  </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");

// Включение кеширования в heap для распределенного кеша.
cacheCfg.setOnheapCacheEnabled(true);

// Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000).
cacheCfg.setEvictionPolicyFactory(() -> new LruEvictionPolicy(1000000));

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);
```
:::

:::{md-tab-item} С#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "cacheName",
            OnheapCacheEnabled = true,
            EvictionPolicy = new LruEvictionPolicy
            {
                MaxSize = 100000
            }
        }
    }
};
```
:::
::::

### Политика вытеснения FIFO

Политика вытеснения FIFO («первым пришел — первым ушел») основана на алгоритме FIFO. Она гарантирует, что первой вытеснится запись, которая была в On-Heap-кеше в течение самого длительного времени. Политика FIFO отличается от `LruEvictionPolicy`: FIFO игнорирует порядок, в котором использовались записи.

Политика FIFO поддерживает вытеснение пакетами (batch) и вытеснение по ограничению объема памяти. Пример, как включить FIFO:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.cache.CacheConfiguration">
  <property name="name" value="myCache"/>

  <!-- Включение кеширования в heap для распределенного кеша. -->
  <property name="onheapCacheEnabled" value="true"/>

  <property name="evictionPolicy">
    <!-- Политика вытеснения FIFO. -->
    <bean class="org.apache.ignite.cache.eviction.fifo.FifoEvictionPolicy">
        <!-- Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000). -->
      <property name="maxSize" value="1000000"/>
    </bean>
  </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");

// Включение кеширования в heap для распределенного кеша.
cacheCfg.setOnheapCacheEnabled(true);

// Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000).
cacheCfg.setEvictionPolicyFactory(() -> new FifoEvictionPolicy(1000000));

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "cacheName",
            OnheapCacheEnabled = true,
            EvictionPolicy = new FifoEvictionPolicy
            {
                MaxSize = 100000
            }
        }
    }
};
```
:::
::::

### Политика вытеснения Sorted

Политика вытеснения на основании сортировки (Sorted) похожа на политику FIFO. В политике Sorted порядок вытеснения определяется с помощью компаратора (comparator) по умолчанию или пользовательского компаратора. `SortedEvictionPolicy` гарантирует, что первой вытеснится запись с наименьшим значением.

Компаратор по умолчанию использует для сравнения записей их ключи кеша, поэтому они должны реализовывать интерфейс `Comparable`. Пользовательская реализация компаратора может использовать для сравнения записей ключи, значения или и то, и другое.

Политика поддерживает вытеснение пакетами (batch) и вытеснение по ограничению объема памяти. Политику вытеснения Sorted можно включить в конфигурации кеша.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.cache.CacheConfiguration">
  <property name="name" value="myCache"/>

  <!-- Включение кеширования в heap для распределенного кеша. -->
  <property name="onheapCacheEnabled" value="true"/>

  <property name="evictionPolicy">
    <!-- Политика вытеснения Sorted. -->
    <bean class="org.apache.ignite.cache.eviction.sorted.SortedEvictionPolicy">
      <!--
      Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000)
      и используйте компаратор по умолчанию.
      -->
      <property name="maxSize" value="1000000"/>
    </bean>
  </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");

// Включение кеширования в heap для распределенного кеша.
cacheCfg.setOnheapCacheEnabled(true);

// Установите максимальный размер кеша 1 миллион (по умолчанию — 100 000).
cacheCfg.setEvictionPolicyFactory(() -> new SortedEvictionPolicy(1000000));

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);
```
:::
::::