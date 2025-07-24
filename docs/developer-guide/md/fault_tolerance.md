# Отказоустойчивость

DataGrid поддерживает автоматическое переключение заданий в случае сбоев. При сбое узла задания автоматически передаются для повторного выполнения на другие доступные узлы. Если в кластере есть хотя бы один узел, ни одно задание не потеряется.

Глобальная стратегия отказоустойчивости контролируется свойством `IgniteConfiguration.failoverSpi`.

Доступные реализации:

- Реализация по умолчанию `AlwaysFailoverSpi` всегда перенаправляет задание со сбоем на другой узел. 

   При сбое задания вычислительной задачи предпринимается попытка перенаправить его на узел, который еще не выполнял заданий этой задачи. Если он недоступен, предпринимается попытка перенаправить неуспешное задание на один из узлов, которые могут выполнять другие задания этой задачи. Если обе попытки провалились, задание не завершается сбоем.

   ::::{md-tab-set}
   :::{md-tab-item} XML
   ```xml
   <bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="failoverSpi">
        <bean class="org.apache.ignite.spi.failover.always.AlwaysFailoverSpi">
            <property name="maximumFailoverAttempts" value="5"/>
        </bean>
    </property>

   </bean>
   ```
   :::

   :::{md-tab-item} Java
   ```java
   AlwaysFailoverSpi failSpi = new AlwaysFailoverSpi();

   // Переопределите максимальное количество попыток failover.
   failSpi.setMaximumFailoverAttempts(5);

   // Переопределите SPI отказоустойчивости по умолчанию.
   IgniteConfiguration cfg = new IgniteConfiguration().setFailoverSpi(failSpi);

   // Запустите узел.
   Ignite ignite = Ignition.start(cfg);
   ```
   :::
   ::::

- Реализация `NeverFailoverSpi` никогда не приводит к сбою из-за неуспешно выполненных заданий.

   ::::{md-tab-set}
   :::{md-tab-item} XML
   ```xml
   <bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="failoverSpi">
        <bean class="org.apache.ignite.spi.failover.never.NeverFailoverSpi"/>
    </property>

   </bean>
   ```
   :::

   :::{md-tab-item} Java
   ```java
   NeverFailoverSpi failSpi = new NeverFailoverSpi();

   IgniteConfiguration cfg = new IgniteConfiguration();

   // Переопределите SPI отказоустойчивости по умолчанию.
   cfg.setFailoverSpi(failSpi);

   // Запустите узел.
   Ignite ignite = Ignition.start(cfg);
   ```
   :::
   ::::

- Реализацию `JobStealingFailoverSpi` нужно использовать только с включенным перехватом заданий — подробнее о нем написано в разделе [«Балансировка нагрузки»](load_balancing.md).