# Настройка каталога снепшотов

По умолчанию сегменты снепшотов хранятся в рабочем каталоге соответствующего узла DataGrid. Этот сегмент использует тот же носитель, на котором DataGrid Persistence хранит данные, индексы, WAL и другие файлы. Снепшоты могут занимать столько же места, сколько файлы Persistence, поэтому рекомендуется хранить их на разных носителях. Совместное использование дискового ввода-вывода снепшотов с подпрограммами DataGrid Persistence может снизить производительность приложения.

Чтобы избежать взаимного влияния DataGrid Native Persistence и создания снепшотов:

- измените каталоги, в которых хранятся файлы Persistence — подробнее написано в разделе [«Персистентность DataGrid»](datagrid_persistence.md);
- или измените расположение снепшотов по умолчанию, как показано в примере ниже.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">
    <!--
       Устанавливает путь к корневому каталогу для хранения файлов снепшотов.
       По умолчанию каталог `snapshots` находится в `IGNITE_HOME/db`.
    -->
    <property name="snapshotPath" value="/snapshots"/>

    <property name="cacheConfiguration">
        <bean class="org.apache.ignite.configuration.CacheConfiguration">
            <property name="name" value="snapshot-cache"/>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration cfg = new IgniteConfiguration();

File exSnpDir = U.resolveWorkDirectory(U.defaultWorkDirectory(), "ex_snapshots", true);

cfg.setSnapshotPath(exSnpDir.getAbsolutePath());
```
:::
::::