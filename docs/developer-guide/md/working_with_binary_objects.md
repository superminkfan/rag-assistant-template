# Работа с бинарными объектами

## Введение

DataGrid хранит данные в бинарном формате — подробнее о нем написано в подразделе [«Введение»](introduction.md) раздела «Моделирование данных». Данные десериализуются в объекты при каждом вызове методов кеша. Также можно работать напрямую с бинарными объектами без десериализации.

Бинарный объект — оболочка бинарного представления записи, которая хранится в кеше. У каждого бинарного объекта есть метод `field(name)`, который возвращает значение данного поля и метод `type()` — он извлекает информацию о типе объекта. Бинарные объекты полезны при работе только с некоторыми областями объектов, если их не нужно десериализовывать целиком.

Для работы с бинарными объектами не требуется определение класса. Можно динамически менять структуру объектов без перезапуска кластера.

Формат бинарного объекта универсален для всех платформ, которые поддерживает DataGrid — Java, .NET и C++. Можно запустить кластер на Java и подключить к нему клиентов на .NET или C++. При этом можно использовать бинарные объекты на этих платформах без определения классов на стороне клиента.

:::{admonition} Ограничения
:class: hint

Существует несколько ограничений, которые связаны с реализацией формата бинарного объекта:

- Тип и поля бинарного объекта определяются по их идентификаторам. Они рассчитываются как хеш-коды от строкового представления названий. Поэтому поля и типы с одинаковым хешем названия не допускаются. Можно создать пользовательскую реализацию генерации идентификаторов с помощью конфигурации.
- По этой же причине формат бинарного объекта не допускает одинаковые названия полей на разных уровнях иерархии классов.
- Если класс реализует интерфейс `Externalizable`, DataGrid использует  `OptimizedMarshaller` вместо `Binary Marshaller`. `OptimizedMarshaller` использует методы `writeExternal()` и `readExternal()` для сериализации и десериализации объектов, поэтому класс нужно добавить в classpath серверных узлов.
:::

## Включение бинарного режима для кеша

По умолчанию при запросе записи из кеша возвращаются в десериализованном формате. Чтобы работать с бинарным форматом, получите экземпляр кеша с помощью метода `withKeepBinary()`. При возможности экземпляр возвращает объекты в бинарном формате.

::::{md-tab-set}
:::{md-tab-item} Java
```java
// Создайте объект `Person` и поместите его в кеш.
Person person = new Person(1, "FirstPerson");
ignite.cache("personCache").put(1, person);

// Получите экземпляр кеша в бинарном формате.
IgniteCache<Integer, BinaryObject> binaryCache = ignite.cache("personCache").withKeepBinary();
BinaryObject binaryPerson = binaryCache.get(1);
```
:::

:::{md-tab-item} C\#/.NET
```c#
ICache<int, IBinaryObject> binaryCache = cache.WithKeepBinary<int, IBinaryObject>();
IBinaryObject binaryPerson = binaryCache[1];
string name = binaryPerson.GetField<string>("Name");

IBinaryObjectBuilder builder = binaryPerson.ToBuilder();
builder.SetField("Name", name + " - Copy");

IBinaryObject binaryPerson2 = builder.Build();
binaryCache[2] = binaryPerson2;
```
:::
::::

Не все типы объектов можно представить в бинарном формате. Классы, которые никогда не конвертируются (метод `toBinary(Object)` возвращает оригинальный объект, экземпляры классов сохраняются без изменений):

- все примитивные типы (`byte`, `int` и так далее) и их классы-оболчоки (`Byte`, `Integer` и так далее);
- массивы примитивов (`byte[]`, `int[]` и так далее​);
- `String` и их массивы;
- `UUID` и их массивы;
- `Date` и их массивы;
- `Timestamp` и их массивы;
- `Enums` и их массивы;
- отображения, коллекции и массивы объектов (если в них есть бинарные объекты, они повторно конвертируются).

## Создание и изменение бинарных объектов

Экземпляры бинарных объектов нельзя менять. Чтобы обновить поля или создать новый объект, используйте шаблон Builder бинарных объектов. Это класс, который позволяет менять поля бинарных объектов без информации об их классах.

:::{admonition} Внимание
:class: danger

Ограничения:

- Нельзя менять типы существующих полей.
- Нельзя менять порядок значений типа `enum` и добавлять новые константы в начало или середину списка значений типа `enum`. Новые константы можно добавлять только в конец списка.
:::

Пример, как получить экземпляр Builder бинарных объектов для определенного типа:

::::{md-tab-set}
:::{md-tab-item} Java
```java
BinaryObjectBuilder builder = ignite.binary().builder("org.apache.ignite.snippets.Person");

builder.setField("id", 2L);
builder.setField("name", "SecondPerson");

binaryCache.put(2, builder.build());
```
:::

:::{md-tab-item} C\#/.NET
```c#
IIgnite ignite = Ignition.Start();

IBinaryObjectBuilder builder = ignite.GetBinary().GetBuilder("Book");

IBinaryObject book = builder
.SetField("ISBN", "xyz")
.SetField("Title", "War and Peace")
.Build();
```
:::
::::

В Builders, которые созданы таким способом, нет полей. Добавить поле можно с помощью метода `setField(…​)`.

Builder бинарных объектов можно получить из существующего объекта с помощью метода `toBuilder()`. В этом случае все значения поля копируются из бинарного объекта в Builder.

Пример, как обновить объект на серверном узле без класса объекта и полной десериализации с помощью `EntryProcessor`:

:::{code-block} java
:caption: Java
// Для этого ключа нужно выполнить `EntryProcessor`.
int key = 1;
ignite.cache("personCache").<Integer, BinaryObject>withKeepBinary().invoke(key, (entry, arguments) -> {
    // Создайте Builder из старого значения.
    BinaryObjectBuilder bldr = entry.getValue().toBuilder();

    // Обновите поле в Builder.
    bldr.setField("name", "Ignite");

    // Установите новое значение для записи.
    entry.setValue(bldr.build());

    return null;
});
:::

## Бинарные типы и поля

В бинарных объектах есть информация о типе объектов, которые они представляют. Она включает названия и типы полей и названия affinity-полей.

Тип каждого поля представлен объектом `BinaryField` . После получения `BinaryField` его можно повторно использовать несколько раз, если нужно прочитать одно и то же поле из каждого объекта в коллекции. Повторное использование объекта `BinaryField` работает быстрее, чем чтение значения поля напрямую из каждого бинарного объекта.

Пример использования бинарного поля:

:::{code-block} java
:caption: Java
Collection<BinaryObject> persons = getPersons();

BinaryField salary = null;
double total = 0;
int count = 0;

for (BinaryObject person : persons) {
    if (salary == null) {
        salary = person.type().field("salary");
    }

    total += (float) salary.value(person);
    count++;
}

double avg = total / count;
:::

## Рекомендации по настройке бинарных объектов

Для каждого бинарного объекта определенного типа DataGrid сохраняет схему, в которой указаны поля объекта, их порядок и типы. Схемы реплицируются на всех узлах кластера. Бинарные объекты, в которых есть одинаковые поля в разном порядке, считаются объектами с разными схемами. Рекомендуется всегда добавлять в бинарные объекты поля  в одном и том же порядке.

Хранение поля `null` обычно занимает пять байт: четыре байта для идентификатора поля и один байт для его длины. То есть если не включать поле, расходуется меньше памяти, чем на включенное поле со значением `null`. Если не включать поле, DataGrid создаcт для этого объекта новую схему, которая будет отличаться от схемы объектов, содержащих поле. При наличии нескольких полей со значениями `null` в случайных комбинациях DataGrid создаст разные схемы бинарного объекта для каждой комбинации.

Из-за этого общий размер схем бинарных объектов в heap-памяти может стать слишком большим. Чтобы расходовать меньше памяти, используйте несколько схем для бинарных объектов с одинаковым набором полей одинаковых типов в одинаковом порядке. Выберите одну из схем при создании бинарного объекта и используйте один и тот же набор полей (даже со значением `null`). По этой же причине стоит устанавливать тип даже для поля `null`.

Также бинарные объекты можно использовать, если есть необязательное подмножество полей, в котором все поля отсутствуют или присутствуют. Можно поместить поля в отдельный бинарный объект, который хранится в поле родительского объекта или имеет значение `null`.

Большое количество необязательных полей в любых комбинациях, которые обычно имеют значение `null`, можно хранить в поле карты. Так в объекте значения будет несколько фиксированных полей и карта для описания дополнительных свойств.

## Настройка бинарных объектов

В большинстве случаев бинарные объекты не нужно настраивать. Чтобы изменить генерацию типов и идентификаторов полей или подключить пользовательский сериализатор, дополнительно настройте бинарные объекты в конфигурации.

Тип и поля бинарного объекта определяются по их идентификаторам. Они рассчитываются как хеш-коды соответствующих названий строк и хранятся в каждом объекте. В конфигурации можно сделать собственную реализацию генерации идентификаторов.

Создание идентификатора на основе названий выполняется в два этапа:

1. Название типа (класса) или поля проходит через преобразователь названий.
2. Преобразователь идентификаторов рассчитывает идентификаторы.

В конфигурации можно указать глобальный преобразователь названий, глобальный преобразователь идентификатора и глобальный сериализитор бинарных объектов, а также преобразователь и сериализатор по типам. Подстановки (wildcards) используются для конфигурации по типам. Она применяется ко всем типам, которые соответствуют шаблону названия.

::::{md-tab-set}
:::{md-tab-item} XML
```xml
<bean class="org.apache.ignite.configuration.IgniteConfiguration">

    <property name="binaryConfiguration">
        <bean class="org.apache.ignite.configuration.BinaryConfiguration">
            <property name="nameMapper" ref="globalNameMapper"/>
            <property name="idMapper" ref="globalIdMapper"/>
            <property name="typeConfigurations">
                <list>
                    <bean class="org.apache.ignite.binary.BinaryTypeConfiguration">
                        <property name="typeName" value="org.apache.ignite.examples.*"/>
                        <property name="serializer" ref="exampleSerializer"/>
                    </bean>
                </list>
            </property>
        </bean>
    </property>

</bean>
```
:::

:::{md-tab-item} Java
```java
IgniteConfiguration igniteCfg = new IgniteConfiguration();

BinaryConfiguration binaryConf = new BinaryConfiguration();
binaryConf.setNameMapper(new MyBinaryNameMapper());
binaryConf.setIdMapper(new MyBinaryIdMapper());

BinaryTypeConfiguration binaryTypeCfg = new BinaryTypeConfiguration();
binaryTypeCfg.setTypeName("org.apache.ignite.snippets.*");
binaryTypeCfg.setSerializer(new ExampleSerializer());

binaryConf.setTypeConfigurations(Collections.singleton(binaryTypeCfg));

igniteCfg.setBinaryConfiguration(binaryConf);
```
:::

:::{md-tab-item} C\#/.NET
```c#
var cfg = new IgniteConfiguration
{
    BinaryConfiguration = new BinaryConfiguration
    {
        NameMapper = new ExampleGlobalNameMapper(),
        IdMapper = new ExampleGlobalIdMapper(),
        TypeConfigurations = new[]
        {
            new BinaryTypeConfiguration
            {
                TypeName = "org.apache.ignite.examples.*",
                Serializer = new ExampleSerializer()
            }
        }
    }
};
```
:::
::::