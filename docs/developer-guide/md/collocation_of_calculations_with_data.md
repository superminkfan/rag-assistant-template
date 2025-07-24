# Коллокация вычислений с данными

Коллоцированные вычисления — тип распределенной обработки данных, при котором вычислительная задача над конкретным набором данных отправляется напрямую на узлы, где расположены необходимые данные. Обратно отправляются только результаты вычислений. Такой подход сводит к минимуму передачу данных между узлами и может значительно сократить время выполнения задачи.

В DataGrid есть несколько способов выполнения коллоцированных вычислений. Они используют affinity-функцию, чтобы определить расположение данных.

В интерфейсе `Compute` есть методы `affinityCall(…​)` и `affinityRun(…​)`, которые коллоцируют задачи с данными по ключу или партиции.

:::{admonition} Важно
:class: attention

Методы `affinityCall(…​)` и `affinityRun(…​)` гарантируют, что данные для ключа или партиции будут присутствовать на целевом узле в течение всего времени выполнения задачи.
:::

:::{admonition} Внимание
:class: danger

Перед выполнением задач на удаленных узлах убедитесь, что определения классов задач доступны на всех узлах:

- добавьте классы в classpath узлов;
- или настройте функцию Peer Class Loading — подробнее о ней написано в подразделе [Peer Class Loading](peer_class_loading.md) раздела «Развертывание кода».
:::

## Коллокация по ключам

Чтобы отправить вычислительную задачу на узел, на котором расположен указанный ключ, используйте методы:

- `IgniteCompute.affinityCall(String cacheName, Object key, IgniteCallable<R> job)`;
- `IgniteCompute.affinityRun(String cacheName, Object key, IgniteRunnable job)`.

DataGrid вызывает настроенную affinity-функцию, чтобы определить расположение указанного ключа.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, String> cache = ignite.cache("myCache");

IgniteCompute compute = ignite.compute();

int key = 1;

// Эта функция выполнится на удаленном узле, где
// находится информация для данного ключа.
compute.affinityRun("myCache", key, () -> {
    // Peek — поиск в локальной памяти.
    System.out.println("Co-located [key= " + key + ", value= " + cache.localPeek(key) + ']');
});
```
:::

:::{md-tab-item} C\#/.NET
```c#
class MyComputeAction : IComputeAction
{
    [InstanceResource] private readonly IIgnite _ignite;

    public int Key { get; set; }

    public void Invoke()
    {
        var cache = _ignite.GetCache<int, string>("myCache");
        // Peek — поиск в локальной памяти.
        Console.WriteLine("Co-located [key= " + Key + ", value= " + cache.LocalPeek(Key) + ']');
    }
}

public static void AffinityRunDemo()
{
    var cfg = new IgniteConfiguration();
    var ignite = Ignition.Start(cfg);

    var cache = ignite.GetOrCreateCache<int, string>("myCache");
    cache.Put(0, "foo");
    cache.Put(1, "bar");
    cache.Put(2, "baz");
    var keyCnt = 3;

    var compute = ignite.GetCompute();

    for (var key = 0; key < keyCnt; key++)
    {
        // Эта функция выполнится на удаленном узле, где
		// находится информация для данного ключа.
         compute.AffinityRun("myCache", key, new MyComputeAction {Key = key});
    }
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
struct FuncAffinityRun : compute::ComputeFunc<void>
{
    /*
    * Конструктор по умолчанию.
    */
    FuncAffinityRun()
    {
        // Без операции.
    }

    /*
    * Параметризованный конструктор.
    */
    FuncAffinityRun(std::string cacheName, int32_t key) :
        cacheName(cacheName), key(key)
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     */
    virtual void Call()
    {
        Ignite& node = GetIgnite();

        Cache<int32_t, std::string> cache = node.GetCache<int32_t, std::string>(cacheName.c_str());

        // Peek — поиск в локальной памяти.
        std::cout << "Co-located [key= " << key << ", value= " << cache.LocalPeek(key, CachePeekMode::ALL) << "]" << std::endl;
    }

    std::string cacheName;
    int32_t key;
};

/**
 * Структура бинарного типа. Определяет набор функций, которые нужны для сериализации или десериализации типа.
 */
namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType<FuncAffinityRun>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("FuncAffinityRun");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "FuncAffinityRun";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const FuncAffinityRun& obj)
            {
                return 0;
            }

            static bool IsNull(const FuncAffinityRun& obj)
            {
                return false;
            }

            static void GetNull(FuncAffinityRun& dst)
            {
                dst = FuncAffinityRun();
            }

            static void Write(BinaryWriter& writer, const FuncAffinityRun& obj)
            {
                writer.WriteString("cacheName", obj.cacheName);
                writer.WriteInt32("key", obj.key);
            }

            static void Read(BinaryReader& reader, FuncAffinityRun& dst)
            {
                dst.cacheName = reader.ReadString("cacheName");
                dst.key = reader.ReadInt32("key");
            }
        };
    }
}


int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите экземпляр кеша.
    Cache<int32_t, std::string> cache = ignite.GetOrCreateCache<int32_t, std::string>("myCache");

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс в качестве вычислительной функции.
    binding.RegisterComputeFunc<FuncAffinityRun>();

    // Получите вычислительный экземпляр.
    compute::Compute compute = ignite.GetCompute();

    int key = 1;

    // Закрытие выполнится на удаленном узле, где
    // находится информация для данного ключа.
    compute.AffinityRun(cache.GetName(), key, FuncAffinityRun(cache.GetName(), key));
}
```
:::
::::

## Коллокация по партициям

Функции `affinityCall(Collection<String> cacheNames, int partId, IgniteCallable job)` и `affinityRun(Collection<String> cacheNames, int partId, IgniteRunnable job)` отправляют задачу на узел, на котором расположена партиция с указанным идентификатором. Функции пригодятся для получения объектов для нескольких ключей, которые принадлежат одной партиции. Так можно создать одну задачу вместо нескольких для каждого ключа.

Например, нужно рассчитать среднее арифметическое значение определенного поля для определенного подмножества ключей. Для распределенных вычислений можно сгруппировать ключи по партициям и отправлять каждую группу ключей на узел с партицией, чтобы получить значения. Количество задач и групп ключей не превышает общего количества партиций (по умолчанию — 1024). Ниже приведен фрагмент кода, который иллюстрирует этот пример.

::::{admonition} Пример
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
// Задача суммирует значения поля `salary` для данного набора ключей.
private static class SumTask implements IgniteCallable<BigDecimal> {
    private Set<Long> keys;

    public SumTask(Set<Long> keys) {
        this.keys = keys;
    }

    @IgniteInstanceResource
    private Ignite ignite;

    @Override
    public BigDecimal call() throws Exception {

        IgniteCache<Long, BinaryObject> cache = ignite.cache("person").withKeepBinary();

        BigDecimal sum = new BigDecimal(0);

        for (long k : keys) {
            BinaryObject person = cache.localPeek(k, CachePeekMode.PRIMARY);
            if (person != null)
                sum = sum.add(new BigDecimal((float) person.field("salary")));
        }

        return sum;
    }
}

public static void calculateAverage(Ignite ignite, Set<Long> keys) {

    // Настройте affinity-функцию для кеша.
    Affinity<Long> affinityFunc = ignite.affinity("person");

    // В этом отображении (map) хранятся коллекции ключей для каждой партиции.
    HashMap<Integer, Set<Long>> partMap = new HashMap<>();
    keys.forEach(k -> {
        int partId = affinityFunc.partition(k);

        Set<Long> keysByPartition = partMap.computeIfAbsent(partId, key -> new HashSet<Long>());
        keysByPartition.add(k);
    });

    BigDecimal total = new BigDecimal(0);

    IgniteCompute compute = ignite.compute();

    List<String> caches = Arrays.asList("person");

    // Выполните итерацию по всем партициям.
    for (Map.Entry<Integer, Set<Long>> pair : partMap.entrySet()) {
        // Отправьте задачу, которая получает определенные ключи для партиции.
        BigDecimal sum = compute.affinityCall(caches, pair.getKey().intValue(), new SumTask(pair.getValue()));
        total = total.add(sum);
    }

    System.out.println("the average salary is " + total.floatValue() / keys.size());
}
:::
::::

Чтобы обработать все данные в кеше, выполните итерацию по всем его партициям и отправьте задачи, которые обрабатывают данные из каждой отдельной партиции.

:::{code-block} java
:caption: Java
// Задача суммирует значения поля 'salary' для всех объектов, которые хранятся
// в указанной партиции.
public static class SumByPartitionTask implements IgniteCallable<BigDecimal> {
    private int partId;

    public SumByPartitionTask(int partId) {
        this.partId = partId;
    }

    @IgniteInstanceResource
    private Ignite ignite;

    @Override
    public BigDecimal call() throws Exception {
        // Используйте бинарные объекты, чтобы избежать десериализации.
        IgniteCache<Long, BinaryObject> cache = ignite.cache("person").withKeepBinary();

        BigDecimal total = new BigDecimal(0);
        try (QueryCursor<Cache.Entry<Long, BinaryObject>> cursor = cache
                .query(new ScanQuery<Long, BinaryObject>(partId).setLocal(true))) {
            for (Cache.Entry<Long, BinaryObject> entry : cursor) {
                total = total.add(new BigDecimal((float) entry.getValue().field("salary")));
            }
        }

        return total;
    }
}
:::

:::{admonition} Вопросы производительности
:class: hint

Использование коллокации вычислений с данными повышает производительность, если объем данных для обработки достаточно велик. В некоторых случаях, когда объем данных небольшой, могут лучше работать запросы сканирования (scan queries). Подробнее о них написано в подразделе [«Использование Cache Queries»](using_cache_queries.md) раздела «Использование Key-Value API».
:::

## Entry Processor

Entry Processor используется для обработки записей кеша на узлах, где он хранится, и для возвращения результатов обработки. Благодаря Entry Processor для выполнения операции с объектом его не нужно передавать целиком. Вместо этого можно выполнить операцию удаленно и передать только результаты.

Если Entry Processor устанавливает значение для несуществующей записи, она добавляется в кеш.

Entry Processor выполняется атомарно в пределах блокировки заданного ключа кеша.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<String, Integer> cache = ignite.cache("mycache");

// Увеличьте значение для определенного ключа на `1`.
// Операция выполнится на узле, где хранится ключ.
// Если в кеше нет записи для конкретного ключа,
// она будет создана.
cache.invoke("mykey", (entry, args) -> {
    Integer val = entry.getValue();

    entry.setValue(val == null ? 1 : val + 1);

    return null;
});
```
:::

:::{md-tab-item} C\#/.NET
```c#
void CacheInvoke()
{
    var ignite = Ignition.Start();

    var cache = ignite.GetOrCreateCache<int, int>("myCache");

    var proc = new Processor();

    // Увеличьте значение для определенного ключа на `1`.
    for (int i = 0; i < 10; i++)
        cache.Invoke(1, proc, 5);
}

class Processor : ICacheEntryProcessor<int, int, int, int>
{
    public int Process(IMutableCacheEntry<int, int> entry, int arg)
    {
        entry.Value = entry.Exists ? arg : entry.Value + arg;

        return entry.Value;
    }
}
```
:::

:::{md-tab-item} C++
```c++
/**
 * Процессор для вызова метода.
 */
class IncrementProcessor : public cache::CacheEntryProcessor<std::string, int32_t, int32_t, int32_t>
{
public:
    /**
     * Конструктор.
     */
    IncrementProcessor()
    {
        // Без операции.
    }

    /**
     * Конструктор копирования.
     *
     * @param Другой экземпляр.
     */
    IncrementProcessor(const IncrementProcessor& other)
    {
        // Без операции.
    }

    /**
     * Оператор назначения.
     *
     * @param Другой экземпляр.
     * @return Данный экземпляр.
     */
    IncrementProcessor& operator=(const IncrementProcessor& other)
    {
        return *this;
    }

    /**
     * Вызов экземпляра.
     */
    virtual int32_t Process(MutableCacheEntry<std::string, int32_t>& entry, const int& arg)
    {
        // Увеличьте значение для определенного ключа на `1`.
        // Операция выполнится на узле, где хранится ключ.
        // Если в кеше нет записи для конкретного ключа,
        // она будет создана.
        if (!entry.IsExists())
            entry.SetValue(1);
        else
            entry.SetValue(entry.GetValue() + 1);

        return entry.GetValue();
    }
};

/**
 * Структура бинарного типа. Определяет набор функций, которые нужны для сериализации и десериализации типа.
 */
namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType<IncrementProcessor>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("IncrementProcessor");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "IncrementProcessor";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const IncrementProcessor& obj)
            {
                return 0;
            }

            static bool IsNull(const IncrementProcessor& obj)
            {
                return false;
            }

            static void GetNull(IncrementProcessor& dst)
            {
                dst = IncrementProcessor();
            }

            static void Write(BinaryWriter& writer, const IncrementProcessor& obj)
            {
                // Без операции.
            }

            static void Read(BinaryReader& reader, IncrementProcessor& dst)
            {
                // Без операции.
            }
        };
    }
}

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "platforms/cpp/examples/put-get-example/config/example-cache.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите экземпляр кеша.
    Cache<std::string, int32_t> cache = ignite.GetOrCreateCache<std::string, int32_t>("myCache");

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс как Entry Processor кеша.
    binding.RegisterCacheEntryProcessor<IncrementProcessor>();

    std::string key("mykey");
    IncrementProcessor inc;

    cache.Invoke<int32_t>(key, inc, NULL);
}
```
:::
::::