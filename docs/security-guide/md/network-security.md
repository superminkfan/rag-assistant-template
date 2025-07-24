# Сетевая безопасность

## Использование SSL/TLS для узлов кластера

Для включения шифрования SSL/TLS для узлов кластера необходимо настроить фабрику `SSLContext` в конфигурации узла. Возможно использование фабрики `org.apache.ignite.ssl.SslContextFactory`, использующей настраиваемое хранилище ключей для инициализации контекста SSL.

### Пример конфигурации фабрики `SSLContext` для использования с узлами

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="sslContextFactory">
        <bean class="org.apache.ignite.ssl.SslContextFactory">
            <property name="keyStoreFilePath" value="keystore/node.jks"/>
            <property name="keyStorePassword" value="password"/>
            <property name="trustStoreFilePath" value="keystore/trust.jks"/>
            <property name="trustStorePassword" value="password"/>
            <property name="protocol" value="TLSv1.3"/>
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
factory.setTrustStoreFilePath("keystore/trust.jks");
factory.setTrustStorePassword("password".toCharArray());
factory.setProtocol("TLSv1.3");

igniteCfg.setSslContextFactory(factory);
```
:::
::::

Хранилище ключей должно содержать в себе сертификат узла, в том числе и его приватный ключ, а также доверенные сертификаты для всех узлов кластера.

После запуска узла в журналах появятся следующие сообщения:

```text
Security status [authentication=off, tls/ssl=on]
```

### Использование SSL/TLS для тонких клиентов и JDBC/ODBC-подключений

DataGrid использует одни и те же настройки SSL/TLS для всех клиентов, включая тонкие клиенты и JDBC/ODBC-подключения. Свойства настраиваются внутри конфигурации клиентского коннектора. Данная конфигурация определяется свойством `IgniteConfiguration.clientConnectorConfiguration`.

Для включения SSL/TLS для клиентских соединений установите для свойства `sslEnabled` значение `true` и определите в конфигурации клиентского коннектора фабрику `SslContextFactory`. При этом вы можете либо повторно использовать фабрику `SSLContextFactory`, настроенную для использования с узлами, либо настроить отдельную фабрику `SSLContext`, которая затем будет использоваться только для клиентских подключений.

Затем таким же образом настройте SSL на стороне клиента.

#### Пример конфигурации фабрики `SslContextFactory` для клиентских подключений

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<property name="clientConnectorConfiguration">
    <bean class="org.apache.ignite.configuration.ClientConnectorConfiguration">
        <property name="sslEnabled" value="true"/>
        <property name="useIgniteSslContextFactory" value="false"/>
        <property name="sslContextFactory">
            <bean class="org.apache.ignite.ssl.SslContextFactory">
                <property name="keyStoreFilePath" value="/path/to/server.jks"/>
                <property name="keyStorePassword" value="password"/>
                <property name="trustStoreFilePath" value="/path/to/trust.jks"/>
                <property name="trustStorePassword" value="password"/>
            </bean>
        </property>
    </bean>
</property>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration igniteCfg = new IgniteConfiguration();

ClientConnectorConfiguration clientCfg = new ClientConnectorConfiguration();
clientCfg.setSslEnabled(true);
clientCfg.setUseIgniteSslContextFactory(false);
SslContextFactory sslContextFactory = new SslContextFactory();
sslContextFactory.setKeyStoreFilePath("/path/to/server.jks");
sslContextFactory.setKeyStorePassword("password".toCharArray());

sslContextFactory.setTrustStoreFilePath("/path/to/trust.jks");
sslContextFactory.setTrustStorePassword("password".toCharArray());

clientCfg.setSslContextFactory(sslContextFactory);

igniteCfg.setClientConnectorConfiguration(clientCfg);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteClientConfiguration
{
    Endpoints = new[] {"xxx.x.x.x:10800"},
    SslStreamFactory = new SslStreamFactory
    {
        CertificatePath = ".../certs/client.pfx",
        CertificatePassword = "password",
    }
};
using (var client = Ignition.StartClient(cfg))
{
    //...
}
```
:::
::::

Если вы планируете повторно использовать фабрику `SSLContext`, настроенную для узлов, то вам нужно лишь изменить значение свойства `sslEnabled` на `true`, и свойство `ClientConnectorConfiguration` будет искать фабрику `SSLContext`, настроенную в `IgniteConfiguration`:

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<property name="clientConnectorConfiguration">
    <bean class="org.apache.ignite.configuration.ClientConnectorConfiguration">
        <property name="sslEnabled" value="true"/>
    </bean>
</property>
```
:::

:::{md-tab-item} Java
```java
ClientConnectorConfiguration clientConnectionCfg = new ClientConnectorConfiguration();
clientConnectionCfg.setSslEnabled(true);
```
:::
::::