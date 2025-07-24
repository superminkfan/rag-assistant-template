# Распределенные вычисления

DataGrid предоставляет API для сбалансированного и отказоустойчивого распределения вычислений по узлам кластера. Можно отправлять на выполнение отдельные задачи или реализовать шаблон `MapReduce` с автоматическим разделением задач. API обеспечивает детальный контроль над стратегией распределения заданий — подробнее о ней написано в разделе [«Балансировка нагрузки»](load_balancing.md).

## Получение интерфейса Compute

Основная точка входа для запуска распределенных вычислений — интерфейс `Compute`, который можно получить из экземпляра `Ignite`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.start();

IgniteCompute compute = ignite.compute();
```
:::

:::{md-tab-item} C\#/.NET
```c#
Ignite ignite = Ignition::Start(cfg);

Compute compute = ignite.GetCompute();
```
:::
::::

В интерфейсе `Compute` есть методы для распределения различных типов задач по узлам кластера и запуска коллоцированных вычислений — подробнее о них написано в разделе [«Коллокация вычислений с данными»](collocation_of_calculations_with_data.md).

## Указание набора узлов для вычислений

Каждый экземпляр интерфейса `Compute` связан с набором узлов, на которых выполняются задачи. Подробнее о наборах узлов написано в разделе [«Группы кластеров»](cluster_groups.md).

При вызове метода `ignite.compute()` без указания аргументов возвращается интерфейс для вычислений, который связан со всеми узлами сервера. Чтобы получить экземпляр для определенного подмножества узлов, используйте `Ignite.compute(ClusterGroup group)`. В примере ниже интерфейс `Compute` связан только с удаленными узлами — со всеми узлами, за исключением того, который запускает этот код:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.start();

IgniteCompute compute = ignite.compute(ignite.cluster().forRemotes());
```
:::

:::{md-tab-item} C\#/.NET
```c#
var ignite = Ignition.Start();
var compute = ignite.GetCluster().ForRemotes().GetCompute();
```
:::
::::

## Выполнение задач

В DataGrid есть три интерфейса, которые можно реализовать для представления задачи и выполнить через интерфейс `Compute`:

- `IgniteRunnable` — расширение `java.lang.Runnable` для реализации вычислений, у которых нет входных параметров и которые не возвращают никаких результатов.
- `IgniteCallable` — расширение `java.util.concurrent.Callable`, которое возвращает конкретное значение.
- `IgniteClosure` — функциональный интерфейс, который принимает параметр и возвращает значение.

Можно выполнить задачу один раз (на одном из узлов) или распространить ее выполнение на все узлы.

:::{admonition} Внимание
:class: danger

Перед выполнением задач на удаленных узлах убедитесь, что определения классов задач доступны на всех узлах:

- добавьте классы в classpath узлов;
- или настройте функцию Peer Class Loading — подробнее о ней написано в подразделе [Peer Class Loading](peer_class_loading.md) раздела «Развертывание кода».
:::

### Запуск задачи Runnable

Чтобы выполнить задачу Runnable, используйте метод `run(…​)` интерфейса `Compute`. Задача отправится на один из узлов, который выполняет вычисления:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCompute compute = ignite.compute();

// Выполните итерацию по всем словам и выведите
// каждое из них на отдельном узле кластера.
for (String word : "Print words on different cluster nodes".split(" ")) {
    compute.run(() -> System.out.println(word));
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
class PrintWordAction : IComputeAction
{
    public void Invoke()
    {
        foreach (var s in "Print words on different cluster nodes".Split(" "))
        {
            Console.WriteLine(s);
        }
    }
}

public static void ComputeRunDemo()
{
    var ignite = Ignition.Start(
        new IgniteConfiguration
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
            }
        }
    );
    ignite.GetCompute().Run(new PrintWordAction());
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class PrintWord : public compute::ComputeFunc<void>
{
    friend struct ignite::binary::BinaryType<PrintWord>;
public:
    /*
     * Конструктор по умолчанию.
     */
    PrintWord()
    {
        // Без операции.
    }

    /*
     * Конструктор.
     *
     * @param text Text.
     */
    PrintWord(const std::string& word) :
        word(word)
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     */
    virtual void Call()
    {
        std::cout << word << std::endl;
    }

    /** Слово для вывода. */
    std::string word;

};

/**
 * Структура бинарного типа. Определяет набор функций, которые нужны для сериализации и десериализации типа.
 */
namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType<PrintWord>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("PrintWord");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "PrintWord";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const PrintWord& obj)
            {
                return 0;
            }

            static bool IsNull(const PrintWord& obj)
            {
                return false;
            }

            static void GetNull(PrintWord& dst)
            {
                dst = PrintWord("");
            }

            static void Write(BinaryWriter& writer, const PrintWord& obj)
            {
                writer.RawWriter().WriteString(obj.word);
            }

            static void Read(BinaryReader& reader, PrintWord& dst)
            {
                dst.word = reader.RawReader().ReadString();
            }
        };
    }
}

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс в качестве вычислительной функции.
    binding.RegisterComputeFunc<PrintWord>();

    // Получите вычислительную функцию.
    compute::Compute compute = ignite.GetCompute();

    std::istringstream iss("Print words on different cluster nodes");
    std::vector<std::string> words((std::istream_iterator<std::string>(iss)),
        std::istream_iterator<std::string>());

	// Выполните итерацию по всем словам и выведите
	// каждое из них на отдельном узле кластера.
    for (std::string word : words)
    {
        // Запустите вычислительную задачу.
        compute.Run(PrintWord(word));
    }
}
```
:::
::::

### Запуск задачи Callable

Чтобы выполнить задачу Callable, используйте метод `call(…​)` интерфейса `Compute`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Collection<IgniteCallable<Integer>> calls = new ArrayList<>();

// Выполните итерацию по всем словам предложения и создайте задачи вызова.
for (String word : "How many characters".split(" "))
    calls.add(word::length);

// Выполните коллекцию вызовов в кластере.
Collection<Integer> res = ignite.compute().call(calls);

// Добавьте длины всех слов, которые получили от узлов кластера.
int total = res.stream().mapToInt(Integer::intValue).sum();
```
:::

:::{md-tab-item} C\#/.NET
```c#
class CharCounter : IComputeFunc<int>
{
    private readonly string arg;

    public CharCounter(string arg)
    {
        this.arg = arg;
    }

    public int Invoke()
    {
        return arg.Length;
    }
}

public static void ComputeFuncDemo()
{
    var ignite = Ignition.Start(
        new IgniteConfiguration
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
            }
        }
    );

    // Выполните итерацию по всем словам предложения и создайте задачи вызова.
     var calls = "How many characters".Split(" ").Select(s => new CharCounter(s)).ToList();

    // Выполните коллекцию вызовов в кластере.
     var res = ignite.GetCompute().Call(calls);

    // Добавьте длины всех слов, которые получили от узлов кластера.
    var total = res.Sum();
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class CountLength : public compute::ComputeFunc<int32_t>
{
    friend struct ignite::binary::BinaryType<CountLength>;
public:
    /*
     * Конструктор по умолчанию.
     */
    CountLength()
    {
        // Без операции.
    }

    /*
     * Конструктор.
     *
     * @param text Text.
     */
    CountLength(const std::string& word) :
        word(word)
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     * Считает количество символов в указанном слове.
     *
     * @return Word's length.
     */
    virtual int32_t Call()
    {
        return word.length();
    }

    /** Слово для вывода. */
    std::string word;

};

/**
 * Структура бинарного типа. Определяет набор функций, которые нужны для сериализации и десериализации типа.  
 */
namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType<CountLength>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("CountLength");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "CountLength";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const CountLength& obj)
            {
                return 0;
            }

            static bool IsNull(const CountLength& obj)
            {
                return false;
            }

            static void GetNull(CountLength& dst)
            {
                dst = CountLength("");
            }

            static void Write(BinaryWriter& writer, const CountLength& obj)
            {
                writer.RawWriter().WriteString(obj.word);
            }

            static void Read(BinaryReader& reader, CountLength& dst)
            {
                dst.word = reader.RawReader().ReadString();
            }
        };
    }
}

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс в качестве вычислительной функции.
    binding.RegisterComputeFunc<CountLength>();

    // Получите экземпляр вычислений.
    compute::Compute compute = ignite.GetCompute();

    std::istringstream iss("How many characters");
    std::vector<std::string> words((std::istream_iterator<std::string>(iss)),
        std::istream_iterator<std::string>());

    int32_t total = 0;

    // Выполните итерацию по всем словам предложения, создайте и вызовите задания.
    for (std::string word : words)
    {
        // Добавьте длины всех слов, которые получили от узлов кластера.
        total += compute.Call<int32_t>(CountLength(word));
    }
}
```
:::
::::

### Выполнение IgniteClosure

Для вызова `IgniteClosure` используйте метод `apply(…​)` интерфейса `Compute`. Метод принимает задачу и входной параметр для нее. Параметр передается в интерфейс `IgniteClosure` во время выполнения:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCompute compute = ignite.compute();

// Выполните вызов функции на всех узлах кластера.
Collection<Integer> res = compute.apply(String::length, Arrays.asList("How many characters".split(" ")));

// Добавьте длины всех слов, которые получили от узлов кластера.
int total = res.stream().mapToInt(Integer::intValue).sum();
```
:::

:::{md-tab-item} C\#/.NET
```c#
class CharCountingFunc : IComputeFunc<string, int>
{
    public int Invoke(string arg)
    {
        return arg.Length;
    }
}

public static void Foo()
{
    var ignite = Ignition.Start(
        new IgniteConfiguration
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
            }
        }
    );

    var res = ignite.GetCompute().Apply(new CharCountingFunc(), "How many characters".Split());

    int total = res.Sum();
}
```
:::
::::

### Распространение (broadcasting) задачи

Метод `broadcast()` выполняет задачу на всех узлах, которые связаны с экземпляром Compute:

::::{md-tab-set}
:::{md-tab-item} Java
```java
// Ограничьте распространение только на удаленные узлы.
IgniteCompute compute = ignite.compute(ignite.cluster().forRemotes());

// Выведите приветственное сообщение на удаленных узлах в группе кластеров.
compute.broadcast(() -> System.out.println("Hello Node: " + ignite.cluster().localNode().id()));
```
:::

:::{md-tab-item} C\#/.NET
```c#
class PrintNodeIdAction : IComputeAction
{
    public void Invoke()
    {
        Console.WriteLine("Hello node: " +
                          Ignition.GetIgnite().GetCluster().GetLocalNode().Id);
    }
}

public static void BroadcastDemo()
{
    var ignite = Ignition.Start(
        new IgniteConfiguration
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
            }
        }
    );

    // Ограничьте распространение только на удаленные узлы.
    var compute = ignite.GetCluster().ForRemotes().GetCompute();
    // Выведите приветственное сообщение на удаленных узлах в группе кластеров.
    compute.Broadcast(new PrintNodeIdAction());
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class Hello : public compute::ComputeFunc<void>
{
    friend struct ignite::binary::BinaryType<Hello>;
public:
    /*
     * Конструктор по умолчанию.
     */
    Hello()
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     */
    virtual void Call()
    {
        std::cout << "Hello" << std::endl;
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
        struct BinaryType<Hello>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("Hello");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "Hello";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const Hello& obj)
            {
                return 0;
            }

            static bool IsNull(const Hello& obj)
            {
                return false;
            }

            static void GetNull(Hello& dst)
            {
                dst = Hello();
            }

            static void Write(BinaryWriter& writer, const Hello& obj)
            {
                // Без операции.
            }

            static void Read(BinaryReader& reader, Hello& dst)
            {
                // Без операции.
            }
        };
    }
}

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс в качестве вычислительной функции.
    binding.RegisterComputeFunc<Hello>();

    // Распространите на все узлы.
    compute::Compute compute = ignite.GetCompute();

    // Объявите экземпляр функции.
    Hello hello;

    // Выведите приветственное сообщение на удаленных узлах в группе кластеров.
    compute.Broadcast(hello);
}
```
:::
::::

### Асинхронное выполнение

У всех методов из разделов выше есть асинхронные аналоги:

- `callAsync(…​)`;
- `runAsync(…​)`;
- `applyAsync(…​)`;
- `broadcastAsync(…​)`.

Асинхронные методы возвращают `IgniteFuture`, который представляет результат операции. В примере коллекция задач Callable выполняется асинхронно:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCompute compute = ignite.compute();

Collection<IgniteCallable<Integer>> calls = new ArrayList<>();

// Выполните итерацию по всем словам предложения и создайте задания Callable.
for (String word : "Count characters using a callable".split(" "))
    calls.add(word::length);

IgniteFuture<Collection<Integer>> future = compute.callAsync(calls);

future.listen(fut -> {
    // Общее количество символов.
    int total = fut.get().stream().mapToInt(Integer::intValue).sum();

    System.out.println("Total number of characters: " + total);
});
```
:::

:::{md-tab-item} C\#/.NET
```c#
class CharCounter : IComputeFunc<int>
{
    private readonly string arg;

    public CharCounter(string arg)
    {
        this.arg = arg;
    }

    public int Invoke()
    {
        return arg.Length;
    }
}
public static void AsyncDemo()
{
    var ignite = Ignition.Start(
        new IgniteConfiguration
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
            }
        }
    );

    var calls = "Count character using async compute"
        .Split(" ").Select(s => new CharCounter(s)).ToList();

    var future = ignite.GetCompute().CallAsync(calls);

    future.ContinueWith(fut =>
    {
        var total = fut.Result.Sum();
        Console.WriteLine("Total number of characters: " + total);
    });
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class CountLength : public compute::ComputeFunc<int32_t>
{
    friend struct ignite::binary::BinaryType<CountLength>;
public:
    /*
     * Конструктор по умолчанию.
     */
    CountLength()
    {
        // Без операции.
    }

    /*
     * Конструктор.
     *
     * @param text Text.
     */
    CountLength(const std::string& word) :
        word(word)
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     * Считает количество символов в указанном слове.
     *
     * @return Word's length.
     */
    virtual int32_t Call()
    {
        return word.length();
    }

    /** Слово для вывода. */
    std::string word;

};

/**
 * Структура бинарного типа. Определяет набор функций, которые нужны для сериализации и десериализации типа.
 */
namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType<CountLength>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("CountLength");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "CountLength";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const CountLength& obj)
            {
                return 0;
            }

            static bool IsNull(const CountLength& obj)
            {
                return false;
            }

            static void GetNull(CountLength& dst)
            {
                dst = CountLength("");
            }

            static void Write(BinaryWriter& writer, const CountLength& obj)
            {
                writer.RawWriter().WriteString(obj.word);
            }

            static void Read(BinaryReader& reader, CountLength& dst)
            {
                dst.word = reader.RawReader().ReadString();
            }
        };
    }
}

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    // Получите связующий экземпляр.
    IgniteBinding binding = ignite.GetBinding();

    // Зарегистрируйте класс в качестве вычислительной функции.
    binding.RegisterComputeFunc<CountLength>();

    // Получите вычислительный экземпляр.
    compute::Compute asyncCompute = ignite.GetCompute();

    std::istringstream iss("Count characters using callable");
    std::vector<std::string> words((std::istream_iterator<std::string>(iss)),
        std::istream_iterator<std::string>());

    std::vector<Future<int32_t>> futures;

    // Выполните итерацию по всем словам предложения, создайте и вызовите задания.
    for (std::string word : words)
    {
        // Удаленное вычисление количества символов.
        futures.push_back(asyncCompute.CallAsync<int32_t>(CountLength(word)));
    }

    int32_t total = 0;

    // Вычисление общего количество символов.
    for (Future<int32_t> future : futures)
    {
        // Ожидание результатов.
        future.Wait();

        total += future.GetValue();
    }

    // Вывод результата.
    std::cout << "Total number of characters: " << total << std::endl;
}
```
:::
::::

## Тайм-аут выполнения задачи

Можно установить тайм-аут для выполнения задачи. Если задача не завершится в течение заданного времени, она остановится. Все задания, которые создала задача, отменятся.

Чтобы выполнить задачу с тайм-аутом, используйте метод `withTimeout(…​)` интерфейса `Compute`. Метод возвращает интерфейс, который выполняет первую переданную ему задачу за заданное время. У последующих задач не будет тайм-аута — метод `withTimeout(…​)` нужно вызывать отдельно для каждой задачи:

:::{code-block} java
:caption: Java
IgniteCompute compute = ignite.compute();

compute.withTimeout(300_000).run(() -> {
    // Расчеты.
    // ...
});
:::

## Обмен состояниями между заданиями на локальном узле

Можно разделить состояние между различными вычислительными заданиями, которые выполняются на одном узле. Для этого используйте разделяемое распределенное локальное отображение, которое доступно на каждом узле:

:::{code-block} java
:caption: Java
IgniteCluster cluster = ignite.cluster();

ConcurrentMap<String, Integer> nodeLocalMap = cluster.nodeLocalMap();
:::

Уникальные для локального узла значения похожи на переменные `thread-local`: они не распределяются между другими узлами и хранятся только на локальном узле. Его данные можно использовать для обмена состояниями между вычислительными задачами. Также эти данные могут использовать развернутые сервисы.

В примере ниже задание увеличивает счетчик локального узла каждый раз, когда оно выполняется на каком-либо узле. В результате счетчик `node-local` сообщает каждому узлу, сколько раз задание выполнилось на нем.

::::{admonition} Пример
:class: hint 
:collapsible:

:::{code-block} java
:caption: Java
IgniteCallable<Long> job = new IgniteCallable<Long>() {
    @IgniteInstanceResource
    private Ignite ignite;

    @Override
    public Long call() {
        // Получите ссылку на локальный узел.
        ConcurrentMap<String, AtomicLong> nodeLocalMap = ignite.cluster().nodeLocalMap();

        AtomicLong cntr = nodeLocalMap.get("counter");

        if (cntr == null) {
            AtomicLong old = nodeLocalMap.putIfAbsent("counter", cntr = new AtomicLong());

            if (old != null)
                cntr = old;
        }

        return cntr.incrementAndGet();
    }
};
:::
::::

## Получение данных из вычислительных задач

Чтобы вычислительные задачи могли получить доступ к данным, которые хранятся в кеше, воспользуйтесь экземпляром `Ignite`.

Пример ниже может отображать не самый эффективный способ получения данных. Объект `Person`, соответствующий ключу 1, может находиться на узле, который отличается от узла выполнения задачи. В таком случае получение объекта происходит через сеть. Чтобы избежать этой проблемы, коллоцируйте задачу с данными. Подробнее об этом написано в разделе [«Коллокация вычислений с данными»](collocation_of_calculations_with_data.md).

:::{admonition} Важно
:class: attention

Чтобы использовать ключи и значения объекта вне задач `IgniteCallable` и `IgniteRunnable`, классы ключей и значений нужно развернуть на узлах кластера.
:::

::::{md-tab-set}
:::{md-tab-item} Java
```java
public class MyCallableTask implements IgniteCallable<Integer> {

    @IgniteInstanceResource
    private Ignite ignite;

    @Override
    public Integer call() throws Exception {

        IgniteCache<Long, Person> cache = ignite.cache("person");

        // Получите нужные данные.
        Person person = cache.get(1L);

        // Выполните требуемые действия с данными.

        return 1;
    }
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
class FuncWithDataAccess : IComputeFunc<int>
{
    [InstanceResource] private IIgnite _ignite;

    public int Invoke()
    {
        var cache = _ignite.GetCache<int, string>("someCache");

        // Получите нужные данные.
        string cached = cache.Get(1);

        // Выполните требуемые действия с данными, например:
        Console.WriteLine(cached);

        return 1;
    }
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class GetValue : public compute::ComputeFunc<void>
{
    friend struct ignite::binary::BinaryType<GetValue>;
public:
    /*
     * Конструктор по умолчанию.
     */
    GetValue()
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     */
    virtual void Call()
    {
        Ignite& node = GetIgnite();

        // Получите нужные данные.
        Cache<int64_t, Person> cache = node.GetCache<int64_t, Person>("person");

        // Выполните требуемые действия с данными.
        Person person = cache.Get(1);
    }
};
```
:::
::::