# Миграция на текущую версию

DataGrid поддерживает обратную совместимость. Переход с предыдущей мажорной версии продукта на текущую мажорную не требует дополнительных действий от пользователя. Переход с текущей версии на предыдущую не поддерживается.

Начиная с версии 4.2130 DataGrid поставляется с SQL-движком, который основан на фреймворке Apache Calcite (подробнее о нем написано в разделе [«Работа с SQL и Apache Calcite»](working_with_sql_and_apache_calcite.md)). В будущих версиях он будет целевым движком по умолчанию.

SQL-движок, который основан на H2, запланирован к удалению.

## Переход на версию DataGrid 17.5.0

**Особенности перехода на версию DataGrid 17.5.0:**

- Ручная настройка следующих параметров конфигурации и связанных с ними beans больше не требуется, так как они автоматически конфигурируются плагином безопасности:

   :::{code-block} java
   :caption: Java
   IgniteConfiguration#localEventListeners
   IgniteConfiguration#includeEventTypes
   IgniteConfiguration#eventStorageSpi
   IgniteConfiguration#sslContextFactory

   ConnectorConfiguration#sslEnabled
   ConnectorConfiguration#sslClientAuth
   ConnectorConfiguration#sslFactory

   ClientConnectorConfiguration#sslClientAuth
   ClientConnectorConfiguration#sslContextFactory
   ClientConnectorConfiguration#useIgniteSslContextFactory
   ClientConnectorConfiguration#sslEnabled
   :::

- Из конфигурации плагина безопасности удалена поддержка следующих параметров:

   :::{code-block} java
   :caption: Java
   SecurityPluginConfiguration#securityDataProvider
   SecurityPluginConfiguration#authenticator
   SecurityPluginConfiguration#authorizer
   SecurityPluginConfiguration#securityCredentialsProvider
   SecurityPluginConfiguration#components
   SecurityPluginConfiguration#globalAuthenticationEnabled
   :::

   Актуальный подход к конфигурации плагина безопасности описан в подразделе [«Конфигурация плагина безопасности»](../../administration-guide/md/administration-scenarios.md#конфигурация-плагина-безопасности) раздела «Сценарии администрирования» документа «Руководство по системному администрированию».

- В версии DataGrid 17.5.0 прекращена поддержка неявной проверки DN пользовательского сертификата.

     Перед обновлением на версию 17.5.0 с версий 16.1.0 и выше убедитесь, что для каждого пользователя настроен параметр `distinguishedName`, который совпадает с DN из сертификата пользователя.
     
     При обновлении на версию 17.5.0 с более ранних версий (до DataGrid 16.1.0) данные безопасности будут реинициализированы на основе файла с начальными данными безопасности, путь к которому указан в конфигурации плагина безопасности. Убедитесь, что для каждого пользователя настроен параметр `distinguishedName`, который совпадает с DN из сертификата пользователя.

- Использование роли `SHOULD_CHANGE_PASSWORD` для указания временного пароля пользователя будет прекращено в следующих версиях. Актуальным подходом является указание параметра `isTemporary` при настройке секрета пользователя.
- Начиная с версии DataGrid 17.5.0 при настроенном плагине безопасности подключения к Ignite HTTP Metric Exporter аутентифицируются плагином безопасности, а соединение должно быть установлено с использованием TLS.