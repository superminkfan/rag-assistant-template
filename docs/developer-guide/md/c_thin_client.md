# Тонкий клиент C++

## Требования

Для работы с тонким клиентом C++ потребуется:

- компилятор C — MS Visual C версии 10.0 и новее, g++ версии 4.4.0 и новее;
- OpenSSL;
- CMake версии 3.6 и новее.

## Установка

Исходный код тонкого клиента C++ поставляется вместе с дистрибутивом DataGrid в каталоге `${IGNITE_HOME}/platforms/cpp`:

::::{md-tab-set}
:::{md-tab-item} Win64
```bash
cd %IGNITE_HOME%\platforms\cpp\
mkdir cmake-build-release
cd cmake-build-release
cmake .. -DWITH_CORE=OFF -DWITH_THIN_CLIENT=ON -DCMAKE_GENERATOR_PLATFORM=x64 -DOPENSSL_ROOT_DIR=<openssl install dir> -DCMAKE_INSTALL_PREFIX=<ignite cpp install dir>
cmake --build . --target install --config Release
```
:::

:::{md-tab-item} Win32
```bash
cd %IGNITE_HOME%\platforms\cpp\
mkdir cmake-build-release
cd cmake-build-release
cmake .. -DWITH_CORE=OFF  -DWITH_THIN_CLIENT=ON -DCMAKE_GENERATOR_PLATFORM=Win32 -DOPENSSL_ROOT_DIR=<openssl install-dir> -DCMAKE_INSTALL_PREFIX=<ignite cpp install dir>
cmake --build . --target install --config Release
```
:::

:::{md-tab-item} Ubuntu
```bash
cd ${CPP_BUILD_DIR}
cmake -DCMAKE_BUILD_TYPE=Release -DWITH_CORE=OFF -DWITH_THIN_CLIENT=ON ${IGNITE_HOME}/platforms/cpp
make
sudo make install
```
:::

:::{md-tab-item} CentOS/RHEL
```bash
cd ${CPP_BUILD_DIR}
cmake3 -DCMAKE_BUILD_TYPE=Release -DWITH_CORE=OFF -DWITH_THIN_CLIENT=ON ${IGNITE_HOME}/platforms/cpp
make
sudo make install
```
:::
::::

## Создание экземпляра клиента

API, который предоставляет тонкий клиент, находится в пространстве имен `ignite::thin`. Основная точка входа в API — метод `IgniteClient::Start(IgniteClientConfiguration)`, который возвращает экземпляр клиента.

:::{code-block} c++
:caption: C++
#include <ignite/thin/ignite_client.h>
#include <ignite/thin/ignite_client_configuration.h>

using namespace ignite::thin;

void TestClient()
{
    IgniteClientConfiguration cfg;

    // Формат списка конечных точек (endpoints): "<host>[port[..range]][,...]".
    cfg.SetEndPoints("xxx.x.x.x:11110,example.com:1234..1240");

    IgniteClient client = IgniteClient::Start(cfg);

    cache::CacheClient<int32_t, std::string> cacheClient =
        client.GetOrCreateCache<int32_t, std::string>("TestCache");

    cacheClient.Put(42, "Hello Ignite Thin Client!");
}
:::

### Partition Awareness

Функция Partition Awareness позволяет тонкому клиенту отправлять запросы напрямую узлу, который содержит нужные данные. Без этой функции приложение, которое подключено к кластеру с помощью тонкого клиента, выполняет все запросы и операции на одном серверном узле (он служит прокси-сервером для входящих запросов). Затем эти операции перенаправляются на узел, где хранятся нужные данные. Это приводит к возникновению узкого места, которое может помешать линейному масштабированию приложения.

Запросы должны проходить через прокси-сервер, откуда они перенаправляются на корректный узел:

![Partition-awareness-off](./resources/partition-awareness-off.png)

С функцией Partition Awareness тонкий клиент может напрямую отправлять запросы основным узлам, где хранятся нужные данные. Функция устраняет узкое место и позволяет приложению проще масштабироваться:

![Partition-awareness-on](./resources/partition-awareness-on.png)

Пример, как использовать Partition Awareness в тонком клиенте C++:

:::{code-block} c++
:caption: C++
#include <ignite/thin/ignite_client.h>
#include <ignite/thin/ignite_client_configuration.h>

using namespace ignite::thin;

void TestClientPartitionAwareness()
{
    IgniteClientConfiguration cfg;
    cfg.SetEndPoints("xxx.x.x.x:10800,xxx.xx.x.x:10800,xxx.xx.xx.x:10800");
    cfg.SetPartitionAwareness(true);

    IgniteClient client = IgniteClient::Start(cfg);

    cache::CacheClient<int32_t, std::string> cacheClient =
        client.GetOrCreateCache<int32_t, std::string>("TestCache");

    cacheClient.Put(42, "Hello Ignite Partition Awareness!");

    cacheClient.RefreshAffinityMapping();

    // Получение значения.
    std::string val = cacheClient.Get(42);
}
:::

## Использование Key-Value API

### Получение экземпляра кеша

Чтобы выполнить основные Key-Value-операции в кеше, получите его экземпляр.

:::{code-block} c++
:caption: C++
cache::CacheClient<int32_t, std::string> cache =
    client.GetOrCreateCache<int32_t, std::string>("TestCache");
:::

Метод `GetOrCreateCache(cacheName)` вернет экземпляр кеша, если он уже существует, и создаст кеш в противном случае.

### Основные операции кеша

Пример, как выполнять основные операции для определенного кеша:

:::{code-block} c++
:caption: C++
std::map<int, std::string> vals;
for (int i = 1; i < 100; i++)
{
    vals[i] = i;
}

cache.PutAll(vals);
cache.Replace(1, "2");
cache.Put(101, "101");
cache.RemoveAll();
:::

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу данных между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

Пример, как настроить параметры SSL в тонком клиенте:

:::{code-block} c++
:caption: C++
IgniteClientConfiguration cfg;

// Устанавливает режим SSL.
cfg.SetSslMode(SslMode::Type::REQUIRE);

// Задает путь к файлу Центра Сертификации SSL для проверки подлинности серверного сертификата при установке соединения.
cfg.SetSslCaFile("path/to/SSL/certificate/authority");

// Задает путь к файлу SSL-сертификата, который будет использоваться при установке соединения.
cfg.SetSslCertFile("path/to/SSL/certificate");

// Задает путь к файлу с приватным SSL-ключом, который будет использоваться при установке соединения.
cfg.SetSslKeyFile("path/to/SSL/private/key");
:::

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента.

:::{code-block} c++
:caption: C++
#include <ignite/thin/ignite_client.h>
#include <ignite/thin/ignite_client_configuration.h>

using namespace ignite::thin;

void TestClientWithAuth()
{
    IgniteClientConfiguration cfg;
    cfg.SetEndPoints("xxx.x.x.x:10800");

    // Используйте собственные учетные данные.
    cfg.SetUser("ignite");
    cfg.SetPassword("ignite");

    IgniteClient client = IgniteClient::Start(cfg);

    cache::CacheClient<int32_t, std::string> cacheClient =
        client.GetOrCreateCache<int32_t, std::string>("TestCache");

    cacheClient.Put(42, "Hello Ignite Thin Client with auth!");
}
:::

### Транзакции

Клиентские транзакции поддерживаются для кешей с режимом `AtomicityMode.TRANSACTIONAL`.

#### Выполнение транзакций

Чтобы запустить транзакцию, получите объект `ClientTransactions` из интерфейса `IgniteClient`. В объекте есть несколько методов `txStart(…​)`, каждый из которых запускает новую транзакцию и возвращает представляющий ее объект (`ClientTransaction`). Используйте этот объект, чтобы сделать коммит (commit) или rollback транзакции.

:::{code-block} c++
:caption: C++
cache::CacheClient<int, int> cache = client.GetCache<int, int>("my_transactional_cache");

transactions::ClientTransactions transactions = client.ClientTransactions();

transactions::ClientTransaction tx = transactions.TxStart();

cache.Put(2, 20);

tx.Commit();
:::

#### Конфигурация транзакций

У клиентских транзакций могут быть разные режимы параллелизма (concurrency), уровни изоляции и тайм-ауты выполнения, которые можно установить сразу для всех для транзакций или отдельно для каждой.

Режим параллелизма, уровень изоляции и тайм-аут можно указать при запуске отдельной транзакции. В этом случае указанные значения переопределяют настройки по умолчанию.

:::{code-block} c++
:caption: C++
transactions::ClientTransactions transactions = client.ClientTransactions();

const uint32_t TX_TIMEOUT = 200;

transactions::ClientTransaction tx = transactions.TxStart(TransactionConcurrency::OPTIMISTIC, TransactionIsolation::SERIALIZABLE, TX_TIMEOUT);

cache.Put(1, 20);

tx.Commit();
:::

Также можно выполнять транзакции с метками.

:::{code-block} c++
:caption: C++
transactions::ClientTransaction tx = transactions.withLabel(label).TxStart();

transactions::ClientTransaction tx = transactions.withLabel(label).TxStart(TransactionConcurrency::OPTIMISTIC, TransactionIsolation::SERIALIZABLE, TX_TIMEOUT);
:::