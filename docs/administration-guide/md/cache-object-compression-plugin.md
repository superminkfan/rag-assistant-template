# Плагин сжатия данных в памяти

## Описание 

Плагин `cache-object-compression-plugin` позволяет уменьшить объемы хранимой и передаваемой между серверными узлами информации за счет сжатия бинарного представления хранимых данных.

Данные сжимаются при операциях записи и распаковываются при операциях чтения.

Существующие данные будут сжаты только при их явной перезаписи.

## Конфигурация

1. Предварительно перенесите плагин из `$IGNITE_HOME/libs/optional` в `$IGNITE_HOME/libs`.
2. Для активации плагина необходимо дополнить `IgniteConfiguration` следующим образом:

    :::{code-block} java
    :caption: Java
    IgniteConfiguration cfg = ...

    cfg.setPluginProviders(new CacheObjectCompressionPluginProvider(cfg));
    :::

    где `cfg` - один из доступных вариантов конфигурации сжатия:

    - `new Lz4CacheObjectCompressionPluginConfiguration(...)` — сжатие на основе библиотеки [LZ4](https://github.com/lz4/lz4);
    - `new SnappyCacheObjectCompressionPluginConfiguration(...)` — сжатие на основе библиотеки [Snappy](https://github.com/google/snappy);
    - `new ZstdCacheObjectCompressionPluginConfiguration(...)` — сжатие на основе библиотеки [Zstandard](https://github.com/facebook/zstd);
    - `null` — только распаковка ранее сжатых данных.

Алгоритм сжатия можно менять. После смены алгоритма требуется перезагрузить кластер. При этом ранее сжатые данные продолжат распаковываться.

Выбрать подходящий алгоритм можно, ориентируясь на [сравнительные тесты](https://github.com/inikep/lzbench).

### XML-конфигурация

Пример XML-конфигурации плагина:

:::{admonition} Примечание
:class: note

`value="10"` — уровень сжатия.

`value="300"` — размер записи, начиная с которого будет проводиться попытка сжатия.
:::

::::{md-tab-set}
:::{md-tab-item} Lz4
```bash
<bean class="com.sbt.ignite.compress.CacheObjectCompressionPluginProvider">
    <constructor-arg>
        <bean class="com.sbt.ignite.compress.config.Lz4CacheObjectCompressionPluginConfiguration">
            <constructor-arg type="int" value="10"/>
            <constructor-arg type="int" value="300"/>
        </bean>
    </constructor-arg>
</bean>
```
:::

:::{md-tab-item} Snappy
```bash
<bean class="com.sbt.ignite.compress.CacheObjectCompressionPluginProvider">
    <constructor-arg>
        <bean class="com.sbt.ignite.compress.config.SnappyCacheObjectCompressionPluginConfiguration">
            <constructor-arg type="int" value="300"/>
        </bean>
    </constructor-arg>
</bean>
```
:::

:::{md-tab-item} Zstd
```bash
<bean class="com.sbt.ignite.compress.CacheObjectCompressionPluginProvider">
    <constructor-arg>
        <bean class="com.sbt.ignite.compress.config.ZstdCacheObjectCompressionPluginConfiguration">
            <constructor-arg type="int" value="10"/>
            <constructor-arg type="int" value="300"/>
        </bean>
    </constructor-arg>
</bean>
```
:::
::::

## Метрики

Эффективность сжатия, помимо явной оценки утилизации ресурсов, можно оценить в реальном времени с помощью события `EVT_CACHE_OBJECT_TRANSFORMED`.

::::{admonition} Пример конфигурации
:class: hint

:::{code-block} java
:caption: Java
IgniteConfiguration cfg = ...

cfg.setIncludeEventTypes(EventType.EVT_CACHE_OBJECT_TRANSFORMED);
:::
::::

`CacheObjectTransformedEvent` содержит информацию о:

- исходных (несжатых) данных, метод `getOriginal()`;
- сжатых данных, метод `getTransformed()`;
- типе операции, метод `isRestore()`.

::::{admonition} Пример оценки эффективности сжатия
:class: hint

:::{code-block} java
:caption: Java
ignite.events().remoteListen(
    (uuid, evt) -> {
        assertTrue(evt instanceof CacheObjectTransformedEvent);

        // Пользовательский код оценки эффективности сжатия.

        return true;
    },
    null,
    EventType.EVT_CACHE_OBJECT_TRANSFORMED);
:::
::::