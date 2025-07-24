# Справочник по REST API

## Версия

Возвращает версию DataGrid.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=version
```
:::

:::{md-tab-item} Ответ
```bash
{
	"successStatus": 0,
	"error": null,
	"sessionToken": null,
	"response": "16.0.0",
	"securitySubjectId": null
}
```
:::
::::

## Состояние кластера

Возвращает текущее состояние кластера — подробнее о нем написано в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/monitoring-metrics/cluster-states).

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=state
```
:::

:::{md-tab-item} Ответ

Возвращает состояние кластера.

```bash
{
	"successStatus": 0,
	"sessionToken": null,
	"securitySubjectId": null,
	"response": "ACTIVE",
	"error": null
}
```
:::
::::

## Изменение состояния кластера

Команда `setstate` изменяет состояние кластера — подробнее о нем написано в [официальной документации Apache Ignite](https://ignite.apache.org/docs/latest/monitoring-metrics/cluster-states).

::::::{md-tab-set}
:::::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=setstate&state=ACTIVE_READ_ONLY
```

::::{list-table}
:header-rows: 1
 
+   *   Параметр
    *   Тип
    *   Описание
+   *   `state`
    *   `string`
    *   Новое состояние кластера. Принимает одно из значений:
        - `ACTIVE` — активное состояние;
        - `ACTIVE_READ_ONLY` — состояние только для чтения;
        - `INACTIVE` — кластер деактивирован
::::

:::{admonition} Внимание
:class: danger

Деактивация освобождает все ресурсы памяти, включая данные приложения, на всех узлах кластера и отключает публичный API кластера. Если есть in-memory-кеши, для которых нет резервных копий в постоянном хранилище (ни в хранилище Native Persistence, ни во внешнем), при деактивации данные потеряются и нужно будет заново заполнить кеши. Неперсистентные системные кеши также очищаются.

Подробнее о постоянном хранилище написано в подразделах [«Персистентность DataGrid»](../../developer-guide/md/datagrid_persistence.md) и [«Внешнее хранение»](../../developer-guide/md/external_storage.md) раздела «Настройка Persistence» документа «Руководство прикладного разработчика».
:::
:::::

:::::{md-tab-item} Ответ
```bash
{
	"successStatus": 0,
	"sessionToken": null,
	"securitySubjectId": null,
	"response": "setstate done",
	"error": null
}
```
:::::
::::::

## Инкремент

Прибавляет и получает текущее значение заданной переменной атомарного типа `long`.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=incr&cacheName=partitionedCache&key=1&init=15&delta=42
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Название переменной атомарного типа `long` | `1` |
| `init` | `long` | Да | Начальное значение | `15` |
| `delta` | `long` | — | Число для добавления | `42` |

:::

:::{md-tab-item} Ответ

Ответ включает значение после операции.

```bash
{
  "affinityNodeId": "e05839d5-6648-43e7-a23b-78d7db9390d5",
  "error": "",
  "response": 42,
  "successStatus": 0
}
```
:::
::::

## Декремент

Вычитает и получает текущее значение заданной переменной атомарного типа `long`.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=incr&cacheName=initCache&key=1&init=2&delta=1 
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Название переменной атомарного типа `long` | `1` |
| `init` | `long` | Да | Начальное значение | `15` |
| `delta` | `long` | — | Число для вычитания | `42` |

:::

:::{md-tab-item} Ответ

Ответ включает значение после операции.

```bash
{
	"successStatus": 0,
	"error": null,
	"securitySubjectId": null,
	"sessionToken": null,
	"response": 3
}
```
:::
::::

## Метрики кеша

Показывает метрики для кеша.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=cache&cacheName=partitionedCache&destId=e05839d5-6648-43e7-a23b-78d7db9390d5
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
	"successStatus": 0,
	"affinityNodeId": null,
	"error": null,
	"securitySubjectId": null,
	"sessionToken": null,
	"response": {
		"reads": 0,
		"writes": 2,
		"hits": 0,
		"misses": 0
	}
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `jsonObject` | Объект JSON содержит метрики кеша, например время создания, число прочтений и так далее | `{ "createTime": 1415179251551, "hits": 0, "misses": 0, "readTime":1415179251551, "reads": 0,"writeTime": 1415179252198, "writes": 2 }` |

:::
::::


## Размер кеша

Получает число всех записей, которые находятся в кеше на всех узлах.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=size&cacheName=partitionedCache
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |

:::

:::{md-tab-item} Ответ
```bash
{
	"successStatus": 0,
	"affinityNodeId": null,
	"error": null,
	"securitySubjectId": null,
	"sessionToken": null,
	"response": 40
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `number` | Получает число всех записей, которые находятся в кеше на всех узлах | `40` |

:::
::::

## Метаданные кеша

Получает метаданные кеша.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=metadata&cacheName=partitionedCache
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, возвращаются метаданные для всех кешей пользователя | `partitionedCache` |

:::

:::{md-tab-item} Ответ
```bash
{
  "error": "",
  "response": {
    "cacheName": "partitionedCache",
    "types": [
      "Person"
    ],
    "keyClasses": {
      "Person": "java.lang.Integer"
    },
    "valClasses": {
      "Person": "org.apache.ignite.Person"
    },
    "fields": {
      "Person": {
        "_KEY": "java.lang.Integer",
        "_VAL": "org.apache.ignite.Person",
        "ID": "java.lang.Integer",
        "FIRSTNAME": "java.lang.String",
        "LASTNAME": "java.lang.String",
        "SALARY": "double"
      }
    },
    "indexes": {
      "Person": [
        {
          "name": "ID_IDX",
          "fields": [
            "id"
          ],
          "descendings": [],
          "unique": false
        },
        {
          "name": "SALARY_IDX",
          "fields": [
            "salary"
          ],
          "descendings": [],
          "unique": false
        }
      ]
    }
  },
  "sessionToken": "",
  "successStatus": 0
}
```
:::
::::

## Compare-And-Swap

Сохраняет данную пару «ключ-значение» в кеше, только если предыдущее значение равно переданному ожидаемому значению.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=cas&key=casKey&val=Jack&val2=Bob&cacheName=partitionedCache&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Значение, которое связано с указанным ключом | `Jack` |
| `val2` | `string` | — | Ожидаемое значение | `Bob` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ

Если была замена значения, возвращает `true`; в противном случае возвращает `false`.

```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```
:::
::::

## Append 

Присоединяет строку для значения, которое связано с ключом.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=append&key=name&val=_Jack&cacheName=partitionedCache&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Значение, которое присоединится к текущему | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если замена произошла — `true`, в противном случае — `false` | `true` |

:::
::::

## Prepend

Добавляет префикс к значению, которое связано с ключом.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=prepend&key={key}&val={value}&cacheName=myCache&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `myCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Строковое значение, которое будет добавлено к текущему | `Name_` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если замена произошла — `true`, в противном случае — `false` | `true` |

:::
::::

## Replace

Сохраняет заданную пару «ключ-значение» в кеше, если в нем уже есть ключ.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=rep&key=repKey&val=newValue&cacheName=partitionedCache&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Значение, которое связано с указанным ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
| `exp` | `long` | Да | Срок действия записи (в мс). С установленным параметром операция выполняется с `ModifiedExpiryPolicy` — подробнее написано в подразделе [«Политика устаревания записей (Expiry Policy)»](../../developer-guide/md/expiry_policy.md) раздела «Настройка кешей» документа «Руководство прикладного разработчика» | `60000` |

:::

:::{md-tab-item} Ответ

Если была замена значения, ответ содержит `true`; в противном случае — `false`.

```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```
:::
::::

## Get

Получение из кеша значения, которое сопоставлено с указанным ключом.

**Запрос:**

```bash
http://localhost:8080/ignite?cmd=get&key={getKey}&cacheName=partitionedCache&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, чье сопоставимое значение должно быть возвращено | `testKey` |
| `keyType` | `Java built-in type` | Да | Подробнее написано в подразделе «Типы данных» раздела [REST API](../../developer-guide/md/rest_api.md) документа «Руководство прикладного разработчика» | — |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

## Get All

Извлекает из заданного кеша значения, которые сопоставлены с указанными ключами.

:::::{md-tab-set}
::::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getall&k1={getKey1}&k2={getKey2}&k3={getKey3}&cacheName=partitionedCache&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `k1…kN` | `string` | — | Ключ, чьи сопоставимые значения должны быть возвращены | `key1, key2, …, keyN` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
::::

::::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "",
  "error": "",
  "response": {
    "key1": "value1",
    "key2": "value2"
  },
  "successStatus": 0
}
```

:::{admonition} Получить вывод в виде массива
:class: hint

Чтобы получить вывод в виде массива, используйте системное свойство `IGNITE_REST_GETALL_AS_ARRAY=true`. После установки значения свойства команда `getall` дает ответ в формате:

```bash
{“successStatus”:0,“affinityNodeId”:null,“error”:null,“sessionToken”:null,“response”:[{“key”:“key1”,“value”:“value1”},{“key”:“key2”,“value”:“value2”}]}
```
:::

::::
:::::

## Get and Remove

Удаляет данное сопоставление ключей из кеша и возвращает предыдущее значение.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getrmv&cacheName=partitionedCache&destId={nodeId}&key={key}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, чьи сопоставимые значения должны быть возвращены | `name` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | — |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": value,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `jsonObject` | Значение для ключа | `{"name": "Bob"}` |

:::
::::

## Get and Put

Хранение полученной пары «ключ-значение» в кеше и возвращение существующего значения, если оно есть.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getput&key=getKey&val=newVal&cacheName=partitionedCache
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, который связан со значением | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ

Ответ содержит предыдущее значение для ключа.

```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": {"name": "bob"},
  "successStatus": 0
}
```
:::
::::

## Get and Put if Absent

Сохраняет данную пару «ключ-значение» в кеше, только если в нем не было предыдущего сопоставления для пары. Если в кеше ранее было значение для данного ключа, вернется оно.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getputifabs&key=getKey&val=newVal&cacheName={cacheName}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, который связан со значением | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": "value",
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `jsonObject` | Предыдущее значение для данного ключа | `{"name": "Bob"}` |

:::
::::

## Get and Replace

Хранение данной пары «ключ-значение» в кеше, если для нее есть предыдущее сопоставление.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getrep&key={key}&val={val}&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ

Ответ содержит предыдущее значение, которое связано с указанным ключом.

```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": oldValue,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `jsonObject` | Предыдущее значение, которое связано с указанным ключом | `{"name": "Bob"}` |

:::
::::

## Replace Value

Заменяет запись для ключа, только если в данный момент он сопоставлен с данным значением.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=repval&key={key}&val={newValue}&val2={oldVal}&cacheName={cacheName}&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ для хранения в кеше | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `val2` | `string` | — | Ожидаемое значение, которое будет связано с указанным ключом | `oldValue` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если замена произошла — `true`, в противном случае — `false` | `true` |

:::
::::

## Remove

Удаляет данное сопоставление ключей из кеша.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=rmv&key={rmvKey}&cacheName={cacheName}&destId=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, для которого из кеша должно быть удалено сопоставление «ключ-значение» | `name` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если замена произошла — `true`, в противном случае — `false` | `true` |

:::
::::

## Remove All

Удаляет из кеша указанные сопоставления для ключа.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=rmvall&k1={rmKey1}&k2={rmKey2}&k3={rmKey3}&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `k1…kN` | `string` | — | Ключ, для которого из кеша должны быть удалены сопоставления «ключ-значение» | `name` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если замена произошла — `true`, в противном случае — `false` | `true` |

:::
::::

## Remove Value

Удаляет значение для ключа, если сейчас с ним сопоставляется это значение.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=rmvval&key={rmvKey}&val={rmvVal}&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ с сопоставленным значением, которое удалится из кеша | `name` |
| `val` | `string` | — | Ожидаемое значение, которое будет связано с указанным ключом  | `oldValue` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | `false`, если нет сопоставимого ключа | `true` |

:::
::::

## Add

Сохраняет пару «ключ-значение» в кеше, если в нем нет такого ключа.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=add&key=newKey&val=newValue&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, который связан со значением | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
| `exp` | `long` | Да | Срок действия записи (в мс). С установленным параметром операция выполняется с `ModifiedExpiryPolicy`. Подробнее написано в подразделе [«Политика устаревания записей (Expiry Policy)»](../../developer-guide/md/expiry_policy.md) раздела «Настройка кешей» документа «Руководство прикладного разработчика» | `60000` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если значение хранилось в кеше — `true`, в противном случае — `false` | `true` |

:::
::::


## Put

Сохраняет в кеше указанную пару «ключ-значение».

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=put&key=newKey&val=newValue&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, который связан со значениями | `name` |
| `val` | `string` | — | Значение, которое связано с ключами | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
| `exp` | `long` | Да | Срок действия записи (в мс). С установленным параметром операция выполняется с `ModifiedExpiryPolicy`. Подробнее написано в подразделе [«Политика устаревания записей (Expiry Policy)»](../../developer-guide/md/expiry_policy.md) раздела «Настройка кешей» документа «Руководство прикладного разработчика» | `60000` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если значение хранилось в кеше — `true`, в противном случае — `false` | `true` |

:::
::::

## Put all

Сохраняет указанную пару «ключ-значение» в кеше.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=putall&k1={putKey1}&k2={putKey2}&k3={putKey3}&v1={value1}&v2={value2}&v3={value3}&cacheName={cacheName}&destId={nodeId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `k1…kN` | `string` | — | Ключи, которые связаны со значениями | `name` |
| `v1…vN` | `string` | — | Значения, которые связаны с ключами | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | Если значения хранились в кеше — `true`, в противном случае — `false` | `true` |

:::
::::


## Put If Absent

Сохраняет указанную пару «ключ-значение» в кеше, если в нем нет данного ключа.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=putifabs&key={getKey}&val={newVal}&cacheName={cacheName}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, который связан со значением | `name` |
| `val` | `string` | — | Значение, которое связано с ключом | `Jack` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
| `exp` | `long` | Да | Срок действия записи (в мс). С установленным параметром операция выполняется с `ModifiedExpiryPolicy` — подробнее написано в подразделе [«Политика устаревания записей (Expiry Policy)»](../../developer-guide/md/expiry_policy.md) раздела «Настройка кешей» документа «Руководство прикладного разработчика» | `60000` |

:::

:::{md-tab-item} Ответ

В поле будет `true`, если запись была помещена в кеш, и `false` в противном случае.

```bash
{
  "affinityNodeId": "2bd7b049-3fa0-4c44-9a6d-b5c7a597ce37",
  "error": "",
  "response": true,
  "successStatus": 0
}
```
:::
::::

## Contains Key

Определяет, содержит ли кеш какие-либо записи для указанных ключей.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=conkey&key={getKey}&cacheName={cacheName}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `key` | `string` | — | Ключ, наличие которого в кеше проверяется при запросе | `testKey` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "2bd7b049-3fa0-4c44-9a6d-b5c7a597ce37",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | `true`, если отображение содержит сопоставление «ключ-значение» для указанного ключа | `true` |

:::
::::

## Contains keys

Определяет, содержит ли кеш какие-либо записи для указанных ключей.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=conkeys&k1={getKey1}&k2={getKey2}&cacheName={cacheName}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |
| `k1…kN` | `string` | — | Ключ, наличие которого в кеше проверяется при запросе | `key1, key2, …, keyN` |
| `destId` | `string` | Да | Идентификатор узла, для которого возвращаются метрики | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
  "affinityNodeId": "2bd7b049-3fa0-4c44-9a6d-b5c7a597ce37",
  "error": "",
  "response": true,
  "successStatus": 0
}
```

| Поле | Тип | Описание | Пример |
|---|---|---|---|
| `response` | `boolean` | `true`, если отображение содержит сопоставление «ключ-значение» для указанного ключа | `true` |

:::
::::

## Get or Create Cache

Создает кеш с указанным названием, если такого кеша еще нет.

:::::{md-tab-set}
::::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=getorcreate&cacheName={cacheName}
```

:::{list-table}
:header-rows: 1
 
+   *   Параметр
    *   Тип
    *   Опциональность
    *   Описание
+   *   `cacheName`
    *   `string`
    *   Да
    *   Имя кеша. Если не указано, используется кеш по умолчанию
+   *   `backups`
    *   `int`
    *   Да
    *   Число резервных копий (backups) для данных кеша. По умолчанию 0
+   *   `dataRegion`
    *   `string`
    *   Да
    *   Название региона данных, которому принадлежит кеш
+   *   `templateName`
    *   `string`
    *   Да
    *   Название шаблона кеша, который зарегистрирован в DataGrid. Конфигурация этого шаблона будет использоваться для распределенного кеша. 
    
        Подробнее о шаблонах написано в подразделе [«Конфигурация кешей»](../../developer-guide/md/cache_setup.md) раздела «Настройка кешей» документа «Руководство прикладного разработчика»
+   *   `cacheGroup`
    *   `string`
    *   Да
    *   Название кеш-группы, которой принадлежит кеш
+   *   `writeSynchronizationMode`
    *   `string`
    *   Да
    *   Устанавливает режим синхронизации для определенного кеша:
        - `FULL_SYNC`;
        - `FULL_ASYNC`;
        - `PRIMARY_SYNC`
:::

::::

::::{md-tab-item} Ответ
```bash
{
  "error": "",
  "response": null,
  "successStatus": 0
}
```
::::
:::::

## Destroy cache

Удаляет кеш с определенным именем.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=destcache&cacheName={cacheName}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `partitionedCache` |

:::

:::{md-tab-item} Ответ
```bash
{
  "error": "",
  "response": null,
  "successStatus": 0
}
```
:::
::::

## Node

Получает информацию о кеше.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=node&attr={includeAttributes}&mtr={includeMetrics}&id={nodeId}&caches={includeCaches}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `mtr` | `boolean` | Да | Ответ включает метрики, если параметр равен `true` | `true` |
| `attr` | `boolean` | Да | Ответ включает атрибуты, если параметр равен `true` | `true` |
| `ip` | `string` | — | Опционален, если передан параметр идентификатора. Ответ возвращается для узла, в котором есть IP-адрес | `xxx.xxx.x.x` |
| `id` | `string` | — | Опционален, если передан параметр IP-адреса. Ответ возвращается для узла, в котором есть идентификатор узла (`nodeID`) | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |
| `caches` | `boolean` | Да | Если значение параметра `true`, узел возвращает информацию по кешу: название, режим, SQL-схему.<br><br>Если значение параметра `false`, команда узла не возвращает информацию по кешу.<br><br>Значение по умолчанию — `true` | `true` |

:::

:::{md-tab-item} Ответ
```bash
{
  "error": "",
  "response": {
    "attributes": null,
    "caches": {},
    "consistentId": "127.0.0.1:47500",
    "defaultCacheMode": "REPLICATED",
    "metrics": null,
    "nodeId": "2d0d6510-6fed-4fa3-b813-20f83ac4a1a9",
    "replicaCount": 128,
    "tcpAddresses": ["127.0.0.1"],
    "tcpHostNames": [""],
    "tcpPort": 11211
  },
  "successStatus": 0
}
```
:::
::::

## Log

Показывает серверные log-файлы.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=log&from={from}&to={to}&path={pathToLogFile}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `from` | `integer` | Да | Номер строки, с которой нужно начать. Является обязательным, если передан параметр `to` | `0` |
| `path` | `string` | Да | Путь к log-файлу. Если не указан, используется путь по умолчанию | `/log/cache_server.log` |
| `to` | `integer` | Да | Номер строки, на которой нужно закончить. Является обязательным, если передан параметр `from` | `1000` |

:::

:::{md-tab-item} Ответ
```bash
{ 
	"successStatus": 0,
	"sessionToken": null,
	"securitySubjectId": null,   
	"response": ["[14:01:56,626][INFO ][test-runner][GridDiscoveryManager] Topology snapshot [ver=1, nodes=1, CPUs=8, heap=1.8GB]"], 	
	"error": null }
```
:::
::::

## Topology

Получает информацию о топологии кластера.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=top&attr=true&mtr=true&id=0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3м
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `mtr` | `boolean` | Да | Ответ включает метрики, если параметр равен `true` | `true` |
| `attr` | `boolean` | Да | Ответ включает атрибуты, если параметр равен `true` | `true` |
| `ip` | `string` | Да | Опционален, если передан параметр идентификатора. Ответ возвращается для узла, в котором есть IP-адрес | `xxx.xxx.x.x` |
| `id` | `string` | Да | Опционален, если передан параметр IP-адреса. Ответ возвращается для узла, в котором есть идентификатор узла (`nodeId`) | `0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3` |

:::

:::{md-tab-item} Ответ
```bash
{
	"successStatus": 0,
	"sessionToken": null,
	"securitySubjectId": null,
	"response": [
		{
			"nodeId": "0b8032dc-82b5-47b0-bbab-b7f5d0ff6cc3",
			"consistentId": "0:0:0:0:0:0:0:1%lo0,127.0.0.1,xxx.xxx.x.xx:47500",
			"tcpHostNames": [
				"xxx.xxx.x.xx"
			],
			"tcpPort": 11211,
			"metrics": null,
			"caches": [],
			"order": 1,
			"tcpAddresses": [
				"127.0.0.1",
				"0:0:0:0:0:0:0:1%lo0",
				"xxx.xxx.x.xx"
			],
			"attributes": null
		}
	],
	"error": null
}
```
:::
::::

## Execute a Task

Выполняет указанное задание в кластере.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=exe&name=taskName&p1=param1&p2=param2&async=true
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `name` | `string` | — | Название задачи для выполнения | `summ` |
| `p1…pN` | `string` | Да | Аргумент выполнения задачи | `arg1…argN` |
| `async` | `boolean` | Да | Определяет, выполняется ли задача асинхронно | `true` |

:::

:::{md-tab-item} Ответ

Ответ содержит:

- сообщение об ошибке;
- уникальный идентификатор задачи;
- статус и результат вычисления.

```bash
{
  "error": "",
  "response": {
    "error": "",
    "finished": true,
    "id": "~ee2d1688-2605-4613-8a57-6615a8cbcd1b",
    "result": 4
  },
  "successStatus": 0
}
```
:::
::::

## Result of a Task

Возвращает результат вычислений по указанной задаче.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=res&id={taskId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `id` | `string` | — | Идентификатор задачи, по которой вернется результат | `69ad0c48941-4689aae0-6b0e-4d52-8758-ce8fe26f497d~4689aae0-6b0e-4d52-8758-ce8fe26f497d` |

:::

:::{md-tab-item} Ответ

Ответ содержит:

- информацию об ошибках, если они есть;
- идентификатор задачи;
- статус и результат вычислений.

```bash
{
  "error": "",
  "response": {
    "error": "",
    "finished": true,
    "id": "69ad0c48941-4689aae0-6b0e-4d52-8758-ce8fe26f497d~4689aae0-6b0e-4d52-8758-ce8fe26f497d",
    "result": 4
  },
  "successStatus": 0
}
```
:::
::::

## SQL Query Execute

Запускает SQL-запросы над кешем.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=qryexe&type={type}&pageSize={pageSize}&cacheName={cacheName}&arg1=1000&arg2=2000&qry={query}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `type` | `string` | — | Тип запроса | `string` |
| `pageSize` | `number` | — | Размер страницы для запроса | `3` |
| `cacheName` | `string` | Да | Имя кеша. Если отсутствует, используется название по умолчанию | `testCache` |
| `arg1…argN` | `string` | — | Аргументы запроса | `1000,2000` |
| `qry` | `strings` | — | Кодирование SQL-запроса | `salary+%3E+%3F+and+salary+%3C%3D+%3F` |
| `keepBinary` | `boolean` | Да | Указывает не десериализовывать бинарные объекты. Значение по умолчанию — `false` | `true` |

:::

:::{md-tab-item} Ответ

Объект ответа содержит:

- элементы, которые возвращаются запросом;
- флаг, который указывает на последнюю страницу;
- `queryId`.

```bash
{
  "error":"",
  "response":{
    "fieldsMetadata":[],
    "items":[
      {"key":3,"value":{"name":"Jane","id":3,"salary":2000}},
      {"key":0,"value":{"name":"John","id":0,"salary":2000}}],
    "last":true,
    "queryId":0},
  "successStatus":0
}
```
:::
::::

## SQL Fields Query Execute

Запускает SQL-запрос по полям кеша.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=qryfldexe&pageSize=10&cacheName={cacheName}&qry={qry}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `pageSize` | `number` | — | Размер страницы для запроса | `3` |
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `testCache` |
| `arg1…argN` | `string` | — | Аргументы запроса | `1000,2000` |
| `qry` | `strings` | — | Кодирование SQL-запроса по полям | `select+firstName%2C+lastName+from+Person` |
| `keepBinary` | `boolean` | Да | Указывает не десериализовывать бинарные объекты. Значение по умолчанию — `false` | `true` |

:::

:::{md-tab-item} Ответ

Объект ответа содержит:

- элементы, которые возвращаются запросом;
- метаданные запроса полей;
- флаг, который указывает на последнюю страницу;
- `queryId`.

```bash
{
  "error": "",
  "response": {
    "fieldsMetadata": [
      {
        "fieldName": "FIRSTNAME",
        "fieldTypeName": "java.lang.String",
        "schemaName": "person",
        "typeName": "PERSON"
      },
      {
        "fieldName": "LASTNAME",
        "fieldTypeName": "java.lang.String",
        "schemaName": "person",
        "typeName": "PERSON"
      }
    ],
    "items": [["Jane", "Doe" ], ["John", "Doe"]],
    "last": true,
    "queryId": 0
  },
  "successStatus": 0
}
```
:::
::::

## SQL Scan Query Execute

Запускает запрос на сканирование по кешу.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=qryscanexe&pageSize={pageSize}&cacheName={cacheName}&className={className}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `pageSize` | `number` | — | Размер страницы для запроса | `3` |
| `cacheName` | `string` | Да | Имя кеша. Если не указано, используется кеш по умолчанию | `testCache` |
| `className` | `string` | Да | Название класса предиката для запроса сканирования. Класс должен реализовывать интерфейс `IgniteBiPredicate` | `org.apache.ignite.filters.PersonPredicate` |
| `keepBinary` | `boolean` | Да | Указывает не десериализовывать бинарные объекты. Значение по умолчанию — `false` | `true` |

:::

:::{md-tab-item} Ответ

Объект ответа содержит:

- элементы, которые возвращаются с помощью запроса на сканирование;
- метаданные запроса поля;
- флаг, который указывает на последнюю страницу;
- `queryId`.

```bash
{
  "error": "",
  "response": {
    "fieldsMetadata": [
      {
        "fieldName": "key",
        "fieldTypeName": "",
        "schemaName": "",
        "typeName": ""
      },
      {
        "fieldName": "value",
        "fieldTypeName": "",
        "schemaName": "",
        "typeName": ""
      }
    ],
    "items": [
      {
        "key": 1,
        "value": {
          "firstName": "Jane",
          "id": 1,
          "lastName": "Doe",
          "salary": 1000
        }
      },
      {
        "key": 3,
        "value": {
          "firstName": "Jane",
          "id": 3,
          "lastName": "Smith",
          "salary": 2000
        }
      }
    ],
    "last": true,
    "queryId": 0
  },
  "successStatus": 0
}
```
:::
::::

## SQL Query Fetch

Получает следующую страницу для запроса.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=qryfetch&pageSize={pageSize}&qryId={queryId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `pageSize` | `number` | — | Размер страницы для запроса | `3` |
| `qryId` | `number` | — | Идентификатор запроса, который возвращается от команд `SQL query execute`, `SQL fields query execute` или `SQL fetch` | `0` |

:::

:::{md-tab-item} Ответ

Объект ответа содержит:

- элементы, которые возвращаются запросом;
- флаг, который указывает на последнюю страницу;
- `queryId`.

```bash
{
  "error":"",
  "response":{
    "fieldsMetadata":[],
    "items":[["Jane","Doe"],["John","Doe"]],
    "last":true,
    "queryId":0
  },
  "successStatus":0
}
```
:::
::::

## SQL Query Close

Закрывает ресурсы запроса.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=qrycls&qryId={queryId}
```

| Параметр | Тип | Опциональность | Описание | Пример |
|---|---|---|---|---|
| `qryId` | `number` | — | Идентификатор запроса возвращается от команд `SQL query execute`, `SQL fields query execute` или `SQL fetch` | `0` |

:::

:::{md-tab-item} Ответ

Команда вернет `true`, если запрос успешно закрыт.

```bash
{
  "error":"",
  "response":true,
  "successStatus":0
}
```
:::
::::

## Probe

Возвращает ответ, запущено ли ядро DataGrid.

::::{md-tab-set}
:::{md-tab-item} Запрос
```bash
http://localhost:8080/ignite?cmd=probe
```
:::

:::{md-tab-item} Ответ

Возвращает код состояния HTTP: если ядро запущено — `200`, в противном случае — `503`.

```bash
{
	"successStatus": 0,
	"sessionToken": null,
	"securitySubjectId": null,
	"response": "grid has started",
	"error": null
}
```
:::
::::