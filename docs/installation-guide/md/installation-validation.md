# Чек-лист валидации установки 

Чтобы убедиться, что все необходимые действия по установке программного компонента были произведены, проверьте, что:

1. Все файлы DataGrid находятся в рабочей директории.
2. При запуске DataGrid не выдается исключений и ошибок уровня `[ERROR]`.
3. Активация кластера при помощи команды `control.sh --set-state ACTIVE` происходит без ошибок уровня `[ERROR]`.

    :::{admonition} Внимание
    :class: danger

    Если DataGrid установлен с SSL, используйте параметры для авторизации и ключей:
    
    ```bash
    control.sh --set-state active --yes --user <ise_admin> --password <admin_password> --keystore <ssl/admin/keystore/path> --keystore-password <ssl_admin_keystore_password> --truststore </ssl/truststore/path> --truststore-password <ssl_truststore_password>
    ```
    :::

4. При выполнении команды `control.sh --baseline` кластер активен и содержит все узлы.

    :::{admonition} Внимание
    :class: danger

    Если DataGrid установлен с SSL, используйте параметры для авторизации и ключей:
    
    ```bash
    control.sh --baseline --user <ise_admin> --password <admin_password> --keystore <ssl/admin/keystore/path> --keystore-password <ssl_admin_keystore_password> --truststore </ssl/truststore/path> --truststore-password <ssl_truststore_password>
    ```
    :::

## Проверка интеграций

Проверка интеграций DataGrid с внешними системами и компонентами Платформы описана в [разделе «Проверка работоспособности» текущего документа](health-check.md).