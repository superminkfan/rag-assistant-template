# Выполнение транзакций

## Введение

Чтобы включить поддержку транзакций для конкретного кеша, установите в его конфигурации параметр `atomicityMode=TRANSACTIONAL`. Подробнее о режимах атомарности написано в подразделе [«Режимы атоматрности»](atomicity_modes.md) раздела «Настройка кешей».

Транзакции позволяют сгруппировать несколько операций кеша на одном или нескольких ключах в одну атомарную транзакцию. Вытеснения операций на указанных ключах не будет. Все операции завершатся успешно или не выполнятся: так как транзакции атомарные, частичное выполнение невозможно.

В конфигурации также можно включить транзакции для определенного кеша:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="transactionConfiguration">
        <bean class="org.apache.ignite.configuration.TransactionConfiguration">
            <!-- Установите тайм-аут на 20 секунд. -->
            <property name="TxTimeoutOnPartitionMapExchange" value="20000"/>
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

// Настройка конфигурации транзакций необязательна. Настроить `TM lookup` можно здесь.
TransactionConfiguration txCfg = new TransactionConfiguration();

cfg.setTransactionConfiguration(txCfg);

// Запустите узел.
Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
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

## Выполнение транзакций

::::{admonition} Важно
:class: attention

Начиная с версии DataGrid 17.5.0 вызов метода `IgniteCache#clear` внутри транзакций запрещен:

:::{code-block} java
:caption: Java
/** */
@Test
public void testClearInTransction() {
    IgniteCache<Object, Object> cache = client.createCache(new CacheConfiguration<>("my-cache").setAtomicityMode(CacheAtomicityMode.TRANSACTIONAL));
    cache.put(1, 1);
    try (Transaction tx = client.transactions().txStart(TransactionConcurrency.PESSIMISTIC, TransactionIsolation.READ_COMMITTED)) {
        cache.put(2, 2);
        cache.clear();
        tx.commit();
    }
    assertFalse(cache.containsKey(1));
    assertTrue(cache.containsKey(2));
}
:::
::::

В Key-Value API есть интерфейс для запуска и выполнения транзакций и для получения метрик, которые связаны с транзакциями:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.ignite();

IgniteTransactions transactions = ignite.transactions();

try (Transaction tx = transactions.txStart()) {
    Integer hello = cache.get("Hello");

    if (hello == 1)
        cache.put("Hello", 11);

    cache.put("World", 22);

    tx.commit();
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
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
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "cacheName",
            AtomicityMode = CacheAtomicityMode.Transactional
        }
    },
    TransactionConfiguration = new TransactionConfiguration
    {
        DefaultTimeoutOnPartitionMapExchange = TimeSpan.FromSeconds(20)
    }
};

var ignite = Ignition.Start(cfg);
var cache = ignite.GetCache<string, int>("cacheName");
cache.Put("Hello", 1);
var transactions = ignite.GetTransactions();

using (var tx = transactions.TxStart())
{
    int hello = cache.Get("Hello");

    if (hello == 1)
    {
        cache.Put("Hello", 11);
    }

    cache.Put("World", 22);

    tx.Commit();
}
```
:::

:::{md-tab-item} C++
```c++
Transactions transactions = ignite.GetTransactions();

Transaction tx = transactions.TxStart();
int hello = cache.Get("Hello");

if (hello == 1)
    cache.Put("Hello", 11);

cache.Put("World", 22);

tx.Commit();
```
:::
::::

:::{admonition} Внимание
:class: danger

Транзакция DataGrid должна быть закрыта (`closed`) независимо от состояния ее коммита. Это гарантирует освобождение всех ресурсов и отключение транзакции от текущего потока. При работе с транзакциями настоятельно рекомендуется использование конструкции `try-with-resources`, так как с ней компилятор автоматически добавляет секцию `finally` с вызовом метода `close()` для объекта с внешними ресурсами.
:::

## Режимы параллелизма и уровни изоляции

Кеши с режимом атомарности `TRANSACTIONAL` поддерживают два режима параллелизма транзакций: `OPTIMISTIC` и `PESSIMISTIC`. Режим параллелизма определяет, когда происходит начальная блокировка транзакции: во время доступа к данным или на этапе подготовки. Блокировка предотвращает одновременный доступ к объекту нескольких операций. Например, при попытке обновить элемент списка дел с помощью `PESSIMISTIC`-блокировки сервер устанавливает блокировку на объекте, пока транзакция не совершится или не откатится. В это время никакая другая транзакция или операция не сможет обновить ту же запись. Независимо от режима параллелизма транзакции существует момент, когда все записи, которые зарегистрированы в транзакции, блокируются перед совершением коммита.

Уровень изоляции определяет, как параллельные транзакции видят и обрабатывают операции на одних и тех же ключах. DataGrid поддерживает уровни изоляции `READ_COMMITTED`, `REPEATABLE_READ` и `SERIALIZABLE`.

Допускаются все комбинации режимов параллелизма и уровней изоляции. Ниже описано поведение системы и гарантии, которые предоставляет каждая комбинация режимов.

### Транзакции в режиме PESSIMISTIC

В `PESSIMISTIC`-транзакциях блокировки ставятся во время первого доступа к чтению или записи (в зависимости от уровня изоляции) и удерживаются до тех пор, пока транзакция не совершится или не откатится. В этом режиме блокировки сначала ставятся на первичных узлах, а на стадии подготовки переходят к резервным узлам. Уровни изоляции, которые можно настроить с режимом параллелизма `PESSIMISTIC`:

- `READ_COMMITTED` — данные читаются без блокировки и никогда не кешируются внутри транзакции. Они могут считываться из резервного узла, если это разрешено в настройках кеша. В этом режиме изоляции можно получить неповторяющиеся чтения, так как параллельная транзакция может изменить данные при повторном чтении. Блокировка происходит только во время первой записи (это включает вызов `EntryProcessor`). Запись, которую прочитали во время транзакции, может иметь другое значение к моменту совершения транзакции. В этом случае исключения не генерируются.
- `REPEATABLE_READ` — при первом чтении или записи ставится входная блокировка. Данные извлекаются из первичного узла и хранятся в локальной карте транзакций. Последовательные доступы к одним и тем же данным являются локальными и возвращают последнее считанное или обновленное значение транзакции. Никакие другие параллельные транзакции не могут вносить изменения в заблокированные данные, поэтому доступны повторяющиеся чтения.
- `SERIALIZABLE` — в режиме `PESSIMISTIC` уровень изоляции работает так же, как `REPEATABLE_READ`.

В режиме `PESSIMISTIC` важен порядок блокировок: они происходят последовательно и в определенном порядке.


:::{admonition} Ограничения изменения топологии
:class: hint

Если получена хотя бы одна блокировка транзакции в режиме `PESSIMISTIC`, топологию кеша нельзя менять, пока транзакция не совершится или не откатится. Избегайте длительного удержания блокировок транзакций.
:::

### Транзакции в режиме OPTIMISTIC

В `OPTIMISTIC`-транзакциях блокировки входа происходят на первичных узлах во время первой фазы протокола 2PC и на шаге подготовки, а затем переходят на резервные узлы и снимаются после совершения транзакции. Блокировки никогда не происходят при откате транзакции и без совершения коммита. Уровни изоляции, которые можно настроить с режимом параллелизма `OPTIMISTIC`:

- `READ_COMMITTED` — изменения, которые должны применяться к кешу. Они собираются на исходном узле и применяются на стадии `commit` транзакции. Ее данные читаются без блокировок и никогда не кешируются в транзакции. Данные могут считываться из резервного узла, если это разрешено в конфигурации кеша. В этом режиме изоляции можно получить неповторяющиеся чтения, так как параллельная транзакция может менять данные при повторном чтении. Комбинация режимов не проверяет, изменилось ли входное значение с первого чтения или записи, и никогда не генерирует `OPTIMISTIC`-исключений.
- `REPEATABLE_READ` — транзакции на этом уровне изоляции похожи на транзакции `OPTIMISTIC READ_COMMITTED`, кроме одного отличия: значения чтения кешируются на исходном узле, а все последующие чтения происходят локально. Комбинация режимов не проверяет, изменилось ли входное значение после первого чтения или записи, и никогда не генерирует `OPTIMISTIC`-исключений.
- `SERIALIZABLE` — хранит входную версию с первого чтения. Если DataGrid обнаруживает, что изменилась хотя бы одна из записей в инициированной транзакции, ее выполнение обрывается на стадии `commit`. Если на стадии совершения транзакции возникает конфликт:
   1. Транзакция не выполняется.
   2. Генерируется исключение `TransactionOptimisticException`.
   3. Происходит откат любых внесенных изменений.

::::{md-tab-set}
:::{md-tab-item} Java
```java
CacheConfiguration<Integer, String> cfg = new CacheConfiguration<>();
cfg.setAtomicityMode(CacheAtomicityMode.TRANSACTIONAL);
cfg.setName("myCache");
IgniteCache<Integer, String> cache = ignite.getOrCreateCache(cfg);

// Повторите выполнение транзакции ограниченное количество раз.
int retryCount = 10;
int retries = 0;

// Запустите выполнение транзакции в режиме `OPTIMISTIC` с уровнем изоляции `SERIALIZABLE`.
while (retries < retryCount) {
    retries++;
    try (Transaction tx = ignite.transactions().txStart(TransactionConcurrency.OPTIMISTIC,
            TransactionIsolation.SERIALIZABLE)) {
        // Измените записи кешей внутри транзакции.
        cache.put(1, "foo");
        cache.put(2, "bar");
        // Совершите транзакцию.
        tx.commit();

        // Транзакция успешно завершена. Выйдите из цикла `while`.
        break;
    } catch (TransactionOptimisticException e) {
        // Транзакция завершилась с ошибками, перезапустите ее.
    }
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
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
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "cacheName",
            AtomicityMode = CacheAtomicityMode.Transactional
        }
    },
    TransactionConfiguration = new TransactionConfiguration
    {
        DefaultTimeoutOnPartitionMapExchange = TimeSpan.FromSeconds(20)
    }
};

var ignite = Ignition.Start(cfg);
// Повторите выполнение транзакции ограниченное количество раз
var retryCount = 10;
var retries = 0;

// Запустите выполнение транзакции в режиме `OPTIMISTIC` с уровнем изоляции `SERIALIZABLE`.
while (retries < retryCount)
{
    retries++;
    try
    {
        using (var tx = ignite.GetTransactions().TxStart(TransactionConcurrency.Optimistic,
            TransactionIsolation.Serializable))
        {
            // Измените записи кешей внутри транзакции.

            // Совершите транзакцию.
            tx.Commit();

            // Транзакция успешно завершена. Выйдите из цикла `while`.
            break;
        }
    }
    catch (TransactionOptimisticException)
    {
        // Транзакция завершилась с ошибками, перезапустите ее.
    }

}
```
:::

:::{md-tab-item} C++
```c++
// Повторите выполнение транзакции ограниченное количество раз
int const retryCount = 10;
int retries = 0;

// Запустите выполнение транзакции в режиме `OPTIMISTIC` с уровнем изоляции `SERIALIZABLE`.
while (retries < retryCount)
{
    retries++;

    try
    {
        Transaction tx = ignite.GetTransactions().TxStart(
                TransactionConcurrency::OPTIMISTIC, TransactionIsolation::SERIALIZABLE);

        // Совершите транзакцию.
        tx.Commit();

        // Транзакция успешно завершена. Выйдите из цикла `while`.
        break;
    }
    catch (IgniteError e)
    {
        // Транзакция завершилась с ошибками, перезапустите ее.
    }
}
```
:::
::::

Транзакция не завершится успешно, даже если запись считается без изменений `(cache.put(…​))`, так как значение записи может быть важным для логики в рамках инициированной транзакции.

Порядок ключа важен для транзакций `READ_COMMITTED` и `REPEATABLE_READ`, так как в этих режимах блокировки происходят последовательно.

### Согласованность чтения

Чтобы достичь полной согласованности операций чтения в режиме `PESSIMISTIC`, установите блокировки для обеспечения чтения. Полной согласованности операций чтения в режиме `PESSIMISTIC` можно достичь только с транзакциями `PESSIMISTIC REPEATABLE_READ` и `SERIALIZABLE`.

При использовании `OPTIMISTIC`-транзакций возможна полная согласованность операций чтения, если не допускать потенциальные конфликты между ними. Такое поведение достигается с помощью режима `OPTIMISTIC SERIALIZABLE`. До совершения коммита можно прочитать состояние частично совершенной транзакции, поэтому логика транзакции должна защищать от конфликтов. Если они все же появились, на фазе совершения коммита сгенерируется исключение `TransactionOptimisticException`. Оно позволит перезапустить выполнение транзакции.

:::{admonition} Внимание
:class: danger

Если не использовать транзакции `PESSIMISTIC REPEATABLE_READ`, `SERIALIZABLE` и `OPTIMISTIC SERIALIZABLE`, есть вероятность появления состояния частично совершенной транзакции. Если одна транзакция обновляет объекты А и В, другая транзакция может считать новое значение для объекта А и старое значение для В.
:::

## Обнаружение взаимоблокировок (deadlock)

Основное правило, которому нужно следовать при работе с распределенными транзакциями: блокировки для ключей, которые участвуют в транзакции, должны быть получены в том же порядке. Нарушение этого правила может привести к распределенным взаимоблокировкам.

В DataGrid возможны распределенные взаимоблокировки. В продукте есть встроенная функциональность, которая облегчает отладку и исправление таких ситуаций.

В примере кода ниже началась транзакция с тайм-аутом. Пока он истекает, процедура обнаружения взаимоблокировок пытается найти возможную причину, которая могла вызвать тайм-аут. Когда он закончился, генерируется исключение `TransactionTimeoutException`. Оно передается в код приложения как причина  `CacheException` (независимо от взаимоблокировки). Но при обнаружении взаимоблокировки причиной `TransactionTimeoutException` будет `TransactionDeadlockException` — по крайней мере для одной транзакции, которая связана с взаимоблокировкой.

::::{md-tab-set}
:::{md-tab-item} Java
```java
CacheConfiguration<Integer, String> cfg = new CacheConfiguration<>();
cfg.setAtomicityMode(CacheAtomicityMode.TRANSACTIONAL);
cfg.setName("myCache");
IgniteCache<Integer, String> cache = ignite.getOrCreateCache(cfg);

try (Transaction tx = ignite.transactions().txStart(TransactionConcurrency.PESSIMISTIC,
        TransactionIsolation.READ_COMMITTED, 300, 0)) {
    cache.put(1, "1");
    cache.put(2, "1");

    tx.commit();
} catch (CacheException e) {
    if (e.getCause() instanceof TransactionTimeoutException
            && e.getCause().getCause() instanceof TransactionDeadlockException)

        System.out.println(e.getCause().getCause().getMessage());
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
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
    CacheConfiguration = new[]
    {
        new CacheConfiguration
        {
            Name = "cacheName",
            AtomicityMode = CacheAtomicityMode.Transactional
        }
    },
    TransactionConfiguration = new TransactionConfiguration
    {
        DefaultTimeoutOnPartitionMapExchange = TimeSpan.FromSeconds(20)
    }
};

var ignite = Ignition.Start(cfg);
var intCache = ignite.GetOrCreateCache<int, int>("intCache");
try
{
    using (var tx = ignite.GetTransactions().TxStart(TransactionConcurrency.Pessimistic,
        TransactionIsolation.ReadCommitted, TimeSpan.FromMilliseconds(300), 0))
    {
        intCache.Put(1, 1);
        intCache.Put(2, 1);
        tx.Commit();
    }
}
catch (TransactionTimeoutException e)
{
    Console.WriteLine(e.Message);
}
catch (TransactionDeadlockException e)
{
    Console.WriteLine(e.Message);
}
```
:::

:::{md-tab-item} C++
```c++
try {
    Transaction tx = ignite.GetTransactions().TxStart(
        TransactionConcurrency::PESSIMISTIC, TransactionIsolation::READ_COMMITTED, 300, 0);
    cache.Put(1, 1);

    cache.Put(2, 1);

    tx.Commit();
}
catch (IgniteError& err)
{
    std::cout << "An error occurred: " << err.GetText() << std::endl;
    std::cin.get();
    return err.GetCode();
}
```
:::
::::

Сообщение `TransactionDeadlockException` содержит полезную информацию, которая может помочь найти причину взаимоблокировки:

```bash
Обнаружена взаимоблокировка:

K1: TX1 holds lock, TX2 waits lock.
K2: TX2 holds lock, TX1 waits lock.

Транзакции:

TX1 [txId=GridCacheVersion [topVer=74949328, time=1463469328421, order=1463469326211, nodeOrder=1], nodeId=ad68354d-07b8-4be5-85bb-f5f2362fbb88, threadId=73]
TX2 [txId=GridCacheVersion [topVer=74949328, time=1463469328421, order=1463469326210, nodeOrder=1], nodeId=ad68354d-07b8-4be5-85bb-f5f2362fbb88, threadId=74]

Ключи:

K1 [key=1, cache=default]
K2 [key=2, cache=default]
```

Процедура обнаружения взаимоблокировки может занимать много итераций в зависимости от количества узлов в кластере, ключей и транзакций, которые участвуют в возможной взаимоблокировке. Ее обнаружение инициирует узел, в котором запущена транзакция и сгенерировано исключение `TransactionTimeoutException`. Узел исследует, произошла ли взаимоблокировка, через обмен запросами и ответами с другими удаленными узлами. По результатам узел готовит отчет по взаимоблокировке и передает его в `TransactionDeadlockException`. Каждое такое сообщение (запрос и ответ) является итерацией.

Так как транзакция не откатывается до завершения процедуры обнаружения взаимоблокировки, иногда стоит настраивать параметры для уточнения времени отката транзакции:

- `IgniteSystemProperties.IGNITE_TX_DEADLOCK_DETECTION_MAX_ITERS` — указывает максимальное количество итераций для процедуры обнаружения взаимоблокировки. Если значение свойства меньше или равно нулю, обнаружение отключено (по умолчанию — 1000).
- `IgniteSystemProperties.IGNITE_TX_DEADLOCK_DETECTION_TIMEOUT` — указывает время ожидания для механизма обнаружения взаимоблокировки (по умолчанию — 1 минута).

Если итераций слишком мало, можно получить неполный отчет о взаимоблокировке.

## Транзакции без взаимоблокировок

Для `OPTIMISTIC SERIALIZABLE`-транзакций блокировки не берутся последовательно. В этом режиме доступ к ключам можно получить в любом порядке, так как блокировки транзакций берутся параллельно с проверкой на появление взаимоблокировок.

Чтобы описать работу блокировки в `SERIALIZABLE`-транзакциях, нужны представления концепций. В DataGrid каждой транзакции присваивается сопоставимая версия, которая называется `XidVersion`. При совершении транзакции каждой ее записи назначается новая сопоставимая версия `EntryVersion`. `OPTIMISTIC SERIALIZABLE`-транзакция с версией `XidVersionA` генерирует исключение `TransactionOptimisticException` по причинам:

- Наличие текущей `PESSIMISTIC`- или несериализуемой `OPTIMISTIC`-транзакции, которая держит блокировку записи `SERIALIZABLE`-транзакции.
- Наличие еще одной текущей `OPTIMISTIC SERIALIZABLE`-транзакции с версией  `XidVersionB`, которая больше `XidVersionA`; транзакция держит блокировку записи `SERIALIZABLE`-транзакции.
- К тому времени, как `OPTIMISTIC SERIALIZABLE`-транзакция получит все необходимые блокировки, уже существует запись, в которой текущая версия отличается от версии до коммита.

:::{admonition} Важно
:class: attention

В среде с высокой степенью параллелизма `OPTIMISTIC`-блокировка может привести к большому количеству сбоев транзакций. `PESSIMISTIC`-блокировка может привести к взаимоблокировкам, если они берутся транзакциями в другом порядке.

В среде с контролируемым доступом сериализуемая `OPTIMISTIC`-блокировка может давать лучшие показатели по производительности для крупных транзакций. Число сетевых соединений зависит только от количества узлов, которые охватывает транзакция, и не зависит от количества ключей в ней.
:::

## Обработка неуспешно завершенных транзакций

Если транзакция завершилась неуспешно, может сгенерироваться исключение:

| Исключение | Описание | Решение |
|---|---|---|
| `CacheException`, которое вызвано `TransactionTimeoutException` | Исключение `TransactionTimeoutException` генерируется при истечении тайм-аута транзакции | Увеличьте тайм-аут или сократите размер транзакции |
| `CacheException`, которое вызвано `TransactionTimeoutException`, которое в свою очередь вызвано `TransactionDeadlockException` | Исключение генерируется при неуспешном завершении `OPTIMISTIC`-транзакции.  В большинстве случаев исключение появляется, когда данные, которые транзакция должна была обновить, одновременно изменил другой поток | Перезапустите выполнение транзакции |
| `TransactionOptimisticException` | Исключение генерируется при неуспешном завершении `OPTIMISTIC`-транзакции. В большинстве случаев исключение появляется, когда данные, которые транзакция должна была обновить, одновременно изменил другой поток | Перезапустите выполнение транзакции |
| `TransactionRollbackException` | Исключение генерируется при откате транзакции (автоматическом или ручном). Данные находятся в согласованном (целостном) состоянии | Данные находятся в согласованном (целостном) состоянии. Выполните перезапуск транзакции |
| `TransactionHeuristicException` | Исключение появляется редко. Оно генерируется из-за неожиданной внутренней или коммуникационной проблемы. Исключение сообщает о ситуациях, которые не предвидела транзакционная подсистема и которые она не обрабатывает должным образом | При появлении ошибки целостность данных может быть нарушена. Выполните перезапуск данных и сообщите команде поддержки DataGrid |

## Завершение длительных транзакций (LRT — long running transaction)

Некоторые события кластера запускают процесс обмена картами партиций и ребалансировку данных в кластере DataGrid, чтобы обеспечить равномерное распределение данных. Например, событие, которое приводит к изменению топологии кластера, происходит каждый раз, когда новый узел добавляется в кластер или существующий узел выходит из него. Также процесс обмена картой партиций запускается при каждом создании нового кеша или SQL-таблицы.

В начале процесса обмена партициями DataGrid берет глобальную блокировку. Блокировку нельзя взять при параллельной работе незавершенных транзакций. Они мешают завершению процесса обмена картой партиций и блокируют некоторые операции, например добавление нового узла в кластер.

Чтобы установить максимальное время, на которое длительным транзакциям разрешается блокировать процесс обмена картой партиций, используйте метод `TransactionConfiguration.setTxTimeoutOnPartitionMapExchange(…​)`. После окончания тайм-аута все неполные транзакции откатятся, и процесс обмена картой партиций продолжится.

Пример, как настроить тайм-аут:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="transactionConfiguration">
        <bean class="org.apache.ignite.configuration.TransactionConfiguration">
            <!-- Установите тайм-аут на 20 секунд. -->
            <property name="TxTimeoutOnPartitionMapExchange" value="20000"/>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
// Создайте конфигурацию DataGrid.
IgniteConfiguration cfg = new IgniteConfiguration();

// Создайте конфигурацию транзакций.
TransactionConfiguration txCfg = new TransactionConfiguration();

// Установите тайм-аут на 20 секунд.
txCfg.setTxTimeoutOnPartitionMapExchange(20000);

cfg.setTransactionConfiguration(txCfg);

// Запустите узел.
Ignition.start(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    TransactionConfiguration = new TransactionConfiguration
    {
        DefaultTimeoutOnPartitionMapExchange = TimeSpan.FromSeconds(20)
    }
};
Ignition.Start(cfg);
```
:::
::::

## Мониторинг транзакций

Список метрик, которые раскрывают информацию по транзакциям, указан в разделе [«События мониторинга»](../../administration-guide/md/monitoring-events.md) документа «Руководство по системному администрированию».

Чтобы получить информацию о транзакциях и прервать выполнение конкретных транзакций, которые выполняются в кластере, можно использовать утилиту `control.sh`. Подробнее об утилите написано в разделе [«Утилита control»](../../administration-guide/md/control-sh.md) документа «Руководство по системному администрированию».