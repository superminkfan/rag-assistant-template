# Изменение функциональности

## Соответствие изменений и тестов для их проверки

Испытания работоспособности изменений в версии Platform V DataGrid 17.5.0 проводятся в порядке и объеме, указанном в таблице.

| Учетный код | Описание функций | Названия тестов |
| --- | --- | --- |
| CRPV-48446, CRPLTFRM-27742 | В Аудит добавлены wrapped- и unwrapped-токены (`.SecmanPropertyProvider`) | [17.5.0 CRPV-48446 — Проверка добавления в Аудит wrapped- и unwrapped-токенов](#1) |
| CRPV-45454, CRPLTFRM-27110 | Добавлена возможность задать путь к собственному отдельному персистентному хранилищу для каждого региона данных через конфигурацию | [17.5.0 CRPV-45454 — Проверка добавления возможности задать путь к собственному отдельному персистентному хранилищу для каждого региона данных через конфигурацию](#2) |
| CRPV-45267, CRPLTFRM-27076 | Добавлена проверка минимальной длины пароля от учетной записи | [17.5.0 CRPV-45267 — Проверка минимальной длины пароля от учетной записи](#3) |
| CRPV-48317, CRPLTFRM-27679 | Выделен `systemPermission` для доступа к JMX | [17.5.0 CRPV-48317 — Проверка выделения systemPermission для доступа к JMX](#4) |
| CRPV-35368, CRPLTFRM-25519 | Добавлена аутентификация в `IgniteSE` с использованием первого фактора доменной учетной записи | [17.5.0 CRPV-35368 — Проверка добавления аутентификации в IgniteSE с использованием первого фактора доменной учетной записи](#5) |
| CRPV-48884, CRPLTFRM-27900 | Добавлена двухфакторная аутентификация/авторизация для `httpMetricExporter` | [17.5.0 CRPV-48884 — Проверка добавления двухфакторной аутентификации/авторизации для httpMetricExporter](#6) |
| CRPV-37178, CRPLTFRM-25756 | Добавлен механизм прерывания процесса `idle-verify` | [17.5.0 CRPV-37178 — Проверка добавления механизма прерывания процесса idle-verify](#7) |
| CRPV-46075, CRPLTFRM-27238 | Добавлена возможность задавать `altNames` в конфигурации Fetch SecMan | [17.5.0 CRPV-46075 — Проверка добавления возможности задавать altNames в конфигурации Fetch SecMan](#8) |
| CRPV-11683, CRPLTFRM-18388 | Добавлено разделение логических и физических записей в WAL | [17.5.0 CRPV-11683 — Проверка добавления разделения логических и физических записей в WAL](#9) |
| CRPV-26290, CRPLTFRM-23393 | Реализована история планов SQL-запросов | [17.5.0 CRPV-26290 — Проверка реализации истории планов SQL-запросов](#10) |
| CRPV-35463, CRPLTFRM-25527 | Доработан ввод пароля пользователя при подключении `control.sh` к кластеру | [17.5.0 CRPV-35463 — Проверка доработки ввода пароля пользователя при подключении control.sh к кластеру](#11) |
| CRPV-48477 | Добавлен плагин `calcite-oracle-dialect-plugin` | [17.5.0 CRPV-48477 — Проверка добавления плагина calcite-oracle-dialect-plugin](#12) |
| CRPV-21107 | Добавлена интеграция с LDAP | Сценарии проверки данного изменения не предусмотрены |
| CRPV-30368, CRPLTFRM-24333 | Добавлен механизм защиты консистентности данных плагина безопасности для in-memory-кластеров | Сценарии проверки данного изменения не предусмотрены |
| CRPV-32124, CRPLTFRM-24967 | Реализован сбор метрик-гистограмм для операций, которые используются CDC для обновления данных в кластере (`putConflict`, `putAllConflict`, `removeAllConflict` и так далее) | Сценарии проверки данного изменения не предусмотрены |
| CRPV-35462, CRPLTFRM-25526 | Запрещен вызов метода `IgniteCache#clear` внутри транзакций | Сценарии проверки данного изменения не предусмотрены |
| CRPV-36515, CRPLTFRM-25678 | Добавлена поддержка типов BLOB и CLOB для тонкого клиента JDBC | Сценарии проверки данного изменения не предусмотрены |
| CRPV-44101, CRPLTFRM-26847 | Выполнена доработка метрик отслеживания скорости репликации I2I | Сценарии проверки данного изменения не предусмотрены | 
| CRPV-45125, CRPLTFRM-27058 | Снижена нагрузка на сборщик мусора Java для случая итерации по всем элементам кеша | Сценарии проверки данного изменения не предусмотрены |
| CRPV-45376 | Добавлен планировщик задач `QueryBlockingTaskExecutor` для блокировки запросов в Apache Calcite | Сценарии проверки данного изменения не предусмотрены |
| CRPV-4570, CRPLTFRM-14720 | Выполнена доработка утилиты выравнивания согласованности партиций | Сценарии проверки данного изменения не предусмотрены |
| CRPV-46122 | Реализовано требование стандарта | Сценарии проверки данного изменения не предусмотрены |
| CRPV-47716 | Выполнена оптимизация сериализации UUID в коммуникационных сообщениях | Сценарии проверки данного изменения не предусмотрены |
| CRPV-47717, CRPLTFRM-27422 | Выполнена переработка плагина безопасности | Сценарии проверки данного изменения не предусмотрены |
| CRPV-47720 | Выполнены оптимизация производительности и снижение накладных расходов на использование ресурсов в SQL-запросах | Сценарии проверки данного изменения не предусмотрены |
| CRPV-47722 | Добавлен механизм управления атрибутами приложения на уровне API | Сценарии проверки данного изменения не предусмотрены |
| CRPV-47873 | Добавлена поддержка пользовательских табличных функций в SQL-движок, который основан на Apache Calcite | Сценарии проверки данного изменения не предусмотрены |
| CRPV-48020 | Добавлена поддержка расширенной конфигурации в SQL-представлениях (учет пользовательских таблиц и операторов) | Сценарии проверки данного изменения не предусмотрены |
| CRPV-48334, CRPLTFRM-27685 | Добавлена интеграция SberCA с `jmxLoginModuleName` | Сценарии проверки данного изменения не предусмотрены |
| CRPV-48605 | Добавлена унификация управления командами в DataGrid | Сценарии проверки данного изменения не предусмотрены |
| CRPV-48910, CRPLTFRM-27905 | Выполнена публикация API плагина безопасности | Сценарии проверки данного изменения не предусмотрены |
| CRPV-48911, CRPLTFRM-27906 | Добавлен инструмент для чтения бинарных данных плагина безопасности | Сценарии проверки данного изменения не предусмотрены |
| CRPV-53504 | Добавлена поддержка транзакций `READ_COMMITTED` для SQL в Apache Calcite | Сценарии проверки данного изменения не предусмотрены |
| CRPV-53507 | Добавлена поддержка типов BLOB и CLOB для тонкого клиента JDBC | Сценарии проверки данного изменения не предусмотрены |

(1)=
## 17.5.0 CRPV-48446 — Проверка добавления в Аудит wrapped- и unwrapped-токенов

### Шаги проверки

**Действие**: Отдельной конфигурации SecMan не требуется. Для проверки запустите серверный узел.

**Успешный результат**: События аудита (`SECMAN_UNWRAP_TOKEN` и `SECMAN_WRAP_TOKEN`) есть на обоих токенах из beans: `com.sbt.security.ignite.core.secman.SecmanPropertyProvider` и `ru.sbrf.kafka.secman.SecmanConfig`.

(2)=
## 17.5.0 CRPV-45454 — Проверка добавления возможности задать путь к собственному отдельному персистентному хранилищу для каждого региона данных через конфигурацию

### Предусловия

Конфигурация с указанием дисков, на которых будут храниться выбранные регионы данных:

:::{code-block} xml
:caption: XML
<property name="defaultDataRegionConfiguration" ref="ignDefaultDataRegionConfiguration"/>
                <property name="dataRegionConfigurations">
            <list>
                <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                    <property name="name" value="dataReg1"/>
                    <property name="maxSize" value="#{40 * 1024 * 1024}"/> <!-- 40 Мб. -->
                    <property name="pageEvictionMode" value="RANDOM_2_LRU"/>
                    <property name="persistenceEnabled"  value="true"/>
                </bean>
                <bean class="org.apache.ignite.configuration.DataRegionConfiguration">
                    <property name="name" value="dataReg2"/>
                    <property name="persistenceEnabled"  value="true"/>
                    <property name="maxSize" value="#{30 * 1024 * 1024}"/> <!-- 30 Мб. -->
                    <property name="storagePath" value="/opt/ignite/disk2/"/>
                </bean>
            </list>
</property>
:::

### Шаги проверки

**Действие**: Запустите серверный узел.

**Успешный результат**: Кластер запущен, по указанным путям создались каталоги с `consistId`, в логе серверного узла появились события региона данных, например:

```bash
YYYY-MM-DD 14:51:15.927 [INFO ][main][org.apache.ignite.internal.processors.cache.persistence.file.FilePageStoreManager] Resolved page store work directory: /opt/ignite/server/work/db/ise_l3_01
YYYY-MM-DD 14:51:15.927 [INFO ][main][org.apache.ignite.internal.processors.cache.persistence.file.FilePageStoreManager] Resolved page store work directory [dataRegion=dataReg2]: /opt/ignite/disk2/db/ise_l3_01
```

Путь к региону данных, у которого не переопределяли `storagePath`: `/opt/ignite/server/work/db/ise_l3_01`. Для `dataReg2`, у которого переопределена данная переменная, путь заменен на ее новое значение: `[dataRegion=dataReg2]: /opt/ignite/disk2/db/ise_l3_01`.

(3)=
## 17.5.0 CRPV-45267 — Проверка минимальной длины пароля от учетной записи

### Шаги проверки

**Действие**: В конфигурацию плагина на серверном узле добавьте свойство `realmConfigurations` и настройте в нем политику минимальных паролей. Вариант для минимального пароля в 12 символов:

:::{code-block} xml
:caption: XML
<bean id="server_securityPluginConfiguration" class="com.sbt.security.ignite.core.SecurityPluginConfiguration">
        <property name="realmConfigurations">
                <list>
                        <ref bean="realmConfiguration"/>
                </list>
</bean>
 
    <bean id="realmConfiguration" class="com.sbt.security.ignite.core.realm.RealmConfiguration">
            <property name="name" value="default"/>
            <property name="passwordPolicy">
                    <bean class="com.sbt.security.ignite.core.PasswordPolicy">
                            <property name="minimumPasswordLength" value="12"/>
                    </bean>
            </property>
    </bean>
:::

**Тестовые данные**:

```bash
./bin/ise-user-control.sh  -l ise_admgrant -p ******  --keystore config/ise_dev_g_ise_admgrant.jks --keystore-password ******
 --truststore config/ise_dev_truststore.jks
 --truststore-password ****** add-user --user-name newUser --distinguished-name newUser --roles CLIENT
```

**Успешный результат**: При создании пользователя с паролем, который не соответствует настроенным ранее требованиям, он не будет создан и в терминале выведется ошибка:

```bash
Password must contain at least 12 symbols [login=newUser]
Command [add-user] finished with exception.
class org.apache.ignite.IgniteException: Password must contain at least 12 symbols [login=newUser]
```

(4)=
## 17.5.0 CRPV-48317 — Проверка выделения systemPermission для доступа к JMX

### Шаги проверки

**Действие**: Для использования встроенной двухфакторной авторизации DataGrid для JMX укажите в конфигурации класса `com.sbt.security.ignite.core.SecurityPluginConfiguration` свойство (оно запустит JMX на порту `1098`):

:::{code-block} xml
:caption: XML
<property name="securedJmxServerConfiguration">
    <bean class="com.sbt.security.ignite.core.jmx.SecuredJmxServerConfiguration">            
        <property name="port" value="1098"/>
    </bean>
</property>
:::

**Успешный результат**: Серверный узел работает, на порту `1098` поднят защищенный JMX.

(5)=
## 17.5.0 CRPV-35368 — Проверка добавления аутентификации в IgniteSE с использованием первого фактора доменной учетной записи

### Шаги проверки

1. **Действие**: В bean `com.sbt.security.ignite.core.SecurityPluginProvider` добавьте свойство:

   :::{code-block} xml
   :caption: XML
   <property name="realmConfigurations">
      <list>
         <ref bean="realm-configuration"/>
         <ref bean="realm-configuration2"/>
      </list>
   </property>
   :::
    
   Затем распишите необходимую конфигурацию Realms:

   :::{code-block} xml
   :caption: XML

   <bean id="realm-configuration" class="com.sbt.security.ignite.core.realm.RealmConfiguration">
       <property name="name" value="default"/>
           <property name="passwordPolicy">
               <bean class="com.sbt.security.ignite.core.PasswordPolicy">
                   <property name="minimumPasswordLength" value="8"/>
               </bean>
               </property>
           <property name="authenticatorConfigurations">
               <list>
                   <bean class="com.sbt.security.ignite.core.authenticator.simple.SimpleAuthenticatorConfiguration"/>
                   <bean class="com.sbt.security.ignite.core.authenticator.certificate.CertificateAuthenticatorConfiguration"/>
               </list>
           </property>
   </bean>
   :::
    
   Для пользователя можно задать необходимые Realms в файле `security-data.json`:

   :::{code-block} json
   :caption: JSON
   "login": "ise_admin",
   "secret": {
   "salt": "*****",
   "key": "******"
    },
   "roles": [
   "ADMIN_SNAPSHOT",
   "MAINTENANCE_ADMIN"
    ],
    "realm":"default2"
    },
    :::

   **Успешный результат**: В bean `com.sbt.security.ignite.core.SecurityPluginProvider` добавлено свойство, конфигурация Realms задана.

2. **Действие**: Запустите серверный узел и выполните проверку состояния кластера:

   ```bash
   ./bin/control.sh --user ise_admin --keystore ./config/ise_dev_a_ise_admin.jks --truststore ./config/ise_dev_truststore.jks --password *****   --keystore-password ***** --truststore-password ***** --state
   ```

   **Успешный результат**: При аутентификации пользователя проверяется только связка «имя пользователя + пароль», у пользователя не задан DN (distinguished name).

(6)=
## 17.5.0 CRPV-48884 — Проверка добавления двухфакторной аутентификации/авторизации для httpMetricExporter

### Шаги проверки

**Действие**: Отдельных настроек не требуется, так как авторизация и аутентификация включаются с плагином по умолчанию. Для проверки выполните curl-запрос:

```bash
curl -k -u ise_admin:**** --cert config/ise_dev_a_ise_admin.cert.pem:**** --key config/ise_dev_a_ise_admin.key.pem --cacert config/ise_dev_truststore_ca.pem https://xx.xx.x.x:xxxx/ignite/
```

**Успешный результат**: Запрос выполнился и вернул запрошенные метрики:

```bash
ignite_longJVMPausesTotalDuration 0
ignite_longJVMPausesCount 0
ignite_lastClusterStateChangeTime 1747204515694
ignite_uptime 10415225
ignite_isRebalanceEnabled 1
ignite_startTimestamp 1747204516248
ignite_isNodeInBaseline 1
```

(7)=
## 17.5.0 CRPV-37178 — Проверка добавления механизма прерывания процесса idle-verify

### Предусловия

Запущенный кластер с любым кешем.

### Шаги проверки

1. **Действие**: Запустите `idle_verify`: `./control.sh --cache idle_verify`.

   **Успешный результат**: Проверка выполняется.

2. **Действие**: Отмените выполнение `idle_verify` до его завершения: `./control.sh --cache idle_verify --cancel`.

   **Успешный результат**: Проверка отменена.

(8)=
## 17.5.0 CRPV-46075 — Проверка добавления возможности задавать altNames в конфигурации Fetch SecMan

### Шаги проверки

**Действие**: В конфигурации `SecmanFetchCertificateConfig` настройте опциональное свойство `<property name="altNames"  value="testAltName"/>`.

**Успешный результат**: При запуске серверного узла сгенерирован сертификат, в котором заполнено поле `altNames`.

(9)=
## 17.5.0 CRPV-11683 — Проверка добавления разделения логических и физических записей в WAL

### Шаги проверки

**Действие**: В bean `org.apache.ignite.configuration.DataStorageConfiguration` добавьте новое свойство `<property name="writeRecoveryDataOnCheckpoint" value="true"/>`.

Опционально можно включить сжатие, для этого добавьте свойство `<property name="checkpointRecoveryDataCompression" value="SNAPPY"/>`. При использовании данного свойства добавьте в `classpath` директорию с библиотеками `ignite-compress` из `libs/optional/`.

**Успешный результат**: Узел запущен и работает без ошибок.

(10)=
## 17.5.0 CRPV-26290 — Проверка реализации истории планов SQL-запросов

### Шаги проверки

1. **Действие**: Для SQL-движка, который основан на Apache Calcite, история планов SQL-запросов работает по умолчанию. Чтобы включить историю планов SQL-запросов для SQL-движка, который основан на H2, добавьте свойство:

   :::{code-block} xml
   :caption: XML
   <property name="sqlConfiguration">
   <bean class="org.apache.ignite.configuration.SqlConfiguration">
            <property name="longQueryWarningTimeout" value="1"/>
            <property name="sqlPlanHistorySize" value="1000"/>
   </bean>
   </property>
   :::

   **Успешный результат**: Узел работает без ошибок.

2. **Действие**: Выполните произвольные SQL-запросы:

   :::{code-block} sql
   :caption: SQL
   CREATE TABLE City (
       id LONG PRIMARY KEY,
       name VARCHAR
   ) WITH "template=replicated";

   INSERT INTO City (id, name) VALUES (1, 'Forest Hill');
   INSERT INTO City (id, name) VALUES (2, 'Denver');
   INSERT INTO City (id, name) VALUES (3, 'St. Petersburg');
   :::

   **Успешный результат**: Данные добавлены.

3. **Действие**: Выполните запрос на просмотр истории планов SQL-запросов: `./bin/control.sh --system-view SQL_PLANS_HISTORY`.

   **Успешный результат**: В выводе запроса присутствует история по выполненным ранее операциям:

   ```bash
   Command [SYSTEM-VIEW] started
   Arguments: --system-view SQL_PLANS_HISTORY
   --------------------------------------------------------------------------------
   Results from node with ID: xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxx
   ---
   schemaName    sql                                                                            plan                                                                 local    engine    lastStartTime              
   PUBLIC        INSERT INTO City (id, name) VALUES (1, 'Forest Hill')                          As part of this DML command no SELECT queries have been executed.    false    h2        Tue May 20 13:51:06 MSK YYYY
   PUBLIC        INSERT INTO City (id, name) VALUES (2, 'Denver')                               As part of this DML command no SELECT queries have been executed.    false    h2        Tue May 20 13:51:06 MSK YYYY
   PUBLIC        INSERT INTO City (id, name) VALUES (3, 'St. Petersburg')                       As part of this DML command no SELECT queries have been executed.    false    h2        Tue May 20 13:51:06 MSK YYYY
   ```   

(11)=
## 17.5.0 CRPV-35463 — Проверка доработки ввода пароля пользователя при подключении control.sh к кластеру

### Шаги проверки

1. **Действие**: Запустите кластер с настроенным плагином безопасности.

   **Успешный результат**: Кластер запущен.

2. **Действие**: Выполните `state`-запрос:

   ```bash
   /bin/control.sh --user ise_admin --keystore ./config/ise_dev_a_ise_admin.jks --truststore ./config/ise_dev_truststore.jks --password *****--keystore-password ***** --truststore-password ******--state
   ```

   **Успешный результат**: В логе нет ошибок подключения пользователя с пустым паролем.

(12)=
## 17.5.0 CRPV-48477 — Проверка добавления плагина calcite-oracle-dialect-plugin

### Шаги проверки

**Действие**: Для включения плагина перенесите дополнительные библиотеки из директории `libs/optional/ise-calcite-oracle-dialect-plugin` в `libs/ise-calcite-oracle-dialect-plugin` и добавьте свойство в конфигруационный файл серверного узла:

:::{code-block} xml
:caption: XML
<property name="pluginProviders">
    <list>
        <bean class="com.sbt.ignite.calcite.CalciteOracleDialectPluginProvider"/>
    </list>
</property>
:::

**Успешный результат**: При запуске узла в его логе присутствуют сообщения о том, что плагин `CALCITE_ORACLE_DIALECT_PROVIDER 1.0` запущен:

```bash
YYYY-MM-DD 17:11:26.046 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor] Configured plugins:
YYYY-MM-DD 17:11:26.046 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- grid-security-basic-plugin 1.0
YYYY-MM-DD 17:11:26.046 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- null
YYYY-MM-DD 17:11:26.046 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor] 
YYYY-MM-DD 17:11:26.046 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- CALCITE_ORACLE_DIALECT_PROVIDER 1.0
YYYY-MM-DD 17:11:26.047 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- null
YYYY-MM-DD 17:11:26.047 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor] 
YYYY-MM-DD 17:11:26.047 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- Check Parameters 1.0.0-SNAPSHOT
YYYY-MM-DD 17:11:26.047 [INFO ][main][org.apache.ignite.internal.processors.plugin.IgnitePluginProcessor]   ^-- SberTech
```