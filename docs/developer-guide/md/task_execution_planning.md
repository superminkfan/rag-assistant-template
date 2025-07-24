# Планирование выполнения заданий

Когда задания поступают на целевой узел, они передаются в пул потоков и планируются к выполнению в произвольном порядке. Порядок выполнения заданий можно изменить в настройках интерфейса `CollisionSpi`. С его помощью можно контролировать план обработки заданий на каждом узле.

В DataGrid есть несколько реализаций интерфейса `CollisionSpi`:

- `FifoQueueCollisionSpi` — упорядочение по FIFO («первым пришел — первым ушел») в нескольких потоках. Реализация по умолчанию.
- `PriorityQueueCollisionSpi` — упорядочение по приоритетам.
- `JobStealingFailoverSpi` — реализация для включения перехвата заданий. Подробнее о нем написано в разделе [«Балансировка нагрузки»](load_balancing.md).

Чтобы включить конкретный Collision SPI, измените свойство `IgniteConfiguration.collisionSpi`.

## Упорядочение по FIFO

В реализации `FifoQueueCollisionSpi` задания выполняются в порядке поступления в нескольких потоках. Количество потоков настраивается с помощью параметра `parallelJobsNumber`. Значение по умолчанию превышает количество ядер процессоров в 2 раза.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="collisionSpi">
        <bean class="org.apache.ignite.spi.collision.fifoqueue.FifoQueueCollisionSpi">
            <!-- Выполняйте по одному заданию за раз. -->
            <property name="parallelJobsNumber" value="1"/>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
FifoQueueCollisionSpi colSpi = new FifoQueueCollisionSpi();

// Выполняйте задания последовательно, по одному за раз.
// Для этого установите количество параллельных заданий равным 1.
colSpi.setParallelJobsNumber(1);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Collision SPI по умолчанию.
cfg.setCollisionSpi(colSpi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

## Упорядочение по приоритетам

Чтобы установить приоритеты отдельным заданиям, используйте `PriorityQueueCollisionSpi`. Задания с более высоким приоритетом выполняются раньше заданий с более низким. Также можно указать количество потоков для обработки заданий.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="collisionSpi">
        <bean class="org.apache.ignite.spi.collision.priorityqueue.PriorityQueueCollisionSpi">
            <!-- При необходимости измените количество параллельных заданий.
                 Значение по умолчанию превышает количество ядер процессоров в 2 раза. -->
            <property name="parallelJobsNumber" value="5"/>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
PriorityQueueCollisionSpi colSpi = new PriorityQueueCollisionSpi();

// При необходимости измените количество параллельных заданий.
// Значение по умолчанию превышает количество ядер процессоров в 2 раза.
colSpi.setParallelJobsNumber(5);

IgniteConfiguration cfg = new IgniteConfiguration();

// Переопределите Collision SPI по умолчанию.
cfg.setCollisionSpi(colSpi);

// Запустите узел.
Ignite ignite = Ignition.start(cfg);
```
:::
::::

Приоритеты по задачам устанавливаются в их сессиях с помощью атрибута `grid.task.priority`. Если задаче не назначили приоритет, по умолчанию используется значение `0`.

Подробнее о сессиях задач написано в разделе [MapReduce API](mapreduce_api.md).

:::{code-block} java
:caption: Java
public class MyUrgentTask extends ComputeTaskSplitAdapter<Object, Object> {
    // Автоматическое внедрение сессии задачи.
    @TaskSessionResource
    private ComputeTaskSession taskSes = null;

    @Override
    protected Collection<ComputeJob> split(int gridSize, Object arg) {
        // Установите высокий приоритет для задачи.
        taskSes.setAttribute("grid.task.priority", 10);

        List<ComputeJob> jobs = new ArrayList<>(gridSize);

        for (int i = 1; i <= gridSize; i++) {
            jobs.add(new ComputeJobAdapter() {

                @Override
                public Object execute() throws IgniteException {

                    // Здесь нужно написать пользовательскую реализацию.

                    return null;
                }
            });
        }

        // Данные задания будут выполняться с более высоким приоритетом.
        return jobs;
    }

    @Override
    public Object reduce(List<ComputeJobResult> results) throws IgniteException {
        return null;
    }
}
:::