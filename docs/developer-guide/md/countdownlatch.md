# CountDownLatch

Функциональность `IgniteCountDownLatch` похожа на `java.util.concurrent.CountDownLatch` и позволяет синхронизировать операции между узлами кластера.

::::{admonition} Пример, как создать распределенный `CountDownLatch`
:class: hint

:::{code-block} java
:caption: Java
Ignite ignite = Ignition.start();

IgniteCountDownLatch latch = ignite.countDownLatch("latchName", // Название `IgniteCountDownLatch`.
        10, // Начальный отсчет.
        false, // Автоматическое удаление, когда счетчик достигнет нуля.
        true // Создайте, если его не существует.
);
:::
::::

После выполнения кода выше все узлы в указанном кеше смогут синхронизироваться с «замком» `latchName`.

::::{admonition} Пример синхронизации
:class: hint

:::{code-block} java
:caption: Java
Ignite ignite = Ignition.start();

final IgniteCountDownLatch latch = ignite.countDownLatch("latchName", 10, false, true);

// Выполнение заданий.
for (int i = 0; i < 10; i++)
    // Выполните задание на удаленном узле кластера.
    ignite.compute().run(() -> {
        int newCnt = latch.countDown();

        System.out.println("Counted down: newCnt=" + newCnt);
    });

// Ожидайте окончания выполнения всех работ.
latch.await();
:::
::::