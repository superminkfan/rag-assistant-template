# Утилита index-reader.sh

В комплект поставки DataGrid входит утилита `index-reader.sh`, которая позволяет проводить проверки дерева данных кеша в файлах партиций и его согласованность с индексами. Утилита работает с файлами напрямую и не требует запуска кластера. Утилита `index-reader.sh` находится в папке `/bin/` дистрибутива.

:::{admonition} Важно
:class: attention

Перед запуском утилиты убедитесь, что кластер остановлен, либо проверьте, что файлы кластера предварительно сохранены.
:::

Чтобы получить подсказки по синтаксису, запустите утилиту без параметров.

Синтаксис:

```bash
index-reader.sh --dir [--part-cnt] [--page-size] [--page-store-ver] [--indexes] [--check-parts]
```

где:

-   `--dir` — путь, по которому расположены файл `index.bin` и (необязательно) файлы разделов;
-   `--part-cnt` — полное количество партиций в группе кеша. Значение по умолчанию — 0;
-   `--page-size` — размер страницы. Значение по умолчанию — 4096;
-   `--page-store-ver` — версия хранилища страниц. Значение по умолчанию — 2;
-   `--indexes` — имена деревьев индексов (через запятую без пробелов), которые будут обрабатываться;
-   `--dest-file` — имя файла для вывода результата работы утилиты. Чтобы вывести отчет на консоль, а не в файл, укажите `--dest-file null`;
-   `--check-parts` — включение проверки дерева данных кеша в файлах партиций и его соответствия индексам.

## Поиск и вывод индексов

Утилита может анализировать файл `index.bin`, а при необходимости — файлы партиций, если присутствует параметр `--part-cnt` со значением больше нуля. Анализ осуществляется по индексу из `index.bin` двумя способами:

-   рекурсивный (\<RECURSIVE\>) — обход индекса от корня к листьям;
-   поуровневый (\<HORIZONTAL\>) — обход индекса по каждому уровню.

Чтобы обнаружить orphan-страницы (те, на которые нет ссылок из индексных деревьев и списков повторного использования), сканируются все страницы файла, в том числе списки повторного использования страниц (reuse list).

Вывод утилиты состоит из четырех основных разделов:

-   информация о рекурсивном обходе (с префиксом \<RECURSIVE\>);
-   информация о горизонтальном обходе (с префиксом \<HORIZONTAL\>);
-   информация со списками повторного использования страниц (с префиксом \<PAGE_LIST\>);
-   последовательное сканирование всех страниц.

Имена индексных деревьев в выводе не совпадают с именами индексов и представлены в формате `cacheId_typeId_indexName##H2Tree%segmentNumber`, например, `2652_885397586_T0_F0_F1_IDX##H2Tree%0`. Имена можно увидеть в поле вывода утилиты и в разделах информации об обходе (\<RECURSIVE\> и \<HORIZONTAL\>).

С помощью параметра `--check-parts` можно получить информацию о том, как CacheDataTree соответствует индексам SQL. 

:::{admonition} Пример вывода с сообщениями об отсутствии ошибок
:class: hint

```bash
Partitions check detected no errors.
 
Partition check finished, total errors: 0, total problem partitions: 0
```
:::

:::{admonition} Пример вывода с сообщениями об ошибках, в случае, когда запись была найдена в `CacheDataTree`, но не обнаружена в индексах SQL
:class: hint

```bash
<ERROR> Errors detected in partition, partId=1023
<ERROR> Entry is missing in index: I [idxName=2652_885397586_T0_F0_F1_IDX##H2Tree%0, pageId=xxxxxxxxxxxx], cacheId=2652, partId=1023, pageIndex=8, itemId=0, link=285868728254472
<ERROR> Entry is missing in index: I [idxName=2652_885397586_T0_F2_IDX##H2Tree%0, pageId=xxxxxxxxxxxx], cacheId=2652, partId=1023, pageIndex=8, itemId=0, link=285868728254472
All errors in the output have prefix <ERROR>.
```
:::

## Примеры использования утилиты

Используйте следующие команды для анализа:

-   всего содержимого `/opt/ignite/ssd/pds/cache`:

    ```bash
    ./index-reader.sh --dir "/opt/ignite/ssd/pds/cache" --part-cnt 1024 --page-size 4096 --page-store-ver 2  --dest-file "report.txt"
    ```

-   SQL-индексов в `/opt/ignite/ssd/pds/cache`:

    ```bash
    ./index-reader.sh --dir "/opt/ignite/ssd/pds/cache" --dest-file "report.txt"
    ```

-   SQL-индексов, которые находятся и в CacheDataTree, и в `/opt/ignite/ssd/pds/cache`:

    ```bash
    ./index-reader.sh --dir "/opt/ignite/ssd/pds/cache" --part-cnt 1024 --check-parts --dest-file "rep"
    ```

    :::{admonition} Пример вывода
    :class: hint 
    :collapsible:

    ```bash
    
    <RECURSIVE> Index tree: I [idxName=2654_-1177891018__key_PK##H2Tree%0, pageId=xxxxxxxxxxxxxxxxxx]
    <RECURSIVE> -- Page stat:
    <RECURSIVE> H2ExtrasLeafIO: 2
    <RECURSIVE> H2ExtrasInnerIO: 1
    <RECURSIVE> BPlusMetaIO: 1
    <RECURSIVE> -- Count of items found in leaf pages: 200
    <RECURSIVE> No errors occurred while traversing.
    
    ...
    
    <RECURSIVE> Total trees: 19
    <RECURSIVE> Total pages found in trees: 49
    <RECURSIVE> Total errors during trees traversal: 2
    ```
    :::

### Вывод информации о списках страниц

Раздел списков страниц содержит данные о сегменте списка повторного использования и информацию о последовательном сканировании: 

-   метаданные списка; 
-   номер сегмента;
-   начальные страницы списков, найденных в сегменте;
-   статистику типов страниц.

:::{admonition} Пример вывода
:class: hint

```bash
<PAGE_LIST> Page lists info.
<PAGE_LIST> ---Printing buckets data:
<PAGE_LIST> List meta id=844420635164675, bucket number=0, lists=[844420635164687]
<PAGE_LIST> -- Page stat:
<PAGE_LIST> H2ExtrasLeafIO: 32
<PAGE_LIST> H2ExtrasInnerIO: 1
<PAGE_LIST> BPlusMetaIO: 1
<PAGE_LIST> ---No errors.
```
:::

:::{admonition} Пример вывода
:class: hint

```bash
---These pages types were encountered during sequential scan:
H2ExtrasLeafIO: 165
H2ExtrasInnerIO: 19
PagesListNodeIO: 1
PagesListMetaIO: 1
MetaStoreLeafIO: 5
BPlusMetaIO: 20
PageMetaIO: 1
MetaStoreInnerIO: 1
TrackingPageIO: 1
---
Total pages encountered during sequential scan: 214
Total errors occurred during sequential scan: 0
```
:::

Утилита сравнивает результаты обходов и размеры индексов одних и тех же кешей.

:::{admonition} Пример сообщения об ошибке, связанной с несоответствием размера индекса
:class: hint 
:collapsible:

```bash
<ERROR> Index size inconsistency: cacheId=2652, typeId=885397586
<ERROR>      Index name: I [idxName=2652_885397586_T0_F0_F1_IDX##H2Tree%0, pageId=xxxxxxxxxxxx], size=1700
<ERROR>      Index name: I [idxName=2652_885397586__key_PK##H2Tree%0, pageId=xxxxxxxxxxxx], size=0
<ERROR>      Index name: I [idxName=2652_885397586_T0_F1_IDX##H2Tree%0, pageId=xxxxxxxxxxxx], size=1700
<ERROR>      Index name: I [idxName=2652_885397586_T0_F0_IDX##H2Tree%0, pageId=xxxxxxxxxxxx], size=1700
<ERROR>      Index name: I [idxName=2652_885397586_T0_F2_IDX##H2Tree%0, pageId=xxxxxxxxxxxx]
```
:::