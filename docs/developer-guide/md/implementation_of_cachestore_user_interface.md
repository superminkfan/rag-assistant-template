# Реализация пользовательского интерфейса CacheStore

Можно реализовать собственный интерфейс `CacheStore` и использовать его в качестве базового хранилища данных для кеша. Методы `IgniteCache`, которые читают или меняют данные, будут вызывать соответствующие методы реализации `CacheStore`.

:::{list-table} Методы интерфейса `CacheStore`
:header-rows: 1
 
+   *   Метод
    *   Описание
+   *   `loadCache()`
    *   Метод `loadCache(…)` вызывается каждый раз при вызове `IgniteCache.loadCache(…)` и обычно используется для предварительной загрузки данных в память. Метод загружает данные на все узлы, в которых есть кеш.
    
        Для загрузки данных на конкретный узел вызовите на нем `IgniteCache.localLoadCache()`
+   *   `load()`,  `write()`, `delete()`
    *   Методы `load()`,  `write()` и `delete()` вызываются всегда, когда в интерфейсe `IgniteCache` вызываются методы `get()`, `put()` и `remove()`. Они используются для настройки сквозных чтения и записи при работе с отдельными записями кеша
+   *   `loadAll()`,  `writeAll()`, `deleteAll()`
    *   Методы `loadAll()`,  `writeAll()` и `deleteAll()` в `CacheStore` вызываются всегда, когда в интерфейсе `IgniteCache` вызываются методы `getAll()`, `putAll()` и `removeAll()`. Они используются для:
        - настройки сквозных чтения и записи при работе с множественными записями кеша;
        - улучшения производительности пакетных операций
:::

## CacheStoreAdapter

`CacheStoreAdapter` — расширение `CacheStore`, которое предоставляет реализации по умолчанию для пакетных операций, например `loadAll(Iterable)`, `writeAll(Collection)` и `deleteAll(Collection)`. Для этого расширение перебирает все записи и вызывает соответствующие операции `load()`, `write()` и `delete()` для конкретных записей.

## CacheStoreSession

`CacheStoreSession` используется для хранения контекста между несколькими операциями в хранилище и для обеспечения поддержки транзакций. Операции внутри одной транзакции выполняются с использованием одного и того же соединения с базой данных, которое совершается при коммите транзакции. Сессия хранилища кеша представлена объектом класса `CacheStoreSession`. Его можно внедрить в реализацию `CacheStore` с помощью аннотации `@GridCacheStoreSessionResource`.

Пример реализации хранилища транзакционного кеша можно найти на [сайте GitHub](https://github.com/apache/ignite/blob/master/examples/src/main/java/org/apache/ignite/examples/datagrid/store/jdbc/CacheJdbcPersonStore.java).

## Пример

Ниже приведен пример нетранзакционной реализации `CacheStore`. Пример реализации с поддержкой транзакций можно посмотреть на [сайте GitHub](https://github.com/apache/ignite/blob/master/examples/src/main/java/org/apache/ignite/examples/datagrid/store/jdbc/CacheJdbcPersonStore.java).

:::{admonition} Пример
:class: hint 
:collapsible:

В примере используется нетранзакционный JDBC.

```bash
public class CacheJdbcPersonStore extends CacheStoreAdapter<Long, Person> {
    // Метод вызывается каждый раз, когда в `IgniteCache` вызывается `get(...)`.
    @Override
    public Person load(Long key) {
        try (Connection conn = connection()) {
            try (PreparedStatement st = conn.prepareStatement("select * from PERSON where id=?")) {
                st.setLong(1, key);

                ResultSet rs = st.executeQuery();

                return rs.next() ? new Person(rs.getInt(1), rs.getString(2)) : null;
            }
        } catch (SQLException e) {
            throw new CacheLoaderException("Failed to load: " + key, e);
        }
    }

    @Override
    public void write(Entry<? extends Long, ? extends Person> entry) throws CacheWriterException {
        try (Connection conn = connection()) {
            // Синтаксис команды `MERGE` зависит от используемой базы данных и должен быть адаптирован для нее.
            // Если база данных не поддерживает команду `MERGE`, используйте последовательные
            // команды обновления и вставки.
            try (PreparedStatement st = conn.prepareStatement("merge into PERSON (id, name) key (id) VALUES (?, ?)")) {
                Person val = entry.getValue();

                st.setLong(1, entry.getKey());
                st.setString(2, val.getName());

                st.executeUpdate();
            }
        } catch (SQLException e) {
            throw new CacheWriterException("Failed to write entry (" + entry + ")", e);
        }
    }

    // Метод вызывается каждый раз, когда в `IgniteCache` вызывается `remove(...)`.
    @Override
    public void delete(Object key) {
        try (Connection conn = connection()) {
            try (PreparedStatement st = conn.prepareStatement("delete from PERSON where id=?")) {
                st.setLong(1, (Long) key);

                st.executeUpdate();
            }
        } catch (SQLException e) {
            throw new CacheWriterException("Failed to delete: " + key, e);
        }
    }

    // Метод вызывается каждый раз, когда в `IgniteCache` вызывается `loadCache()`
    // и `localLoadCache()`. Он используется при массовой загрузке кеша.
    // Если массовая загрузка кеша не используется, пропустите этот метод.
    @Override
    public void loadCache(IgniteBiInClosure<Long, Person> clo, Object... args) {
        if (args == null || args.length == 0 || args[0] == null)
            throw new CacheLoaderException("Expected entry count parameter is not provided.");

        final int entryCnt = (Integer) args[0];

        try (Connection conn = connection()) {
            try (PreparedStatement st = conn.prepareStatement("select * from PERSON")) {
                try (ResultSet rs = st.executeQuery()) {
                    int cnt = 0;

                    while (cnt < entryCnt && rs.next()) {
                        Person person = new Person(rs.getInt(1), rs.getString(2));
                        clo.apply(person.getId(), person);
                        cnt++;
                    }
                }
            }
        } catch (SQLException e) {
            throw new CacheLoaderException("Failed to load values from cache store.", e);
        }
    }

    // Откройте JDBC-соединение.
    private Connection connection() throws SQLException {
        // Откройте соединение с RDBMS-системами (MySQL, Postgres, DB2, Microsoft SQL и так далее).
        Connection conn = DriverManager.getConnection("jdbc:mysql://[host]:[port]/[database]", "YOUR_USER_NAME", "YOUR_PASSWORD");

        conn.setAutoCommit(true);

        return conn;
    }
}
```
:::