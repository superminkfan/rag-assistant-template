# Использование API continuous query

Сontinuous query (непрерывный запрос) — запрос, который отслеживает изменения данных в кеше. При запуске API continuous query пользователь получает уведомления обо всех изменениях данных, которые попадают в фильтр запросов.

Все события по обновлению данных передаются локальному слушателю, который нужно указать в запросе. API continuous query гарантирует передачу события локальному слушателю однократно (семантика exactly-once).

Чтобы сузить диапазон записей, которые проверяются на наличие обновлений, укажите удаленный фильтр.

## Локальный слушатель

При обновлении кеша (добавлении, удалении или обновлении записи) в локальный слушатель запроса отправляется соответствующее событие для последующих действий со стороны приложения. Локальный слушатель выполняется на узле, который запускает запрос. В данном случае под узлом подразумевается толстый клиент или узел, который выполняет пользовательские вычислительные задачи и сервисы. Подробнее об API continuous query тонких клиентов написано в подразделе [«Тонкий клиент Java»](java_thin_client.md) раздела «Тонкие клиенты».

Если API continuous query запускается без локального слушателя, сгенерируется исключение.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, String> cache = ignite.getOrCreateCache("myCache");

ContinuousQuery<Integer, String> query = new ContinuousQuery<>();

query.setLocalListener(new CacheEntryUpdatedListener<Integer, String>() {

    @Override
    public void onUpdated(Iterable<CacheEntryEvent<? extends Integer, ? extends String>> events)
        throws CacheEntryListenerException {
        // Обработка события.
    }
});

cache.query(query);
```
:::

:::{md-tab-item} C\#/.NET
```c#
class LocalListener : ICacheEntryEventListener<int, string>
{
    public void OnEvent(IEnumerable<ICacheEntryEvent<int, string>> evts)
    {
        foreach (var cacheEntryEvent in evts)
        {
            // Обработка события.
        }
    }
}
public static void ContinuousQueryListenerDemo()
{
    var ignite = Ignition.Start(new IgniteConfiguration
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
    });
    var cache = ignite.GetOrCreateCache<int, string>("myCache");

    var query = new ContinuousQuery<int, string>(new LocalListener());

    var handle = cache.QueryContinuous(query);

    cache.Put(1, "1");
    cache.Put(2, "2");
}
```
:::

:::{md-tab-item} C++
```c++
/**
 * Класс слушателя.
 */
template<typename K, typename V>
class Listener : public event::CacheEntryEventListener<K, V>
{
public:
    /**
     * Конструктор по умолчанию.
     */
    Listener()
    {
        // Без операции.
    }

    /**
     * Callback-функция обработки события.
     *
     * @param evts События.
     * @param num Количество событий.
     */
    virtual void OnEvent(const CacheEntryEvent<K, V>* evts, uint32_t num)
    {
        for (uint32_t i = 0; i < num; ++i)
        {
            std::cout << "Queried entry [key=" << (evts[i].HasValue() ? evts[i].GetKey() : K())
                << ", val=" << (evts[i].HasValue() ? evts[i].GetValue() : V()) << ']'
                << std::endl;
        }
    }
};

int main()
{
    IgniteConfiguration cfg;
    cfg.springCfgPath = "/path/to/configuration.xml";

    Ignite ignite = Ignition::Start(cfg);

    Cache<int32_t, std::string> cache = ignite.GetOrCreateCache<int32_t, std::string>("myCache");

    // Создание пользовательского слушателя.
    Listener<int32_t, std::string> listener;

    // Создание API continuous query. 
    continuous::ContinuousQuery<int32_t, std::string> query(MakeReference(listener));

    continuous::ContinuousQueryHandle<int32_t, std::string> handle = cache.QueryContinuous(query);
}
```
:::
::::

## Первичный запрос

Можно создать первичный запрос, который будет выполняться до регистрации API continuous query в кластере и получения обновления данных. Чтобы указать первичный запрос, используйте метод  `ContinuousQuery.setInitialQuery(…​)`.

Как и scan query (запрос сканирования), API continuous query выполняется с помощью метода `query()`, который возвращает курсор. Его можно использовать для итерации по результатам первичного запроса (после его установки).

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, String> cache = ignite.getOrCreateCache("myCache");

ContinuousQuery<Integer, String> query = new ContinuousQuery<>();

// Установка необязательного первичного запроса.
// Запрос вернет записи для ключей больше 10.
query.setInitialQuery(new ScanQuery<>((k, v) -> k > 10));

// Обязательный локальный слушатель событий.
query.setLocalListener(events -> {
...
});

try (QueryCursor<Cache.Entry<Integer, String>> cursor = cache.query(query)) {
    // Итерация по записям, которые вернул первичный запрос.
    for (Cache.Entry<Integer, String> e : cursor)
        System.out.println("key=" + e.getKey() + ", val=" + e.getValue());
}
```
:::

:::{md-tab-item} C++
```c++
Cache<int32_t, std::string> cache = ignite.GetOrCreateCache<int32_t, std::string>("myCache");

// Пользовательский слушатель.
Listener<int32_t, std::string> listener;

// Объявление API continuous query.
continuous::ContinuousQuery<int32_t, std::string> query(MakeReference(listener));

// Объявление необязательного первичного запроса.
ScanQuery initialQuery = ScanQuery();

continuous::ContinuousQueryHandle<int32_t, std::string> handle = cache.QueryContinuous(query, initialQuery);

// Итерация по существующим данным, которые хранятся в кеше.
QueryCursor<int32_t, std::string> cursor = handle.GetInitialQueryCursor();

while (cursor.HasNext())
{
    std::cout << cursor.GetNext().GetKey() << std::endl;
}
```
:::
::::

## Удаленный фильтр (Remote filter)

Фильтр выполняется для каждого обновленного ключа и оценивает, нужно ли передавать информацию об обновлении локальному слушателю запроса. Если фильтр возвращает `true`, слушателю передается информация о событии.

Из соображений избыточности фильтр выполняется и для основных, и для резервных версий ключа (если настроены резервные копии партиций). Удаленный фильтр можно использовать как удаленный слушатель для событий обновления данных.

::::{md-tab-set}
:::{md-tab-item} Java
```java
ContinuousQuery<Integer, String> qry = new ContinuousQuery<>();

qry.setLocalListener(events ->
    events.forEach(event -> System.out.format("Entry: key=[%s] value=[%s]\n", event.getKey(), event.getValue()))
);

qry.setRemoteFilterFactory(new Factory<CacheEntryEventFilter<Integer, String>>() {
    @Override
    public CacheEntryEventFilter<Integer, String> create() {
        return new CacheEntryEventFilter<Integer, String>() {
            @Override
            public boolean evaluate(CacheEntryEvent<? extends Integer, ? extends String> e) {
                System.out.format("the value for key [%s] was updated from [%s] to [%s]\n", e.getKey(), e.getOldValue(), e.getValue());
                return true;
            }
        };
    }
});
```
:::

:::{md-tab-item} C\#/.NET
```c#
class LocalListener : ICacheEntryEventListener<int, string>
{
    public void OnEvent(IEnumerable<ICacheEntryEvent<int, string>> evts)
    {
        foreach (var cacheEntryEvent in evts)
        {
            // Обработка событий.
        }
    }
}
class RemoteFilter : ICacheEntryEventFilter<int, string>
{
    public bool Evaluate(ICacheEntryEvent<int, string> e)
    {
        if (e.Key == 1)
        {
            return false;
        }
        Console.WriteLine("the value for key {0} was updated from {1} to {2}", e.Key, e.OldValue, e.Value);
        return true;
    }
}
public static void ContinuousQueryFilterDemo()
{
    var ignite = Ignition.Start(new IgniteConfiguration
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
    });
    var cache = ignite.GetOrCreateCache<int, string>("myCache");

    var query = new ContinuousQuery<int, string>(new LocalListener(), new RemoteFilter());

    var handle = cache.QueryContinuous(query);

    cache.Put(1, "1");
    cache.Put(2, "2");
}
```
:::

:::{md-tab-item} C++
```c++
template<typename K, typename V>
struct RemoteFilter : event::CacheEntryEventFilter<int32_t, std::string>
{
    /**
     * Конструктор по умолчанию.
     */
    RemoteFilter()
    {
        // Без операции.
    }

    /**
     * Деструктор.
     */
    virtual ~RemoteFilter()
    {
        // Без операции.
    }

    /**
     * Callback-функция обработки события.
     *
     * @param event Событие.
     * @return Принимает значение `true`, если событие проходит фильтр.
     */
    virtual bool Process(const CacheEntryEvent<K, V>& event)
    {
        std::cout << "The value for key " << event.GetKey() <<
            " was updated from " << event.GetOldValue() << " to " << event.GetValue() << std::endl;
        return true;
    }
};

namespace ignite
{
    namespace binary
    {
        template<>
        struct BinaryType< RemoteFilter<int32_t, std::string> >
        {
            static int32_t GetTypeId()
            {
                return GetBinaryStringHashCode("RemoteFilter<int32_t,std::string>");
            }

            static void GetTypeName(std::string& dst)
            {
                dst = "RemoteFilter<int32_t,std::string>";

            }

            static int32_t GetFieldId(const char* name)
            {
                return GetBinaryStringHashCode(name);
            }

            static bool IsNull(const RemoteFilter<int32_t, std::string>&)
            {
                return false;
            }

            static void GetNull(RemoteFilter<int32_t, std::string>& dst)
            {
                dst = RemoteFilter<int32_t, std::string>();
            }

            static void Write(BinaryWriter& writer, const RemoteFilter<int32_t, std::string>& obj)
            {
                // Без операции.
            }

            static void Read(BinaryReader& reader, RemoteFilter<int32_t, std::string>& dst)
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

    // Запуск узла.
    Ignite ignite = Ignition::Start(cfg);

    IgniteBinding binding = ignite.GetBinding();

    // Регистрация удаленного фильтра.
    binding.RegisterCacheEntryEventFilter<RemoteFilter<int32_t, std::string>>();

    // Кеш.
    Cache<int32_t, std::string> cache = ignite.GetOrCreateCache<int32_t, std::string>("myCache");

    // Регистрация пользовательского слушателя.
    Listener<int32_t, std::string> listener;

    // Объявление удаленного фильтра.
    RemoteFilter<int32_t, std::string> filter;

    // Объявление API continuous query.
    continuous::ContinuousQuery<int32_t, std::string> qry(MakeReference(listener), MakeReference(filter));
}
```
:::
::::

:::{admonition} Внимание
:class: danger

Перед использованием удаленных фильтров убедитесь, что определения класса фильтров доступны на серверных узлах:

- добавьте классы в classpath каждого серверного узла;
- или включите функцию загрузки классов — подробнее о ней написано в подразделе [Peer Class Loading](peer_class_loading.md) раздела «Развертывание кода».
:::

## Преобразование результатов с помощью Remote transformer

По умолчанию API continuous query отправляет весь обновленный объект данных локальному слушателю. Это может привести к большой загрузке сети (в зависимости от размера объекта). При этом приложениям часто не нужен весь объект и требуется только подмножество его полей.

Чтобы решить эту проблему, используйте API continuous query с преобразованием записей. Преобразователь (Remote transformer) — функция, которая выполняется на удаленных узлах для каждого обновленного объекта и возвращает только результаты преобразования.

:::{code-block} java
:caption: Java
IgniteCache<Integer, Person> cache = ignite.getOrCreateCache("myCache");

// API continuous query с преобразователем.
ContinuousQueryWithTransformer<Integer, Person, String> qry = new ContinuousQueryWithTransformer<>();

// Фабрика для создания преобразователей.
Factory factory = FactoryBuilder.factoryOf(
    // Вернет одно поле сложного объекта.
    // Только это поле передается в локальный слушатель событий.
    (IgniteClosure<CacheEntryEvent, String>)
        event -> ((Person)event.getValue()).getName()
);

qry.setRemoteTransformerFactory(factory);

// Слушатель, который получит преобразованные данные.
qry.setLocalListener(names -> {
    for (String name : names)
        System.out.println("New person name: " + name);
});
:::

:::{admonition} Внимание
:class: danger

Перед использованием преобразования записей убедитесь, что классы фабрики и реализация Remote transformer доступны на серверных узлах:

- добавьте классы в classpath каждого серверного узла;
- или включите функцию загрузки классов — подробнее о ней написано в подразделе [Peer Class Loading](peer_class_loading.md) раздела «Развертывание кода».
:::

## Гарантии доставки событий

API continuous query передает события локальным слушателям клиентов однократно (семантика exactly-once).

Основные (primary) и резервные (backup) узлы обеспечивают очередь обновлений — она содержит обработанные API continuous query события, которые еще не доставили клиентам. Если происходит сбой основного узла или меняется топология кластера, каждый резервный узел отправляет содержимое данной очереди клиентам и следит за тем, чтобы все события доставили локальному слушателю клиента.

Каждая партиция DataGrid содержит специальный счетчик обновлений (`update counter`), который позволяет избежать дублирования уведомлений. Когда запись в партиции обновилась, счетчик для этой партиции увеличится на основных и резервных узлах. Значение счетчика также отправится клиентскому узлу вместе с уведомлением о событии. Таким образом клиент может пропускать уже обработанные события. Как только клиент подтверждает получение события, основные и резервные узлы удаляют запись о нем из своих очередей.