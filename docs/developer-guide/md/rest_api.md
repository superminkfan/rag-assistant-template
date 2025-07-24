# REST API

DataGrid поставляется с клиентом HTTP REST. Он устанавливает коммуникацию с кластером через протоколы HTTP и HTTPS с помощью подхода REST. REST API можно использовать для операций чтения и записи кеша, выполнения задач, получения различных метрик и других действий.

Внутри DataGrid для функциональных возможностей HTTP-сервера используется Jetty. Подробнее об этом написано ниже в разделе [«Настройка»](#настройка).

## Первые шаги

Перед включением HTTP-соединения проверьте, что модуль `ignite-rest-http` включен. При использовании бинарного дистрибутива скопируйте модуль `ignite-rest-http` из папки `IGNITE_HOME/libs/optional/` в `IGNITE_HOME/libs`. Подробнее об этом написано в разделе [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/setup#enabling-modules).

Пример конфигурации описан ниже. Проверить, работает ли настройка, можно с помощью curl:

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=version
```
:::

:::{md-tab-item} Вывод
```bash
{
	"successStatus": 0,
	"error": null,
	"sessionToken": null,
	"response": "16.0.0",
	"securitySubjectId": null
}
```
:::
::::

Параметры запроса могут предоставляться как часть URL-адреса или в виде данных формы:

```bash
curl 'http://localhost:8080/ignite?cmd=put&cacheName=myCache' -X POST -H 'Content-Type: application/x-www-form-urlencoded' -d 'key=testKey&val=testValue'
```

### Настройка

Можно изменить параметры HTTP-сервера:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration" id="ignite.cfg">
    <property name="connectorConfiguration">
        <bean class="org.apache.ignite.configuration.ConnectorConfiguration">
            <property name="jettyPath" value="jetty.xml"/>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();
cfg.setConnectorConfiguration(new ConnectorConfiguration().setJettyPath("jetty.xml"));
```
:::
::::

В таблице ниже описаны параметры свойства `ConnectorConfiguration`, которые относятся к HTTP-серверу:

| Название параметра | Описание | Опциональность | Значение по умолчанию |
|---|---|---|---|
| `setSecretKey(String)` | Определяет секретный ключ для аутентификации клиента. Если свойство указано, в запросе клиента должен быть HTTP-заголовок `X-Signature` со строковым представлением в формате `[1]:[2]`, где [1] — временная метка (в мс), и [2] — хеш `SHA1` секретного ключа в кодировке Base64 | Да | `null` |
| `setPortRange(int)` | Диапазон портов для сервера Jetty. Если системное свойство `IGNITE_JETTY_PORT` или порт, который указан в конфигурации Jetty, уже используется, DataGrid постепенно увеличивает номер порта на `1` и пытается повторно соединиться, пока указанный диапазон не будет исчерпан | Да | `100` |
| `setJettyPath(String)` | Путь к конфигурационному файлу Jetty. Должен быть абсолютным или относительным к `IGNITE_HOME`. Если путь не указан, DataGrid запускает сервер Jetty с простым HTTP-коннектором. Он использует системные свойства `IGNITE_JETTY_HOST` и `IGNITE_JETTY_PORT` в качестве хоста и порта соответственно. Если не указан `IGNITE_JETTY_HOST`, по умолчанию используется `localhost`. Если не указан `IGNITE_JETTY_PORT`, используется порт `8080` | Да | `null` |
| `setMessageInterceptor(…)` | Перехватчик преобразует все объекты, которыми обмениваются по протоколу REST. Например, при использовании пользовательской сериализации на клиенте можно написать перехватчик и преобразовать двоичные представления от клиента в объекты Java, а затем напрямую обращаться к ним из кода Java | Да | `null` |

#### Пример XML-конфигурации Jetty

Путь к файлу конфигурации нужно указать в `ConnectorConfiguration.setJettyPath(String)`:

```bash
<!DOCTYPE Configure PUBLIC "-//Jetty//Configure//EN" "http://www.eclipse.org/jetty/configure.dtd">
<Configure id="Server" class="org.eclipse.jetty.server.Server">
    <Arg name="threadpool">
        <!-- Пул блокирующих потоков в очереди по умолчанию. -->
        <New class="org.eclipse.jetty.util.thread.QueuedThreadPool">
            <Set name="minThreads">20</Set>
            <Set name="maxThreads">200</Set>
        </New>
    </Arg>
    <New id="httpCfg" class="org.eclipse.jetty.server.HttpConfiguration">
        <Set name="secureScheme">https</Set>
        <Set name="securePort">8443</Set>
        <Set name="sendServerVersion">true</Set>
        <Set name="sendDateHeader">true</Set>
    </New>
    <Call name="addConnector">
        <Arg>
            <New class="org.eclipse.jetty.server.ServerConnector">
                <Arg name="server"><Ref refid="Server"/></Arg>
                <Arg name="factories">
                    <Array type="org.eclipse.jetty.server.ConnectionFactory">
                        <Item>
                            <New class="org.eclipse.jetty.server.HttpConnectionFactory">
                                <Ref refid="httpCfg"/>
                            </New>
                        </Item>
                    </Array>
                </Arg>
                <Set name="host">
                  <SystemProperty name="IGNITE_JETTY_HOST" default="localhost"/>
                </Set>
                <Set name="port">
                  <SystemProperty name="IGNITE_JETTY_PORT" default="8080"/>
                </Set>
                <Set name="idleTimeout">30000</Set>
                <Set name="reuseAddress">true</Set>
            </New>
        </Arg>
    </Call>
    <Set name="handler">
        <New id="Handlers" class="org.eclipse.jetty.server.handler.HandlerCollection">
            <Set name="handlers">
                <Array type="org.eclipse.jetty.server.Handler">
                    <Item>
                        <New id="Contexts" class="org.eclipse.jetty.server.handler.ContextHandlerCollection"/>
                    </Item>
                </Array>
            </Set>
        </New>
    </Set>
    <Set name="stopAtShutdown">false</Set>
</Configure>
```

### Безопасность

Если в кластере настроена проверка аутентификации, все приложения, которые используют REST API, запрашивают проверку подлинности с помощью предоставления учетных данных. Запрос аутентификации возвращает токен сессии. Его можно использовать с любой командой внутри сессии.

Есть два способа запросить авторизацию:

- Используйте команду авторизации с параметрами `ignite.login=\[user\]&ignite.password=\[password\]`:
   ```bash
   http://localhost:8080/ignite?cmd=authenticate&ignite.login=[user]&ignite.password=[password]
   ```

- Или используйте REST-команду с параметрами `ignite.login=[user]` и `ignite.password=[password]` в пути строки подключения. В примере используется команда `version`:
   ```bash
   http://localhost:8080/ignite?cmd=version&ignite.login=[user]&ignite.password=[password]
   ```

В примерах выше замените `[host]`, `[port]`, `[user]` и `[password]` на фактические значения.

Если выполнить любую из команд выше в браузере, вернется ответ с токеном сессии:

```bash
{"successStatus":0,"error":null,"sessionToken":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","response":true}
```

После получения токена сессии используйте параметр `sessionToken` в строке подключения:

```bash
http://localhost:8080/ignite?cmd=top&sessionToken=[sessionToken]
```

В строке подключения замените`[sessionToken]` на фактическое значение.

:::{admonition} Внимание
:class: danger

При включенной аутентификации на сервере потребуются учетные данные пользователя или токен сессии. Если не указать параметры `sessionToken` или `user` и `password` в строке подключения REST, появится ошибка.
:::

:::{admonition} Срок действия токена сессии
:class: hint

Токен сессии можно использовать в течение 30 секунд. Использование просроченного токена приведет к ошибке.

Для установки пользовательского срока действия токена сессии укажите системную переменную `IGNITE_REST_SESSION_TIMEOUT` (в секундах):

```bash
-DIGNITE_REST_SESSION_TIMEOUT=3600
```
:::

## Типы данных

По умолчанию REST API обменивается параметрами запроса в строковом формате (`String`). Кластер работает с параметрами так же, как со строковыми объектами.

Если тип параметра отличается от `String`, используйте `keyType` или `valueType`, чтобы указать реальный тип аргумента. REST API поддерживает [типы Java](#типы-java)  и [пользовательские типы](#пользовательские-типы).

### Типы Java

| REST KeyType/ValueType | Соответствующий тип Java |
|---|---|
| `boolean` | `java.lang.Boolean` |
| `byte` | `java.lang.Byte` |
| `short` | `java.lang.Short` |
| `integer` | `java.lang.Integer` |
| `long` | `java.lang.Long` |
| `float` | `java.lang.Float` |
| `double` | `java.lang.Double` |
| `date` | `java.sql.Date`<br><br>Значение даты должно быть в формате, который указан в методе `valueOf(String)` в [официальной документации Java](https://docs.oracle.com/javase/8/docs/api/java/sql/Date.html#valueOf-java.lang.String-).<br><br>Пример: `YYYY-MM-DD` |
| `time` | `java.sql.Time`<br><br>Значение времени должно быть в формате, который указан в методе `valueOf(String)` в [официальной документации Java](https://docs.oracle.com/javase/8/docs/api/java/sql/Date.html#valueOf-java.lang.String-).<br><br>Пример: `01:01:01` |
| `timestamp` | `java.sql.Timestamp`<br><br>Значение временной метки должно быть в формате, который указан в методе `valueOf(String)` в [официальной документации Java](https://docs.oracle.com/javase/8/docs/api/java/sql/Date.html#valueOf-java.lang.String-).<br><br>Пример: `2018-02-18%2001:01:01` |
| `uuid` | `java.util.UUID` |
| `IgniteUuid` | `org.apache.ignite.lang.IgniteUuid` |

Пример команды `put` с `keyType=int` и `valueType=date`:

```bash
http://localhost:8080/ignite?cmd=put&key=1&val=2024-03-20&cacheName=myCache&keyType=int&valueType=date
```

Пример команды `get` c `keyType=int` и `valueType=date`:

```bash
http://localhost:8080/ignite?cmd=get&key=1&cacheName=myCache&keyType=int&valueType=date
```

### Пользовательские типы

Формат JSON используется для обмена сложными пользовательскими объектами через протокол DataGrid REST.

JSON-представление экземпляра объекта класса `Person`, который нужно отправить в кластер:

```bash
 {
  "uid": "7e51118b",
  "name": "John Doe",
  "orgId": 5678901,
  "married": false,
  "salary": 156.1
 }
```

REST-запрос, который помещает объект в кластер с помощью установки параметра `valueType` в класс `Person`, а параметра `val` — в значение объекта JSON:

```bash
http://localhost:8080/ignite?cacheName=testCache&cmd=put&keyType=int&key=1&valueType=Person
&val=%7B%0A%22uid%22%3A%227e51118b%22%2C%0A%22name%22%3A%22John Doe%22%2C%0A%22orgId%22%3A5678901%2C%0A%22married%22%3Afalse%2C%0A%22salary%22%3A156.1%0A%7D&
```

Когда сервер получает запрос, он переводит объект из JSON во внутренний формат бинарного объекта с помощью процедуры преобразования:

- Если класс `Person` существует и есть в classpath сервера, объект JSON разрешается в экземпляр класса `Person`.
- Если класса `Person` недоступен в classpath сервера, но есть объект `QueryEntity`, который определяет класс `Person`, объект JSON разрешается в двоичный объект типа `Person`:

  ::::{md-tab-set}
  :::{md-tab-item} Объект запроса
  ```bash
  <bean class="org.apache.ignite.cache.QueryEntity">
  <property name="keyType" value="java.lang.Integer"/>
  <property name="valueType" value="Person"/>
  <property name="fields">
  <map>
  <entry key="uid"     value="java.util.UUID"/>
  <entry key="name"    value="java.lang.String"/>
  <entry key="orgId"   value="java.lang.Long"/>
  <entry key="married" value="java.lang.Boolean"/>
  <entry key="salary"  value="java.lang.Float"/>
  </map>
  </property>
  </bean>
  ```
  :::

  :::{md-tab-item} Бинарный объект
  ```bash
  "uid": "7e51118b",  // UUID
  "name": "John Doe", // string
  "orgId": 5678901,   // long
  "married": false,   // boolean
  "salary": 156.1     // float
  ```
  :::
  ::::

- В противном случае типы полей объекта JSON разрешаются в соответствии с обычным соглашением JSON:

  ```bash
  "uid": "7e51118b",   // string
  "name": "John Doe",  // string
  "orgId": 5678901,    // int
  "married": false,    // boolean
  "salary": 156.1      // double
  ```

Те же правила преобразования применяются, когда есть пользовательский тип ключа, который установлен с помощью параметра `keyType` протокола DataGrid REST.

## Возвращаемое значение

Запрос HTTP REST возвращает объект JSON с аналогичной структурой для каждой команды:

:::{list-table}
:header-rows: 1
 
+   *   Поле
    *   Тип
    *   Описание
    *   Пример
+   *   `affinityNodeId`
    *   `string`
    *   Идентификатор affinity-узла
    *   `2bd7b049-3fa0-4c44-9a6d-b5c7a597ce37`
+   *   `error`
    *   `string`
    *   Если сервер не сможет обработать запрос, в поле появится описание ошибки
    *   Уникальный для каждой команды
+   *   `sessionToken`
    *   `string`
    *   Если на сервере включена аутентификация, в поле появится токен сессии, который можно использовать с любой командой в этой сессии. Например, у поля будет значение `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
    
        Если аутентификация отключена, у поля будет значение `null`
    *   Иначе `null`
+   *   `response`
    *   `jsonObject`
    *   Результаты выполнения команды
    *   Уникальный для каждой команды
+   *   `successStatus`
    *   `integer`
    *   Код завершения. Может иметь следующие значения:
        - `success = 0`;
        - `failed = 1`;
        - `authorization failed = 2`;
        - `security check failed = 3`
    *   `0`
:::

Подробнее о REST API написано в документе [«Справочник по REST API»](../../rest-api/md/index.md).