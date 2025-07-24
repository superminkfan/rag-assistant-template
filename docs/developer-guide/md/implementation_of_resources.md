# Внедрение ресурсов

DataGrid позволяет внедрять внутренние ресурсы на основе полей и методов в задачу (task), задание (job), функцию (closure) или SPI, в том числе пользовательские. Ресурсы нужно внедрять до инициализации соответствующего класса.

## Внедрение на основе полей и методов

Чтобы внедрить ресурс DataGrid, в требуемом классе укажите соответствующую аннотацию в поле или методе. Тип поля или параметра метода должен соответствовать используемой аннотации — примеры указаны в разделе ниже.

Внедрение экземпляра узла DataGrid (класс `Ignite`) в пользовательский класс `IgniteCallable` c помощью указания аннотации для поля:

```bash
Ignite ignite = Ignition.ignite();

Collection<String> res = ignite.compute().broadcast(new IgniteCallable<String>() {
  // Введите экземпляр Ignite.
  @IgniteInstanceResource
  private Ignite ignite;

  @Override
  public String call() throws Exception {
    IgniteCache<Object, Object> cache = ignite.getOrCreateCache(CACHE_NAME);

    // Выполните действия с кешем.
     ...
  }
});
```

Внедрение экземпляра узла DataGrid (класс `Ignite`) в пользовательский класс `ComputeJob` с помощью указания аннотации для метода:

```bash
public class MyClusterJob implements ComputeJob {
    ...
    private Ignite ignite;
    ...
    // Введите экземпляр Ignite.
    @IgniteInstanceResource
    public void setIgnite(Ignite ignite) {
        this.ignite = ignite;
    }
    ...
}
```

## Внедряемые ресурсы DataGrid

Существует ряд ресурсов, которые соответствуют аннотациям и которые можно внедрять:

| Ресурс | Тип | Описание |
|---|---|---|
| `@CacheNameResource` | `String` | Внедряет имя кеша кластера через `CacheConfiguration.getName()` |
| `@CacheStoreSessionResource` | `CacheStoreSession` | Внедряет экземпляр текущей `CacheStoreSession` |
| `@IgniteInstanceResource` | `Ignite` | Внедряет экземпляр узла DataGrid |
| `@JobContextResource` | `ComputeJobContext` | Внедряет экземпляр `ComputeJobContext`. Контекст содержит полезную информацию о выполнении конкретного задания. Например, можно получить имя кеша, содержащего запись, для которой задача была коллоцирована |
| `@LoadBalancerResource` | `ComputeLoadBalancer` | Внедряет экземпляр `ComputeLoadBalancer`, который задача может использовать для балансировки нагрузки |
| `@ServiceResource` | Пользовательская реализация интерфейса `Service` | Внедряет сервис `Ignite` по его названию |
| `@SpringApplicationContextResource` | `ApplicationContext` | Внедряет контекст `Spring ApplicationContext` |
| `@SpringResource` | Пользовательский класс | Внедряет ресурс из контекста `Spring`. Позволяет получить доступ к bean, который указан в XML-конфигурации |
| `@TaskContinuousMapperResource` | `ComputeTaskContinuousMapper` | Внедряет ресурc от `ComputeTaskContinuousMapper`. Непрерывное отображение (маппинг) позволяет получить задание из задачи в любой момент, даже после начальной фазы `map` |
| `@TaskSessionResource` | `ComputeTaskSession` | Внедряет экземпляр ресурса `ComputeTaskSession`, который определяет распределенную сессию для выполнения конкретной задачи |