# Политика вытеснения данных из кеша (Eviction Policies)

Если включен Native Persistence, DataGrid хранит все записи кеша в памяти вне heap (Off-Heap) и выделяет новые страницы по мере поступления данных. При достижении предела памяти, когда DataGrid не может выделить новую страницу, нужно удалить некоторые данные из памяти во избежание ошибок ее нехватки (OutOfMemory). Этот процесс называется вытеснением (eviction). Он предотвращает нехватку памяти системы за счет потери данных и необходимости их повторной загрузки, если данные снова понадобятся.

Вытеснение применяется в случаях:

- для памяти вне heap при выключенном Native Persistence — подробнее написано в подразделе [«Персистентность DataGrid»](datagrid_persistence.md) раздела «Настройка Persistence»;
- для памяти вне heap, когда DataGrid использует внешнее хранилище — подробнее написано в подразделе [«Внешнее хранение»](external_storage.md) раздела «Настройка Persistence»;
- для кешей в heap-памяти — подробнее написано в подразделе [«Кеширование в heap-памяти (On-Heap)»](on-heap-caching.md) раздела «Настройка кешей»;
- для near-кешей, если они настроены — подробнее написано в подразделе [«Near-кеши»](near_caches.md) раздела «Настройка кешей».

Если Native Persistence включен и DataGrid не может выделить новую страницу, для очистки памяти вне heap используется похожий процесс, который называется заменой страниц (page replacement). При замене страниц данные не теряются, так как они находятся в постоянном хранилище — подробнее об этом написано в разделе [«Политика замены страниц (Replacement Policies)»](replacement_policies.md).

## Вытеснение данных из кеша вне heap

Когда использование памяти превышает установленный предел, DataGrid применяет один из предварительно настроенных алгоритмов выбора страниц памяти, которые лучше всего подходят для вытеснения данных. Каждая запись кеша, которая есть на выбранной странице, удаляется с нее. Если транзакция заблокировала запись, она сохранится. Вся страница или ее большая часть очищается и готова к повторному использованию.

![Eviction-policies](./resources/eviction-policies.png)

По умолчанию вытеснение вне heap отключено, поэтому объем используемой памяти постоянно растет, пока не достигает предела. Чтобы включить `eviction`, укажите режим вытеснения страниц в конфигурации каждого региона данных. Если регионы данных не используются, явно пропишите в конфигурации параметры по умолчанию, чтобы воспользоваться вытеснением.

По умолчанию вытеснение данных начинается, когда занято 90% оперативной памяти. Чтобы начать вытеснение данных из кеша раньше или позже, используйте параметр `DataRegionConfiguration.setEvictionThreshold(…​)`.

DataGrid использует два алгоритма выбора страниц: Random-LRU и Random-2-LRU. Подробнее о разнице между ними написано в разделах ниже.

### Random-LRU

Ниже пример настройки для подключения алгоритма Random-LRU.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <!-- Конфигурация памяти. -->
    <property name="dataStorageConfiguration">
        <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
            <property name="dataRegionConfigurations">
                <list>
                    <!-- Определение региона данных, который будет занимать до 20 Гб оперативной памяти (ОЗУ). -->
                    <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                        <!-- Пользовательское название региона данных. -->
                        <property name="name" value="20GB_Region"/>
                        <!-- Начальный размер — 500 Мб (ОЗУ). -->
                        <property name="initialSize" value="#{500L * 1024 * 1024}"/>
                        <!-- Максимальный размер — 20 Гб (ОЗУ). -->
                        <property name="maxSize" value="#{20L * 1024 * 1024 * 1024}"/>
                        <!-- Включение алгоритма вытеснения RANDOM_LRU для данного региона.  -->
                        <property name="pageEvictionMode" value="RANDOM_LRU"/>
                    </bean>
                </list>
            </property>
        </bean>
    </property>
</bean>

<bean class="org.apache.ignite.configuration.IgniteConfiguration">
  <!-- Конфигурация памяти. -->
  <property name="dataStorageConfiguration">
    <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
      <property name="dataRegionConfigurations">
        <list>
          <!--
              Определение региона данных, который будет занимать до 20 Гб оперативной памяти (ОЗУ).
          -->
          <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
            <!-- Пользовательское название региона данных. -->
            <property name="name" value="20GB_Region"/>

            <!-- Начальный размер — 500 Мб (ОЗУ). -->
            <property name="initialSize" value="#{500L * 1024 * 1024}"/>

            <!-- Максимальный размер — 20 Гб (ОЗУ). -->
            <property name="maxSize" value="#{20L * 1024 * 1024 * 1024}"/>

            <!-- Включение алгоритма вытеснения RANDOM_LRU для данного региона.  -->
            <property name="pageEvictionMode" value="RANDOM_LRU"/>
          </bean>
        </list>
      </property>
    </bean>
  </property>

  <!-- Остальная конфигурация. -->
</bean>
```
:::

:::{md-tab-item} Java
```java
// Конфигурация узла.
IgniteConfiguration cfg = new IgniteConfiguration();

// Конфигурация памяти.
DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Создание нового региона данных.
DataRegionConfiguration regionCfg = new DataRegionConfiguration();

// Название региона.
regionCfg.setName("20GB_Region");

// Начальный размер — 500 Мб (ОЗУ).
regionCfg.setInitialSize(500L * 1024 * 1024);

// Максимальный размер — 20 Гб (ОЗУ).
regionCfg.setMaxSize(20L * 1024 * 1024 * 1024);

// Включение алгоритма вытеснения RANDOM_LRU для данного региона.
regionCfg.setPageEvictionMode(DataPageEvictionMode.RANDOM_LRU);

// Установка конфигурации региона данных.
storageCfg.setDataRegionConfigurations(regionCfg);

// Применение новой конфигурации.
cfg.setDataStorageConfiguration(storageCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        DataRegionConfigurations = new[]
        {
            new DataRegionConfiguration
            {
                Name = "20GB_Region",
                InitialSize = 500L * 1024 * 1024,
                MaxSize = 20L * 1024 * 1024 * 1024,
                PageEvictionMode = DataPageEvictionMode.RandomLru
            }
        }
    }
};
```
:::
::::

Алгоритм Random-LRU работает следующим образом:

1. После настройки региона данных в Off-Heap выделяется массив для отслеживания временной метки последнего использования каждой страницы данных.
2. Если страница данных доступна, ее временная метка обновляется в массиве отслеживания.
3. Когда наступает время вытеснить страницу, алгоритм случайным образом выбирает 5 индексов из массива отслеживания и вытесняет страницу с самой старой временной меткой. Если некоторые индексы указывают на страницы не с данными, а с индексами или системной информацией, алгоритм выбирает другую страницу.

### Random-2-LRU

Пример настройки региона данных для подключения алгоритма Random-2-LRU — устойчивой к сканированию версии Random-LRU:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
  <!-- Конфигурация памяти. -->
  <property name="dataStorageConfiguration">
    <bean class="org.apache.ignite.configuration.DataStorageConfiguration">
      <property name="dataRegionConfigurations">
        <list>
          <!--
              Определение региона данных, который будет занимать до 20 Гб оперативной памяти (ОЗУ).
          -->
          <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
            <!-- Пользовательское название региона данных. -->
            <property name="name" value="20GB_Region"/>

            <!-- Начальный размер — 500 Мб (ОЗУ). -->
            <property name="initialSize" value="#{500L * 1024 * 1024}"/>

            <!-- Максимальный размер — 20 Гб (ОЗУ). -->
            <property name="maxSize" value="#{20L * 1024 * 1024 * 1024}"/>

            <!-- Включение алгоритма вытеснения RANDOM_2_LRU для данного региона.  -->
            <property name="pageEvictionMode" value="RANDOM_2_LRU"/>
          </bean>
        </list>
      </property>
    </bean>
  </property>

  <!-- Остальная конфигурация. -->
</bean>
```
:::

:::{md-tab-item} Java
```java
// Конфигурация DataGrid.
IgniteConfiguration cfg = new IgniteConfiguration();

// Конфигурация памяти.
DataStorageConfiguration storageCfg = new DataStorageConfiguration();

// Создание нового региона данных.
DataRegionConfiguration regionCfg = new DataRegionConfiguration();

// Название региона.
regionCfg.setName("20GB_Region");

// Начальный размер — 500 Мб (ОЗУ).
regionCfg.setInitialSize(500L * 1024 * 1024);

// Максимальный размер — 20 Гб (ОЗУ).
regionCfg.setMaxSize(20L * 1024 * 1024 * 1024);

// Включение алгоритма вытеснения RANDOM_2_LRU для данного региона.
regionCfg.setPageEvictionMode(DataPageEvictionMode.RANDOM_2_LRU);

// Установка конфигурации региона данных.
storageCfg.setDataRegionConfigurations(regionCfg);

// Применение новой конфигурации.
cfg.setDataStorageConfiguration(storageCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    DataStorageConfiguration = new DataStorageConfiguration
    {
        DataRegionConfigurations = new[]
        {
            new DataRegionConfiguration
            {
                Name = "20GB_Region",
                InitialSize = 500L * 1024 * 1024,
                MaxSize = 20L * 1024 * 1024 * 1024,
                PageEvictionMode = DataPageEvictionMode.Random2Lru
            }
        }
    }
};
```
:::
::::

В алгоритме Random-2-LRU для каждой страницы данных хранятся две последние временные метки доступа. В момент вытеснения данных из кеша алгоритм случайным образом выбирает 5 индексов из массива отслеживания. Затем алгоритм находит минимальное значение из двух последних временных меток. Они сравниваются с соответствующими минимальными значениями четырех других страниц, которые алгоритм выбрал в качестве возможных кандидатов на вытеснение данных.

Алгоритм Random-2-LRU превосходит LRU, так как решает проблему «однократного попадания»: если к странице данных редко обращались, но она использовалась незадолго до запуска алгоритма, страница будет на долгое время защищена от вытеснения.

## Вытеснение данных из кеша в heap-памяти

Подробнее о настройке политики вытеснения для кеша в heap-памяти написано в подразделе [«Кеширование в heap-памяти (On-Heap)»](on-heap-caching.md) раздела «Настройка кешей».