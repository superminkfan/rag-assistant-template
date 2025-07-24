# Тонкий клиент Node.js

## Требования

Для работы с тонким клиентом требуется Node.js версии 8 или новее:

- загрузите готовый бинарный файл для целевой платформы на [официальном сайте Node.js](https://nodejs.org/en/download/);
- или установите с помощью менеджера пакетов с [официального сайта Node.js](https://nodejs.org/en/download/package-manager).

Когда загружены `node` и `npm`, можно переходить к установке.

## Установка

Тонкий клиент Node.js поставляется в виде `npm`-пакета. Также его можно самостоятельно собрать из репозитория с исходным кодом. Для установки клиента можно использовать любой из предложенных способов.

### NPM

Чтобы установить клиент из NPM-репозитория, используйте команду:

```bash
npm install -g apache-ignite-client
```

### Установка из исходников

Тонкий клиент можно установить из репозитория, который доступен для скачивания в [GitHub Apache Ignite](https://github.com/apache/ignite-nodejs-thin-client):

```bash
git clone git@github.com:apache/ignite-nodejs-thin-client.git
cd nodejs-thin-client
npm install
npm run build
npm link
npm link apache-ignite-client
```

## Создание экземпляра клиента

API тонкого клиента предоставляет класс `IgniteClient`.

::::{admonition} Пример, как получить экземпляр клиента
:class: hint

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');

const igniteClient = new IgniteClient(onStateChanged);

function onStateChanged(state, reason) {
    if (state === IgniteClient.STATE.CONNECTED) {
        console.log('Client is started');
    }
    else if (state === IgniteClient.STATE.DISCONNECTED) {
        console.log('Client is stopped');
        if (reason) {
            console.log(reason);
        }
    }
}
:::
::::

Конструктор принимает один необязательный параметр, который представляет функцию обратного вызова (callback-функцию). Она вызывается каждый раз при изменении состояния соединения — подробнее написано ниже в разделе [«Подключение к кластеру»](#подключение-к-кластеру).

Можно создавать любое количество экземпляров `IgniteClient` — они будут работать независимо друг от друга.

## Подключение к кластеру

Чтобы подключиться к кластеру, используйте метод `IgniteClient.connect()`. Он принимает объект класса `IgniteClientConfiguration`, который представляет параметры соединения. Параметры должны содержать список узлов в формате `host:port` — он будет использоваться в целях отказоустойчивости.

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');
const IgniteClientConfiguration = IgniteClient.IgniteClientConfiguration;

async function connectClient() {
    const igniteClient = new IgniteClient(onStateChanged);
    try {
        const igniteClientConfiguration = new IgniteClientConfiguration(
            'xxx.x.x.x:10800', 'xxx.x.x.x:10801', 'xxx.x.x.x:10802');
        // Подключитесь к узлу DataGrid.
        await igniteClient.connect(igniteClientConfiguration);
    }
    catch (err) {
        console.log(err.message);
    }
}

function onStateChanged(state, reason) {
    if (state === IgniteClient.STATE.CONNECTED) {
        console.log('Client is started');
    }
    else if (state === IgniteClient.STATE.CONNECTING) {
        console.log('Client is connecting');
    }
    else if (state === IgniteClient.STATE.DISCONNECTED) {
        console.log('Client is stopped');
        if (reason) {
            console.log(reason);
        }
    }
}

connectClient();
:::

Подробнее об отказоустойчивости клиентского соединения написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

У клиента есть три состояния подключения: `CONNECTING`, `CONNECTED` и `DISCONNECTED`. Можно указать функцию обратного вызова в объекте конфигурации клиента — она будет вызываться каждый раз, когда меняется состояние подключения.

Взаимодействие с кластером возможно только в состоянии `CONNECTED`. Если соединение разорвано, клиент автоматически переходит в состояние `CONNECTING` и пытается повторно подключиться с помощью механизма отказоустойчивости. Если клиент не смог подключиться ни по одному адресу узла из списка, он переходит в состояние `DISCONNECTED`.

Чтобы закрыть соединение, вызовите метод `disconnect()` — клиент перейдет в состояние `DISCONNECTED`.

## Partition Awareness

Функция Partition Awareness позволяет тонкому клиенту отправлять запросы напрямую узлу, который содержит нужные данные. Без этой функции приложение, которое подключено к кластеру с помощью тонкого клиента, выполняет все запросы и операции на одном серверном узле (он служит прокси-сервером для входящих запросов). Затем эти операции перенаправляются на узел, где хранятся нужные данные. Это приводит к возникновению узкого места, которое может помешать линейному масштабированию приложения.

Запросы должны проходить через прокси-сервер, откуда они перенаправляются на корректный узел:

![Partition-awareness-off](./resources/partition-awareness-off.png)

С функцией Partition Awareness тонкий клиент может напрямую отправлять запросы основным узлам, где хранятся нужные данные. Функция устраняет узкое место и позволяет приложению проще масштабироваться:

![Partition-awareness-on](./resources/partition-awareness-on.png)

Чтобы включить Partition Awareness, установите для параметра конфигурации `partitionAwareness` значение `true`.

:::{code-block} js
:caption: JSON
const ENDPOINTS = ['xxx.x.x.x:10800', 'xxx.x.x.x:10801', 'xxx.x.x.x:10802'];
let cfg = new IgniteClientConfiguration(...ENDPOINTS);
const useTls = false;
const partitionAwareness = true;

cfg.setConnectionOptions(useTls, null, partitionAwareness);
await igniteClient.connect(cfg);
:::

## Включение отладки (debug)

::::{admonition} Пример, как включить отладку
:class: hint

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');

const igniteClient = new IgniteClient();
igniteClient.setDebug(true);
:::
::::

## Использование Key-Value API

### Получение экземпляра кеша

Key-Value API предоставляется экземпляром кеша. Тонкий клиент предоставляет несколько методов получения экземпляра кеша:

- получение кеша по его имени;
- создание кеша с указанным именем и опциональной конфигурацией;
- получение, создание, уничтожение кеша и так далее.

Можно создать любое количество экземпляров для одного и того же или разных кешей и работать с ними параллельно.

::::{admonition} Пример, как получить доступ кешу по имени и затем уничтожить его
:class: hint 
:collapsible:

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');
const IgniteClientConfiguration = IgniteClient.IgniteClientConfiguration;

async function getOrCreateCacheByName() {
    const igniteClient = new IgniteClient();
    try {
        await igniteClient.connect(new IgniteClientConfiguration('xxx.x.x.x:10800'));
        // Получите или создайте кеш по имени.
        const cache = await igniteClient.getOrCreateCache('myCache');

        // Выполните Key-Value-операции кеша.
        // ...

        // Уничтожьте кеш.
        await igniteClient.destroyCache('myCache');
    }
    catch (err) {
        console.log(err.message);
    }
    finally {
        igniteClient.disconnect();
    }
}

getOrCreateCacheByName();
:::
::::

### Конфигурация кеша

При создании нового кеша можно предоставить экземпляр конфигурации.

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');
const IgniteClientConfiguration = IgniteClient.IgniteClientConfiguration;
const CacheConfiguration = IgniteClient.CacheConfiguration;

async function createCacheByConfiguration() {
    const igniteClient = new IgniteClient();
    try {
        await igniteClient.connect(new IgniteClientConfiguration('xxx.x.x.x:10800'));
        // Создайте кеш с указанными именем и конфигурацией.
        const cache = await igniteClient.createCache(
            'myCache',
            new CacheConfiguration().setSqlSchema('PUBLIC'));
    }
    catch (err) {
        console.log(err.message);
    }
    finally {
        igniteClient.disconnect();
    }
}

createCacheByConfiguration();
:::

### Конфигурация отображения типов (Type Mapping)

Типы Node.js не всегда однозначно соответствуют типам Java. В некоторых случаях может потребоваться явно указать типы ключей и значений в конфигурации кеша. Клиент будет использовать эти типы для преобразования объектов `key` и `value` между типами данных Java/JavaScript во время выполнения операций чтения и записи кеша.

Если не указать типы, клиент будет использовать стандартное отображение. 

::::{admonition} Пример  отображения типов
:class: hint

:::{code-block} js
:caption: JSON
const cache = await igniteClient.getOrCreateCache('myCache');
// Установите типы ключей и значений кеша.
cache.setKeyType(ObjectType.PRIMITIVE_TYPE.INTEGER)
    .setValueType(new MapObjectType(
        MapObjectType.MAP_SUBTYPE.LINKED_HASH_MAP,
        ObjectType.PRIMITIVE_TYPE.SHORT,
        ObjectType.PRIMITIVE_TYPE.BYTE_ARRAY));
:::
::::

### Типы данных

Клиент поддерживает два способа отображения между типами DataGrid и JavaScript: явный и стандартный.

#### Явное отображение

Маппинг происходит каждый раз, когда приложение выполняет операции чтения и записи поля в/из кластера с помощью API клиента. Полем могут быть любые данные, которые хранятся в DataGrid — полные ключ или значение записи DataGrid, элемент массива или набора, поле сложного объекта и так далее.

С помощью методов API клиента приложение может явно указать тип DataGrid для определенного поля. Клиент использует эту информацию для преобразования поля из типа JavaScript в тип Java и наоборот во время операций чтения и записи. Поле преобразуется в тип JavaScript в результате операций чтения. Оно проверяет соответствие типу JavaScript во входных данных операций записи.

Если в приложении явно не указан тип DataGrid для поля, во время операций его чтения и записи клиент будет использовать стандартное отображение.

### Основные Key-Value-операции

Класс `CacheClient` предоставляет методы для работы с записями кеша при помощи Key-Value-операций (`put`, `get`, `putAll`, `getAll`, `replace` и другие).

:::{code-block} js
:caption: JSON
const IgniteClient = require('apache-ignite-client');
const IgniteClientConfiguration = IgniteClient.IgniteClientConfiguration;
const ObjectType = IgniteClient.ObjectType;
const CacheEntry = IgniteClient.CacheEntry;

async function performCacheKeyValueOperations() {
    const igniteClient = new IgniteClient();
    try {
        await igniteClient.connect(new IgniteClientConfiguration('1xxx.x.x.x:10800'));
        const cache = (await igniteClient.getOrCreateCache('myCache')).
        setKeyType(ObjectType.PRIMITIVE_TYPE.INTEGER);
        // Подставьте и получите значение.
        await cache.put(1, 'abc');
        const value = await cache.get(1);
        console.log(value);

        // Подставьте и получите несколько значений с помощью методов `putAll()` и `getAll()`.
        await cache.putAll);
        const values = await cache.getAll);
        console.log(values.flatMap(val => val.getValue()));

        // Удалите все записи из кеша.
        await cache.clear();
    }
    catch (err) {
        console.log(err.message);
    }
    finally {
        igniteClient.disconnect();
    }
}

performCacheKeyValueOperations();
:::

## Scan Queries

Метод `IgniteClient.query(scanquery)` можно использовать для получения всех записей кеша. Он возвращает объект курсора, который можно использовать для ленивого перебора множества результатов или получения всех результатов сразу.

Чтобы выполнить запрос сканирования, создайте объект `ScanQuery` и вызовите метод `IgniteClient.query(scanquery)`.

:::{code-block} js
:caption: JSON
const cache = (await igniteClient.getOrCreateCache('myCache')).
    setKeyType(ObjectType.PRIMITIVE_TYPE.INTEGER);

// Поместите несколько значений с помощью `putAll()`.
await cache.putAll([
    new CacheEntry(1, 'value1'),
    new CacheEntry(2, 'value2'),
    new CacheEntry(3, 'value3')]);

// Создайте и настройте scan query.
const scanQuery = new ScanQuery().
    setPageSize(1);
// Получите курсор scan query.
const cursor = await cache.query(scanQuery);
// Получите все записи кеша, которые вернул scan query.
for (let cacheEntry of await cursor.getAll()) {
    console.log(cacheEntry.getValue());
}
:::

## Выполнение SQL-запросов

Тонкий клиент Node.js поддерживает все команды SQL, которые поддерживает DataGrid. Подробнее о командах SQL написано в подразделе «Справочник по SQL» раздела [«Работа с SQL и Apache Calcite»](working_with_sql_and_apache_calcite.md).

Команды выполняются с помощью метода объекта кеша `query(SqlFieldQuery)`. Он принимает экземпляр `SqlFieldsQuery`, который представляет собой SQL-запрос, и возвращает экземпляр класса `SqlFieldsCursor`. Используйте курсор для перебора множества результатов или получения всех результатов сразу.

:::{code-block} js
:caption: JSON
// Конфигурация кеша, которая нужна для выполнения SQL-запроса:
const cacheConfiguration = new CacheConfiguration().
    setQueryEntities(
        new QueryEntity().
            setValueTypeName('Person').
            setFields([
                new QueryField('name', 'java.lang.String'),
                new QueryField('salary', 'java.lang.Double')
            ]));
const cache = (await igniteClient.getOrCreateCache('sqlQueryPersonCache', cacheConfiguration)).
    setKeyType(ObjectType.PRIMITIVE_TYPE.INTEGER).
    setValueType(new ComplexObjectType({ 'name' : '', 'salary' : 0 }, 'Person'));

// Поместите несколько значений с помощью `putAll()`.
await cache.putAll([
    new CacheEntry(1, { 'name' : 'John Doe', 'salary' : 1000 }),
    new CacheEntry(2, { 'name' : 'Jane Roe', 'salary' : 2000 }),
    new CacheEntry(3, { 'name' : 'Mary Major', 'salary' : 1500 })]);

// Создайте и настройте SQL-запрос.
const sqlQuery = new SqlQuery('Person', 'salary > ? and salary <= ?').
    setArgs(900, 1600);
// Получите курсор SQL-запроса.
const cursor = await cache.query(sqlQuery);
// Получите все записи кеша, которые вернул SQL-запрос.
for (let cacheEntry of await cursor.getAll()) {
    console.log(cacheEntry.getValue());
}
:::

## Безопасность

### Протокол TLS версии 1.2 и выше

Чтобы использовать зашифрованную передачу данных между тонким клиентом и кластером, включите протокол TLS версии 1.2 и выше в конфигурации кластера и клиента. Подробнее о настройке кластера написано в разделе [«Обзор тонких клиентов»](thin_clients_overview.md).

::::{admonition} Пример конфигурации для включения SSL в тонком клиенте
:class: hint 
:collapsible:

:::{code-block} js
:caption: JSON
const tls = require('tls');

const FS = require('fs');
const IgniteClient = require("apache-ignite-client");
const ObjectType = IgniteClient.ObjectType;
const IgniteClientConfiguration = IgniteClient.IgniteClientConfiguration;

const ENDPOINT = 'localhost:10800';
const USER_NAME = 'ignite';
const PASSWORD = 'ignite';

const TLS_KEY_FILE_NAME = __dirname + '/certs/client.key';
const TLS_CERT_FILE_NAME = __dirname + '/certs/client.crt';
const TLS_CA_FILE_NAME = __dirname + '/certs/ca.crt';

const CACHE_NAME = 'AuthTlsExample_cache';

// Пример показывает, как установить безопасное соединение с узлом DataGrid и использовать аутентификацию с именем пользователя и паролем
// и основные запросы Key-Value-операций для примитивных типов:
// - подключиться к узлу с помощью протокола TLS и введения имени пользователя и пароля;
// - создать кеш, если его еще нет;
// - определить типы ключа и значения кеша;
// - поместить данные примитивного типа в кеш;
// - получить данные из кеша;
// - уничтожить кеш.

class AuthTlsExample {

    async start() {
        const igniteClient = new IgniteClient(this.onStateChanged.bind(this));
        igniteClient.setDebug(true);
        try {
            const connectionOptions = {
                'key' : FS.readFileSync(TLS_KEY_FILE_NAME),
                'cert' : FS.readFileSync(TLS_CERT_FILE_NAME),
                'ca' : FS.readFileSync(TLS_CA_FILE_NAME)
            };
            await igniteClient.connect(new IgniteClientConfiguration(ENDPOINT).
            setUserName(USER_NAME).
            setPassword(PASSWORD).
            setConnectionOptions(true, connectionOptions));

            const cache = (await igniteClient.getOrCreateCache(CACHE_NAME)).
            setKeyType(ObjectType.PRIMITIVE_TYPE.INTEGER).
            setValueType(ObjectType.PRIMITIVE_TYPE.SHORT_ARRAY);

            await this.putGetData(cache);

            await igniteClient.destroyCache(CACHE_NAME);
        }
        catch (err) {
            console.log('ERROR: ' + err.message);
        }
        finally {
            igniteClient.disconnect();
        }
    }

    async putGetData(cache) {
        let keys = [1, 2, 3];
        let values = keys.map(key => this.generateValue(key));

        // Поместите несколько значений параллельно.
        await Promise.all([
            await cache.put(keys[0], values[0]),
            await cache.put(keys[1], values[1]),
            await cache.put(keys[2], values[2])
        ]);
        console.log('Cache values put successfully');

        // Получите значения последовательно.
        let value;
        for (let i = 0; i < keys.length; i++) {
            value = await cache.get(keys[i]);
            if (!this.compareValues(value, values[i])) {
                console.log('Unexpected cache value!');
                return;
            }
        }
        console.log('Cache values get successfully');
    }

    compareValues(array1, array2) {
        return array1.length === array2.length &&
            array1.every((value1, index) => value1 === array2[index]);
    }

    generateValue(key) {
        const length = key + 5;
        const result = new Array(length);
        for (let i = 0; i < length; i++) {
            result[i] = key * 10 + i;
        }
        return result;
    }

    onStateChanged(state, reason) {
        if (state === IgniteClient.STATE.CONNECTED) {
            console.log('Client is started');
        }
        else if (state === IgniteClient.STATE.DISCONNECTED) {
            console.log('Client is stopped');
            if (reason) {
                console.log(reason);
            }
        }
    }
}

const authTlsExample = new AuthTlsExample();
authTlsExample.start().then();
:::
::::

### Аутентификация

Настройте аутентификацию на стороне кластера и укажите имя пользователя и пароль в конфигурации клиента.

:::{code-block} js
:caption: JSON
const ENDPOINT = 'localhost:10800';
const USER_NAME = 'ignite';
const PASSWORD = 'ignite';

const igniteClientConfiguration = new IgniteClientConfiguration(
    ENDPOINT).setUserName(USER_NAME).setPassword(PASSWORD);
:::