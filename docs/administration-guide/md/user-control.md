# Утилита ise-user-control для управления пользователями

Утилита запускается на сервере, который имеет доступ к кластеру DataGrid. Она предназначена для добавления, изменения и удаления ролей и пользователей в DataGrid администраторами безопасности в неинтерактивном режиме.

Для работы утилиты в конфигурации серверного узла разрешите подключение и выполнение задач для `IgniteClient`.

:::{code-block} xml
:caption: XML
<!-- Bean `ignClientConnectorConfiguration`. -->
    <bean id="ignClientConnectorConfiguration" class="org.apache.ignite.configuration.ClientConnectorConfiguration">
        ...
        <property name="thinClientEnabled" value="true"/>    
        <property name="thinClientConfiguration" ref="thinClientConfiguration"/>
        ...
    </bean>

    <!-- Bean `thinClientConfiguration`. -->
    <bean id="thinClientConfiguration" class="org.apache.ignite.configuration.ThinClientConfiguration">
        <property name="maxActiveComputeTasksPerConnection" value="100"/>
    </bean>
:::

## Запуск утилиты

Для запуска утилиты выполните команду:

```bash
ise-user-control.(sh|bat) connection_parameters command command_parameters
```

где:

- `connection_parameters` — параметры для создания подключения `IgniteClient` (имя пользователя, путь к хранилищу сертификатов, наборы шифрования);
- `command` — команда администрирования; 
- `command_parameters` — параметры команды администрирования.


:::{admonition} Примечание
:class: note

Чтобы получить справку по используемым командам, выполните:

`ise-user-control.(sh|bat) --help`
:::

## Параметры для подключения

Для подключения к кластеру используйте параметры:

| Параметр | Описание|
|---|---|
| `--distinguished-name` | Добавление произвольного имени для CN (`Common Name`) сертификата |
| `-h`, `--help` | Вызов справки |
| `-l`, `--login` | Логин администратора доступа |
| `-p`, `--password` | Пароль администратора доступа |
| `--host` | Имя хоста или IP-адрес узла |
| `--port` | Порт, к которому нужно подключиться |
| `--ssl-protocol` | Список SSL-протоколов для подключения к кластеру (укажите через запятую) |
| `--ssl-cipher-suites` | Наборы SSL-шифров (укажите через запятую) |
| `--ssl-key-algorithm` | Алгоритм SSL-ключей |
| `--keystore` | Путь к хранилищу сертификатов |
| `--keystore-type` | Тип хранилища сертификатов |
| `--keystore-password` | Пароль от хранилища сертификатов |
| `--truststore` | Путь к хранилищу доверенных сертификатов |
| `--truststore-type` | Тип хранилища доверенных сертификатов |
| `--truststore-password` | Пароль от хранилища доверенных сертификатов |
| `--ssl-factory SSL_FACTORY_PATH` | Пользовательский путь к XML-файлу `Spring` SSL-фабрики |
| `--ping-timeout` | Время ожидания `ping` (в мс) |
| `--ping-interval` | Интервал между `ping` (в мс) |

## Команды

Список команд утилиты:

| Команда | Описание |
|---|---|
| `add-role` | Добавление роли |
| `add-user` | Добавление пользователя |
| `add-user-with-salt` | Добавление пользователя с посоленным паролем |
| `change-password` | Изменение пароля |
| `delete-role` | Удаление роли |
| `delete-user` | Удаление пользователя |
| `generate-hash` | Генерация хеша |
| `get-roles` | Просмотр списка ролей |
| `get-users` | Просмотр списка пользователей |
| `update-role` | Изменение роли |
| `update-user` | Изменение пользователя |
| `load-security-model` | Атомарная замена текущих данных безопасности пользователей на указанные | 

:::{admonition} Внимание
:class: danger

Команда `load-security-model` доступна для выполнения только на кластере в состоянии `INACTIVE`.
:::

### Параметры команд

Ниже указаны параметры, которые используются для конкретных команд.

#### add-role

| Параметр | Описание |
|---|---|
| `-r`, `--role` | Название роли |
| `--perms`, `--permissions` | Разрешения роли в формате JSON |

#### add-user

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Имя пользователя |
| `-up`, `--user-password` | Пароль пользователя |
| `-r`, `--roles` | Список ролей через запятую |
| `-dn`, `--distinguished-name`| Произвольное имя в ролевой модели для поля CN (`Common Name`) сертификата |

#### add-user-with-salt

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Имя пользователя |
| `-up`, `--user-password` | Посоленный пароль пользователя |
| `-s`, `--salt` | Соль |
| `-r`, `--roles` | Список ролей через запятую |
| `-dn`, `--distinguished-name`| Произвольное имя в ролевой модели для поля CN (`Common Name`) сертификата |

#### change-password

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Имя пользователя. Если не указано, используется логин администратора доступа |
| `-s`, `--salt` | Соль. Необязательно |
| `-up`, `--user-password` | Новый пароль. Если указана соль, пароль должен быть посолен |

#### delete-role

| Параметр | Описание |
|---|---|
| `-r`, `--role` | Название роли |

#### delete-user

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Имя пользователя |

#### generate-hash

| Параметр | Описание |
|---|---|
| `-p`, `--password` | Пароль, который нужно хешировать |
| `--confirm-password` | Повторный пароль |
| `--password-policy` | Конфигурация Password Policy |

#### get-roles

| Параметр | Описание |
|---|---|
| `-r`, `--role` | Регулярное выражения для поиска роли |

#### get-users

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Регулярное выражения для поиска пользователя |
| `-r`, `--roles` | Список ролей, которые должны быть у пользователя (через запятую) |

#### update-role

| Параметр | Описание |
|---|---|
| `-r`, `--role` | Название роли |
| `--perms`, `--permissions` | Разрешения роли в формате JSON |


#### update-user

| Параметр | Описание |
|---|---|
| `-un`, `--user-name` | Имя пользователя |
| `-r`, `--roles` | Список ролей через запятую |

#### load-security-model

| Параметр | Описание |
|---|---|
| `-f`, `-file-path` | Путь к файлу с обновленными данными безопасности пользователей в формате JSON |

## Примеры использования

```bash
> ./ise-user-control.sh -l userAdmin -p Default-password-1 --keystore "path/to/userAdmin.jks" --keystore-password 123456 --truststore "path/to/trust-one.jks" --truststore-password 123456 --ssl-cipher-suites "TLS_RSA_WITH_NULL_SHA256" add-role -r asd123 --perms "{\"dfltAll\":false,\"cachePerms\":{\"test-cache\":[\"CACHE_READ\",\"CACHE_PUT\",\"CACHE_REMOVE\"]},\"taskPerms\":{},\"servicePerms\":{},\"systemPerms\":[\"CACHE_DESTROY\",\"ADMIN_OPS\",\"CACHE_CREATE\"]}"
User control utility.
Time: YYYY-MM-DDT14:24:40.922
Command [add-role] started.
Command [add-role] finished successfully.
Control utility has completed execution at: YYYY-MM-DDT14:24:43.271
Execution time: 2349 ms
```

Пароли указывать небезопасно, поэтому их значения можно опустить (сами параметры опускать нельзя):

```bash
> ./ise-user-control.sh -l userAdmin -p --keystore "path/to/userAdmin.jks" --keystore-password --truststore "path/to/trust-one.jks" --truststore-password --ssl-cipher-suites "TLS_RSA_WITH_NULL_SHA256" add-role -r asd123 --perms "{\"dfltAll\":false,\"cachePerms\":{\"test-cache\":[\"CACHE_READ\",\"CACHE_PUT\",\"CACHE_REMOVE\"]},\"taskPerms\":{},\"servicePerms\":{},\"systemPerms\":[\"CACHE_DESTROY\",\"ADMIN_OPS\",\"CACHE_CREATE\"]}"
User control utility.
Time: YYYY-MM-DDT14:24:40.922
Enter value for --password (User password.):
Enter value for --keystore-password (Keystore password.):
Enter value for --truststore-password (Truststore password.):
Command [add-role] started.
Command [add-role] finished successfully.
Control utility has completed execution at: YYYY-MM-DDT14:24:43.271
Execution time: 2349 ms
```

:::{admonition} Примечание
:class: note

Если в тексте команды не будет указан пароль, утилита предложит ввести его в интерактивном режиме.
:::

### Добавление произвольного имени CN сертификата

С помощью утилиты `ise-user-control` можно указать произвольное имя в ролевой модели для `Common Name` (CN) сертификата. Для этого используйте параметр `--distinguished-name`:

```bash
./bin/ise-user-control.sh --host xxx.x.x.x --login=ise_admgrant --password=***** --keystore=config/ise_dev_g_ise_admgrant.jks  --truststore=config/ise_dev_truststore.jks --keystore-password=**** --truststore-password=**** add-user --user-name=AddUserTest --user-password=***** --roles=MAINTENANCE_ADMIN --distinguished-name=customName
```

### Генерация Salt и Salted-хеша пароля с помощью утилиты ise-user-control.sh

:::{admonition} Пример запуска
:class: hint 
:collapsible:

```bash
ise-user-control.sh generate-hash
User control utility.
Time: YYYY-MM-DDT17:55:57.432
Command [generate-hash] started.
Enter value for --password (password):
Enter value for --confirm-password (confirm password):
Salt: <salt>
Salted hash: <salted-hash>
Command [generate-hash] finished successfully.
Control utility has completed execution at: YYYY-MM-DDT17:56:05.029
Execution time: 7597 ms
```
:::

Опционально можно передать конфигурацию Password Policy для валидатора пароля с помощью флага `--password-policy`. В качестве аргумента данная опция принимает путь к конфигурации в виде: 

:::{admonition} Пример `password-policy.properties`
:class: hint

```bash
user.password.length.min=12
```
:::