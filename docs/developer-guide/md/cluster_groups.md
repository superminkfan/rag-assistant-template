# Группы кластеров

Интерфейс `ClusterGroup` представляет логическую группу узлов, которые можно использовать во многих API DataGrid для ограничения объема конкретных операций подмножеством узлов (вместо всего кластера). Например, можно развернуть сервис только на удаленных узлах или выполнить задание на наборе узлов с конкретным атрибутом.

:::{admonition} Внимание
:class: danger

Интерфейс `IgniteCluster` тоже является группой, которая включает все узлы кластера.
:::

С помощью интерфейса `IgniteCluster` можно ограничить выполнением только на определенном наборе узлов:

- развертывание сервисов;
- выполнение заданий;
- обмен сообщениями;
- события и другие задачи.

Пример, как распространить выполнение задания только на удаленные узлы (за исключением локального):

::::{md-tab-set}
:::{md-tab-item} Java
```java
Ignite ignite = Ignition.ignite();

IgniteCluster cluster = ignite.cluster();

// Получите экземпляр вычисления, которое будет выполняться 
// только на удаленных узлах, то есть на всех узлах, кроме этого.
IgniteCompute compute = ignite.compute(cluster.forRemotes());

// Распространите на все удаленные узлы и выведите идентификатор узла,
// на котором выполняется функция.
compute.broadcast(
        () -> System.out.println("Hello Node: " + ignite.cluster().localNode().id()));
```
:::

:::{md-tab-item} C\#/.NET
```c#
class PrintNodeIdAction : IComputeAction
{
    public void Invoke()
    {
        Console.WriteLine("Hello node: " +
                          Ignition.GetIgnite().GetCluster().GetLocalNode().Id);
    }
}

public static void RemotesBroadcastDemo()
{
    var ignite = Ignition.Start();

    var cluster = ignite.GetCluster();

    // Получите экземпляр вычисления, которое будет выполняться
    // только на удаленных узлах, то есть на всех узлах, кроме этого. 
    var compute = cluster.ForRemotes().GetCompute();      

	// Распространите на все удаленные узлы и выведите идентификатор узла,
	// на котором выполняется функция.     
	compute.Broadcast(new PrintNodeIdAction());
}
```
:::

:::{md-tab-item} C++
```c++
class PrintNodeIdAction : public ComputeFunc<void> {
public:
    virtual void Call() {
        std::cout << "Hello node " <<  Ignition::Get().GetCluster().GetLocalNode().GetId() << std::endl;
    }
};
namespace ignite { namespace binary {
    template<> struct BinaryType<PrintNodeIdAction>: BinaryTypeDefaultAll<PrintNodeIdAction> {
        static void GetTypeName(std::string& dst) {
            dst = "PrintNodeIdAction";
        }
        static void Write(BinaryWriter& writer, const PrintNodeIdAction& obj) {}
        static void Read(BinaryReader& reader, PrintNodeIdAction& dst) {}
    };
}}
void void RemotesBroadcastDemo()
{
    Ignite ignite = Ignition::Get();
    IgniteCluster cluster = ignite.GetCluster();
    // Получите экземпляр вычисления, которое будет выполняться
    // только на удаленных узлах, то есть на всех узлах, кроме этого.
    Compute compute = ignite.GetCompute(cluster.AsClusterGroup().ForRemotes());
    // Распространите на все удаленные узлы и выведите идентификатор узла,
    // на котором выполняется функция.
    compute.Broadcast(PrintNodeIdAction());
}
```
:::
::::

Для удобства DataGrid поставляется с несколькими предопределенными группами кластеров:

::::{md-tab-set}
:::{md-tab-item} Java
```java
IgniteCluster cluster = ignite.cluster();

// Все узлы, на которых развернуты кеши `myCache`,
// в клиентском или серверном режиме.
ClusterGroup cacheGroup = cluster.forCacheNodes("myCache");

// Все узлы, которые отвечают за кеширование данных для `myCache`.
ClusterGroup dataGroup = cluster.forDataNodes("myCache");

// Все клиентские узлы, у которых есть доступ к `myCache`.
ClusterGroup clientGroup = cluster.forClientNodes("myCache");
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cluster = ignite.GetCluster();

// Все узлы, на которых развернуты кеши `myCache`,
// в клиентском или серверном режиме.
var cacheGroup = cluster.ForCacheNodes("myCache");

// Все узлы, которые отвечают за кеширование данных для `myCache`.
var dataGroup = cluster.ForDataNodes("myCache");

// Все клиентские узлы, у которых есть доступ к `myCache`.
var clientGroup = cluster.ForClientNodes("myCache");
```
:::

:::{md-tab-item} C++
```c++
Ignite ignite = Ignition::Get();
ClusterGroup cluster = ignite.GetCluster().AsClusterGroup();
// Все узлы, на которых развернуты кеши `myCache`,
// в клиентском или серверном режиме.
ClusterGroup cacheGroup = cluster.ForCacheNodes("myCache");
// Все узлы, которые отвечают за кеширование данных для `myCache`.
ClusterGroup dataGroup = cluster.ForDataNodes("myCache");
// Все клиентские узлы, у которых есть доступ к `myCache`.
ClusterGroup clientGroup = cluster.ForClientNodes("myCache");
```
:::
::::