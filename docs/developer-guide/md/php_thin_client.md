# Тонкий клиент PHP

## Требования

Для работы с тонким клиентом PHP потребуется:

- [PHP версии 7.2 или новее](https://www.php.net/manual/en/install.php) и [менеджер зависимостей Composer](https://getcomposer.org/download/).
- Модуль `php-xml`.
- Расширение [PHP MBString](https://www.php.net/manual/en/mbstring.installation.php). В зависимости от конфигурации PHP может потребоваться установить или настроить расширение.

## Установка

Тонкий клиент PHP поставляется в виде пакета Composer. Также его можно самостоятельно собрать из репозитория с исходным кодом. Для установки клиента можно использовать любой из предложенных способов.

### Composer

Чтобы установить тонкий клиент PHP с помощью Composer, используйте команду:

:::{code-block} php
:caption: PHP
composer require apache/apache-ignite-client
:::

Чтобы использовать клиент в приложении, включите в исходный код файл `vendor/autoload.php`, который сгенерирован в Composer.

:::{code-block} php
:caption: PHP
require_once __DIR__ . '/vendor/autoload.php';
:::

### Установка из исходников

Тонкий клиент можно установить из репозитория, который доступен для скачивания в [GitHub Apache Ignite](https://github.com/apache/ignite-php-thin-client).

:::{code-block} php
:caption: PHP
git clone git@github.com:apache/ignite-php-thin-client.git
composer install --no-dev
:::

Чтобы использовать клиент в приложении, включите в исходный код файл `vendor/autoload.php`, который сгенерирован в Composer.

:::{code-block} php
:caption: PHP
require_once "<php_client_root_dir>/vendor/autoload.php";
:::

## Создание экземпляра клиента

Все операции тонкого клиента PHP выполняются через экземпляр класса `Client`. Можно создать столько экземпляров `Client`, сколько потребуется — они будут работать независимо друг от друга.

:::{code-block} php
:caption: PHP
use Apache\Ignite\Client;

$client = new Client();
:::

## Подключение к кластеру

Чтобы подключиться к кластеру, задайте параметры подключения в объекте `ClientConfiguration` и используйте метод `Client.connect(…​)`.

:::{code-block} php
:caption: PHP
use Apache\Ignite\Client;
use Apache\Ignite\ClientConfiguration;
use Apache\Ignite\Exception\ClientException;

function connectClient(): void
{
    $client = new Client();
    try {
        $clientConfiguration = new ClientConfiguration(
            'xxx.x.x.x:10800', 'xxx.x.x.x:10801', 'xxx.x.x.x:10802');
        // Подключитесь к узлу DataGrid.
        $client->connect($clientConfiguration);
    } catch (ClientException $e) {
        echo($e->getMessage());
    }
}

connectClient();
:::

Конструктор `ClientConfiguration` принимает список конечных точек (endpoints) узла, поэтому нужно указать хотя бы одну конечную точку. Если указать несколько точек, тонкий клиент будет использовать их в целях отказоустойчивости — подробнее об этом написано в подразделе «Отказоустойчивость клиентского соединения» раздела [«Обзор тонких клиентов»](thin_clients_overview.md).

Если клиент не может подключиться к кластеру, при попытке выполнить какую-либо удаленную операцию сгенерируется исключение `NoConnectionException`.

Если клиент неожиданно теряет соединение до или во время операции, генерируется исключение `OperationStatusUnknownException`. В этом случае невозможно узнать, была ли операция фактически выполнена в кластере. Когда приложение вызовет следующую операцию, клиент попытается повторно подключиться к следующему узлу, который указан в конфигурации.

Чтобы закрыть соединение, вызовите метод `disconnect()`.

## Использование Key-Value API

### Получение и создание экземпляра кеша

Экземпляр клиента предоставляет методы для получения экземпляра кеша:

- `getCache(name)` — возвращает существующий кеш по имени. Метод не проверяет, есть ли кеш в кластере — если попытаться выполнить любую операцию с кешем, сгенерируется исключение.
- `getOrCreateCache(name, config)` — возвращает существующий кеш по имени или создает кеш с указанной конфигурацией.
- `createCache(name, config)` — создает кеш с указанными именем и параметрами.

::::{admonition} Пример, как создать экземпляр кеша
:class: hint

:::{code-block} php
:caption: PHP
$cacheCfg = new CacheConfiguration();
$cacheCfg->setCacheMode(CacheConfiguration::CACHE_MODE_REPLICATED);
$cacheCfg->setWriteSynchronizationMode(CacheConfiguration::WRITE_SYNC_MODE_FULL_SYNC);

$cache = $client->getOrCreateCache('References', $cacheCfg);
:::
::::

### Основные Key-Value-операции

::::{admonition} Пример, как выполнять основные операции с экземпляром кеша
:class: hint 
:collapsible:

:::{code-block} php
:caption: PHP
$val = array();
$keys = range(1, 100);
foreach ($keys as $number) {
    $val[] = new CacheEntry($number, strval($number));
}
$cache->putAll($val);

$replace = $cache->replaceIfEquals(1, '2', '3');
echo $replace ? 'true' : 'false'; //false
echo "\r\n";

$value = $cache->get(1);
echo $value; //1
echo "\r\n";

$replace = $cache->replaceIfEquals(1, "1", 3);
echo $replace ? 'true' : 'false'; //true
echo "\r\n";

$value = $cache->get(1);
echo $value; //3
echo "\r\n";

$cache->put(101, '101');

$cache->removeKeys($keys);
$sizeIsOne = $cache->getSize() == 1;
echo $sizeIsOne ? 'true' : 'false'; //true
echo "\r\n";

$value = $cache->get(101);
echo $value; //101
echo "\r\n";

$cache->removeAll();
$sizeIsZero = $cache->getSize() == 0;
echo $sizeIsZero ? 'true' : 'false'; //true
echo "\r\n";
:::
::::

## Scan Queries

Метод `Cache.query(ScanQuery)` можно использовать для получения всех записей из кеша. Он возвращает объект `cursor` со стандартным интерфейсом PHP Iterator — используйте курсор для «ленивого» перебора результатов по одному. Также в курсоре есть методы для получения всех результатов сразу.

:::{code-block} php
:caption: PHP
$cache = $client->getOrCreateCache('personCache');

$cache->put(1, new Person(1, 'John Smith'));
$cache->put(1, new Person(1, 'John Johnson'));

$qry = new ScanQuery();
$cache->query(new ScanQuery());
:::

## Выполнение SQL-запросов

Тонкий клиент PHP поддерживает все команды SQL, которые поддерживает DataGrid. Подробнее о командах SQL написано в разделе [«Работа с SQL и Apache Calcite»](working_with_sql_and_apache_calcite.md).

Команды выполняются с помощью метода объекта кеша `query(SqlFieldQuery)`. Он принимает экземпляр `SqlFieldsQuery`, который представляет собой SQL-запрос. Метод `query()` возвращает объект `cursor` со стандартным интерфейсом PHP Iterator — используйте курсор для «ленивого» перебора результатов по одному. Также в курсоре есть методы для получения всех результатов сразу.

:::{code-block} php
:caption: PHP
$create_table = new SqlFieldsQuery(
    sprintf('CREATE TABLE IF NOT EXISTS Person (id INT PRIMARY KEY, name VARCHAR) WITH "VALUE_TYPE=%s"', Person::class)
);
$create_table->setSchema('PUBLIC');
$cache->query($create_table)->getAll();

$key = 1;
$val = new Person(1, 'Person 1');

$insert = new SqlFieldsQuery('INSERT INTO Person(id, name) VALUES(?, ?)');
$insert->setArgs($val->id, $val->name);
$insert->setSchema('PUBLIC');
$cache->query($insert)->getAll();

$select = new SqlFieldsQuery('SELECT name FROM Person WHERE id = ?');
$select->setArgs($key);
$select->setSchema('PUBLIC');
$cursor = $cache->query($select);
// Получите результаты. Метод `getAll()` закрывает курсор. Не вызывайте `cursor.close()`.
$results = $cursor->getAll();

if (sizeof($results) != 0) {
    echo 'name = ' . $results[0][0];
    echo "\r\n";
}
:::

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

::::{admonition} Пример конфигурации для включения SSL в тонком клиенте
:class: hint

:::{code-block} php
:caption: PHP
$tlsOptions = [
    'local_cert' => '/path/to/client/cert',
    'cafile' => '/path/to/ca/file',
    'local_pk' => '/path/to/key/file'
];

$config = new ClientConfiguration('localhost:10800');
$config->setTLSOptions($tlsOptions);

$client = new Client();
$client->connect($config);
:::
::::

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента.

:::{code-block} php
:caption: PHP
$config = new ClientConfiguration('localhost:10800');
$config->setUserName('ignite');
$config->setPassword('ignite');
//$config->setTLSOptions($tlsOptions);

$client = new Client();
$client->connect($config);
:::