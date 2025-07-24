# Атомарные типы

DataGrid поддерживает распределенный атомарный тип `long` и атомарные ссылки по аналогии с `java.util.concurrent.atomic.AtomicLong` и `java.util.concurrent.atomic.AtomicReference` соответственно.

Атомарные классы в DataGrid распределяются по кластеру и позволяют выполнять атомарные операции с одинаковым глобально видимым значением, например «увеличить и получить» (`increment-and-get`) и «сравнить и установить» (`compare-and-set`). Таким образом можно обновить значение атомарного типа `long` на одном узле и прочитать его с другого.

Функциональные возможности:

- получить текущее значение;
- атомарно изменить текущее значение;
- атомарно увеличить или уменьшить текущее значение на `1`;
- атомарно сравнить и установить текущее значение в качестве нового.

Распределенный атомарный тип `long` и атомарные ссылки можно получить с помощью интерфейсов `IgniteAtomicLong` и `IgniteAtomicReference` соответственно, как показано в примерах:

- Интерфейс `IgniteAtomicLong`:

  :::{code-block} java
  :caption: Java
  Ignite ignite = Ignition.start();

  IgniteAtomicLong atomicLong = ignite.atomicLong("atomicName", // Название атомарного типа `long`.
          0, // Начальное значение.
          true // Создайте, если его не существует.
  );

  // Увеличьте значение атомарного типа `long` на локальном узле.
  System.out.println("Incremented value: " + atomicLong.incrementAndGet());
  :::

- Интерфейс `IgniteAtomicReference`:

  :::{code-block} java
  :caption: Java
  Ignite ignite = Ignition.start();

  // Создайте `AtomicReference`.
  IgniteAtomicReference<String> ref = ignite.atomicReference("refName", // Название ссылки.
          "someVal", // Начальное значение для атомарной ссылки.
          true // Создайте, если его не существует.
  );

  // Сравните и обновите значение
  ref.compareAndSet("WRONG EXPECTED VALUE", "someNewVal"); // Не изменится.
  :::

Все атомарные операции, которые представлены `IgniteAtomicLong` и `IgniteAtomicReference`, являются синхронными. Время выполнения атомарной операции зависит от:

- количества узлов, которые выполняют параллельные операции с одним и тем же экземпляром атомарного `long`;
- интенсивности операций;
- задержек сети.

## Настройки атомарности

Чтобы настроить атомарные классы в DataGrid, установите свойство `atomicConfiguration` в `IgniteConfiguration`.

Доступные параметры настройки:

| Setter | Описание | Значение по умолчанию |
|---|---|---|
| `setBackups(int)` | Устанавливает количество резервных копий | `1` |
| `setCacheMode(CacheMode)` | Устанавливает режим кеша для всех атомарных типов: `PARTITIONED` или `REPLICATED` | `PARTITIONED` |
| `setAtomicSequenceReserveSize(int)` | Устанавливает количество значений последовательности, которые зарезервированы для экземпляров `IgniteAtomicSequence` | `1000` |