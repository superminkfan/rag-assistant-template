# Использование Cache Queries

## Общая информация

В `IgniteCache` есть несколько методов запроса, которые получают подкласс класса `Query` и возвращают курсор `QueryCursor`. Доступные типы запросов: `ScanQuery`, `IndexQuery` и `TextQuery`.

Класс `Query` представляет абстрактный постраничный запрос, который выполняется на кеше. Размер страницы настраивается с помощью метода `Query.setPageSize(…​)` (по умолчанию — 1024).

`QueryCursor` представляет набор результатов запроса и обеспечивает прозрачную постраничную итерацию. Когда пользователь начинает итерацию на последней странице, `QueryCursos` автоматически (в фоновом режиме) запрашивает следующую страницу. Если разбивка на страницы не требуется, используйте метод `QueryCursor.getAll()` — он запрашивает записи и хранит их в коллекции.

Курсор — альтернативное хранилище данных, которое содержит финальный набор записей, полученный с помощью запроса `SELECT`.

:::{admonition} Закрытие курсоров
:class: hint

Курсоры закрываются автоматически при вызове метода `QueryCursor.getAll()`. При итерации над курсором в цикле `for` или явном получении `Iterator` нужно явно закрыть курсор или использовать оператор `try-with-resources`.
:::

## Выполнение запросов сканирования (Scan Queries)

Запрос сканирования — поисковый запрос, который используется для получения данных из кеша распределенным способом. При выполнении без параметров запрос возвращает все записи из кеша.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, Person> cache = ignite.getOrCreateCache("myCache");

QueryCursor<Cache.Entry<Integer, Person>> cursor = cache.query(new ScanQuery<>());
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cursor = cache.Query(new ScanQuery<int, Person>());
```
:::

:::{md-tab-item} C++
```c++
Cache<int64_t, Person> cache = ignite.GetOrCreateCache<int64_t, ignite::Person>("personCache");

QueryCursor<int64_t, Person> cursor = cache.Query(ScanQuery());
```
:::
::::

Запросы сканирования возвращают записи, которые соответствуют предикату (если он указан). Предикат применяется на удаленных узлах.

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCache<Integer, Person> cache = ignite.getOrCreateCache("myCache");

// Найдите людей, которые зарабатывают больше 1,000.
IgniteBiPredicate<Integer, Person> filter = (key, p) -> p.getSalary() > 1000;

try (QueryCursor<Cache.Entry<Integer, Person>> qryCursor = cache.query(new ScanQuery<>(filter))) {
    qryCursor.forEach(
            entry -> System.out.println("Key = " + entry.getKey() + ", Value = " + entry.getValue()));
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
class SalaryFilter : ICacheEntryFilter<int, Person>
{
    public bool Invoke(ICacheEntry<int, Person> entry)
    {
        return entry.Value.Salary > 1000;
    }
}

public static void ScanQueryFilterDemo()
{
    var ignite = Ignition.Start();
    var cache = ignite.GetOrCreateCache<int, Person>("person_cache");

    cache.Put(1, new Person {Name = "person1", Salary = 1001});
    cache.Put(2, new Person {Name = "person2", Salary = 999});

    using (var cursor = cache.Query(new ScanQuery<int, Person>(new SalaryFilter())))
    {
        foreach (var entry in cursor)
        {
            Console.WriteLine("Key = " + entry.Key + ", Value = " + entry.Value);
        }
    }
}
```
:::
::::

Запросы сканирования также поддерживают дополнительное закрытие преобразователя. Это позволяет преобразовывать запись на серверном узле перед обратной отправкой. Это может пригодиться для случаев, когда нужно получить только несколько полей большого объекта и минимизировать сетевой трафик.

::::{admonition} Пример, как получить только ключи без значений
:class: hint

:::{code-block} java
:caption: Java
IgniteCache<Integer, Person> cache = ignite.getOrCreateCache("myCache");

// Получите только ключи для людей, которые зарабатывают больше 1,000.
List<Integer> keys = cache.query(new ScanQuery<>(
        // Удаленный фильтр (remote filter).
        (IgniteBiPredicate<Integer, Person>) (k, p) -> p.getSalary() > 1000),
        // Преобразователь (transformer).
        (IgniteClosure<Cache.Entry<Integer, Person>, Integer>) Cache.Entry::getKey).getAll();
:::
::::

## Локальные запросы сканирования

По умолчанию запрос сканирования распределяется по всем узлам. Также можно выполнить запрос локально — в этом случае он работает по данным, которые хранятся на локальном узле (то есть узле, где выполняется запрос).

::::{md-tab-set}
:::{md-tab-item} Java
```java
QueryCursor<Cache.Entry<Integer, Person>> cursor = cache
        .query(new ScanQuery<Integer, Person>().setLocal(true));
```
:::

:::{md-tab-item} C\#/.NET
```c#
var query = new ScanQuery<int, Person> {Local = true};
var cursor = cache.Query(query);
```
:::

:::{md-tab-item} C++
```c++
ScanQuery sq;
sq.SetLocal(true);

QueryCursor<int64_t, Person> cursor = cache.Query(sq);
```
:::
::::

## Выполнение индексных запросов (Index Queries)

:::{admonition} Внимание
:class: danger

Это экспериментальный API, который добавлен в DataGrid версии 4.2120. Поддерживает только Java API. Вопросы и сообщения об ошибках можно направить службе поддержки DataGrid.
:::

Индексные запросы работают по распределенным индексам и извлекают записи кеша, которые соответствуют указанному запросу. `QueryCursor` предоставляет отсортированные записи кеша в порядке, который определен для запроса индекса. `IndexQuery` можно использовать, если небольшой объем данных соответствует критериям фильтра. В таких случаях использование `ScanQuery` не является оптимальным: он сначала извлекает все записи кеша, а затем применяет к ним фильтр. `IndexQuery` опирается на структуру дерева индекса и фильтрует большую часть записей без их извлечения:

:::{code-block} java
:caption: Java
      // Создайте индекс по двум полям (`orgId`, `salary`).
      LinkedHashMap<String,String> fields = new LinkedHashMap<>();
          fields.put("orgId", Integer.class.getName());
          fields.put("salary", Integer.class.getName());

      QueryEntity personEntity = new QueryEntity(Integer.class, Person.class)
          .setFields(fields)
          .setIndexes(Collections.singletonList(
              new QueryIndex(Arrays.asList("orgId", "salary"), QueryIndexType.SORTED)
                  .setName("ORG_SALARY_IDX")
          ));

      CacheConfiguration<Integer, Person> ccfg = new CacheConfiguration<Integer, Person>("entityCache")
          .setQueryEntities(Collections.singletonList(personEntity));

      IgniteCache<Integer, Person> cache = ignite.getOrCreateCache(ccfg);

      // Найдите людей, которые работают в Организации 1.
      QueryCursor<Cache.Entry<Integer, Person>> cursor = cache.query(
          new IndexQuery<Integer, Person>(Person.class, "ORG_SALARY_IDX")
              .setCriteria(eq("orgId", 1))
      );
:::

Критерии индексного запроса определяются в `IndexQueryCriteriaBuilder`. Цель критериев — создать достоверный диапазон для поиска по индексному дереву. По этой причине поля критериев должны соответствовать указанному индексу.

Для индекса, который определен с помощью набора (A, B), допустимыми наборами критериев являются (A) и (A, B). Критерии только с полем (B) недопустимы, так как оно не является набором префикса указанных полей индекса — построить узкий индексный диапазон не получится:

:::{admonition} Примечание
:class: note

Критерии соединяются с помощью оператора `AND`. Можно использовать несколько критериев для одного поля.
:::

:::{code-block} java
:caption: Java
// Найдите людей, которые работают в Организации 1 и зарабатывают больше 1,000.
QueryCursor<Cache.Entry<Integer, Person>> cursor = cache.query(
    new IndexQuery<Integer, Person>(Person.class, "ORG_SALARY_IDX")
        .setCriteria(eq("orgId", 1), gt("salary", 1000))
);
:::

Название индекса не является обязательным параметром. В этом случае DataGrid пытается самостоятельно найти индекс с помощью указанных полей критериев:

:::{code-block} java
:caption: Java
// DataGrid находит подходящий индекс `ORG_SALARY_IDX` по критерию, который указан в поле `orgId`.
QueryCursor<Cache.Entry<Integer, Person>> cursor = cache.query(
    new IndexQuery<Integer, Person>(Person.class)
        .setCriteria(eq("orgId", 1))
);
:::

Для пустого списка критериев выполняется полное сканирование выбранного индекса. Если название индекса не указано, используется индекс `PrimaryKey`.

### Дополнительная фильтрация

`IndexQuery` также поддерживает дополнительный предикат (как и `ScanQuery`). Он подходит для дополнительной фильтрации по записям кеша в тех случаях, когда фильтр не соответствует диапазону дерева индексов. Например, если он содержит какую-то логику, операции `OR` или поля, которые не являются частью индекса:

:::{code-block} java
:caption: Java
// Найдите людей, которые работают в Организации 1 и чьи имена содержат 'Vasya'.
QueryCursor<Cache.Entry<Integer, Person>> cursor = cache.query(
    new IndexQuery<Integer, Person>(Person.class)
        .setCriteria(eq("orgId", 1))
        .setFilter((k, v) -> v.getName().contains("Vasya"))
);
:::

## Связанные темы

Подробнее о событиях Cache Queries написано в подразделе [«События»](events.md) раздела «Работа с событиями».