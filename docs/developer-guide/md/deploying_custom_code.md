# Развертывание пользовательского кода

Можно развернуть (deploy) пользовательский код с помощью функциональности [Peer Class Loading](peer_class_loading.md) или `UriDeploymentSpi`. После настройки `UriDeploymentSpi` DataGrid сканирует указанное местоположение и повторно загружает классы, если они изменились. Библиотеки могут располагаться в каталоге файловой системы или в URL. Когда DataGrid обнаруживает, что библиотек нет по указанному местоположению, происходит отмена развертывания (undeploy) классов на кластере.

Можно указать несколько местоположений разных типов — предоставьте путь к каталогу или HTTP-адрес.

## Развертывание из локального каталога

Чтобы развернуть библиотеки из каталога файловой системы, добавьте путь к каталогу в список URI в конфигурации `UriDeploymentSpi`. Каталог должен существовать на тех узлах, где он указан, и содержать JAR-файлы с классами, которые нужно развернуть. Путь нужно указывать с использованием схемы `file://`. Можно указать разные каталоги на разных узлах.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="deploymentSpi">
            <bean class="org.apache.ignite.spi.deployment.uri.UriDeploymentSpi">
                <property name="temporaryDirectoryPath" value="/tmp/temp_ignite_libs"/>
                <property name="uriList">
                    <list>
                        <value>file://freq=2000@localhost/home/username/user_libs</value>
                    </list>
                </property>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

UriDeploymentSpi deploymentSpi = new UriDeploymentSpi();

deploymentSpi.setUriList(Arrays.asList("file://freq=2000@localhost/home/username/user_libs"));

cfg.setDeploymentSpi(deploymentSpi);

try (Ignite ignite = Ignition.start(cfg)) {
    // Выполните задачу, которая представлена классом из каталога `user_libs`.
    ignite.compute().execute("org.mycompany.HelloWorldTask", "My Args");
}
```
:::
::::

Можно передать следующий параметр через URL:

| Параметр | Описание | Значение по умолчанию |
|---|---|---|
| `freq` | Частота сканирования (в мс) | `5000` |

## Развертывание из URL

DataGrid анализирует HTML-файл, чтобы найти атрибуты `HREF` всех тегов `<a>` на странице. Ссылки должны указывать на JAR-файлы, которые нужно развернуть.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<beans xmlns="http://www.springframework.org/schema/beans" xmlns:util="http://www.springframework.org/schema/util" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="         http://www.springframework.org/schema/beans         http://www.springframework.org/schema/beans/spring-beans.xsd         http://www.springframework.org/schema/util         http://www.springframework.org/schema/util/spring-util.xsd">
    <bean class="org.apache.ignite.configuration.IgniteConfiguration">
        <property name="deploymentSpi">
            <bean class="org.apache.ignite.spi.deployment.uri.UriDeploymentSpi">
                <property name="temporaryDirectoryPath" value="/tmp/temp_ignite_libs"/>
                <property name="uriList">
                    <list>
                        <value>http://username:password;freq=10000@www.mysite.com:110/ignite/user_libs</value>
                    </list>
                </property>
            </bean>
        </property>
    </bean>
</beans>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

UriDeploymentSpi deploymentSpi = new UriDeploymentSpi();

deploymentSpi.setUriList(Arrays
        .asList("http://username:password;freq=10000@www.mysite.com:110/ignite/user_libs"));

cfg.setDeploymentSpi(deploymentSpi);

try (Ignite ignite = Ignition.start(cfg)) {
    // Выполните задачу, которая представлена классом из каталога `user_libs`.
    ignite.compute().execute("org.mycompany.HelloWorldTask", "My Args");
}
```
:::
::::

Можно передать следующий параметр через URL:

| Параметр | Описание | Значение по умолчанию |
|---|---|---|
| `freq` | Частота сканирования (в мс) | `300000` |