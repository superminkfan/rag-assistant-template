# Affinity Collocation

Если разные данные часто используются вместе, во многих случаях их полезно размещать рядом. При таком расположении сложные запросы выполняются на одном узле, на котором хранятся объекты. Этот принцип называется Affinity Collocation.

Записи распределяются по партициям при помощи affinity-функции. Объекты с одинаковыми affinity-ключами хранятся в одной партиции, поэтому при создании модели данных связанные записи можно расположить рядом. Под «связанными» имеются в виду объекты, которые находятся в отношениях «родитель-потомок» или которые часто запрашиваются вместе.

Например, есть объекты `Person` и `Company`. Каждому человеку соответствует поле `companyId` — в нем отображается компания, на которую работает человек. Если указать `Person.companyId` и `Company.ID` в качестве affinity-ключей, список сотрудников будет храниться на одном узле с данными компании. Запрос списка всех людей, которые работают в определенной компании, будет выполняться на одном узле.

Также можно располагать рядом вычислительные задачи и данные. Подробнее об этом написано в подразделе [«Коллокация вычислений с данными»](collocation_of_calculations_with_data.md) раздела «Распределенные вычисления».

## Конфигурация affinity-ключа

Если явно не указать affinity-ключ, вместо него по умолчанию будет использоваться кеш-ключ. Если создавать кеши как SQL-таблицы через SQL-запросы, affinity-ключом по умолчанию будет `PRIMARY KEY`.

Чтобы объединить данные из двух кешей по разным полям, в качестве ключа нужно использовать сложный объект. Обычно он содержит два поля: первое однозначно идентифицирует объект в данном кеше, а второе используется для объединения данных (оно называется полем affinity).

Ниже описаны способы настройки поля affinity. В примерах ниже показывается, как можно разместить рядом объекты `Person` и `Company` с помощью пользовательского класса affinity-ключа и аннотации `@AffinityKeyMapped`.

Примеры:

::::{md-tab-set}
:::{md-tab-item} Java
```java
public class AffinityCollocationExample {

    static class Person {
        private int id;
        private String companyId;
        private String name;

        public Person(int id, String companyId, String name) {
            this.id = id;
            this.companyId = companyId;
            this.name = name;
        }

        public int getId() {
            return id;
        }
    }

    static class PersonKey {
        private int id;

        @AffinityKeyMapped
        private String companyId;

        public PersonKey(int id, String companyId) {
            this.id = id;
            this.companyId = companyId;
        }
    }

    static class Company {
        private String id;
        private String name;

        public Company(String id, String name) {
            this.id = id;
            this.name = name;
        }

        public String getId() {
            return id;
        }
    }

    public void configureAffinityKeyWithAnnotation() {
        CacheConfiguration<PersonKey, Person> personCfg = new CacheConfiguration<PersonKey, Person>("persons");
        personCfg.setBackups(1);

        CacheConfiguration<String, Company> companyCfg = new CacheConfiguration<>("companies");
        companyCfg.setBackups(1);

        try (Ignite ignite = Ignition.start()) {
            IgniteCache<PersonKey, Person> personCache = ignite.getOrCreateCache(personCfg);
            IgniteCache<String, Company> companyCache = ignite.getOrCreateCache(companyCfg);

            Company c1 = new Company("company1", "My company");
            Person p1 = new Person(1, c1.getId(), "John");

            // Оба объекта p1 и c1 будут кешироваться на одном и том же узле.
            personCache.put(new PersonKey(p1.getId(), c1.getId()), p1);
            companyCache.put("company1", c1);

            // Получите объект `Person`.
            p1 = personCache.get(new PersonKey(1, "company1"));
        }
    }

}
```
:::

:::{md-tab-item} C\#/.NET
```c#
class Person
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int CityId { get; set; }
    public string CompanyId { get; set; }
}

class PersonKey
{
    public int Id { get; set; }

    [AffinityKeyMapped] public string CompanyId { get; set; }
}

class Company
{
    public string Name { get; set; }
}

class AffinityCollocation
{
    public static void Example()
    {
        var personCfg = new CacheConfiguration
        {
            Name = "persons",
            Backups = 1,
            CacheMode = CacheMode.Partitioned
        };

        var companyCfg = new CacheConfiguration
        {
            Name = "companies",
            Backups = 1,
            CacheMode = CacheMode.Partitioned
        };

        using (var ignite = Ignition.Start())
        {
            var personCache = ignite.GetOrCreateCache<PersonKey, Person>(personCfg);
            var companyCache = ignite.GetOrCreateCache<string, Company>(companyCfg);

            var person = new Person {Name = "Vasya"};

            var company = new Company {Name = "Company1"};

            personCache.Put(new PersonKey {Id = 1, CompanyId = "company1_key"}, person);
            companyCache.Put("company1_key", company);
        }
    }
}
```
:::

:::{md-tab-item} C++
```c++
struct Person
{
    int32_t id;
    std::string name;
    int32_t cityId;
    std::string companyId;
};

struct PersonKey
{
    int32_t id;
    std::string companyId;
};

struct Company
{
    std::string name;
};

namespace ignite { namespace binary {
template<> struct BinaryType<Person> : BinaryTypeDefaultAll<Person>
{
    static void GetTypeName(std::string& dst)
    {
        dst = "Person";
    }

    static void Write(BinaryWriter& writer, const Person& obj)
    {
        writer.WriteInt32("id", obj.id);
        writer.WriteString("name", obj.name);
        writer.WriteInt32("cityId", obj.cityId);
        writer.WriteString("companyId", obj.companyId);
    }

    static void Read(BinaryReader& reader, Person& dst)
    {
        dst.id = reader.ReadInt32("id");
        dst.name = reader.ReadString("name");
        dst.cityId = reader.ReadInt32("cityId");
        dst.companyId = reader.ReadString("companyId");
    }
};

template<> struct BinaryType<PersonKey> : BinaryTypeDefaultAll<PersonKey>
{
    static void GetTypeName(std::string& dst)
    {
        dst = "PersonKey";
    }

    static void GetAffinityFieldName(std::string& dst)
    {
        dst = "companyId";
    }

    static void Write(BinaryWriter& writer, const PersonKey& obj)
    {
        writer.WriteInt32("id", obj.id);
        writer.WriteString("companyId", obj.companyId);
    }

    static void Read(BinaryReader& reader, PersonKey& dst)
    {
        dst.id = reader.ReadInt32("id");
        dst.companyId = reader.ReadString("companyId");
    }
};

template<> struct BinaryType<Company> : BinaryTypeDefaultAll<Company>
{
    static void GetTypeName(std::string& dst)
    {
        dst = "Company";
    }

    static void Write(BinaryWriter& writer, const Company& obj)
    {
        writer.WriteString("name", obj.name);
    }

    static void Read(BinaryReader& reader, Company& dst)
    {
        dst.name = reader.ReadString("name");
    }
};
}};  // namespace ignite::binary

int main()
{
    using namespace ignite;
    using namespace cache;

    IgniteConfiguration cfg;
    Ignite ignite = Ignition::Start(cfg);

    Cache<PersonKey, Person> personCache = ignite.GetOrCreateCache<PersonKey, Person>("person");
    Cache<std::string, Company> companyCache = ignite.GetOrCreateCache<std::string, Company>("company");

    Person person{};
    person.name = "Vasya";

    Company company{};
    company.name = "Company1";

    personCache.Put(PersonKey{1, "company1_key"}, person);
    companyCache.Put("company1_key", company);

    return 0;
}
```
:::

:::{md-tab-item} SQL
```sql
CREATE TABLE IF NOT EXISTS Person (
  id int,
  city_id int,
  name varchar,
  company_id varchar,
  PRIMARY KEY (id, city_id)
) WITH "template=partitioned,backups=1,affinity_key=company_id";

CREATE TABLE IF NOT EXISTS Company (
  id int,
  name varchar,
  PRIMARY KEY (id)
) WITH "template=partitioned,backups=1";
```
:::
::::

Можно настроить affinity-ключ в конфигурации кешей через класс `CacheKeyConfiguration`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
public void configureAffinityKeyWithCacheKeyConfiguration() {
    CacheConfiguration<PersonKey, Person> personCfg = new CacheConfiguration<PersonKey, Person>("persons");
    personCfg.setBackups(1);

    // Настройте affinity-ключ.
    personCfg.setKeyConfiguration(new CacheKeyConfiguration("Person", "companyId"));

    CacheConfiguration<String, Company> companyCfg = new CacheConfiguration<String, Company>("companies");
    companyCfg.setBackups(1);

    Ignite ignite = Ignition.start();

    IgniteCache<PersonKey, Person> personCache = ignite.getOrCreateCache(personCfg);
    IgniteCache<String, Company> companyCache = ignite.getOrCreateCache(companyCfg);

    Company c1 = new Company("company1", "My company");
    Person p1 = new Person(1, c1.getId(), "John");

    // Оба объекта p1 и c1 будут кешироваться на одном и том же узле.
    personCache.put(new PersonKey(1, c1.getId()), p1);
    companyCache.put(c1.getId(), c1);

    // Получите объект `Person`.
    p1 = personCache.get(new PersonKey(1, "company1"));
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var personCfg = new CacheConfiguration("persons")
{
    KeyConfiguration = new[]
    {
        new CacheKeyConfiguration
        {
            TypeName = nameof(Person),
            AffinityKeyFieldName = nameof(Person.CompanyId)
        }
    }
};

var companyCfg = new CacheConfiguration("companies");

IIgnite ignite = Ignition.Start();

ICache<PersonKey, Person> personCache = ignite.GetOrCreateCache<PersonKey, Person>(personCfg);
ICache<string, Company> companyCache = ignite.GetOrCreateCache<string, Company>(companyCfg);

var companyId = "company_1";
Company c1 = new Company {Name = "My company"};
Person p1 = new Person {Id = 1, Name = "John", CompanyId = companyId};

// Оба объекта p1 и c1 будут кешироваться на одном и том же узле.
personCache.Put(new PersonKey {Id = 1, CompanyId = companyId}, p1);
companyCache.Put(companyId, c1);

// Получите объект `Person`.
p1 = personCache.Get(new PersonKey {Id = 1, CompanyId = companyId});
```
:::
::::

Вместо пользовательского класса для ключа можно использовать класс `AffinityKey`:

::::{md-tab-set}
:::{md-tab-item} Java
```java
public void configureAffinitKeyWithAffinityKeyClass() {
    CacheConfiguration<AffinityKey<Integer>, Person> personCfg = new CacheConfiguration<AffinityKey<Integer>, Person>(
    "persons");
    personCfg.setBackups(1);

    CacheConfiguration<String, Company> companyCfg = new CacheConfiguration<String, Company>("companies");
    companyCfg.setBackups(1);

    Ignite ignite = Ignition.start();

    IgniteCache<AffinityKey<Integer>, Person> personCache = ignite.getOrCreateCache(personCfg);
    IgniteCache<String, Company> companyCache = ignite.getOrCreateCache(companyCfg);

    Company c1 = new Company("company1", "My company");
    Person p1 = new Person(1, c1.getId(), "John");

    // Оба объекта p1 и c1 будут кешироваться на одном и том же узле.
    personCache.put(new AffinityKey<Integer>(p1.getId(), c1.getId()), p1);
    companyCache.put(c1.getId(), c1);

    // Получите объект `Person`.
    p1 = personCache.get(new AffinityKey(1, "company1"));
}
```
:::

:::{md-tab-item} C\#/.NET
```c#
var personCfg = new CacheConfiguration("persons");
var companyCfg = new CacheConfiguration("companies");

IIgnite ignite = Ignition.Start();

ICache<AffinityKey, Person> personCache = ignite.GetOrCreateCache<AffinityKey, Person>(personCfg);
ICache<string, Company> companyCache = ignite.GetOrCreateCache<string, Company>(companyCfg);

var companyId = "company_1";
Company c1 = new Company {Name = "My company"};
Person p1 = new Person {Id = 1, Name = "John", CompanyId = companyId};

// Оба объекта p1 и c1 будут кешироваться на одном и том же узле.
personCache.Put(new AffinityKey(1, companyId), p1);
companyCache.Put(companyId, c1);

// Получите объект `Person`.
p1 = personCache.Get(new AffinityKey(1, companyId));
```
:::
::::