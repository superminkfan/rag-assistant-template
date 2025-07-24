# Управление ключами и сертификатами

Помимо обычной проверки логина и пароля пользователя, аутентификатор выполняет проверку TLS-сертификата, предоставленного пользователем при соединении с кластером. Для успешной аутентификации поле `Common Name (CN)` в составе `Distinguished Name` сертификата должно иметь жесткую структуру, указанную в документе «Дополнительные инструкции для пользователей ПАО «Сбербанк».

В DataGrid существует два типа сертификатов: серверные (для связи одного сервера с другим) и клиентские (для связи клиента с сервером). Для обоих типов администратор DataGrid может самостоятельно настроить название и путь к сертификату вручную или с помощью SecMan.
 
**Рекомендации по работе с сертификатами:**

1. Сертификат должен быть подписан только удостоверяющим центром (CA). Необходимо удостовериться в отсутствии самоподписных сертификатов.
2. Сертификат должен «принадлежать» конкретному программному Компоненту (нельзя использовать один и тот же сертификат для функционирования разных Компонентов в рамках одной инсталляции Platform V).
3. Сертификат должен быть действительным на текущую дату. Необходима проверка срока действия сертификата.
4. Сертификат не должен быть отозван соответствующим удостоверяющим центром (CA). Необходима проверка списков исключения сертификатов.
5. Должны быть подключены механизмы аутентификации, авторизации и валидации по сертификатам (если у Компонента есть интеграция с компонентами Platform V, которые реализуют данный функционал).
6. Приватный/доверенный ключ не должен распространяться по каналам связи и должен иметь стойкий пароль.
7. Криптоключи, в отношении которых возникло подозрение в компрометации, а также действующие совместно с ними другие криптоключи рекомендуется немедленно вывести из действия и перевыпустить, если иной порядок не оговорен в эксплуатационной и технической документации владельца инфраструктуры.

## Считывание секретов из Secret Management System (SecMan)

Для загрузки секретов из Secret Management System добавьте настройки:

:::{code-block} xml
:caption: XML
    <bean id="secmanProperties" class="com.sbt.security.ignite.core.secman.SecmanPropertyProvider">
        <property name="secmanConfig">
            <bean class="ru.sbrf.kafka.secman.SecmanConfig">
                <property name="tokenPath" value="/path/to/secman.token"/>
                <property name="endpoint" value="https://secman.url"/>
                <property name="namespace" value="secman_namespace"/>
                <property name="path" value="PATH/TO/SECMAN/SECRETS"/>
            </bean>
        </property>
        <property name="auditListener" ref="auditListener"/>
    </bean>

    <bean id="ignSslContextFactoryNoEnc" class="com.sbt.security.ignite.core.ssl.SecmanSslContextFactory">
        <property name="trustStoreFilePath" value="${TEST_TRUSTORE_PATH}"/>
        <!-- Значение `trustore.password` будет взято из SecMan. -->
        <property name="trustStorePassword" value="#{secmanProperties.getProperty('trustore.password')}"/>
        ...
    </property>
</bean>
:::

## Считывание сертификатов из Secret Management System (SecMan)

Для загрузки сертификатов из Secret Management System добавьте настройки:

:::{code-block} xml
:caption: XML
    <bean id="ignSslContextFactoryNoEnc" class="com.sbt.security.ignite.core.ssl.SecmanSslContextFactory">
        <property name="trustStoreFilePath" value="/path/to/truststore.jks"/>
        <property name="trustStorePassword" value="truststore_password"/>
        <property name="cipherSuites" value="TLS_RSA_WITH_NULL_SHA256"/>
        <property name="secmanConfig">
            <bean class="ru.sbrf.kafka.secman.SecmanConfig">
                <property name="tokenPath" value="/path/to/secman.token"/>
                <property name="endpoint" value="https://secman.url"/>
                <property name="namespace" value="secman_namespace"/>
                <property name="fetchConfig">
                    <bean class="ru.sbrf.kafka.secman.SecmanFetchCertificateConfig">
                        <property name="role" value="secman_PKI_role"/>
                        <property name="mountPath" value="PKI_mount_path"/>
                        <property name="cn" value="CN_for_generated_certificate"/>
                        <property name="altNames"  value="testAltName"/>
                    </bean>
                </property>
            </bean>
        </property>
        <property name="auditListener" ref="auditListener" />
        <property name="cipherSuites">
            <list>
                <value>TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256</value>
                <value>TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384</value>
                <value>TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256</value>
                <value>TLS_DHE_RSA_WITH_AES_128_GCM_SHA256</value>
                <value>TLS_DHE_RSA_WITH_AES_256_GCM_SHA384</value>
                <value>TLS_RSA_WITH_AES_256_GCM_SHA384</value>
                <value>TLS_RSA_WITH_AES_128_GCM_SHA256</value>
            </list>
        </property>
    </bean>
:::

Данные, получаемые с помощью wrapped токена, должны содержать авторизационные параметры для SecMan.

Формат json:

:::{code-block} json
:caption: JSON
{
    "roleId" : "<roleId_credential>",
    "secretId": "<secretId_credential>"
}
:::

Сертификат с заданным CN извлекается из SecMan. Если сертификата с указанным CN не существует или истек срок его действия, то SecMan создает сертификат с указанным CN и сохраняет его в своем внутреннем хранилище.

`SecmanFetchCertificateConfig` описывает настройку fetch-функции SecMan:

- `cn` — CN получаемого или генерируемого сертификата. Обратите внимание, что настройка роли SecMan может ограничивать произвольный CN (подробнее в документации SecMan).
- `role` — роль SecMan для PKI.
- `mountPath` — путь для SecMan PKI `endpoint` (обычно имеет значение `PKI`).
- `altNames` (string) — параметр для указания `hostname` в сертификате в конфигурации `SecmanFetchCertificateConfig`. Если не указать значение `altNames`, в сертификате поле `hostname` будет пустым.

## Отключение проверки сертификатов

В некоторых случаях, например, при подключении к серверу с самоподписаным сертификатом, рекомендуется отключать проверку сертификатов. Для этого можно использовать отключенный trust manager, который можно получить вызовом метода `SslContextFactory.getDisabledTrustManager()`.

### Пример конфигурации для отключения проверки сертификатов

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="sslContextFactory">
        <bean class="org.apache.ignite.ssl.SslContextFactory">
            <property name="keyStoreFilePath" value="keystore/node.jks"/>
            <property name="keyStorePassword" value="password"/>
            <property name="trustManagers">
                <bean class="org.apache.ignite.ssl.SslContextFactory" factory-method="getDisabledTrustManager"/>
            </property>
        </bean>
    </property>
</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration igniteCfg = new IgniteConfiguration();

SslContextFactory factory = new SslContextFactory();

factory.setKeyStoreFilePath("keystore/node.jks");
factory.setKeyStorePassword("password".toCharArray());
factory.setTrustManagers(SslContextFactory.getDisabledTrustManager());

igniteCfg.setSslContextFactory(factory);
```
:::
::::

### Обновление сертификатов

Если срок действия используемых SSL-сертификатов заканчивается или они скомпрометированы, вы можете установить новые сертификаты без необходимости полного отключения кластера.

Процедура обновления сертификатов проходит по следующему алгоритму:

1.  Убедитесь в том, что новые сертификаты являются доверенными для всех узлов.

    :::{admonition} Примечание
    :class: note

    Данный шаг можно пропустить, если в хранилище доверенных сертификатов содержится корневой сертификат и новые сертификаты подписаны тем же СА.
    :::

    Если сертификаты не являются доверенными, то процедура обновления проходит по следующему алгоритму:

    1.  Импортируйте новый сертификат в хранилище доверенных сертификатов узла.
    2.  Перезапустите узел.
    3.  Повторите эти шаги для всех серверных узлов.
    4.  Теперь все узлы доверяют новым сертификатам.

2.  Импортируйте новые сертификаты (в том числе и приватный ключ) в хранилище ключей соответствущего узла и удалите старый сертификат. После этого перезапустите узел и повторите эту процедуру для всех сертификатов, которые необходимо обновить.

### Свойства фабрики `SslContextFactory`

С подробным описанием фабрики `SslContextFactory` вы можете ознакомиться в [официальной документации](https://ignite.apache.org/releases/latest/javadoc/org/apache/ignite/ssl/SslContextFactory.html).

| Свойство | Описание | Значение по умолчанию |
|---|---|---|
| `keyAlgorithm` | Алгоритм менеджера управления ключами, который будет использоваться для создания менеджера управления ключами | SunX509 |
| `keyStoreFilePath` | Путь к файлу хранилища ключей. Это обязательный параметр, так как контекст SSL не может быть инициализирован без менеджера управления ключами | Неприменимо |
| `keyStorePassword` | Пароль хранилища ключей | Неприменимо |
| `keyStoreType` | Тип хранилища ключей | `JKS` |
| `protocol` | Протокол безопасной передачи. Поддерживаются алгоритмы | `TLS` |
| `trustStoreFilePath` | Путь к файлу доверенного хранилища | Неприменимо |
| `trustStorePassword` | Пароль доверенного хранилища | Неприменимо |
| `trustStoreType` | Тип доверенного хранилища | `JKS` |
| `trustManagers` | Список предварительно настроенных доверенных менеджеров | Неприменимо |