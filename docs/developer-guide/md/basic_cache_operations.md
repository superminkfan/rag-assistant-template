# Основные операции с кешем

## Получение экземпляра кеша

Все операции с кешем выполняются через экземпляр `IgniteCache`. Его можно получить для существующего кеша или динамически создать новый:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.ignite();  

// Получите экземпляр кеша `myCache`.
// У разных кешей разные дженерики (generics). 
IgniteCache<Integer, String> cache = ignite.cache("myCache");
```
:::

:::{md-tab-item} С#/.NET
```c#
IIgnite ignite = Ignition.Start();  

// Получите экземпляр кеша `myCache`.
// Аргументы дженериков (generics) используются только для удобства пользователя.
// Можно работать с любым кешем в контексте аргументов дженериков.
// Попытка получить запись несовместимого типа
// приведет к исключению. 
ICache<int, string> cache = ignite.GetCache<int, string>("myCache");
```
:::

:::{md-tab-item} C++
```c++
IIgnite ignite = Ignition.Start();  

// Получите экземпляр кеша `myCache`.
// Аргументы дженериков (generics) используются только для удобства пользователя.
// Можно работать с любым кешем в контексте аргументов дженериков.
// Попытка получить запись несовместимого типа
// приведет к исключению. 
ICache<int, string> cache = ignite.GetCache<int, string>("myCache");
```
:::
::::

## Динамическое создание кеша

Пример, как создать кеш динамическим способом:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.ignite();

CacheConfiguration<Integer, String> cfg = new CacheConfiguration<>();

cfg.setName("myNewCache");
cfg.setAtomicityMode(CacheAtomicityMode.TRANSACTIONAL);

// Создать кеш с указанным названием, если его еще нет.
IgniteCache<Integer, String> cache = ignite.getOrCreateCache(cfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
IIgnite ignite = Ignition.Start();   

// Создать кеш с указанным названием, если его еще нет.
var cache = ignite.GetOrCreateCache<int, string>("myNewCache");
```
:::

:::{md-tab-item} C++
```c++
IIgnite ignite = Ignition.Start();   

// Создать кеш с указанным названием, если его еще нет.
var cache = ignite.GetOrCreateCache<int, string>("myNewCache");
```
:::
::::

Если во время изменения базовой топологии используются методы, которые создают кеши, сгенерируется исключение `org.apache.ignite.IgniteCheckedException`:

```bash
javax.cache.CacheException: class org.apache.ignite.IgniteCheckedException: Failed to start/stop cache, cluster state change is in progress.
        at org.apache.ignite.internal.processors.cache.GridCacheUtils.convertToCacheException(GridCacheUtils.java:1323)
        at org.apache.ignite.internal.IgniteKernal.createCache(IgniteKernal.java:3001)
        at org.apache.ignite.internal.processors.platform.client.cache.ClientCacheCreateWithNameRequest.process(ClientCacheCreateWithNameRequest.java:48)
        at org.apache.ignite.internal.processors.platform.client.ClientRequestHandler.handle(ClientRequestHandler.java:51)
        at org.apache.ignite.internal.processors.odbc.ClientListenerNioListener.onMessage(ClientListenerNioListener.java:173)
        at org.apache.ignite.internal.processors.odbc.ClientListenerNioListener.onMessage(ClientListenerNioListener.java:47)
        at org.apache.ignite.internal.util.nio.GridNioFilterChain$TailFilter.onMessageReceived(GridNioFilterChain.java:278)
        at org.apache.ignite.internal.util.nio.GridNioFilterAdapter.proceedMessageReceived(GridNioFilterAdapter.java:108)
        at org.apache.ignite.internal.util.nio.GridNioAsyncNotifyFilter$3.body(GridNioAsyncNotifyFilter.java:96)
        at org.apache.ignite.internal.util.worker.GridWorker.run(GridWorker.java:119)

        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1128)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:628)
        at java.base/java.lang.Thread.run(Thread.java:834)
```

При появлении такого исключения выполните операцию повторно.

## Удаление кеша (cache destroy)

Чтобы удалить кеш со всех узлов кластера, используйте метод `destroy()`.

:::{code-block} java
:caption: Java
Ignite ignite = Ignition.ignite();

IgniteCache<Long, String> cache = ignite.cache("myCache");

cache.destroy();
:::

## Атомарные операции

Когда экземпляры кеша получены, с ним можно выполнять операции `get`/`put`.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, String> cache = ignite.cache("myCache");

// Храните ключи в кеше (значения окажутся на разных узлах кеша).
for (int i = 0; i < 10; i++)
    cache.put(i, Integer.toString(i));

for (int i = 0; i < 10; i++)
    System.out.println("Got [key=" + i + ", val=" + cache.get(i) + ']');
```
:::

:::{md-tab-item} C\#/.NET
```c#
using (var ignite = Ignition.Start("examples/config/example-cache.xml"))
{
    var cache = ignite.GetCache<int, string>("cache_name");

    for (var i = 0; i < 10; i++)
    {
        cache.Put(i, i.ToString());
    }

    for (var i = 0; i < 10; i++)
    {
        Console.Write("Got [key=" + i + ", val=" + cache.Get(i) + ']');
    }
}
```
:::

:::{md-tab-item} C++
```c++
IgniteConfiguration cfg;
cfg.springCfgPath = "/path/to/configuration.xml";

try
{
    Ignite ignite = Ignition::Start(cfg);

    Cache<int32_t, std::string> cache = ignite.GetOrCreateCache<int32_t, std::string>(CACHE_NAME);

	// Храните ключи в кеше (значения окажутся на разных узлах кеша).
    for (int32_t i = 0; i < 10; i++)
    {
        cache.Put(i, std::to_string(i));
    }

    for (int i = 0; i < 10; i++)
    {
        std::cout << "Got [key=" << i << ", val=" + cache.Get(i) << "]" << std::endl;
    }
}
catch (IgniteError& err)
{
    std::cout << "An error occurred: " << err.GetText() << std::endl;
    return err.GetCode();
}
```
:::
::::

:::{admonition} Внимание 
:class: danger

Пакетные операции, например `putAll()` и `removeAll()`, выполняются как последовательность атомарных операций. При получении частичного отказа по операциям генерируется исключение `CachePartialUpdateException`. Оно содержит список ключей, которые получили отказ по операции обновления.

Чтобы обновить коллекцию записей с помощью одной операции, воспользуйтесь транзакциями — подробнее о них написано в разделе [«Выполнение транзакций»](execution_of_transactions.md).
:::

### Примеры основных атомарных операций

::::{md-tab-set}
:::{md-tab-item} Java
```java
// Операция `put-if-absent` возвращает предыдущее значение.
String oldVal = cache.getAndPutIfAbsent(11, "Hello");

// Операция `put-if-absent` возвращает логический флаг успешного выполнения.
boolean success = cache.putIfAbsent(22, "World");

// Операция `replace-if-exists` (противоположная `getAndPutIfAbsent`) возвращает предыдущее
// значение.
oldVal = cache.getAndReplace(11, "New value");

// Операция `replace-if-exists` (противоположная операции `putIfAbsent`) возвращает логический флаг
// успешного выполнения.
success = cache.replace(22, "Other new value");

// Операция `replace-if-matches`.
success = cache.replace(22, "Other new value", "Yet-another-new-value");

// Операция `remove-if-matches`.
success = cache.remove(11, "Hello");
```
:::

:::{md-tab-item} С#/.NET
```c#
 using (var ignite = Ignition.Start("examples/config/example-cache.xml"))
{
    var cache = ignite.GetCache<string, int>("cache_name");  
	
	// Операция `put-if-absent` возвращает предыдущее значение.
    var oldVal = cache.GetAndPutIfAbsent("Hello", 11);  

	// Операция `put-if-absent` возвращает логический флаг успешного выполнения.
    var success = cache.PutIfAbsent("World", 22); 

	// Операция `replace-if-exists` (противоположная для `getAndPutIfAbsent`) возвращает предыдущее
	// значение.     
	oldVal = cache.GetAndReplace("Hello", 11);   
	
	// Операция `replace-if-exists` (противоположная операции `putIfAbsent`) возвращает логический флаг
	// успешного выполнения.      
	success = cache.Replace("World", 22);  

	// Операция `replace-if-matches`. 
    success = cache.Replace("World", 2, 22);   
	
	// Операция `remove-if-matches`.
    success = cache.Remove("Hello", 1);
}
```
:::

:::{md-tab-item} C++
```c++
IgniteConfiguration cfg;
cfg.springCfgPath = "/path/to/configuration.xml";

Ignite ignite = Ignition::Start(cfg);

Cache<std::string, int32_t> cache = ignite.GetOrCreateCache<std::string, int32_t>("myNewCache");  

// Операция `put-if-absent` возвращает предыдущее значение.
int32_t oldVal = cache.GetAndPutIfAbsent("Hello", 11);  

// Операция `put-if-absent` возвращает логический флаг успешного выполнения.
boolean success = cache.PutIfAbsent("World", 22); 

// Операция `replace-if-exists` (противоположная для `getAndPutIfAbsent`) возвращает предыдущее
// значение.
 oldVal = cache.GetAndReplace("Hello", 11);  

// Операция `replace-if-exists` (противоположная операции `putIfAbsent`) возвращает логический флаг
// успешного выполнения. 
success = cache.Replace("World", 22);  

// Операция `replace-if-matches`.  
success = cache.Replace("World", 2, 22); 
 	
// Операция `remove-if-matches`. 
success = cache.Remove("Hello", 1);
```
:::
::::

## Асинхронное выполнение операций

У большей части операций с кешем есть асинхронные аналоги — в их названиях есть суффикс `Async`.

::::{md-tab-set}
:::{md-tab-item} Java
```java
// Синхронный метод `get`.
V get(K key);

// Асинхронный метод `get`.
IgniteFuture<V> getAsync(K key);
```
:::

:::{md-tab-item} С#/.NET
```c#
// Синхронный метод `get`.
TV Get(TK key);

// Асинхронный метод `get`.
Task<TV> GetAsync(TK key);
```
:::

:::{md-tab-item} С++
```c++
// Синхронный метод `get`.
V Get(K key);

// Асинхронный метод `get`.
Future<V> GetAsync(K key);
```
:::
::::

Асинхронные операции возвращают объект, который представляет результат операции. Можно ожидать завершения операции блокирующим или неблокирующим способом.

Чтобы дождаться результатов неблокирующим способом, зарегистрируйте обратный вызов с помощью метода `IgniteFuture.listen()` или `IgniteFuture.chain()`. Обратный вызов выполняется после завершения операции.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCompute compute = ignite.compute();

// Закройте операцию асинхронно.
IgniteFuture<String> fut = compute.callAsync(() -> "Hello World");

// Дождитесь завершения операции и выведите ее результат.
fut.listen(f -> System.out.println("Job result: " + f.get()));
```
:::

:::{md-tab-item} C\#/.NET
```c#
class HelloworldFunc : IComputeFunc<string>
{
    public string Invoke()
    {
        return "Hello World";
    }
}

public static void AsynchronousExecution()
{
    var ignite = Ignition.Start();
    var compute = ignite.GetCompute();  

	// Закройте операцию асинхронно.
    var fut = compute.CallAsync(new HelloworldFunc());

	// Дождитесь завершения операции и выведите ее результат.
     fut.ContinueWith(Console.Write);
}
```
:::

:::{md-tab-item} C++
```c++
/*
 * Функциональный класс.
 */
class HelloWorld : public compute::ComputeFunc<void>
{
    friend struct ignite::binary::BinaryType<HelloWorld>;
public:
    /*
     * Конструктор по умолчанию.
     */
    HelloWorld()
    {
        // Без операции.
    }

    /**
     * Обратный вызов.
     */
    virtual void Call()
    {
        std::cout << "Job Result: Hello World" << std::endl;
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
        struct BinaryType<HelloWorld>
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("HelloWorld");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "HelloWorld";
            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static int32_t GetHashCode(const HelloWorld& obj)
            {
                return 0;
            }

            static bool IsNull(const HelloWorld& obj)
            {
                return false;
            }

            static void GetNull(HelloWorld& dst)
            {
                dst = HelloWorld();
            }

            static void Write(BinaryWriter& writer, const HelloWorld& obj)
            {
                // Без операции.
            }

            static void Read(BinaryReader& reader, HelloWorld& dst)
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
    binding.RegisterComputeFunc<HelloWorld>();

    // Получите экземпляр вычислений.
    compute::Compute compute = ignite.GetCompute();

    // Объявите экземпляр функции.
    HelloWorld helloWorld;

    // Сделайте асинхронный вызов.
    compute.RunAsync(helloWorld);
}
```
:::
::::

### Выполнение обратных вызовов и пулы потоков

Если асинхронная операция завершается к моменту передачи методу `IgniteFuture.listen()` или  `IgniteFuture.chain()` обратного вызова, он выполняется синхронно с помощью вызванного потока. В противном случае обратный вызов выполняется асинхронно после завершения операции.

Потоки из публичного пула DataGrid выполняют обратные вызовы для асинхронных вычислительных операций. Вызов синхронного кеша и вычислительных операций из обратного вызова может привести к взаимоблокировкам из-за проблемы нехватки пулов (pools starvation). Можно создать пользовательский пул потоков для вложенного выполнения асинхронных вычислительных операций.

Обратные вызовы для асинхронных операций с кешем выполняются с помощью `ForkJoinPool#commonPool`, если в `IgniteConfiguration#asyncContinuationExecutor` не настроен другой исполнитель задачи:

- Исполнитель по умолчанию безопасен для операций внутри обратного вызова.
- Поведение по умолчанию изменилось в DataGrid версии 4.2110. До этого обратные вызовы асинхронных операций с кешем выполнялись из системного пула операций (`striped`).
- Чтобы восстановить поведение по умолчанию, которое было до DataGrid версии 4.2110, используйте `IgniteConfiguration.setAsyncContinuationExecutor(Runnable::run)`:
  - Предыдущее поведение по умолчанию может немного повысить эффективность операций, так как обратные вызовы выполняются без перенаправлений и расписаний.
  - **Небезопасно** — нельзя продолжать операции с кешем, пока системные потоки выполняют обратные вызовы. Если операции с кешем вызываются из обратных вызовов, возможно появление взаимоблокировок.