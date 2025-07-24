# Binary Marshaller

## Основные понятия

`Binary Marshaller` — компонент DataGrid, который отвечает за сериализацию данных и может:

- Читать произвольное поле из сериализованного объекта без его полной десериализации. Это полностью устраняет необходимость добавлять классы ключа и значения в classpath серверного узла.
- Добавлять или удалять поля из объектов одного типа. На серверных узлах нет определений классов моделей, и эта возможность позволяет динамически менять структуру объекта и одновременно существовать нескольким клиентам с разными версиями определений классов.
- Создавать новые объекты на основе названия типа без определений классов. Это обеспечивает динамическое создание типа.

Бинарные объекты можно использовать, если в конфигурации установлен `marshaller` по умолчанию и не установлены другие.

В фасаде `IgniteBinary` есть все методы, которые нужны для работы с бинарными объектами.

### Ограничения

Существует несколько ограничений, связанных с реализацией формата `BinaryObject`:

- Для идентификации полей и типов вместо их названий используются хеши названий в нижнем регистре. Поля или типы с одинаковыми хешами названий не допускаются. В случае коллизий по хешам сериализация не будет работать, но в DataGrid есть способ решения проблемы с помощью конфигурации.
- Формат `BinaryObject` не допускает использование одинаковых названий полей на разных уровнях иерархии класса.
- Если класс реализует интерфейс `Externalizable`, DataGrid будет использовать `OptimizedMarshaller` вместо `Binary Marshaller`. `OptimizedMarshaller` использует методы `writeExternal()` и `readExternal()` для сериализации и десериализации объектов класса, поэтому в classpath серверных узлов нужно добавить классы объектов `Externalizable`.

### Автоматический расчет хеш-кода и реализация метода Equals

Если объект можно сериализовать в бинарную форму, DataGrid вычислит его хеш-код во время сериализации и запишет в получившийся бинарный массив. В DataGrid есть собственная реализация метода `equals` для сравнения бинарных объектов.

Если пользовательские классы данных можно сериализовать в бинарную форму, их можно использовать в DataGrid без переопределения методов `GetHashCode` и `Equals`. Например, объекты типа `Externalizable` нельзя сериализовать в бинарную форму — они требуют ручной реализации методов `equals` и `hashCode`. Подробнее о других ограничениях написано в разделе выше.

## Настройка бинарных объектов

В большинстве случаев нет необходимости дополнительно настраивать бинарные объекты.

Конфигурация понадобится при переопределении типов и расчетов идентификаторов полей по умолчанию или при дополнительном подключения `BinarySerializer`. В этом случае нужно прописать объект `BinaryConfiguration` в `IgniteConfiguration`. Для этого укажите:

- глобальный mapper имен;
- глобальный mapper идентификаторов;
- глобальный binary serializer;
- mappers и serializers для каждого типа.

Если указать шаблон (wildcard), конфигурация применится ко всем подходящим под него типам.

:::{code-block} xml
:caption: XML
<bean id="ignite.cfg" class="org.apache.ignite.configuration.IgniteConfiguration">

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
:::

## BinaryObject API

По умолчанию API DataGrid работает с десериализованными значениями (то есть с пользовательскими классами данных), так как они используются чаще всего. Для работы с `BinaryObject` получите экземпляр кеша с помощью метода `withKeepBinary()`. В таком случае объекты, которые возвращаются из кеша, будут в формате `BinaryObject` всегда, когда это возможно. Это относится и к значениям, которые передаются в `EntryProcessor` и `CacheInterceptor`.

:::{admonition} Важно
:class: attention

Не все типы объектов будут представлены в качестве `BinaryObject` при использовании метода `withKeepBinary()`. Некоторые платформенные типы — `String`, `UUID`, `Date`, `Timestamp`, `BigDecimal`, `Collections`, `Maps` и их массивы — никогда не будут `BinaryObject`.
:::

В примере ниже тип ключа `Integer` не меняется, так как это платформенный тип.

:::{code-block} java
:caption: Java
// Создайте стандартный объект `Person` и поместите его в кеш.
Person person = buildPerson(personId);
ignite.cache("myCache").put(personId, person);

// Получите экземпляр бинарного кеша.
IgniteCache<Integer, BinaryObject> binaryCache = ignite.cache("myCache").withKeepBinary();

// Получите указанный выше объект `Person` в формате `BinaryObject`.
BinaryObject binaryPerson = binaryCache.get(personId);
:::

## Изменение бинарных объектов с помощью BinaryObjectBuilder

Экземпляры `BinaryObject` нельзя изменить. Чтобы обновить поля и создать новый бинарный объект, используйте `BinaryObjectBuilder`.

Получить экземпляр `BinaryObjectBuilder` можно из фасада `IgniteBinary`. Чтобы создать `BinaryObjectBuilder`:

- укажите название типа — вернувшийся конструктор (builder) не будет содержать полей;
- используйте существующий `BinaryObject` — конструктор будет содержать копии всех полей указанного `BinaryObject`;
- вызовите метод `toBuilder()` на существующем экземпляре `BinaryObject` — в `BinaryObjectBuilder` скопируются все данные из `BinaryObject`.

:::{admonition} Примечание
:class: note

Ограничения:

- Типы существующих полей нельзя изменить.
- Нельзя изменить порядок значений перечисляемого типа (`enum`) и добавить новые значения в начало или середину списка. Новые значения можно добавлять только в конец списка.
:::

Пример, как использовать API `BinaryObject` для доступа к данным на серверных узлах без размещения пользовательских классов на серверах и без десериализации данных:

:::{code-block} java
:caption: Java
// Для этого ключа должен быть выполнен `EntryProcessor`.
int key = 101;

cache.<Integer, BinaryObject>withKeepBinary().invoke(
  key, new CacheEntryProcessor<Integer, BinaryObject, Object>() {
    public Object process(MutableEntry<Integer, BinaryObject> entry,
                          Object... objects) throws EntryProcessorException {
            // Создайте конструктор на основе старого значения.
        BinaryObjectBuilder bldr = entry.getValue().toBuilder();

        // Обновите поле в конструкторе.
        bldr.setField("name", "Ignite");

        // Установите новое значение для записи.
        entry.setValue(bldr.build());

        return null;
     }
  });
:::

## Тип метаданных BinaryObject

Интерфейс `BinaryType` позволяет получать информацию о конкретном типе, который хранится в кеше, например о названиях полей, названиях типов полей и названии поля affinity. Это возможно благодаря тому, что структуру бинарного объекта можно менять во время выполнения.

Интерфейс `BinaryType` также предоставляет более быструю возможность получения поля через `BinaryField`. Интерфейс похож на Java Reflection: он позволяет кешировать определенную информацию о считываемом поле в экземпляре `BinaryField`. Это может пригодиться при прочтении одного и того же поля в большой коллекции бинарных объектов.

:::{code-block} java
:caption: Java
Collection<BinaryObject> persons = getPersons();

BinaryField salary = null;

double total = 0;
int cnt = 0;

for (BinaryObject person : persons) {
    if (salary == null)
        salary = person.type().field("salary");

    total += salary.value(person);
    cnt++;
}

double avg = total / cnt;
:::

## BinaryObject и CacheStore API

Установка `withKeepBinary()` в API кеша не влияет на способ передачи пользовательских объектов в `CacheStore`. Это сделано намеренно, так как в большинстве случаев одна реализация `CacheStore` работает или с десериализованными классами, или с представлениями `BinaryObject`. Чтобы управлять способом передачи объектов в `CacheStore`, используйте флаг `storeKeepBinary` в `CacheConfiguration`. Если у флага установлено значение `false`, в `CacheStore` передадутся десериализованные значения; если `true` — будут использоваться представления `BinaryObject`.

Пример псевдокода реализации `CacheStore`, который работает с `BinaryObject`:

:::{code-block} java
:caption: Java
public class CacheExampleBinaryStore extends CacheStoreAdapter<Integer, BinaryObject> {
    @IgniteInstanceResource
    private Ignite ignite;

    /** {@inheritDoc} */
    @Override public BinaryObject load(Integer key) {
        IgniteBinary binary = ignite.binary();

        List<?> rs = loadRow(key);

        BinaryObjectBuilder bldr = binary.builder("Person");

        for (int i = 0; i < rs.size(); i++)
            bldr.setField(name(i), rs.get(i));

        return bldr.build();
    }

    /** {@inheritDoc} */
    @Override public void write(Cache.Entry<? extends Integer, ? extends BinaryObject> entry) {
        BinaryObject obj = entry.getValue();

        BinaryType type = obj.type();

        Collection<String> fields = type.fieldNames();

        List<Object> row = new ArrayList<>(fields.size());

        for (String fieldName : fields)
            row.add(obj.field(fieldName));

        saveRow(entry.getKey(), row);
    }
}
:::

## Binary Name Mapper и Binary ID Mapper

DataGrid никогда не записывает полные строки для названий полей или типов. Вместо строк для повышения производительности DataGrid записывает целочисленные хеш-коды. Результаты тестирования показали, что конфликтов хеш-кодов для названий типов или полей в пределах одного типа практически не существует, поэтому для повышения производительности можно работать с хеш-кодами. Если конфликт все же возник, DataGrid поддерживает возможность переопределения автоматически сгенерированных идентификаторов хеш-кодов для названий типов или полей через `BinaryNameMapper` и `BinaryIdMapper`.

Реализации mappers в DataGrid:

- `BinaryBasicNameMapper` — базовая реализация `BinaryNameMapper`, которая возвращает полное или простое название класса в зависимости от того, установлен ли `setSimpleName(boolean useSimpleName)`.
- `BinaryBasicIdMapper` — базовая реализация ` BinaryIdMapper`, в которой есть свойство конфигурации `setLowerCase(boolean isLowerCase)`. Если `isLowerCase` равен `false`, вернется хеш-код типа или названия поля. Если `isLowerCase` равен `true`, вернется хеш-код заданного типа или названия поля в нижнем регистре.

Если использовать клиенты на Java или .NET и не указывать mappers в `BinaryConfiguration`, DataGrid будет применять `BinaryBasicNameMapper` (`simpleName` равен `false`) и `BinaryBasicIdMapper` (`lowerCase` равен `true`).

Если использовать клиенты на С++ и не указывать mappers в `BinaryConfiguration`, DataGrid будет применять `BinaryBasicNameMapper` (`simpleName` равен `true`) и `BinaryBasicIdMapper` (`lowerCase` равен `true`).

Если используется Java, .NET или C++, по умолчанию дополнительная конфигурация mappers не нужна. Она понадобится, если возникнет сложное преобразование названий при взаимодействии платформ.