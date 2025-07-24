# Режимы атомарности

По умолчанию кеш поддерживает только единичные атомарные операции (режим `ATOMIC`). Массовые (bulk) операции, например `putAll()` и `removeAll()`, выполняются как последовательность отдельных операций добавления и удаления.

Транзакционный режим кеша позволяет выполнить группировку нескольких кеш-операций по одному или нескольким ключам. Все сгруппированные операции или завершаются успешно, или завершаются неудачей. Частичное изменение записей, которые охвачены транзакцией, невозможно: транзакция целиком выполняется как атомарная операция.

Чтобы включить поддержку транзакций в кеше, установите в его конфигурации значение `TRANSACTIONAL` для параметра `atomicityMode`.

:::{admonition} Внимание
:class: danger

Если настраивается несколько кешей в одной кеш-группе, они должны быть полностью атомарными или полностью транзакционными. В одной кеш-группе не могут одновременно присутствовать и транзакционный, и атомарный кеши. Подробнее о группах написано в разделе [«Кеш-группы»](cache_groups.md).
:::

Режимы атомарности, которые поддерживает DataGrid:

| Режим атомарности | Описание |
|---|---|
| `ATOMIC` | Режим по умолчанию. Все операции выполняются атомарно, по одной. Транзакции не поддерживаются. <br><br>Режим `ATOMIC` обеспечивает более высокую производительность за счет исключения блокировок транзакций и при этом гарантирует атомарность и согласованность данных для каждой отдельной операции.<br><br>Массовые операции, например методы `putAll(…)` и `removeAll(…)`, не выполняются за одну транзакцию и могут частично завершиться сбоем. В этом случае генерируется исключение `CachePartialUpdateException` со списком ключей, для которых не удалось выполнить обновление |
| `TRANSACTIONAL` | Включает поддержку ACID-транзакций, которые выполняются через Key-Value API. Транзакции SQL не поддерживаются.<br><br>В режиме `TRANSACTIONAL` у транзакций могут быть разные режимы параллелизма и уровни изоляции. Включайте его только в случаях, когда нужна поддержка операций, которые совместимы с ACID. Подробнее о транзакциях и их режимах написано в разделе [«Выполнение транзакций»](execution_of_transactions.md) |

:::{admonition} Внимание
:class: danger

Режим `TRANSACTIONAL` увеличивает издержки на кеш-операции. Включайте его только в случаях, когда нужны транзакционные гарантии.
:::

Включить поддержку транзакций можно в конфигурации кеша:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="myCache"/>

            <property name="atomicityMode" value="TRANSACTIONAL"/>
        </bean>
    </property>

    <!-- Дополнительная конфигурация транзакций по умолчанию. -->
    <property name="transactionConfiguration">
        <bean class="org.apache.ignite.configuration.TransactionConfiguration">
        ...
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
CacheConfiguration cacheCfg = new CacheConfiguration();

cacheCfg.setName("cacheName");

cacheCfg.setAtomicityMode(CacheAtomicityMode.TRANSACTIONAL);

IgniteConfiguration cfg = new IgniteConfiguration();

cfg.setCacheConfiguration(cacheCfg);

// Дополнительная конфигурация транзакций по умолчанию.
TransactionConfiguration txCfg = new TransactionConfiguration();

cfg.setTransactionConfiguration(txCfg);

// Запустите узел.
Ignition.start(cfg);
```
:::

:::{md-tab-item} С#/.NET
```c#
var cfg = new IgniteConfiguration
{
    CacheConfiguration = new[]
    {
        new CacheConfiguration("txCache")
        {
            AtomicityMode = CacheAtomicityMode.Transactional
        }
    },
    TransactionConfiguration = new TransactionConfiguration
    {
        DefaultTransactionConcurrency = TransactionConcurrency.Optimistic
    }
};
```
:::
::::