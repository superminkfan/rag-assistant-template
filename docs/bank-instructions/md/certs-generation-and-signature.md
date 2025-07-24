# Создание и подпись сертификатов

## Подготовка сертификатов пользователей

### Генерация сертификата

При создании сертификата придумайте уникальный пароль, удовлетворяющий требованиям инфобезопасности.

```
keytool -genkey \
  -alias <Alias> \
  -keystore <FileName>-keystore.jks \
  -keyalg RSA \
  -keysize 2048 \
  -dname "CN=<CN>, OU=00CA, O=Savings Bank of the Russian Federation, C=RU"
```

где:

-   `Alias` - псевдоним сертификата в `jks`-файле;
-   `FileName` – имя файла сертификата;
-   `CN` – значение `Common Name`.

::::{admonition} Пример
:class: hint

:::{code-block} xml
:caption: XML
keytool -genkey \
  -alias ntsecuritySgg_server \
  -keystore ntsecuritySgg_server-keystore.jks \
  -keyalg RSA \
  -keysize 2048 \
  -dname "CN=00CA0000Sgg_server.snnode.nt.security"
:::
::::

#### Структура сертификата

В DataGrid версии 16.1.0 и выше допускается использование произвольного имени в ролевой модели для поля CN (`Common Name`) сертификата.

Указать произвольное имя в ролевой модели можно двумя способами:

- Запустите утилиту [`ise-user-control`](../../administration-guide/md/user-control.md) с параметром `--distinguished-name`:

   ```bash
   ./bin/ise-user-control.sh --host xxx.x.x.x --login=ise_admgrant --password=***** --keystore=config/ise_dev_g_ise_admgrant.jks  --truststore=config/ise_dev_truststore.jks --keystore-password=**** --truststore-password=**** add-user --user-name=AddUserTest --user-password=***** --roles=MAINTENANCE_ADMIN --distinguished-name=customName
   ```

- Задайте в файле `default-security.json` поле `dn`.
    
   :::{code-block} json
   :caption: JSON
   {
    "login": "*****",
    "secret": {
       "key": "*****",
       "salt": "*****"
     },
     "dn": "customName",
     "roles": [
       "MAINTENANCE_ADMIN"
     ]
   }
   :::

### Создание запроса на подпись сертификата

Чтобы создать запрос на подпись сертификата, используйте команду для выполнения в консоли ОС:

```text
    keytool -keystore <FileName>-keystore.jks \
    -alias <Alias> \
    -certreq \
    -file <FileName>-certreq.csr \
    -ext ExtendedkeyUsage=serverAuth,clientAuth
```

где укажите имя файла сертификата (`FileName`) и псевдоним сертификата (`Alias`).

### Создание и подпись сертификата

Воспользуйтесь [Release Lifecycle Management (RLM)](https://rlm.sigma.sbrf.ru/dashboard/services/tls_cert) для создания и подписи сертификата: вставьте содержимое запроса в соответствующий шаблон (job). Полученный файл запроса (*.csr) отправьте в Центр Сертификации.

### Импорт сертификатов УЦ

:::{admonition} Примечание
:class: note

Далее используйте сертификаты (root, intermediate, publisher), полученные от RLM.
:::

Необходимо импортировать сертификаты УЦ в JKS-хранилище.  Импорт сертификатов УЦ является необходимым действием для последующего импорта подписанного сертификата, поскольку при импорте `keytool` проверяет корректность всей цепочки сертификации.

:::{admonition} Пример
:class: hint

```
keytool -keystore <FileName>-keystore.jks \
  -alias "Test Root CA 2" \
  -import \
  -file "Test Root CA 2.cer"
keytool -keystore <FileName>-keystore.jks \
  -alias "Sberbank Test Issuing CA 2" \
  -import \
  -file "Sberbank Test Issuing CA 2.cer"
```
:::

### Импорт подписанного сертификата

Необходимо импортировать подписанный сертификат в JKS-хранилище:

```
keytool -keystore <FileName>-keystore.jks \
  -alias <Alias> \
  -import \
  -file <FileName>-certreq.csr_cert.cer
```
 
**Примечание**

Значение `-alias` здесь должно совпадать со значением `-alias` на шаге генерации (описан в разделе «Генерация сертификата выше»).

### Удаление сертификатов УЦ

Необходимо удалить из jks-хранилища сертификаты УЦ, добавленные на шаге «Импорт сертификатов УЦ». Это необходимо, поскольку текущая реализация менеджера ключей в DataGrid и плагине использует первый встретившийся сертификат, поэтому он должен быть один.

```
keytool -keystore <FileName>-keystore.jks \
  -alias "Test Root CA 2" \
  -delete
keytool -keystore <FileName>-keystore.jks \
  -alias "Sberbank Test Issuing CA 2" \
  –delete
```

### Генерация `truststore`, содержащего сертификаты УЦ

```
keytool -keystore truststore.jks \
  -alias "Test Root CA 2" \
  -import \
  -file "Test Root CA 2.cer"
keytool -keystore truststore.jks \
  -alias "Sberbank Test Issuing CA 2" \
  -import \
  -file "Sberbank Test Issuing CA 2.cer"
```

### Проверка корректности созданных сертификатов

В keystore должен находиться ровно один сертификат.

```
keytool -v --list --keystore <FileName>-keystore.jks | awk '/Owner:|Issuer:|Your keystore contains|Certificate chain length/'
```

Пример вывода:

```
Your keystore contains 1 entry
Certificate chain length: 3
Owner: CN=00CA0000Sgg_server.snnode.nt.security
Issuer: CN=Sberbank Test Issuing CA 2, DC=ca, DC=sbrf, DC=ru
Owner: CN=Sberbank Test Issuing CA 2, DC=ca, DC=sbrf, DC=ru
Issuer: CN=Test Root CA 2
Owner: CN=Test Root CA 2
Issuer: CN=Test Root CA 2
```

Вывод должен содержать следующую информацию:

-   `Your keystore contains 1 entry`;
-   `Certificate chain length: 3`;
-   `Issuer:` — УЦ банка. 

### Импорт сертификата из JKS в PEM формат

Для импорта в PEM сначала требуется импортировать в PKCS12:

```
keytool -importkeystore \
  -srcstoretype JKS -srckeystore "${ALIAS}.jks" -srcstorepass "${PSWD}" \
  -deststoretype PKCS12 -destkeystore "${ALIAS}.p12" -deststorepass "${PSWD}" -destkeypass "${PSWD}"
```

Далее из PKCS12 с помощью openssl получаем PEM:

 -   закрытый ключ:

    ```
    openssl pkcs12 -in "${ALIAS}.p12" -out "${ALIAS}.key.pem" -nocerts
    ```

 -   сертификат:

    ```
    openssl pkcs12 -in "${ALIAS}.p12" -out "${ALIAS}.cert.pem" -nokeys -clcerts
    ```

 -   сертификат CA:

    ```
    openssl pkcs12 -in "${ALIAS}.p12" -out "ca.cert.pem" -nokeys -cacerts
    ```

## Подготовка сертификатов для утилиты управления пользователями

Для работы утилиты необходимо сгенерировать сертификат узла, на котором будет запускаться утилита. Данный сертификат имеет следующие особенности:

-   в нем должно быть указано соответствующее DNS-имя данного узла (браузер проверяет FQDN);
-   в `CN` указывается имя сервера.

В примерах ниже используется сервер `grid785`.

### Генерация сертификата

```
keytool -genkey \
  -alias grid785 \
  -keystore grid785-keystore.jks \
  -keyalg RSA \
  -keysize 2048 \
  -dname "CN=grid785.delta.sbrf.ru, OU=00CA, O=Savings Bank of the Russian Federation, C=RU"
```

### Создание запроса на подпись сертификата

```
keytool -keystore \
  grid785-keystore.jks \
  -alias grid785 \
  -certreq \
  -file grid785-certreq.csr \
  -ext SAN="dns:grid785.delta.sbrf.ru,dns:grid785" \
  -ext ExtendedkeyUsage=serverAuth
```

Дальнейшие шаги совпадают с шагами раздела «Подготовка сертификатов пользователей» текущего документа.

Утилита управления использует аутентификацию клиентов, поэтому необходимо создать копию `keystore` в формате `PKCS12` и импортировать ее в браузер:

```
keytool -importkeystore \
  -srckeystore petrov-keystore.jks \
  -destkeystore petrov-keystore.p12 \
  -srcstoretype JKS \
  -deststoretype PKCS12
```

Импорт копии `keystore` в браузер осуществляется стандартными средствами ОС. Например, для Windows импорт происходит через контекстное меню файла `*.p12`.

## Подключение сертификатов по SSL

Пример подключения сертификатов, выпущенных для стенда `name_group_servers1`:

1. Проверьте, что полученные от хранилища ключей (`keystore`) пароли валидные. Выполните команду`$ keytool -list -v -keystore ntRubinNTS-keystore.jks` и введите пароль.
2. После ввода верного пароля посмотрите вывод `Owner` для серверного сертификата:

    -  `Keystore type: jks`;
    -  ` Keystore provider: SUN`;
    -  `Owner: CN=00CA0000Sign_srv@snnode.nt.name_group_servers1.sbrf.ru, OU=00CA, O=Savings Bank of the Russian Federation, C=RU`.

3. Разместите новые сертификаты в `inventory`, в каталоге `files`:

   ```
       files
       └── name_group_servers1
           ├── nt_Name_group_servers1-keystore.jks
           ├── nt_Name_group_servers1-truststore.jks
           ├── ...
       ├── inventory
           ├── group_vars
               ├── name_group_servers1
               ├── ...
   ```

4. Задайте соответствующие параметры кластера `inventory/group_vars/name_group_servers1/vars_for_name_group_servers1.yml`:

    ```yaml
        # Путь, по которому локально хранятся `keystore` и `truststore` на control (ansible) хосте:
        datagrid_local_ssl_keystore: "{{inventory_dir}}/../files/name_group_servers1/ntRubinNTS-keystore.jks"
        datagrid_local_ssl_truststore: "{{inventory_dir}}/../files/name_group_servers1/trustore.jks"
        datagrid_local_client_keystore: "{{inventory_dir}}/../files/name_group_servers1/ntRubinNTC-keystore.jks"
        datagrid_local_admin_keystore: "{{inventory_dir}}/../files/name_group_servers1/ntRubinNTA-keystore.jks"

        # Задайте соответствующие пароли к JKS в переменных:
        datagrid_ssl_keystore_password: "passServerKeystore"
        datagrid_ssl_truststore_password: "passTruststore"
        datagrid_ssl_admin_keystore_password: "passAdminKeystore"

        # Задайте логин (должен соответствовать тому, который указан в серверном JKS):
        datagrid_credentials_SecurityCredentials_login: "ign_srv"
        datagrid_credentials_SecurityCredentials_password: "passServerKeystore" # Для авторизации серверных узлов на этом кластере.

        # Измените путь к файлу-шаблону с пользователями и ролями:
        datagrid_json_credentials_template: "{{inventory_dir}}/../files/name_group_servers1/security-data.json.j2"

        # Укажите имя и тип кластера:
        datagrid_cluster_name: "name_group_servers1"
        datagrid_cluster_type: "dev"
    ```

    :::{admonition} Важно
    :class: attention

    Cуществующие файлы с логинами и паролями на хостах кластера по умолчанию **не** переписываются. Для принудительной перезаписи необходимо установить переменную «Перезапись credentials»: `datagrid_credentials_overwrite: yes`.
    :::