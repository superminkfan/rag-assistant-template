# Сервис Executor

В DataGrid есть распределенная реализация `java.util.concurrent.ExecutorService`, которая отправляет задачи для выполнения на серверные узлы кластера. Задачи распределяются по нагрузке между узлам кластера. Они гарантированно выполнятся, если в кластере есть хотя бы один узел.

Сервис `Executor` можно получить из экземпляра `Ignite`:

```bash
// Получите сервис `Executor` с поддержкой кластера.
ExecutorService exec = ignite.executorService();

// Выполните итерацию по всем словам предложения и создайте задачи.
for (final String word : "Print words using runnable".split(" ")) {
    // Запустите поток выполнения на узле.
    exec.submit(new IgniteRunnable() {
        @Override
        public void run() {
            System.out.println(">>> Printing '" + word + "' on this node from grid job.");
        }
    });
}
```

Чтобы ограничить набор узлов, которые доступны сервису `Executor`, укажите группу кластеров (подробнее об этом написано в разделе [«Группы кластеров»](cluster_groups.md)):

```bash
// Группа для узлов, в которых определен атрибут `worker`.
ClusterGroup workerGrp = ignite.cluster().forAttribute("ROLE", "worker");

// Получите сервис `Executor` для группы кластеров.
ExecutorService exec = ignite.executorService(workerGrp);
```