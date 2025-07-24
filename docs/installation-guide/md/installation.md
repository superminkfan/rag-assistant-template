# Установка

DataGrid, в отличие от open-source-версии Apache Ignite, содержит в себе библиотеки, отвечающие за авторизацию и работу с SSL.

Установка производится с помощью находящейся в дистрибутиве ansible-роли.

Подробнее процесс установки описан в [разделе «Установка DataGrid с помощью Ansible» текущего документа](./ansible-role-datagrid.md).

Настройка подключения к сервису ZooKeeper описана в подразделе [«Рекомендации по конфигурации DataGrid и ZooKeeper»](../../developer-guide/md/zookeeper_discovery.md#рекомендации-по-конфигурации-datagrid-и-zookeeper) раздела «ZooKeeper Discovery» документа «Руководство прикладного разработчика».

Конфигурация настройки протокола LDAP описана в подразделе [«LDAP Authenticator»](../../administration-guide/md/administration-scenarios.md#ldap-authenticator) раздела «Сценарии администрирования» документа «Руководство по системному администрированию».

## Настройка интеграции со смежными сервисами

Ниже описана процедура интеграции с рекомендованными АО «СберТех» продуктами. На усмотрения пользователя может быть настроена интеграция с аналогичными по функциональности продуктом от других производителей:

- настройка интеграции с локальным syslog — подробнее о ней написано ниже в разделе [«Настройка интеграции с локальным syslog»](#настройка-интеграции-с-локальным-syslog);
- настройка интеграции с компонентом PACMAN (CFGA) продукта Platform V Backend — подробнее о ней написано ниже в разделе [«Настройка интеграции с компонентом PACMAN (CFGA)»](#настройка-интеграции-с-компонентом-pacman-cfga);
- настройка интеграции с продуктом Platform V Corax — подробнее о ней написано в подразделе «Репликация DataGrid с использованием Platform V Corax» раздела [«Сценарии администрирования»](../../administration-guide/md/administration-scenarios.md) документа «Руководство по системному администрированию».

### Настройка интеграции с локальным syslog

Чтобы настроить интеграцию:

1. Перед запуском кластера выполните действия:
   - Скопируйте библиотеку `ise-audit-syslog-integration` из каталога `./libs/optional` в каталог `./libs` дистрибутива DataGrid:

     ```bash
     cp -r ./libs/optional/ise-audit-syslog-integration/ ./libs/
     ```

   - Включите аудит — добавьте в конфигурационный файл кластера блок:
  
     ```bash
     <bean id="securityPluginConfiguration" class="com.sbt.security.ignite.core.SecurityPluginConfiguration">
         <property name="auditIntegrationConfiguration" ref="auditCfg"/>
     </bean>
 
     <bean id="auditCfg" class="com.sbt.security.ignite.integration.audit.syslog.SyslogIntegrationConfiguration">
     <property name="sourceSystemName" value="IgniteSE"/>
     <property name="moduleName" value="IgniteSE"/>
     <property name="nodeName" value="localhost"/>
     </bean>
     ```

2. Запустите и активируйте кластер DataGrid.

   :::{code-block} java
   :caption: Java
    // Запуск кластера.
    ./bin/startServer.sh
 
    // Активация кластера.
    ./bin/control.sh --set-state ACTIVE
    :::

3. Проверьте записи аудита с помощью команды:

   ```bash
   sudo less /var/log/messages
   ```
    
При корректной настройке события кластера DataGrid будут отправляться в локальный syslog.

### Настройка интеграции с компонентом PACMAN (CFGA)

Взаимодействие DataGrid с конфигуратором возможно в двух режимах: режим эмуляции и режим с обычным сервером конфигуратора. Сейчас используется только первый режим. 

Чтобы настроить интеграцию:

1. Используйте заглушки (placeholders) в конфигурации узлов DataGrid вместо логинов и паролей.
   
   ::::{admonition} Пример
   :class: hint
   :collapsible:

   :::{code-block} xml
   :caption: XML
   <?xml version="1.0" encoding="UTF-8"?>
 
   <beans xmlns="http://www.springframework.org/schema/beans"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xmlns:util="http://www.springframework.org/schema/util"
          xsi:schemaLocation="
               http://www.springframework.org/schema/beans
               http://www.springframework.org/schema/beans/spring-beans.xsd
               http://www.springframework.org/schema/util
               http://www.springframework.org/schema/util/spring-util.xsd">
 
 
       <bean abstract="false"  id="ignIgniteConfiguration" class="org.apache.ignite.configuration.IgniteConfiguration">
           <!-- ############# inc/property/ ############# -->
           <!-- Свойство `binaryConfiguration`. -->
           <property name="binaryConfiguration">
               <bean class="org.apache.ignite.configuration.BinaryConfiguration">
                   <property name="compactFooter" value="true"/>
               </bean>
           </property>
           <!-- Конец свойства `binaryConfiguration`. -->
           <property name="discoverySpi">
               <ref bean="ignTcpDiscoverySpi"/>
           </property>
           <property name="communicationSpi">
               <ref bean="ignTcpCommunicationSpi"/>
           </property>
           <!-- Свойство `gridLogger`. -->
           <property name="gridLogger">
                <bean class="org.apache.ignite.logger.log4j2.Log4J2Logger">
                   <constructor-arg type="java.lang.String" value="/opt/ignite/server/config/ignite-log4j2.xml"/>
               </bean>
           </property>
           <!-- Конец свойства `gridLogger`. -->
 
           <!-- Свойство `metricExporterSpi`. -->
           <property name="metricExporterSpi">
             <list>
               <bean class="org.apache.ignite.spi.metric.jmx.JmxMetricExporterSpi"/>
             </list>
           </property>
           <!-- Конец свойства `metricExporterSpi`. -->
 
           <!-- `property_main`. -->
           <property name="consistentId"            value="node-01"/>
           <property name="workDirectory"           value="/opt/ignite/server/work"/>
           <property name="metricsLogFrequency"     value="30000"/>
           <property name="failureDetectionTimeout" value="30000"/>
           <property name="rebalanceThreadPoolSize" value="4"/>
           <property name="peerClassLoadingEnabled" value="true"/>
           <property name="activeOnStart"           value="true"/>
           <!-- Конец `property_main`. -->
           <property name="dataStorageConfiguration">
               <ref bean="ignDataStorageConfiguration"/>
           </property>
 
           <property name="connectorConfiguration">
               <ref bean="ignConnectorConfiguration"/>
           </property>
           <property name="clientConnectorConfiguration">
               <ref bean="ignClientConnectorConfiguration"/>
           </property>
           <property name="transactionConfiguration">
               <ref bean="ignTransactionConfiguration"/>
           </property>
 
 
           <!-- `pluginProviders_with_ssl_audit`. -->
           <property name="pluginProviders">
               <list>
                   <ref bean="securityPlugin"/>
 
 
 
                   <bean class="com.sbt.ignite.CheckParametersPluginProvider">
                       <property name="stopNodeOnCheckFailure" value="false" />
                       <property name="nodeAttributesHardCheck" value="true" />
                   </bean>
                   <bean class="org.apache.ignite.cdc.conflictresolve.CacheVersionConflictResolverPluginProvider">
                       <property name="clusterId" value="2" />
                       <property name="caches">
                           <list>
                               <value>rb_app_callbacks</value>
                               <value>rb_app_message</value>
                               <value>rb_app</value>
                           </list>
                       </property>
                       <property name="conflictResolveField" value="timestamp" />
                   </bean>
               </list>
           </property>
 
           <!-- Свойство `snapshotThreadPoolSize`. -->
           <property name="snapshotThreadPoolSize"  value="4"/>
           <!-- Конец свойства `snapshotThreadPoolSize`. -->
 
 
           <!-- Запустите `CustomConfiguration`. -->
           <!-- Завершите `CustomConfiguration`. -->
       </bean>
 
       <!-- ############# inc/bean/ ############# -->
       <!-- `TcpDiscoverySpi`. -->
       <bean id="ignTcpDiscoverySpi" class="org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi">
           <property name="localPort"      value="47500"/>
           <property name="localPortRange" value="9"/>
           <property name="connectionRecoveryTimeout" value="30000"/>
           <property name="ipFinder">
               <bean class="org.apache.ignite.spi.discovery.tcp.ipfinder.vm.TcpDiscoveryVmIpFinder">
                   <property name="addresses">
                       <list>
                           ...
                           ...
                           ...
                       </list>
                   </property>
               </bean>
           </property>
       </bean>
       <!-- Конец `TcpDiscoverySpi`. -->    <!-- Bean `TcpCommunicationSpi`. -->
       <bean id="ignTcpCommunicationSpi" class="org.apache.ignite.spi.communication.tcp.TcpCommunicationSpi">
           <property name="localPort"             value="47100"/>
           <property name="localAddress"          value="#{localhostInetAddress.getHostAddress()}"/>
           <property name="sharedMemoryPort"      value="-1"/>
           <property name="idleConnectionTimeout" value="600000"/>
           <property name="socketWriteTimeout"    value="30000"/>
           <property name="selectorsCount"        value="18"/>
           <property name="connectionsPerNode"    value="1"/>
           <property name="usePairedConnections"  value="false"/>
           <property name="messageQueueLimit"     value="0"/>
       </bean>
       <!-- Конец bean `TcpCommunicationSpi`. -->
 
       <bean id="securityPlugin" class="com.sbt.security.ignite.core.SecurityPluginProvider">
           <constructor-arg ref="securityPluginConfiguration"/>
       </bean>
 
        <bean id="securityPluginConfiguration" class="com.sbt.security.ignite.core.SecurityPluginConfiguration">
        <property name="nodeLogin" value="#{igniteProperties.getProperty('SecurityPluginConfiguration.nodeLogin')}"/> 
        <property name="nodePassword" value="#{igniteProperties.getProperty('SecurityPluginConfiguration.nodePassword')}"/> 
        <property name="selfKeyStorePath" value="/opt/ignite/server/config/keystore.jks"/> 
        <property name="selfKeyStorePassword" value="#{igniteProperties.getProperty('SecurityPluginConfiguration.selfKeyStorePwd')}"/> 
        <property name="trustStorePath" value="/opt/ignite/server/config/truststore.jks"/> 
        <property name="trustStorePassword" value="#{igniteProperties.getProperty('SslContextFactory.trustStorePassword')}"/> 
        <property name="userDataStore" value="/opt/ignite/server/config/ansible-security-data.json"/>
        <property name="auditIntegrationConfiguration">
            <bean class="com.sbt.security.ignite.integration.audit3.AuditConnectionConfiguration">
                <property name="connectionProperties" value="#{auditConfigurator.getPlatformPropertyLoader().loadProperties()}"/>
            </bean>
        </property>
    </bean>
 
     <!-- `client: False.` -->
     <!-- `configurator: True`. -->
       <!-- Bean `ignConnectorConfiguration`. -->
       <bean id="ignConnectorConfiguration" class="org.apache.ignite.configuration.ConnectorConfiguration">
           <property name="host"          value="0.0.0.0"/>
           <property name="port"          value="11211"/>
           <property name="idleTimeout"   value="180000"/>
 
       </bean>
       <!-- Конец bean `ignConnectorConfiguration`. -->
       <!-- Bean `ignClientConnectorConfiguration`. -->
       <bean id="ignClientConnectorConfiguration" class="org.apache.ignite.configuration.ClientConnectorConfiguration">
           <property name="host"           value="0.0.0.0"/>
           <property name="port"           value="10800"/>
           <property name="portRange"      value="100"/>
           <property name="jdbcEnabled"    value="false"/>
           <property name="odbcEnabled"    value="false"/>
           <property name="threadPoolSize" value="16"/>
 
           <property name="thinClientEnabled" value="true"/>
           <property name="thinClientConfiguration" ref="thinClientConfiguration"/>
       
       </bean>
       <!-- Конец bean `ClientConnectorConfiguration`. -->
       <!-- Bean `thinClientConfiguration`. -->
       <bean id="thinClientConfiguration" class="org.apache.ignite.configuration.ThinClientConfiguration">
           <property name="maxActiveComputeTasksPerConnection" value="100"/>
       </bean>
       <!-- Конец bean `thinClientConfiguration`. -->
       <!-- `TransactionConfiguration`. -->
       <bean id="ignTransactionConfiguration"  class="org.apache.ignite.configuration.TransactionConfiguration">
           <property name="defaultTxIsolation"              value="READ_COMMITTED"/>
           <property name="defaultTxTimeout"                value="300000"/>
           <property name="txTimeoutOnPartitionMapExchange" value="10000"/>
       </bean>
       <!-- Конец `TransactionConfiguration`. -->
       <!-- Запустите bean `ignDefaultDataRegionConfiguration`. -->
       <bean id="ignDefaultDataRegionConfiguration" class="org.apache.ignite.configuration.DataRegionConfiguration">
           <property name="name"                       value="default"/>
           <property name="metricsRateTimeInterval"                    value="1000"/>
           <property name="persistenceEnabled"                    value="false"/>
           <property name="maxSize"                    value="#{5L * 1024 * 1024 * 1024}"/>
           <property name="metricsEnabled"                    value="true"/>
           <property name="cdcEnabled"                    value="true"/>
           <property name="initialSize"                    value="#{5L * 1024 * 1024 * 1024}"/>
           <property name="pageEvictionMode"           value="RANDOM_2_LRU"/>
       </bean>
           <!-- Завершите bean `ignDefaultDataRegionConfiguration`. -->
 
       <!-- Bean `ignDataStorageConfiguration`. -->
       <!-- Настройка durable памяти для узла DataGrid. -->
       <bean id="ignDataStorageConfiguration" class="org.apache.ignite.configuration.DataStorageConfiguration">
 
           <!-- Переопределяет конфигурацию региона данных по умолчанию, которая создается автоматически. -->
           <property name="defaultDataRegionConfiguration">
               <ref bean="ignDefaultDataRegionConfiguration"/>
           </property>
 
 
           <!-- Установите максимальный размер, который WAL-архив может занимать в файловой системе. -->
           <property name="maxWalArchiveSize" value="#{15L * 1024 * 1024 * 1024}"/>
           <!-- Добавьте любую строку в конечную конфигурацию. -->
                   <!-- Устанавливает путь к каталогу WAL-архива. -->
                   <property name="walArchivePath" value="/opt/ignite/wal_archive"/>
                   <property name="walPath" value="/opt/ignite/wal"/>
                   <!-- Устанавливает размер WAL-сегмента. -->
                   <property name="walSegmentSize" value="#{1024*1024*1024}"/>
                   <!-- Устанавливает свойство, которое определеяет поведение операции `WAL fsync`. -->
                   <property name="walMode" value="LOG_ONLY"/>
                   <property name="metricsEnabled" value="true"/>
                   <property name="metricsRateTimeInterval" value="60000"/>
                   <property name="walCompactionEnabled" value="true"/>
                   <!-- Установите максимальный размер, который WAL-архив может занимать в файловой системе. -->
                   <property name="walForceArchiveTimeout" value="10000"/>
                   <property name="cdcWalPath" value="/opt/ignite/wal_archive/cdc" />
 
       </bean>
      <!-- Конец bean `ignDataStorageConfiguration`. -->
 
       <bean id="auditConfigurator" class="com.sbt.core.commons.config_spring.PlatformPlaceholderConfigurer">
           <constructor-arg name="artifactId" value="audit-client-core2-platform" />
           <property name="ignoreUnresolvablePlaceholders" value="false" />
       </bean>

     <!-- `configurator: True`. -->
       <!-- Beans для `ignite_se_use_configurator`. -->
       <bean id="igniteConfigurator" class="com.sbt.core.commons.config_spring.PlatformPlaceholderConfigurer">
           <constructor-arg name="artifactId" value="ise" />
           <property name="ignoreUnresolvablePlaceholders" value="false" />
       </bean>
       <bean id="ignitePlatformProperties" factory-bean="igniteConfigurator" factory-method="getPlatformPropertyLoader" />
       <bean id="igniteProperties" factory-bean="ignitePlatformProperties" factory-method="loadProperties" />
       <!-- Конец beans для `ignite_se_use_configurator`. -->
 
       <!-- Запустите `CustomConfiguration`. -->
          <import resource="file:/opt/ignite/server/config/caches.xml"/>
       <!-- Завершите `CustomConfiguration`. -->
 
   </beans>
   :::
   ::::

2. Запустите узлы с помощью JVM-опций:

   - для режима эмуляции:
  
     ```bash
     -Dgroup.id=somegroupid
     -Dnode.id=somenodeid
     -Dmodule.id=somemoduleid
     -Dconfig-store.disabled=true
     -Dplatform-config=file:platform.config
     ```
   - для режима с сервером конфигуратора:

     ```bash
     -Dgroup.id=somegroupid
     -Dnode.id=somenodeid
     -Dmodule.id=somemoduleid
     -Dconfig-store.disabled=false
     -Dplatform-config=file:platform.config
     ```

3. Создайте файл `platform.config`:

   ::::{md-tab-set}
   :::{md-tab-item} Для режима эмуляции
   ```bash
   ######################
   # Managed via Ansible
   # DO NOT EDIT
   ######################
   ise@SslContextFactory.keyStorePassword=****
   ise@SslContextFactory.trustStorePassword=****
   ise@SecurityPluginConfiguration.selfKeyStorePwd=*****
   ise@SecurityPluginConfiguration.nodeLogin=****
   ise@SecurityPluginConfiguration.nodePassword=*****
   ```
   :::

   :::{md-tab-item} Для режима с сервером конфигуратора
   ```bash
   ######################
   # Managed via Ansible
   # DO NOT EDIT
   ######################
   config-store@jdbc.url=*******
   config-store@crypto.password=***
   config-store@jdbc.password=***
   config-store@jdbc.login=***
 
   platform-commons@sudirLogoutUrl=******
   platform-commons@sudir-enabled=true
   platform-commons@monitoring.enabled=false
   platform-commons@sudirLoginUrl=*******
   platform-commons@net.ssl.enabled=true
   platform-commons@net.ssl.keyStoreType=jks
   platform-commons@net.jmx.port=1115
   platform-commons@net.ssl.trustStoreType=jks
   platform-commons@access.dev-mode=false
 
   audit-client-core2-platform@mock[GROUP]/enabled.mock=true
   audit-client-core2-platform@main.server=
   audit-client-core2-platform@fallback.server=
   audit-client-core2-platform@retry.attempts=3
   audit-client-core2-platform@delivery.timeout.ms=120000
   audit-client-core2-platform@request.timeout.ms=30000
   audit-client-core2-platform@linger.ms=10
 
   audit-client-core2-platform@security.protocol=PLAINTEXT
   audit-client-core2-platform@ssl.protocol=TLSv1.2
   audit-client-core2-platform@ssl.truststore.location=
   audit-client-core2-platform@ssl.truststore.password=
   audit-client-core2-platform@ssl.keystore.location=
   audit-client-core2-platform@ssl.keystore.password=
   audit-client-core2-platform@ssl.key.password=
 
 
   ise@SslContextFactory.keyStorePassword=****
   ise@SslContextFactory.trustStorePassword=****
   ise@SecurityPluginConfiguration.selfKeyStorePwd=*****
   ise@SecurityPluginConfiguration.nodeLogin=****
   ise@SecurityPluginConfiguration.nodePassword=*****
   ```
   :::
   ::::

## Варианты работы в различном окружении

DataGrid работает только с Java 11 и новее.

### Запуск DataGrid на Java 11 и новее

Для запуска DataGrid на Java 11 и новее выполните следующие шаги:

1.  Задать переменную среды `JAVA_HOME`.
2.  DataGrid использует проприетарные SDK API, недоступные «из коробки». Для включения этих API необходимо передать JVM определенные признаки. При использовании для запуска DataGrid скрипта `ignite.sh` дополнительных действий не требуется, поскольку необходимые признаки уже есть в скрипте. Если скрипт не используется, задайте для JVM следующие параметры:

    ```bash
        --add-exports=java.base/jdk.internal.misc=ALL-UNNAMED
        --add-exports=java.base/sun.nio.ch=ALL-UNNAMED
        --add-exports=java.management/com.sun.jmx.mbeanserver=ALL-UNNAMED
        --add-exports=jdk.internal.jvmstat/sun.jvmstat.monitor=ALL-UNNAMED
        --add-exports=java.base/sun.reflect.generics.reflectiveObjects=ALL-UNNAMED
        --add-opens=jdk.management/com.sun.management.internal=ALL-UNNAMED
        --illegal-access=permit
    ```

3.  TLSv1.3, доступная в Java 11, не поддерживается DataGrid версии 2.9 и ниже. Если необходимо использовать протокол SSL для связи между узлами, к параметрам добавьте `-Djdk.tls.client.protocols=TLSv1.2`.