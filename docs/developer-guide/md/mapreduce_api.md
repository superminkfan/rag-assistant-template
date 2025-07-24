# MapReduce API

DataGrid предоставляет API для выполнения упрощенных операций `MapReduce`. Паттерн `MapReduce` основан на предположении, что для выполнения задачи ее можно разделить на несколько заданий (этап сопоставления — маппинг), при этом каждое задание выполняется отдельно. Результаты, которые получены в каждом задании, агрегируются в конечные результаты (этап сокращения — reducing).

В распределенных системах, таких как DataGrid, задачи распределяются по узлам согласно настроенной стратегии балансировки нагрузки (подробнее о ней написано в разделе [«Балансировка нагрузки»](load_balancing.md)). Результаты агрегируются на узле, который отправил задачу на выполнение.

Паттерн `MapReduce` предоставляется интерфейсом `ComputeTask`.

:::{admonition} Внимание
:class: danger

Используйте интерфейс `ComputeTask`, только если нужен детальный контроль над распределением задач по узлам или при пользовательской логике переключения при сбоях системы. Для всех остальных случаев используйте стандартный `IgniteClosure` — подробнее о нем написано в разделе [«Распределенные вычисления»](distributed_computing.md).
:::

## Интерфейс ComputeTask

Интерфейс `ComputeTask` предоставляет способ реализовать пользовательскую логику map-reduce. В интерфейсе есть три метода: `map(…​)`, `result()` и `reduce()`.

Реализация метода `map()` нужна для создания вычислительных заданий на основе входного параметра и их маппинга на рабочих узлах. Метод получает коллекцию узлов кластера, на которых должна выполняться задача, и ее входной параметр. Метод возвращает отображение (map) с заданиями в качестве ключей и распределенными рабочими узлами в качестве значений. Затем задания отправляются на распределенные узлы и выполняются там.

Метод `result()` вызывается после завершения каждого задания и возвращает экземпляр `ComputeJobResultPolicy`. Он указывает, как выполнять задачу далее. Метод получает результаты выполнения задания и список всех полученных на данный момент результатов. Метод может вернуть одно из значений:

- `WAIT` — дождитесь завершения всех оставшихся заданий (при наличии);
- `REDUCE` — незамедлительно переходите к этапу сокращения (reduce), отбросив все оставшиеся задания и еще не полученные результаты;
- `FAILOVER` — перенесите задание на другой узел (подробнее об этом написано в разделе [«Отказоустойчивость»](fault_tolerance.md)).

Метод `reduce()` вызывается на этапе сокращения (reduce), когда все задания выполнены или когда метод `result()` вернул результирующую политику `REDUCE` для конкретного задания. Метод получает список завершенных результатов и возвращает итоговый результат вычислений.

## Выполнение вычислительной задачи

Для выполнения вычислительной задачи вызовите метод `IgniteCompute.execute(…​)` и передайте для нее входной параметр в качестве последнего аргумента:

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.start();

IgniteCompute compute = ignite.compute();

int count = compute.execute(new CharacterCountTask(), "Hello Grid Enabled World!");
```
:::

:::{md-tab-item} C\#/.NET
```c#
class CharCountComputeJob : IComputeJob<int>
{
    private readonly string _arg;

    public CharCountComputeJob(string arg)
    {
        Console.WriteLine(">>> Printing '" + arg + "' from compute job.");
        this._arg = arg;
    }

    public int Execute()
    {
        return _arg.Length;
    }

    public void Cancel()
    {
        throw new System.NotImplementedException();
    }
}


class CharCountTask : IComputeTask<string, int, int>
{
    public IDictionary<IComputeJob<int>, IClusterNode> Map(IList<IClusterNode> subgrid, string arg)
    {
        var map = new Dictionary<IComputeJob<int>, IClusterNode>();
        using (var enumerator = subgrid.GetEnumerator())
        {
            foreach (var s in arg.Split(" "))
            {
                if (!enumerator.MoveNext())
                {
                    enumerator.Reset();
                    enumerator.MoveNext();
                }

                map.Add(new CharCountComputeJob(s), enumerator.Current);
            }
        }

        return map;
    }

    public ComputeJobResultPolicy OnResult(IComputeJobResult<int> res, IList<IComputeJobResult<int>> rcvd)
    {
        // Если исключений нет, дождитесь получения всех результатов задания.
        return res.Exception != null ? ComputeJobResultPolicy.Failover : ComputeJobResultPolicy.Wait;
    }

    public int Reduce(IList<IComputeJobResult<int>> results)
    {
        return results.Select(res => res.Data).Sum();
    }
}

public static void MapReduceComputeJobDemo()
{
    var ignite = Ignition.Start(new IgniteConfiguration
    {
        DiscoverySpi = new TcpDiscoverySpi
        {
            LocalPort = 48500,
            LocalPortRange = 20,
            IpFinder = new TcpDiscoveryStaticIpFinder
            {
                Endpoints = new[]
                {
                    "xxx.x.x.x:48500..48520"
                }
            }
        }
    });

    var compute = ignite.GetCompute();

    var res = compute.Execute(new CharCountTask(), "Hello Grid Please Count Chars In These Words");

    Console.WriteLine("res=" + res);
}
```
:::
::::

Можно ограничить выполнение заданий подмножеством узлов с помощью группы кластеров. Подробнее о ней написано в разделе [«Группы кластеров»](cluster_groups.md).

## Обработка неудачного выполнения задания

Если узел вылетает или становится недоступным во время выполнения задачи, все запланированные для узла задания автоматически отправляются на другой доступный узел благодаря встроенному механизму отказоустойчивости. Если задание генерирует исключение, задание считается неудачно завершившимся и передается на другой узел для повторного выполнения. Для этого верните `FAILOVER` в методе `result(…​)`.

:::{code-block} java
:caption: Java
@Override
public ComputeJobResultPolicy result(ComputeJobResult res, List<ComputeJobResult> rcvd) {
    IgniteException err = res.getException();

    if (err != null)
        return ComputeJobResultPolicy.FAILOVER;

    // Если исключений нет, дождитесь получения всех результатов задания.
    return ComputeJobResultPolicy.WAIT;
}
:::

## Адаптеры вычислительных задач

Существует несколько вспомогательных классов, которые предоставляют наиболее часто используемые реализации методов `result(…​)` и `map(…​)`:

- Класс `ComputeTaskAdapter` реализует метод `result()`, который выполняет необходимые действия для ожидания успешного завершения всех вычислительных заданий (compute jobs) и обработки их результатов. Метод последовательно проверяет результаты всех вычислительных заданий на наличие исключений и при отсутствии исключений возвращает политику ожидания `WAIT`. Подробнее о политике `WAIT` написано выше в разделе [«Интерфейс ComputeTask»](#интерфейс-computetask).

   В следующих сценариях вычислительные задания будут автоматически повторно развернуты (подробнее о политике `FAILOVER` написано выше в разделе [«Интерфейс ComputeTask»](#интерфейс-computetask)):

    - предоставленный пользователем исполнитель (executor) отказался обрабатывать сопоставленное вычислительное задание;
    - узел, который был предназначен для выполнения вычислительного задания, отсутствует в составе кластера;
    - пользовательский код вычислительного задания явно сгенерировал специальное исключение `ComputeJobFailoverException`.

   Если любое сопоставленное вычислительное задание генерирует пользовательское исключение, вся вычислительная задача немедленно завершается сбоем, а все оставшиеся вычислительные задания останавливаются асинхронно.
- Класс `ComputeTaskSplitAdapter` наследует `ComputeTaskAdapter` и реализует метод `map(…​)` для автоматического назначения заданий узлам. В классе есть метод `split(…​)`, который реализует логику создания заданий на основе входных данных.

## Сессии распределенных задач

:::{admonition} Внимание
:class: danger

Сессии распределенных задач недоступны для языков .NET/C#/C++.
:::

Для каждой задачи DataGrid создает распределенную сессию. Она содержит информацию по задаче и видна самой задаче и всем созданным ею заданиям. Можно использовать сессию для обмена атрибутами между заданиями. Атрибуты можно назначить до или во время выполнения задания. Они становятся видимыми для других заданий в том же порядке, в котором их установили.

:::{code-block} java
:caption: Java
@ComputeTaskSessionFullSupport
private static class TaskSessionAttributesTask extends ComputeTaskSplitAdapter<Object, Object> {

    @Override
    protected Collection<? extends ComputeJob> split(int gridSize, Object arg) {
        Collection<ComputeJob> jobs = new LinkedList<>();

        // Сгенерируйте задания по количеству узлов в кластере.
        for (int i = 0; i < gridSize; i++) {
            jobs.add(new ComputeJobAdapter(arg) {
                // Автоматическое внедрение сессии задачи.
                @TaskSessionResource
                private ComputeTaskSession ses;

                // Автоматическое внедрение контекста задания.
                @JobContextResource
                private ComputeJobContext jobCtx;

                @Override
                public Object execute() {
                    // Выполните шаг 1.
                    // ...

                    // Передайте остальным заданиям, что шаг 1 выполнен.
                    ses.setAttribute(jobCtx.getJobId(), "STEP1");

                    // Дождитесь выполнения шага 1 другими заданиями.
                    for (ComputeJobSibling sibling : ses.getJobSiblings())
                        try {
                            ses.waitForAttribute(sibling.getJobId(), "STEP1", 0);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }

                    // Перейдите к шагу 2.
                    // ...

                    return ...

                }
            });
        }
        return jobs;
    }

    @Override
    public Object reduce(List<ComputeJobResult> results) {
        // Без операции.
        return null;
    }

}
:::

## Пример вычислительной задачи

Ниже пример простого приложения для подсчета символов. Оно разбивает строку на слова и считает длину каждого в отдельном задании. Все задания распределяются по узлам кластера.

::::{md-tab-set}
:::{md-tab-item} Java
```java
public class ComputeTaskExample {
    public static class CharacterCountTask extends ComputeTaskSplitAdapter<String, Integer> {
        // 1. Разделяет полученную строку на слова.
        // 2. Создает дочернее задание для каждого слова.
        // 3. Отправляет задания на другие узлы для обработки.
        @Override
        public List<ComputeJob> split(int gridSize, String arg) {
            String[] words = arg.split(" ");

            List<ComputeJob> jobs = new ArrayList<>(words.length);

            for (final String word : words) {
                jobs.add(new ComputeJobAdapter() {
                    @Override
                    public Object execute() {
                        System.out.println(">>> Printing '" + word + "' on from compute job.");

                        // Возвращает количество букв в слове.
                        return word.length();
                    }
                });
            }

            return jobs;
        }

        @Override
        public Integer reduce(List<ComputeJobResult> results) {
            int sum = 0;

            for (ComputeJobResult res : results)
                sum += res.<Integer>getData();

            return sum;
        }
    }

    public static void main(String[] args) {

        Ignite ignite = Ignition.start();

        IgniteCompute compute = ignite.compute();

        // Выполните задачу в кластере и дождитесь ее завершения.
        int cnt = compute.execute(CharacterCountTask.class, "Hello Grid Enabled World!");

        System.out.println(">>> Total number of characters in the phrase is '" + cnt + "'.");
    }
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
class CharCountComputeJob : IComputeJob<int>
{
    private readonly string _arg;

    public CharCountComputeJob(string arg)
    {
        Console.WriteLine(">>> Printing '" + arg + "' from compute job.");
        this._arg = arg;
    }

    public int Execute()
    {
        return _arg.Length;
    }

    public void Cancel()
    {
        throw new System.NotImplementedException();
    }
}

public class ComputeTaskExample
{
    private class CharacterCountTask : ComputeTaskSplitAdapter<string, int, int>
    {
        public override int Reduce(IList<IComputeJobResult<int>> results)
        {
            return results.Select(res => res.Data).Sum();
        }

        protected override ICollection<IComputeJob<int>> Split(int gridSize, string arg)
        {
            return arg.Split(" ")
                .Select(word => new CharCountComputeJob(word))
                .Cast<IComputeJob<int>>()
                .ToList();
        }
    }

    public static void RunComputeTaskExample()
    {
        var ignite = Ignition.Start(new IgniteConfiguration
        {
            DiscoverySpi = new TcpDiscoverySpi
            {
                LocalPort = 48500,
                LocalPortRange = 20,
                IpFinder = new TcpDiscoveryStaticIpFinder
                {
                    Endpoints = new[]
                    {
                        "xxx.x.x.x:48500..48520"
                    }
                }
            }
        });

        var cnt = ignite.GetCompute().Execute(new CharacterCountTask(), "Hello Grid Enabled World!");
        Console.WriteLine(">>> Total number of characters in the phrase is '" + cnt + "'.");
    }
}
```
:::
::::