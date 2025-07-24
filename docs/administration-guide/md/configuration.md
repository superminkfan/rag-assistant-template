# Конфигурирование

## Введение

Platform V DataGrid предоставляет мощную и гибкую систему конфигурации, которая позволяет управлять множеством аспектов работы кластеров, кешированием данных, сетевыми соединениями, настройками безопасности и так далее. DataGrid состоит из множества модулей, которые реализованы в виде Spring-компонентов. Это обеспечивает их связность и позволяет конфигурировать их как Spring-beans. Основной элемент конфигурации — класс `IgniteConfiguration`, который определяет большинство параметров, необходимых для корректного функционирования системы, и значения которого считываются при запуске DataGrid. Но существуют и другие способы изменения параметров, например, использование JVM-параметров, управление с помощью JMX и настройка значений по умолчанию для распределенных свойств (distributed properties) на уровне конфигурации DataGrid. Конфигурацию DataGrid можно задать программно или с использованием XML-конфигурации.

### Ключевые компоненты конфигурации

Для конфигурирования DataGrid администратору необходимо понимать ключевые компоненты конфигурации:

- `IgniteConfiguration` — главный объект конфигурации. Содержит все основные параметры, которые нужны для запуска и работы DataGrid.
- `TcpDiscoverySpi` — реализация механизма обнаружения узлов с помощью TCP-соединений. Поддерживает различные стратегии поиска IP-адресов, например:

   - `IpFinder` — абстрактный интерфейс для поиска IP-адресов узлов.
   - `TcpDiscoveryJdbcIpFinder` — стратегия поиска IP-адресов с помощью базы данных.
   - `TcpDiscoveryMulticastIpFinder` — использование протокола Multicast для поиска узлов.
   - `TcpDiscoverySharedFsIpFinder` — поиск узлов с помощью общего файлового ресурса.
   - `TcpDiscoveryVmIpFinder` — поиск узлов внутри одной виртуальной машины.

- `ZookeeperDiscoverySpi` — альтернативный механизм обнаружения узлов, который использует ZooKeeper для координации и управления состоянием кластера.
- `TcpCommunicationSpi` — компонент, который отвечает за сетевые соединения между узлами кластера. Определяет способ передачи данных и управляет взаимодействием узлов.
- `DataStorageConfiguration` — параметры хранения данных, которые определяют механизмы распределения памяти и управления дисковым пространством.
- `DataRegionConfiguration` — настройки регионов данных, которые определяют области памяти для хранения разных типов данных.
- `CacheConfiguration` — конкретные настройки кешей, которые включают политики хранения, очистки и репликации данных.
- `IgniteSystemProperties` — глобальные свойства системы, которые могут влиять на поведение всех компонентов DataGrid.

Также ниже описан набор свойств, который контролирует различные аспекты поведения и производительности DataGrid, например, тайминги операций, сбор статистики, управление транзакциями, политика завершения работы и обработка длительных операций. Они помогают оптимизировать работу кластера, улучшить обработку запросов и предотвратить возникновение ошибок, которые связаны с длительными операциями и транзакциями.

Эти компоненты играют ключевую роль в управлении работой DataGrid и позволяют адаптировать систему под конкретные требования проекта. Ниже описаны основные компоненты конфигурации, полный список доступен в [официальной документации Apache Ignite](https://ignite.apache.org/releases/latest/javadoc/).

## IgniteConfiguration

| Название параметра | Описание | Тип | Значение по умолчанию |
|---|---|---|---|
| `activeOnStart` | Устарел, используйте параметр `clusterStateOnStart` | boolean | `DFLT_ACTIVE_ON_START = true` |
| `addressResolver` | Устанавливает пользовательский `addressResolver` для сопоставления адресов | `AddressResolver` | — |
| `allSegmentationResolversPassRequired` | Устанавливает флаг для определения, требуется ли успешное прохождение проверок от всех `SegmentationResolvers`, чтобы узел находился в правильном сегменте | boolean | `DFLT_ALL_SEG_RESOLVERS_PASS_REQ = true` |
| `asyncCallbackPoolSize` | Устанавливает размер пула потоков, который отвечает за асинхронную обработку обратных вызовов для использования внутри кластера | int | `DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`<br>`AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `asyncContinuationExecutor` | Устанавливает пользовательский исполнитель (`Executor`) для выполнения продолжений (continuations) асинхронных операций для работы с кешем | `Executor` | Значение по умолчанию для `asyncContinuationExecutor` — `null`. Если не указывать конкретный исполнитель (`Executor`), будет использоваться `ForkJoinPool.commonPool()` |
| `atomicConfiguration` | Устанавливает настройку атомарных структур данных | `AtomicConfiguration` | `Backups` — `0`, что означает отсутствие резервирования.<br><br>`Cache mode` — режим работы кеша: `PARTITIONED`.<br><br>`ATOMIC_SEQUENCE_RESERVE_SIZE` — размер резерва для последовательностей, которые создаются с помощью атомарного API: `1000` |
| `authenticationEnabled` | Устанавливает флаг, который определяет необходимость включения или отключения аутентификации пользователей при подключении к кластеру | boolean | `false` |
| `autoActivationEnabled` | Устарел, используйте параметр `setClusterStateOnStart(ClusterState)` | boolean | `DFLT_AUTO_ACTIVATION = true` |
| `binaryConfiguration` | Устанавливает параметры для настройки бинарной сериализации и десериализации данных | `BinaryConfiguration` | — |
| `buildIndexThreadPoolSize` | Устанавливает размер пула потоков для построения/перестроения индексов для использования внутри кластера | int | `DFLT_BUILD_IDX_THREAD_POOL_SIZE = min(4, max(1, AVAILABLE_PROC_CNT / 4))`<br>`AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `cacheConfiguration` | Задает конфигурации кешей, которые будут созданы при запуске кластера | `CacheConfiguration` | `aff = cc.getAffinity();`<br>`affMapper = cc.getAffinityMapper();`<br>`atomicityMode = cc.getAtomicityMode()= DFLT_CACHE_ATOMICITY_MODE = CacheAtomicityMode.ATOMIC;<br>backups = cc.getBackups() = DFLT_BACKUPS = 0;`<br>`cacheLoaderFactory = cc.getCacheLoaderFactory();`<br>`cacheMode = cc.getCacheMode() = DFLT_CACHE_MODE = CacheMode.PARTITIONED;`<br>`cacheWriterFactory = cc.getCacheWriterFactory();`<br>`cpOnRead = cc.isCopyOnRead() = DFLT_COPY_ON_READ = true;`<br>`dfltLockTimeout = cc.getDefaultLockTimeout() = DFLT_LOCK_TIMEOUT = 0;`<br>`eagerTtl = cc.isEagerTtl() = DFLT_EAGER_TTL = true;`<br>`encryptionEnabled = cc.isEncryptionEnabled();`<br>`evictFilter = cc.getEvictionFilter();`<br>`evictPlc = cc.getEvictionPolicy() = null;`<br>`evictPlcFactory = cc.getEvictionPolicyFactory() = null;`<br>`expiryPolicyFactory = cc.getExpiryPolicyFactory();`<br>`grpName = cc.getGroupName();`<br>`indexedTypes = cc.getIndexedTypes();`<br>`interceptor = cc.getInterceptor();`<br>`invalidate = cc.isInvalidate() = DFLT_INVALIDATE = false;`<br>`isReadThrough = cc.isReadThrough();`<br>`isWriteThrough = cc.isWriteThrough();`<br>`keyCfg = cc.getKeyConfiguration();`<br>`listenerConfigurations = cc.listenerConfigurations;`<br>`loadPrevVal = cc.isLoadPreviousValue() = DFLT_LOAD_PREV_VAL = false;`<br>`longQryWarnTimeout = cc.getLongQueryWarningTimeout() = DFLT_LONG_QRY_WARN_TIMEOUT = 3000;`<br>`maxConcurrentAsyncOps = cc.getMaxConcurrentAsyncOperations() = DFLT_MAX_CONCURRENT_ASYNC_OPS = 500;`<br>`memPlcName = cc.getDataRegionName();`<br>`name = cc.getName();`<br>`nearCfg = cc.getNearConfiguration();`<br>`platformCfg = cc.getPlatformCacheConfiguration();`<br>`nodeFilter = cc.getNodeFilter();`<br>`onheapCache = cc.isOnheapCacheEnabled();`<br>`diskPageCompression = cc.getDiskPageCompression() = DFLT_DISK_PAGE_COMPRESSION = DiskPageCompression.DISABLED;`<br>`diskPageCompressionLevel = cc.getDiskPageCompressionLevel() = null;`<br>`partLossPlc = cc.getPartitionLossPolicy() = DFLT_PARTITION_LOSS_POLICY = PartitionLossPolicy.IGNORE;pluginCfgs = cc.getPluginConfigurations();`<br>`qryDetailMetricsSz = cc.getQueryDetailMetricsSize() = DFLT_QRY_DETAIL_METRICS_SIZE = 0;`<br>`qryEntities = cc.getQueryEntities();`<br>`qryParallelism = cc.getQueryParallelism()= DFLT_QUERY_PARALLELISM = 1;`<br>`readFromBackup = cc.isReadFromBackup() = DFLT_READ_FROM_BACKUP = true;`<br>`rebalanceBatchSize = cc.getRebalanceBatchSize() = DFLT_REBALANCE_BATCH_SIZE = 512 * 1024;`<br>`rebalanceBatchesPrefetchCnt = cc.getRebalanceBatchesPrefetchCount() = DFLT_REBALANCE_BATCHES_PREFETCH_COUNT = 3;`<br>`rebalanceDelay = cc.getRebalanceDelay() = 0;`<br>`rebalanceMode = cc.getRebalanceMode() = DFLT_REBALANCE_MODE = CacheRebalanceMode.ASYNC;`<br>`rebalanceOrder = cc.getRebalanceOrder() = 0;`<br>`rebalancePoolSize = cc.getRebalanceThreadPoolSize() = DFLT_REBALANCE_THREAD_POOL_SIZE = min(4, max(1, AVAILABLE_PROC_CNT / 4)) `<br>`(где: AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors());`<br>`rebalanceTimeout = cc.getRebalanceTimeout() = DFLT_REBALANCE_TIMEOUT = 10000;`<br>`rebalanceThrottle = cc.getRebalanceThrottle() = DFLT_REBALANCE_THROTTLE = 0;`<br>`sqlSchema = cc.getSqlSchema() = null;`<br>`sqlEscapeAll = cc.isSqlEscapeAll();`<br>`sqlFuncCls = cc.getSqlFunctionClasses();`<br>`sqlIdxMaxInlineSize = cc.getSqlIndexMaxInlineSize() = DFLT_SQL_INDEX_MAX_INLINE_SIZE = -1;`<br>`storeFactory = cc.getCacheStoreFactory();`<br>`storeKeepBinary = cc.isStoreKeepBinary() != null ? cc.isStoreKeepBinary() : DFLT_STORE_KEEP_BINARY `<br>`(где: DFLT_STORE_KEEP_BINARY = new Boolean(false));`<br>`storeSesLsnrs = cc.getCacheStoreSessionListenerFactories();`<br>`tmLookupClsName = cc.getTransactionManagerLookupClassName();`<br>`topValidator = cc.getTopologyValidator();`<br>`writeBehindBatchSize = cc.getWriteBehindBatchSize() = DFLT_WRITE_BEHIND_BATCH_SIZE = 512;`<br>`writeBehindCoalescing = cc.getWriteBehindCoalescing() = DFLT_WRITE_BEHIND_COALESCING = true;`<br>`writeBehindEnabled = cc.isWriteBehindEnabled() = DFLT_WRITE_BEHIND_ENABLED = false;`<br>`writeBehindFlushFreq = cc.getWriteBehindFlushFrequency() = DFLT_WRITE_BEHIND_FLUSH_FREQUENCY = 5000;`<br>`writeBehindFlushSize = cc.getWriteBehindFlushSize() = DFLT_WRITE_BEHIND_FLUSH_SIZE = 10240;`<br>`writeBehindFlushThreadCnt = cc.getWriteBehindFlushThreadCount() = DFLT_WRITE_FROM_BEHIND_FLUSH_THREAD_CNT = 1;`<br>`writeSync = cc.getWriteSynchronizationMode();`<br>`storeConcurrentLoadAllThreshold = cc.getStoreConcurrentLoadAllThreshold() = DFLT_CONCURRENT_LOAD_ALL_THRESHOLD = 5;`<br>`maxQryIterCnt = cc.getMaxQueryIteratorsCount() = DFLT_MAX_QUERY_ITERATOR_CNT = 1024;`<br>`sqlOnheapCache = cc.isSqlOnheapCacheEnabled();`<br>`sqlOnheapCacheMaxSize = cc.getSqlOnheapCacheMaxSize() = DFLT_SQL_ONHEAP_CACHE_MAX_SIZE = 0;`<br>`evtsDisabled = cc.isEventsDisabled() = DFLT_EVENTS_DISABLED = false;` |
| `cacheKeyConfiguration` | Задает конфигурации ключей для одного или нескольких кешей, которые будут созданы при запуске кластера | `CacheKeyConfiguration` | — |
| `cacheSanityCheckEnabled` | Задает флаг проверки целостности кеша | boolean | `DFLT_CACHE_SANITY_CHECK_ENABLED = true` |
| `cacheStoreSessionListenerFactories` | Задает фабрики слушателей сессий для хранилищ кеша. Слушатели уведомляют приложение о событиях, которые происходят во время сессии взаимодействия с хранилищем кешей, например об открытии и закрытии сессии | `javax.cache.configuration.Factory<CacheStoreSessionListener>` | — |
| `checkpointSpi` | Используется для настройки SPI (Service Provider Interface) для контрольных точек | `CheckpointSpi` | `null`, будет использоваться реализация `NoopCheckpointSpi` по умолчанию |
| `classLoader` | Задает загрузчик классов (`ClassLoader`), который будет использоваться для конкретизации контекста выполнения (`EntryProcessors`, `CacheEntryListeners`, `CacheLoaders` и `ExpiryPolicys`). Метод позволяет контролировать, каким образом классы загружаются и разрешаются в контексте конкретного экземпляра DataGrid | `ClassLoader` | — |
| `clientConnectorConfiguration` | Задает конфигурацию подключения тонкого клиента | `ClientConnectorConfiguration` | — |
| `clientFailureDetectionTimeout` | Устанавливает тайм-аут обнаружения отказов в `TcpDiscoverySpi` и `TcpCommunicationSpi`. Таймер определяет интервал времени, в течение которого сервер ожидает активности от клиента перед тем, как считать его вышедшим из строя | long | `DFLT_CLIENT_FAILURE_DETECTION_TIMEOUT = 30_000` |
| `clientMode` | Устанавливает флаг, который используется для переключения между клиентским и серверным режимами работы узла | boolean | — |
| `clusterStateOnStart` | Устанавливает начальное состояние кластера при его запуске | `ClusterState` | `DFLT_STATE_ON_START = ClusterState.ACTIVE` |
| `collisionSpi` | Устанавливает пользовательский настроенный экземпляр `CollisionSpi`. Используется для настройки SPI для разрешения коллизий. Они могут возникнуть, когда несколько узлов пытаются выполнить одни и те же операции параллельно — в таком случае необходимо выбрать, какой узел продолжит выполнение (остальные узлы откатятся к предыдущему состоянию) | `CollisionSpi` | `null`, будет использоваться реализация `NoopCheckpointSpi` по умолчанию |
| `communicationFailureResolver` | Используется для установки пользовательского компонента `Resolver`, который отвечает за разрешение проблем, связанных с коммуникационными сбоями между узлами кластера | `CommunicationFailureResolver` | — |
| `communicationSpi` | Используется для установки пользовательской настройки SPI для коммуникации между узлами кластера. SPI отвечает за передачу сообщений между узлами, обеспечивает обмен данными и командами | `CommunicationSpi` | `null`, будет использоваться реализация `TcpCommunicationSpi` по умолчанию |
| `connectorConfiguration` | Используется для пользовательской настройки конфигурации коннектора, который отвечает за взаимодействие с внешними клиентами, например с тонкими клиентами, которые работают на других платформах (.NET, C++, Python и так далее) | `ConnectorConfiguration` | `msgInterceptor = cfg.getMessageInterceptor() = null;`<br>`threadPoolSize = cfg.getThreadPoolSize() = DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT) (где AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors());`<br>`idleTimeout = cfg.getIdleTimeout() = DFLT_IDLE_TIMEOUT = 7000;`<br>`jettyPath = cfg.getJettyPath();`<br>`portRange = cfg.getPortRange() = DFLT_PORT_RANGE = 100;`<br>`secretKey = cfg.getSecretKey();`<br>`directBuf = cfg.isDirectBuffer() = DFLT_TCP_DIRECT_BUF = false;`<br>`host = cfg.getHost() = null;`<br>`noDelay = cfg.isNoDelay() = DFLT_TCP_NODELAY = true;`<br>`port = cfg.getPort() = DFLT_TCP_PORT = 11211;`<br>`rcvBufSize = cfg.getReceiveBufferSize() = 0;`<br>`selectorCnt = cfg.getSelectorCount() = Math.min(4, Runtime.getRuntime().availableProcessors());`<br>`sndBufSize = cfg.getSendBufferSize() = DFLT_SOCK_BUF_SIZE = 32 * 1024;`<br>`sndQueueLimit = cfg.getSendQueueLimit();`<br>`sslClientAuth = cfg.isSslClientAuth();`<br>`sslEnabled = cfg.isSslEnabled();`<br>`sslFactory = cfg.getSslFactory();`<br>`idleQryCurTimeout = cfg.getIdleQueryCursorTimeout() = DFLT_IDLE_QRY_CUR_TIMEOUT = 10 * 60 * 1000;`<br>`idleQryCurCheckFreq = cfg.getIdleQueryCursorCheckFrequency() = DFLT_IDLE_QRY_CUR_CHECK_FRQ = 60 * 1000;` |
| `consistentId` | Используется для установки консистентного глобально уникального идентификатора узла, который сохраняется после перезапуска узла. <br><br>Идентификатор используется для поддержания консистентности топологии между различными узлами кластера. Это позволяет узлу легко присоединиться к существующему кластеру или инициировать новый кластер, если текущего нет | `Serializable` | — |
| `dataStorageConfiguration` | Устанавливает конфигурацию хранения данных в памяти | `DataStorageConfiguration` | — |
| `dataStreamerThreadPoolSize` | Устанавливает размер пула потоков, который отвечает за обработку потоков, используемых для обработки сообщений потока данных | int | `DFLT_DATA_STREAMER_POOL_SIZE = DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`<br>`(где AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors())` |
| `defaultQueryTimeout` | Устарел, используйте параметр `SqlConfiguration.setDefaultQueryTimeout(long)` | long | `DFLT_QRY_TIMEOUT = 0` |
| `deploymentMode` | Устанавливает режим развертывания, который определяет, как классы используются и загружаются на узлах. Режимы влияют на способ передачи классов между узлами кластера и на их поведение при выполнении задач | `DeploymentMode` | `DFLT_DEPLOYMENT_MODE = DeploymentMode.SHARED` |
| `deploymentSpi` | Используется для настройки механизма развертывания узлов в кластере | `DeploymentSpi` | — |
| `discoverySpi` | Используется для настройки обнаружения узлов в кластере | `DiscoverySpi` | `null`, будет использоваться реализация `TcpDiscoverySpi` по умолчанию |
| `discoveryStartupDelay` | Устарел, больше не используется | long | `DFLT_DISCOVERY_STARTUP_DELAY = 60000` |
| `encryptionSpi` | Устанавливает настройку шифрования для защиты данных в кеше | `EncryptionSpi` | — |
| `eventStorageSpi` | Позволяет настроить SPI для хранения событий. Метод определяет, каким образом события будут сохраняться и обрабатываться в системе | `EventStorageSpi` | `null`, будет использоваться реализация `NoopEventStorageSpi` по умолчанию |
| `executorConfiguration` | Устанавливает настройки пулов выполнения задач (executors). Позволяет определить несколько конфигураций для различных типов задач, например вычисления, кеширования, запросов и других операций | `ExecutorConfiguration` | — |
| `failoverSpi` | Используется для настройки механизма автоматического переключения на резервную копию (failover) в случае сбоя узла или компонента кластера | `FailoverSpi` | `null`, будет использоваться реализация `AlwaysFailoverSpi` по умолчанию |
| `failureDetectionTimeout` | Устанавливает тайм-аут обнаружения сбоев для использования в `TcpDiscoverySpi` и `TcpCommunicationSpi` | long | `DFLT_FAILURE_DETECTION_TIMEOUT = 10_000` |
| `failureHandler` | Устанавливает обработчик ошибок, который будет вызван в случае возникновения критических ошибок в работе кластера | `FailureHandler` | — |
| `gridLogger` | Устанавливает логер, который будет использоваться для записи сообщений о событиях и действиях внутри кластера | `IgniteLogger` | — |
| `gridName` | Устарел, используйте параметр `setIgniteInstanceName(String)` | String | `null` |
| `igniteHome` | Задает установочную директорию DataGrid, в которой находятся файлы конфигурации и рабочие файлы | String | — |
| `igniteInstanceName` | Устанавливает имя локального экземпляра DataGrid. Это имя используется для идентификации отдельных экземпляров внутри одного кластера | String | `null` |
| `includeEventTypes` | Устанавливает множество типов событий, которое будет записано `GridEventStorageManager.record(Event)` | int | `0` (по умолчанию все события отключены) |
| `includeProperties` | Предназначен для включения определенных системных свойств и имен свойств окружения для включения в метаданные кластера | String | `null` |
| `indexingSpi` | Предназначен для настройки SPI для индексации данных в кластере, чтобы улучшать производительность операций поиска и фильтрации с помощью ускорения доступа к данным | `IndexingSpi` | — |
| `lateAffinityAssignment` | Параметр устарел | boolean | `true` |
| `lifecycleBeans` | Предназначен для регистрации beans жизненного цикла (lifecycle beans). Beans предоставляют методы, которые выполняются на определенных этапах жизненного цикла кластера, например запуск и остановка | `LifecycleBean` | — |
| `loadBalancingSpi` | Предназначен для настройки механизмов балансировки нагрузки в кластере | `LoadBalancingSpi` | `null`, будет использоваться реализация `RoundRobinLoadBalancingSpi` по умолчанию |
| `localEventListeners` | Предназначен для настройки локальных слушателей событий | `Map<IgnitePredicate<? extends Event>,int[]>` | — |
| `localHost` | Предназначен для указания общесистемного IP-адреса или имени хоста, который будет использоваться для подключения всех компонентов DataGrid | String | `null` |
| `longQueryWarningTimeout` | Устарел, используйте параметр `SqlConfiguration.setLongQueryWarningTimeout(long)` | long | `DFLT_LONG_QRY_WARN_TIMEOUT = 3000` |
| `managementThreadPoolSize` | Предназначен для настройки размера пула потоков, которые используются для выполнения management-задач в кластере | int | `DFLT_MGMT_THREAD_CNT = 4` |
| `marshaller` | При использовании пользовательского `marshaller` перестанут работать некоторые важные функции DataGrid, поэтому его использование не рекомендуется | int | — |
| `marshalLocalJobs` | Предназначен для настройки поведения системы относительно сериализации локальных задач. Определяет, должна ли система сериализовать задачи, которые выполняются локально на узле | boolean | `DFLT_MARSHAL_LOCAL_JOBS = false` |
| `mBeanServer` | Предназначен для интеграции с `MBeanServer`, который используется для управления и мониторинга Java-приложений через JMX (Java Management Extensions) | `MBeanServer` | `null`, система будет использовать сервер `MBean` по умолчанию для платформы |
| `memoryConfiguration` | Устарел, используйте параметр `DataStorageConfiguration` | `MemoryConfiguration` | — |
| `metricExporterSpi` | Предназначен для настройки SPI для экспорта метрик из кластера | `MetricExporterSpi` | — |
| `metricsExpireTime` | Предназначен для настройки времени жизни метрик в кластере. Определяет, сколько времени метрики остаются актуальными перед тем, как они устаревают и удаляются | long | `DFLT_METRICS_EXPIRE_TIME = Long.MAX_VALUE` |
| `metricsHistorySize` | Предназначен для настройки максимального размера истории метрик, которые сохраняются в кластере. Определяет, сколько последних значений каждой метрики будет сохраняться в памяти | int | `DFLT_METRICS_HISTORY_SIZE = 10000` |
| `metricsLogFrequency` | Предназначен для настройки частоты записи метрик в журнал. Определяет, как часто метрики будут записываться в лог | long | `DFLT_METRICS_LOG_FREQ = 60000` |
| `metricsUpdateFrequency` | Предназначен для настройки частоты обновления метрик в кластере | long | `DFLT_METRICS_UPDATE_FREQ = 2000` |
| `networkCompressionLevel` | Устанавливает уровень сжатия данных, которые передаются по сети. Определяет степень сжатия данных (это может влиять на скорость передачи данных и использование ресурсов) | int | `DFLT_NETWORK_COMPRESSION = Deflater.BEST_SPEED = 1` (отсутствие сжатия данных) |
| `networkSendRetryCount` | Задает количество повторных попыток отправки данных в случае неудачного соединения. Определяет количество повторных попыток отправки сообщения в случае потери соединения или сбоя передачи данных | int | `DFLT_SEND_RETRY_CNT = 3` (3 повторных попытки) |
| `networkSendRetryDelay` | Устанавливает задержку между попытками повторной отправки данных в случае неудачных передач | long | `DFLT_SEND_RETRY_DELAY = 1000` |
| `networkTimeout` | Устанавливает максимальное время ожидания завершения передачи данных через сеть. Устанавливает период времени, в течение которого соединение считается активным и передача данных может продолжаться | long | `DFLT_NETWORK_TIMEOUT = 5000` |
| `nodeId` | Устарел, используйте параметр `setConsisentId(Serializable)` | `UUID` | — |
| `odbcConfiguration` | Устарел, используйте параметр `setClientConnectorConfiguration(ClientConnectorConfiguration)` | `OdbcConfiguration` | — |
| `peerClassLoadingEnabled` | Задает включение/отключение одноранговой (peer-to-peer, P2P) загрузки классов | boolean | `DFLT_P2P_ENABLED = false` |
| `peerClassLoadingLocalClassPathExclude` | Предназначен для исключения определенных классов или пакетов из процесса одноранговой загрузки классов. Когда включен режим P2P-загрузки классов, узлы кластера могут запрашивать отсутствующие классы друг у друга. Но иногда может потребоваться исключить некоторые классы или пакеты из этого процесса, чтобы они всегда загружались локально | String | — |
| `peerClassLoadingMissedResourcesCacheSize` | Устанавливает размер кеша пропущенных ресурсов при использовании механизма одноранговой загрузки классов. Для избежания кеширования пропущенных ресурсов установите значение `0` | int | `DFLT_P2P_MISSED_RESOURCES_CACHE_SIZE = 100` |
| `peerClassLoadingThreadPoolSize` | Устанавливает размер пула потоков, которые выделяются для обработки запросов на загрузку классов с помощью механизма одноранговой загрузки классов | int | `DFLT_P2P_THREAD_CNT = 2` |
| `persistentStoreConfiguration` | Устарел (часть старого API), для настройки персистентности используйте параметр `DataStorageConfiguration` | `PersistentStoreConfiguration` | — |
| `platformConfiguration` | Предназначен для настройки платформы, на которой развернут кластер | `PlatformConfiguration` | — |
| `pluginConfigurations` | Устарел. `PluginProviders` можно установить с помощью `setPluginProviders(PluginProvider[])`, поэтому корректнее хранить `PluginConfiguration` как часть `PluginProvider` | `PluginConfiguration` | — |
| `pluginProviders` | Предназначен для регистрации поставщиков плагинов. Они предоставляют способ динамической загрузки и инициализации плагинов в рамках кластера DataGrid | `PluginProvider` | — |
| `publicThreadPoolSize` | Используется для настройки размера общего пула потоков. Пул потоков используется для выполнения пользовательских задач, которые не относятся к внутренним операциям DataGrid, например обработка SQL-запросов, выполнение вычислений и так далее | int | `DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `queryThreadPoolSize` | Используется для настройки размера пула потоков, который предназначен для выполнения запросов. Пул потоков управляет параллельными запросами к данным, что особенно важно в высоконагруженных системах, которые работают с большими объемами данных | int | `DFLT_QUERY_THREAD_POOL_SIZE = DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `rebalanceBatchesPrefetchCount` | Используется для настройки количества предварительно загружаемых партий (batches) данных, которые питающий узел создаст в начале процесса ребалансировки | long | `DFLT_REBALANCE_BATCHES_PREFETCH_COUNT = 3` (минимальное значение — `1`) |
| `rebalanceBatchSize` | Устанавливает размер сообщения поставки в байтах, который будет загружен в рамках одного пакета ребалансировки | int | `rebalanceBatchSize = IgniteConfiguration.DFLT_REBALANCE_BATCH_SIZE = 512 * 1024;` <br>`// 512K` |
| `rebalanceThreadPoolSize` | Используется для настройки размера пула потоков, которые предназначены для выполнения операций ребалансировки данных в кластере | int | `DFLT_REBALANCE_THREAD_POOL_SIZE = min(4, max(1, AVAILABLE_PROC_CNT / 4))`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `rebalanceThrottle` | Используется для настройки ограничения скорости (троттлинга) процесса ребалансировки данных в кластере. Устанавливает интервал между сообщениями о ребалансировке, чтобы избежать перегрузки ЦПУ (центрального процессора) или сети | long | `DFLT_REBALANCE_THROTTLE = 00` (троттлинг отключен) |
| `rebalanceTimeout` | Используется для настройки времени ожидания завершения процесса ребалансировки данных в кластере между узлами | long | `DFLT_REBALANCE_TIMEOUT = 10000` |
| `segmentationPolicy` | Используется для настройки политики сегментации кластера | `SegmentationPolicy` | `DFLT_SEG_PLC = USE_FAILURE_HANDLER` |
| `segmentationResolveAttempts` | Устанавливает число попыток разрешения сегментации перед применением политики сегментации | int | `DFLT_SEG_RESOLVE_ATTEMPTS = 2` |
| `segmentationResolvers` | Используется для настройки одного или нескольких разрешений сегментации, которые определяют, какие действия предпринять в случае обнаружения сетевой сегментации. Устанавливает пользовательское средство разрешения сегментации | `SegmentationResolver` | — |
| `segmentCheckFrequency` | Используется для настройки частоты проверки состояния кластера на предмет наличия сетевой сегментации | long | `DFLT_SEG_CHK_FREQ = 10000` |
| `serviceConfiguration` | Используется для настройки сервисов, которые предоставляет кластер | `ServiceConfiguration` | — |
| `serviceThreadPoolSize` | Устанавливает размер пула потоков, который используется для выполнения сервисов в кластере | int | `DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `shutdownPolicy` | Устанавливает политику завершения работы узлов в кластере | `ShutdownPolicy` | `DFLT_SHUTDOWN_POLICY = ShutdownPolicy.IMMEDIATE` |
| `snapshotPath` | Используется для настройки пути сохранения снепшотов данных кластера | String | `DFLT_SNAPSHOT_DIRECTORY = "snapshots"` |
| `snapshotThreadPoolSize` | Используется для настройки размера пула потоков, который занимается созданием снепшотов данных в кластере | int | `DFLT_SNAPSHOT_THREAD_POOL_SIZE = 4` |
| `sqlConfiguration` | Используется для настройки конфигурации SQL-профиля, который управляет работой с SQL-запросами в кластере | `SqlConfiguration` | — |
| `sqlConnectorConfiguration` | Устарел, используйте параметр `SqlConfiguration.setSqlQueryHistorySize()` | `SqlConnectorConfiguration` | — |
| `sqlQueryHistorySize` | Устарел, используйте параметр `setClientConnectorConfiguration(ClientConnectorConfiguration)` | int | `DFLT_SQL_QUERY_HISTORY_SIZE = 1000` |
| `sqlSchemas` | Устарел, используйте параметр `SqlConfiguration.setSqlSchemas(String...)` | String | — |
| `sslContextFactory` | Используется для настройки фабрики SSL-контекста, которая управляет генерацией и управлением SSL-сертификатами в кластере. Этот метод позволяет определять источник создания и управления сертификатами для обеспечения безопасного обмена данными между узлами кластера | `javax.cache.configuration.Factory<SSLContext>` | — |
| `stripedPoolSize` | Устанавливает striped pool потоков, который будет использоваться для обработки запросов в кеше | int | `DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `systemThreadPoolSize` | Устанавливает размер пула потоков, который управляет передачей данных внутри системы | int | `DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `systemViewExporterSpi` | Используется для настройки экспортируемой системы для экспорта системных представлений (системных метрик) с помощью внешних интерфейсов | `SystemViewExporterSp` | — |
| `systemWorkerBlockedTimeout` | Устанавливает максимальное время ожидания, в течение которого поток системного воркера (worker thread) считается заблокированным до того, как система зарегистрирует предупреждение об этом событии | long | — |
| `timeServerPortBase` | Устанавливает базовый порт для сервера времени, который отвечает за синхронизацию времени между узлами кластера | int | `DFLT_TIME_SERVER_PORT_BASE = 31100` |
| `timeServerPortRange` | Устанавливает диапазон портов для сервера времени, который отвечает за синхронизацию времени между узлами кластера | int | `DFLT_TIME_SERVER_PORT_RANGE = 100` |
| `tracingSpi` | Устанавливает полностью настроенный экземпляр `TracingSpi` | `TracingSpi` | — |
| `transactionConfiguration` | Используется для настройки транзакционной конфигурации кластера | `TransactionConfiguration` | `dfltConcurrency = PESSIMISTIC;`<br>`dfltIsolation = REPEATABLE_READ;`<br>`dfltTxTimeout = 0;`<br>`txTimeoutOnPartitionMapExchange = 0;`<br>`pessimisticTxLogLinger = 10_000;`<br>`pessimisticTxLogSize = 0;`<br>`txSerEnabled = false;`<br>`tmLookupClsName = cfg.getTxManagerLookupClassName();`<br>`txManagerFactory = cfg.getTxManagerFactory();`<br>`useJtaSync = cfg.isUseJtaSynchronization();`<br>`txAwareQueriesEnabled = false;` |
| `userAttributes` | Задает пользовательские атрибуты для узла | `Map<String,?>` | — |
| `utilityCacheKeepAliveTime` | Устанавливает время сохранения размера пула потоков, который будет использоваться для обработки сообщений служебного кеша | long | `DFLT_THREAD_KEEP_ALIVE_TIME = 60_000L` |
| `utilityCachePoolSize` | Устанавливает размер пула потоков, который будет использоваться для обработки сообщений служебного кеша | int | `DFLT_SYSTEM_CORE_THREAD_CNT = DFLT_PUBLIC_THREAD_CNT = max(8, AVAILABLE_PROC_CNT)`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` |
| `waitForSegmentOnStart` | Устанавливает флаг ожидания сегмента при запуске | boolean | `DFLT_WAIT_FOR_SEG_ON_START = true`<br><br>По умолчанию узел будет ожидать завершения инициализации всех сегментов перед началом работы. Такой подход гарантирует, что все необходимые данные будут доступны сразу после запуска узла |
| `warmupClosure` | Устанавливает завершение прогрева (warm-up) узла перед его полным запуском | `IgniteInClosure<IgniteConfiguration>` | — |
| `workDirectory` | Устанавливает рабочую директорию DataGrid | String | `(${IGNITE_HOME}/work)`<br><br>Если переменная окружения `IGNITE_HOME` не установлена, рабочая директория будет создана в текущем рабочем каталоге процесса |

## TcpDiscoverySpi

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `ackTimeout` | Используется для настройки тайм-аута для получения подтверждения (acknowledgment timeout) о приеме отправленных сообщений, которые передаются между узлами кластера | long | `DFLT_ACK_TIMEOUT = 5000`<br>`DFLT_ACK_TIMEOUT_CLIENT = 5000` | мс |
| `addressFilter` | Используется для настройки фильтра для IP-адресов | `IgnitePredicate<InetSocketAddress>` | — | — |
| `addressResolver` | Устанавливает resolver адресов, используется для настройки механизма разрешения адресов | `AddressResolver` | — | — |
| `authenticator` | Используется для настройки аутентификатора узлов, который обеспечивает проверку подлинности узлов при их присоединении к кластеру | `DiscoverySpiNodeAuthenticator` | — | — |
| `clientReconnectDisabled` | Устанавливает флаг отключения повторного подключения клиента, используется для настройки возможности автоматического переподключения клиентов к кластеру | boolean | — | — |
| `connectionRecoveryTimeou`t | Используется для установки максимального времени восстановления соединения, в течение которого клиент будет пытаться восстановить соединение с кластером после его потери | long | `DFLT_FAILURE_DETECTION_TIMEOUT = 10_000` | мс |
| `dataExchange` | Используется для настройки обработчика обмена начальными данными между узлами DataGrid | `DiscoverySpiDataExchange` | — | — |
| `internalListener` | Устанавливает внутренний слушатель, используется только для тестирования | `org.apache.ignite.internal.managers.discovery.IgniteDiscoverySpiInternalListener` | — | — |
| `ipFinder` | Используется для настройки поиска IP-адресов узлов в кластере | `TcpDiscoveryIpFinder` | `TcpDiscoveryMulticastIpFinder` | — |
| `ipFinderCleanFrequency` | Устанавливает частоту очистки IP Finder | long | `DFLT_IP_FINDER_CLEAN_FREQ = 60 * 1000` | мс |
| `joinTimeout` | Устанавливает тайм-аут присоединения | long | `DFLT_JOIN_TIMEOUT = 0` | мс |
| `listener` | Устанавливает слушатель для обнаружения (discovery) событий | `@Nullable DiscoverySpiListener` | — | — |
| `localAddress` | Устанавливает сетевые адреса для Discovery SPI | String | — | — |
| `localPort` | Устанавливает локальный порт для прослушивания | int | `DFLT_PORT = 47500` | — |
| `localPortRange` | Диапазон для локальных портов | int | `DFLT_PORT_RANGE = 100` | — |
| `maxAckTimeout` | Устанавливает максимальный тайм-аут для получения подтверждения о приеме отправленного сообщения | long | `DFLT_MAX_ACK_TIMEOUT = 10 * 60 * 1000` | мс |
| `metricsProvider` | Устанавливает поставщика метрик обнаружения (discovery) | `DiscoveryMetricsProvider` | — | — |
| `name` | Устанавливает имя SPI | String | — | — |
| `networkTimeout` | Устанавливает максимальный сетевой тайм-аут для использования в сетевых операциях | long | `DFLT_NETWORK_TIMEOUT = 5000` | мс |
| `nodeAttributes, version` | Задает атрибуты узла и его версию, которые будут распространены по сети в процессе присоединения узла к кластеру | `Map<String,Object>, IgniteProductVersion` | — | — |
| `reconnectCount` | Задает количество попыток узла установить (или восстановить) соединение с другим узлом | int | `DFLT_RECONNECT_CNT = 10` | — |
| `reconnectDelay` | Задает интервал, в течение которого узел находится в ожидании перед повторной попыткой подключения к кластеру | int | `DFLT_RECONNECT_DELAY = 2000` | мс |
| `socketTimeout` | Задает время ожидания операций сокета. Данное время ожидания используется для ограничения времени соединения и записи в сокет | long | `DFLT_SOCK_TIMEOUT = 5000`<br>`DFLT_SOCK_TIMEOUT_CLIENT = 5000` | мс |
| `soLinger` | Задает время задержки при закрытии сокетов TCP, которые используются Discovery SPI. Подробности по настройке этого параметра можно посмотреть в Java API (`Socket.setSoLinger`).<br><br>В DataGrid по умолчанию установлено неотрицательное значение тайм-аута, чтобы предотвратить потенциальные блокировки с SSL-соединениями. Это может увеличить время обнаружения сбоев в узлах кластера. Можно обновить JRE до той версии, в которой исправлена проблема с SSL, и настроить свойство после этого | int | `DFLT_SO_LINGER = 0` | — |
| `statisticsPrintFrequency` | Задает частоту отображения статистики. Значение `0` — вывод статистики не нужен. Если данное значение больше нуля, а в логах отображается информация, значит статистика отображается вместе с уровнем `INFO` раз в период. Это может быть крайне полезно для отслеживания проблем топологии | long | `DFLT_STATS_PRINT_FREQ = 0` | мс |
| `threadPriority` | Задает приоритет для потоков, которые запущены SPI | int | `DFLT_THREAD_PRI = 10` | — |
| `topHistorySize` | Задает максимальное количество хранимых версий снепшотов топологии кластера | int | `DFLT_TOP_HISTORY_SIZE = 1000` | — |

### TcpDiscoveryJdbcIpFinder

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `registerAddresses` | Регистрирует новые адреса | `Collection<InetSocketAddress>` | — | — |
| `dataSource` | Задает источник данных | `DataSource` | — | — |
| `initScheme` | Устанавливает флаг, который указывает, должна ли схема базы данных инициализироваться с помощью DataGrid (поведение по умолчанию) или должна быть явно создана пользователем | `boolean` | `true` | — |
| `shared` | Устанавливает флаг общего доступа. Если у параметра установлено значение `true`, предполагается, что IP-адреса, которые зарегистрированы с помощью IP Finder, будут видны им на всех остальных узлах | `boolean` | — | — |
| `unregisterAddresses` | Отменяет регистрацию представленных адресов | `Collection<InetSocketAddress` | — | — |

### TcpDiscoveryMulticastIpFinder

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `initializeLocalAddresses` | Инициализирует локальные адреса, к которым осуществляется привязка по Discovery SPI | `Collection<InetSocketAddress>` | — | — |
| `addressRequestAttempts` | Устанавливает количество попыток отправки Multicast-запроса | int | `DFLT_ADDR_REQ_ATTEMPTS = 2` | — |
| `localAddress` | Задает адрес локального сервера, который используется `TcpDiscoveryMulticastIpFinder` | String | Если не указано, свойство инициализирует локальный адрес, который установлен в конфигурации `{@link org.apache.ignite.spi.discovery.tcp.TcpDiscoverySpi}` | — |
| `multicastGroup` | Устанавливает IP-адрес Multicast-группы | String | `DFLT_MCAST_GROUP = "xxx.x.x.x"` | — |
| `multicastPort` | Устанавливает номер порта, на который отправляются Multicast-сообщения | int | `DFLT_MCAST_PORT = 47400` | — |
| `responseWaitTime` | Устанавливает время, в течение которого IP Finder ожидает ответа на Multicast-запрос | int | `DFLT_RES_WAIT_TIME = 500` | мс |
| `shared` | Устанавливает флаг совместного использования | boolean | — | — |
| `timeToLive` | Устанавливает время жизни по умолчанию для Multicast-пакетов, которые отправляются с помощью данного IP Finder для контроля области действия Multicast | int | `-1` | — |

### TcpDiscoverySharedFsIpFinder

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `registerAddresses` | Регистрирует новые адреса | `Collection<InetSocketAddress>` | — | — |
| `path` | Устанавливает путь | String | `DFLT_PATH = "disco/tcp"` | — |
| `shared` | Устанавливает флаг совместного использования | boolean | — | — |
| `unregisterAddresses` | Отменяет регистрацию представленных адресов | `Collection<InetSocketAddress>` | — | — |

### TcpDiscoveryVmIpFinder

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `registerAddresses` | Регистрирует новые адреса | `Collection<InetSocketAddress>` | — | — |
| `addresses` | Разбирает предоставленные значения и инициализирует внутреннюю коллекцию адресов | `Collection<String>` | — | — |
| `shared` | Устанавливает флаг совместного использования | boolean | — | — |
| `unregisterAddresses` | Отменяет регистрацию представленных адресов | `Collection<InetSocketAddress>` | — | — |

## ZookeeperDiscoverySpi

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `authenticator` | Устанавливает аутентификатор узлов для Discovery SPI | `DiscoverySpiNodeAuthenticator` | — | — |
| `clientReconnectDisabled` | Устанавливает флаг отключения повторного подключения клиента | boolean | — | — |
| `dataExchange` | Устанавливает обработчик для первоначального обмена данными между узлами DataGrid | `DiscoverySpiDataExchange` | — | — |
| `internalListener` | Используется только для тестов | `org.apache.ignite.internal.managers.discovery.IgniteDiscoverySpiInternalListener` | — | — |
| `joinTimeout` | Устанавливает тайм-аут процесса присоединения узла к кластеру. Этот тайм-аут определяет максимальное время, в течение которого узел будет пытаться присоединиться к существующему кластеру перед тем, как операция будет считаться неудачной | long | `DFLT_JOIN_TIMEOUT = 0` (отсутствие ограничения по времени для процесса присоединения) | — |
| `listener` | Устанавливает слушатель для событий обнаружения (discovery) | `DiscoverySpiListener` | — | — |
| `metricsProvider` | Устанавливает поставщик метрик обнаружения | `DiscoveryMetricsProvider` | — | — |
| `nodeAttributes, version` | Задает атрибуты узла и его версию, которые будут распространены по сети в процессе присоединения узла к кластеру | `Map<String,Object>, IgniteProductVersion` | — | — |
| `sessionTimeout` | Устанавливает тайм-аут сессии ZooKeeper. Тайм-аут определяет максимальное время, в течение которого сессия ZooKeeper может оставаться неактивной, прежде чем она будет закрыта | long | — | — |
| `zkConnectionString` | Используется для настройки строки подключения к ZooKeeper. Строка содержит информацию о серверах ZooKeeper, к которым нужно подключаться для координации действий узлов в кластере | String | — | — |
| `zkRootPath` | Устанавливает корневой путь в ZooKeeper, по которому будут храниться данные о состоянии узлов и кластеров | String | `DFLT_ROOT_PATH = "/apacheIgnite"` | — |

## TcpCommunicationSpi

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `ackSndThreshold` | Определяет, сколько сообщений должно быть получено при соединении с узлом, прежде чем будет отправлено подтверждение | int | `DFLT_ACK_SND_THRESHOLD = 32` | — |
| `addressResolver` | Устанавливает resolver адресов | `AddressResolver` | — | — |
| `connectionRequestor` | Устанавливает обработчик запросов соединений (`ConnectionRequestor`) | `ConnectionRequestor` | — | — |
| `connectionsPerNode` | Устанавливает максимальное количество соединений на узел (`maxConnectionsPerNode`) | int | `DFLT_CONN_PER_NODE = 1` | — |
| `connectTimeout` | Задает тайм-аут подключения, который применяется при установлении соединения с удаленными узлами. Значение `0` — бесконечный тайм-аут | long | `DFLT_CONN_TIMEOUT = 5000` | мс |
| `directBuffer` | Определяет, какой тип буфера будет выделен в SPI: прямой (direct) буфер или heap-буфер. Если у параметра установлено значение `true`, SPI использует метод `ByteBuffer.allocateDirect(int)`. В противном случае SPI использует метод `ByteBuffer.allocate(int)` | boolean | `directBuf = true` | — |
| `directSendBuffer` | Устанавливает использование прямого буфера для отправки данных | boolean | `false` | — |
| `filterReachableAddresses` | Устанавливает фильтр для доступных адресов. Если у параметра установлено значение `true`, при создании TCP-клиента будет включена фильтрация доступных адресов | boolean | `DFLT_FILTER_REACHABLE_ADDRESSES = false` | — |
| `forceClientToServerConnections` | Предназначен только для клиентских узлов. Активирует режим PSI (Port Stripping Interface), в котором серверный узел не может установить TCP-соединение с текущим узлом. Возможными причинами могут быть особенности настройки сети или правила безопасности. В таком режиме, когда серверу нужно подключиться к клиенту, он использует протокол `DiscoverySpi` для оповещения клиента. После этого клиент сам инициирует требуемое соединение | boolean | — | — |
| `idleConnectionTimeout` | Задает максимально допустимое время простоя соединения, после которого соединение с клиентом будет разорвано | long | `DFLT_IDLE_CONN_TIMEOUT = 10 * 60_000` | мс |
| `localAddress` | Задает локальный адрес хоста, который будет использоваться для привязки сокетов. Следует учитывать, что у узла может быть несколько адресов, включая адрес обратной связи. Данный параметр является необязательным | String | Любой доступный локальный IP-адрес | — |
| `localPort` | Устанавливает локальный порт для привязки сокета | int | `DFLT_PORT = 47100` | — |
| `localPortRange` | Задает диапазон локальных портов для портов локального хоста (значение должно быть больше или равно `<tt>0</tt>`). Если указанный локальный порт уже занят, система попробует увеличивать номер порта, пока он не станет меньше начального значения плюс этот диапазон | int | `DFLT_PORT_RANGE = 100` | — |
| `maxConnectTimeout` | Задает максимальный тайм-аут для установки соединения. Если подтверждение подключения (handshake) не удается завершить в пределах установленного тайм-аута, SPI повторяет попытку с увеличенным временем ожидания. Тайм-аут может постепенно увеличиваться вплоть до максимального значения. Если максимальное значение достигнуто, попытка подключения считается неудавшейся | long | `DFLT_MAX_CONN_TIMEOUT = 10 * 60 * 1000` | мс |
| `messageQueueLimit` | Устанавливает лимит для очередей входящих и исходящих сообщений. При положительном значении размер очереди отправки ограничивается установленным пределом. Значение `0` отключает ограничения на размер очереди | int | `DFLT_MSG_QUEUE_LIMIT = GridNioServer.DFLT_SEND_QUEUE_LIMIT =0` | — |
| `name` | Устанавливает имя SPI | String | — | — |
| `reconnectCount` | Задает максимальное количество попыток переподключения при установке соединения с удаленными (remote) узлами | int | `DFLT_RECONNECT_CNT = 10` | — |
| `selectorsCount` | Устанавливает количество селекторов, которые будут использоваться на TCP-сервере | int | `DFLT_SELECTORS_CNT = Math.max(4, Runtime.getRuntime().availableProcessors() / 2)` | — |
| `selectorSpins` | Определяет, сколько раз нужно вызвать неблокирующий метод `selector.selectNow()`, прежде чем перейти к вызову `selector.select(long)` на NIO-сервере. Чтобы потоки селектора никогда не блокировались, установите значение `Long.MAX_VALUE` | long | `0` | — |
| `slowClientQueueLimit` | Задает ограничение на размер очереди для медленных клиентов. Если установлено положительное значение, коммуникационный SPI будет контролировать размеры очередей исходящих сообщений клиентов и отсекать тех, чьи очереди превышают данный лимит. Это значение должно быть меньше или равно значению, которое установлено в `getMessageQueueLimit()` (управляет контролем обратного давления сообщений для серверных узлов) | int | `0` (`unlimited` — неограниченный) | — |
| `socketReceiveBuffer` | Задает размер буфера для приема данных в сокетах, которые создаются или принимаются данным SPI | int | `DFLT_SOCK_BUF_SIZE = 32 * 1024` | — |
| `socketSendBuffer` | Задает размер буфера передачи для сокетов, которые создаются или принимаются данным SPI | int | `DFLT_SOCK_BUF_SIZE = 32 * 1024` | — |
| `socketWriteTimeout` | Задает тайм-аут записи в сокет для TCP-соединений. Если сообщение не удается записать в сокет в рамках этого интервала, соединение закрывается и предпринимается попытка переподключения | long | `DFLT_SOCK_WRITE_TIMEOUT = 2000` | мс |
| `tcpNoDelay` | Задает значение опции сокета `TCP_NODELAY`. Все сокеты будут открыты с использованием заданного значения. Если у параметра установлено значение `true`, алгоритм Nagle для сокета отключится. Это уменьшит задержку и время доставки маленьких сообщений. Для систем, которые работают под высокой сетевой нагрузкой, рекомендуется установить для параметра значение `false` | boolean | `DFLT_TCP_NODELAY = true` | — |
| `unacknowledgedMessagesBufferSize` | Задает максимальное количество неподтвержденных сообщений, которые могут храниться для каждого соединения с узлом. Если их количество превышает это значение, соединение с узлом разрывается, и выполняется попытка переподключения | int | — | — |
| `usePairedConnections` | Определяет необходимость принудительной установки двухсокетного соединения между узлами.<br><br>Если у параметра установлено значение `true`, между связанными узлами будет установлено два отдельных соединения: одно для исходящих сообщений и одно для входящих. Если у параметра установлено значение `false`, для обоих направлений будет использоваться одно TCP-соединение. Этот флаг будет полезен для некоторых операционных систем, в которых доставка сообщений занимает слишком много времени | boolean | `false` | — |

## DataStorageConfiguration

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `alwaysWriteFullPages` | Устанавливает флаг, который обеспечивает запись полной страницы в WAL (Write-Ahead Log) при каждом изменении (вместо записи дельты изменений) | boolean | `DFLT_WAL_ALWAYS_WRITE_FULL_PAGES = false` | — |
| `cdcWalDirectoryMaxSize` | Устанавливает максимальный размер каталога CDC в байтах | long | `DFLT_CDC_WAL_DIRECTORY_MAX_SIZE = 0` (`unlimited` — неограниченный) | — |
| `cdcWalPath` | Устанавливает путь к каталогу CDC | long | `DFLT_WAL_CDC_PATH = "db/wal/cdc"` | — |
| `checkpointFrequency` | Устанавливает частоту создания контрольных точек, которая определяет минимальный интервал записи «грязных» страниц в постоянное хранилище | long | `DFLT_CHECKPOINT_FREQ = 180000` | — |
| `checkpointReadLockTimeout` | Устанавливает тайм-аут для получения блокировки чтения при создании контрольной точки | long | — | — |
| `checkpointThreads` | Устанавливает количество потоков, которые используются для создания контрольных точек | int | `DFLT_CHECKPOINT_THREADS = 4` | — |
| `checkpointWriteOrder` | Определяет порядок записи страниц в дисковое хранилище во время создания контрольных точек | `CheckPointWriteOrder` | `DFLT_CHECKPOINT_WRITE_ORDER = CheckpointWriteOrder.SEQUENTIAL` | — |
| `concurrencyLevel` | Устанавливает количество параллельных сегментов во внутренних таблицах отображения страниц DataGrid | int | `Runtime.getRuntime().availableProcessors()` | — |
| `dataRegionConfigurations` | Устанавливает конфигурацию регионов данных | `DataRegionConfiguration` | — | — |
| `defaultDataRegionConfiguration` | Переопределяет конфигурацию регионов данных по умолчанию, которая была создана автоматически | `DataRegionConfiguration` | `DFLT_METRICS_ENABLED = false`<br>`DFLT_SUB_INTERVALS = 5`<br>`DFLT_RATE_TIME_INTERVAL_MILLIS = 60_000`<br>`DFLT_PAGE_REPLACEMENT_MODE = PageReplacementMode.CLOCK`<br>`DFLT_DATA_REG_DEFAULT_NAME = "default"`<br>`maxSize = DataStorageConfiguration.DFLT_DATA_REGION_MAX_SIZE =`<br>`Math.max(`<br>   `(long)(DFLT_DATA_REGION_FRACTION * U.getTotalMemoryAvailable()),`<br>    `DFLT_DATA_REGION_INITIAL_SIZE)`, где <br>`DFLT_DATA_REGION_FRACTION = 0.2`<br>`DFLT_DATA_REGION_INITIAL_SIZE =256L * 1024 * 1024`<br>`initSize = Math.min(DataStorageConfiguration.DFLT_DATA_REGION_MAX_SIZE, DataStorageConfiguration.DFLT_DATA_REGION_INITIAL_SIZE)`, где<br>`DFLT_DATA_REGION_MAX_SIZE = Math.max((long)(DFLT_DATA_REGION_FRACTION * U.getTotalMemoryAvailable()), DFLT_DATA_REGION_INITIAL_SIZE)`<br>и `DFLT_DATA_REGION_INITIAL_SIZE = 256L * 1024 * 1024`<br>`pageReplacementMode = DFLT_PAGE_REPLACEMENT_MODE` | — |
| `defaultWarmUpConfiguration` | Устанавливает конфигурацию прогрева (warm-up) по умолчанию | `@Nullable WarmUpConfiguration` | — | — |
| `defragmentationThreadPoolSize` | Устанавливает максимальное количество партиций, которые могут одновременно дефрагментироваться | int | `DFLT_DEFRAGMENTATION_THREAD_POOL_SIZE = 4` | — |
| `encryptionConfiguration` | Устанавливает настройки шифрования | `EncryptionConfiguration` | `DFLT_REENCRYPTION_BATCH_SIZE = 100`<br><br>`DFLT_REENCRYPTION_RATE_MBPS = 0.0` | — |
| `extraStoragePathes` | Указывает диски в конфигурации серверных узлов (для хранения кешей на разных дисках). Диски можно указать с помощью списка:<br><br>`<list>`<br>`<value>/opt/disk1</value>`<br>`<value>/opt/disk2</value>`<br>`</list>`<br><br>или с помощью свойства: `<property name="extraStoragePathes" value="/opt/disk1>`.<br><br>При создании кеша в его конфигурации нужно вызвать `setStoragePath` и передать в него один из путей, которые указали в `DataStorageConfiguration`:<br><br>`client.createCache(new CacheConfiguration<>()`<br>`.setStoragePath("/opt/disk1")`<br>`.setName("newCache");` | String | — | — |
| `fileIOFactory` | Устанавливает фабрику, которая реализует интерфейс `FileIO` для использования при операциях чтения/записи файлов данных | `org.apache.ignite.internal.processors.cache.persistence.file.FileIOFactory` | — | — |
| `lockWaitTime` | Устанавливает время, в течение которого ожидается захват файла блокировки постоянного хранилища, прежде чем произойдет сбой локального узла | long | `DFLT_LOCK_WAIT_TIME = 10 * 1000` | мс |
| `walArchiveMaxSize` | Устанавливает максимальный размер WAL-архива в файловой системе | long | `DFLT_WAL_ARCHIVE_MAX_SIZE = 1024 * 1024 * 1024` (1 Гб) | б |
| `memoryAllocator` | Устанавливает распределитель памяти по умолчанию для всех областей памяти | `MemoryAllocator` | `memoryAllocator = null` | — |
| `metricsEnabled` | Устанавливает флаг, который указывает, включен ли сбор показателей персистентности | `DFLT_METRICS_ENABLED = false` | — |
| `metricsRateTimeInterval` | Устарел, используйте параметр `MetricsMxBean.configureHitRateMetric(String, long)` | long | `DFLT_RATE_TIME_INTERVAL_MILLIS = 60_000` | мс |
| `metricsSubIntervalCnt` | Устарел, используйте параметр `MetricsMxBean.configureHitRateMetric(String, long)` | int | `DFLT_SUB_INTERVALS = 5` | — |
| `minWalArchiveSize` | Устанавливает минимальный размер WAL-архива в файловой системе | long | — | — |
| `pageSize` | Меняет размер страницы | int | `DFLT_PAGE_SIZE = 4 * 1024` | б |
| `persistenceStorePath` | Устанавливает путь к корневому каталогу, в котором постоянное хранилище будет сохранять данные и индексы | String | — | — |
| `systemDataRegionConfiguration` | Переопределяет конфигурацию системной области данных, которая была создана автоматически | `SystemDataRegionConfiguration` | `DFLT_SYS_REG_INIT_SIZE = 40L * 1024 * 1024`<br><br>`DFLT_SYS_REG_MAX_SIZE = 100L * 1024 * 1024` | Мб |
| `systemRegionInitialSize` | Устарел, используйте параметр `SystemDataRegionConfiguration.setInitialSize(long)` | long | `DFLT_SYS_REG_INIT_SIZE = 40L * 1024 * 1024` | Мб |
| `systemRegionMaxSize` | Устарел, используйте параметр `SystemDataRegionConfiguration.setMaxSize(long)` | long | `DFLT_SYS_REG_MAX_SIZE = 100L * 1024 * 1024` | Мб |
| `walArchivePath` | Устанавливает путь к WAL-архиву | String | `DFLT_WAL_ARCHIVE_PATH = "db/wal/archive"` | — |
| `walAutoArchiveAfterInactivity` | Установка этого значения с режимом `WALMode.FSYNC` может привести к увеличению размера файлов для WAL при редком использовании кластера | long | `walAutoArchiveAfterInactivity = -1` | — |
| `walBufferSize` | Устанавливает размер буфера WAL | int | — | — |
| `walCompactionEnabled` | Устанавливает флаг, который указывает, включен ли режим сжатия WAL-архива | boolean | `DFLT_WAL_COMPACTION_ENABLED = false` | — |
| `walCompactionLevel` | Устанавливает уровень сжатия WAL-журнала. Уровень сжатия влияет на баланс между скоростью обработки записей и степенью их сжатия | int | `DFLT_WAL_COMPACTION_LEVEL = Deflater.BEST_SPEED = 1` (уровень сжатия для самой быстрой компрессии) | — |
| `walFlushFrequency` | Устанавливает, как часто WAL-журнал будет синхронизироваться с файловой системой в фоновом режиме | long | `DFLT_WAL_FLUSH_FREQ = 2000` | мс |
| `walForceArchiveTimeout` | Устанавливает тайм-аут для принудительной отправки сегмента WAL-журнала в архив (даже если обработка сегмента не завершена).<br><br>Обязательно установите тайм-аут, иначе репликация будет происходить только при архивировании WAL-сегмента по его заполненности, что непредсказуемо по длительности. Расхождения между кластерами в таком случае могут достигать нескольких минут или десятков минут (зависит от нагрузки). Если нагрузка низкая, ротация может происходить еще реже | long | `walForceArchiveTimeout = -1` (`disabled` — отключен) | — |
| `walFsyncDelayNanos` | Устанавливает свойство, которое позволяет обменять задержку на пропускную способность в режиме `WALMode.FSYNC` | long | `DFLT_WAL_FSYNC_DELAY = 1000` | нс |
| `walHistorySize` | Устарел, для управления размером WAL-архива используйте параметр `maxWalArchiveSize` | int | `DFLT_WAL_HISTORY_SIZE = 20` | — |
| `walMode` | Устанавливает свойство, которое определяет поведение `fsync` для WAL-журнала | `WALMode` | `DFLT_WAL_MODE = WALMode.LOG_ONLY` | — |
| `walPageCompression` | Устанавливает алгоритм сжатия для записей снепшотов WAL-страниц | `DiskPageCompression` | `DFLT_WAL_PAGE_COMPRESSION = DiskPageCompression.DISABLED` | — |
| `walPageCompressionLevel` | Устанавливает уровень сжатия страниц, который подходит для выбранного алгоритма | Integer | Если у `walPageCompressionLevel` установлено значение `null`, будет использоваться значение по умолчанию: `Zstd` — от `-131072` до `22` (по умолчанию `3`), `LZ4` — от `0` до `17` (по умолчанию `0`) | — |
| `walStorePath` | Устанавливает путь к каталогу, в котором хранятся активные сегменты WAL-журнала | String | `DFLT_WAL_PATH = "db/wal"` | — |
| `walRecordIteratorBufferSize` | Устанавливает свойство, которое определяет, сколько байтов итератор читает с диска (за одно чтение) при прохождении WAL-журнала | int | `DFLT_WAL_RECORD_ITERATOR_BUFFER_SIZE = 64 * 1024 * 1024` | Мб |
| `walSegments` | Устанавливает количество сегментов WAL-журнала, с которыми необходимо работать | int | `DFLT_WAL_SEGMENTS = 10` | — |
| `walSegmentSize` | Устанавливает размер файла сегмента WAL-журнала | int | `DFLT_WAL_SEGMENT_SIZE = 64 * 1024 * 1024` | Мб |
| `walThreadLocalBufferSize` | Устанавливает размер буфера, который выделяется для каждого потока | int | `DFLT_TLB_SIZE = 128 * 1024` | Кб |
| `writeThrottlingEnabled` | Устанавливает флаг, который указывает, включена ли функция ограничения записи | boolean | `DFLT_WRITE_THROTTLING_ENABLED = false` | — |

## DataRegionConfiguration

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `cdcEnabled` | Устанавливает флаг включения CDC на серверном узле для региона данных. Флаг явно настраивает регионы данных, для которых CDC включен | boolean | `false` | — |
| `checkpointPageBufferSize` | Устанавливает размер буфера страницы для контрольных точек | long | — | — |
| `emptyPagesPoolSize` | Указывает минимальное количество пустых страниц, которые должны присутствовать в списках повторного использования для этой области данных | int | `100` | — |
| `evictionThreshold` | Устанавливает порог вытеснения страниц в памяти | double | `0.9` (память страниц начнет вытеснение только после того, как область данных будет занята на 90%) | — |
| `initialSize` | Устанавливает первоначальный размер области памяти, который определяется данной областью данных | long | `initSize = Math.min(`<br>    `DataStorageConfiguration.DFLT_DATA_REGION_MAX_SIZE, DataStorageConfiguration.DFLT_DATA_REGION_INITIAL_SIZE),` <br>где<br>`DFLT_DATA_REGION_INITIAL_SIZE = 256L * 1024 * 1024`<br>`DFLT_DATA_REGION_MAX_SIZE = Math.max(`<br>    `(long)(DFLT_DATA_REGION_FRACTION * U.getTotalMemoryAvailable()),`<br>    `DFLT_DATA_REGION_INITIAL_SIZE);`<br>где<br>`DFLT_DATA_REGION_FRACTION = 0.2`<br>`DFLT_DATA_REGION_INITIAL_SIZE = 256L * 1024 * 1024` | Мб |
| `lazyMemoryAllocation` | Устанавливает флаг значения `lazyMemoryAllocation` (отложенного распределения памяти) | boolean | `true` (память для региона данных будет выделяться только при создании первого кеша, который принадлежит этому региону) | — |
| `maxSize` | Устанавливает максимальный размер области памяти, которая определена этим регионом данных | long | `maxSize = DataStorageConfiguration.DFLT_DATA_REGION_MAX_SIZE =``Math.max(`<br>`(long)(DFLT_DATA_REGION_FRACTION * U.getTotalMemoryAvailable()),`<br>`DFLT_DATA_REGION_INITIAL_SIZE),` где <br>`DFLT_DATA_REGION_FRACTION = 0.2`<br>`DFLT_DATA_REGION_INITIAL_SIZE = 256L * 1024 * 1024` (размер области данных по умолчанию составляет 20% от доступной физической памяти на текущем устройстве) | — |
| `memoryAllocator` | Устанавливает распределитель памяти | `MemoryAllocator` | `memoryAllocator = null` | — |
| `metricsEnabled` | Устанавливает флаг включения метрик памяти | boolean | `DFLT_METRICS_ENABLED = false` | — |
| `metricsRateTimeInterval` | Устарел, используйте параметр `MetricsMxBean.configureHitRateMetric(String, long)` | long | `DFLT_RATE_TIME_INTERVAL_MILLIS = 60_000` | мс |
| `metricsSubIntervalCount` | Устарел, используйте параметр `MetricsMxBean.configureHitRateMetric(String, long)` | int | `DFLT_SUB_INTERVALS = 5` | — |
| `name` | Устанавливает имя области данных | String | `DFLT_DATA_REG_DEFAULT_NAME = "default"` | — |
| `pageEvictionMode` | Устанавливает режим вытеснения страниц памяти | `DataPageEvictionMode` | `DataPageEvictionMode.DISABLED` | — |
| `pageReplacementMode` | Устанавливает режим замены страниц памяти | `PageReplacementMode` | `DFLT_PAGE_REPLACEMENT_MODE = PageReplacementMode.CLOCK` | — |
| `persistenceEnabled` | Устанавливает флаг включения режима постоянного persistence-хранилища данных | boolean | `persistenceEnabled = false` | — |
| `swapPath` | Устанавливает путь к файлам, которые отображаются в памяти | String | — | — |
| `warmUpConfiguration` | Устанавливает настройки прогрева (warm-up) региона данных | `WarmUpConfiguration` | При установленном значении `null` будет использоваться конфигурация по умолчанию `DataStorageConfiguration.getDefaultWarmUpConfiguration` | — |

## CacheConfiguration

| Название параметра | Описание | Тип | Значение по умолчанию | Единицы измерения |
|---|---|---|---|---|
| `affinity` | Устанавливает affinity-функцию для ключей кеша | `AffinityFunction` | — | — |
| `affinityMapper` | Устанавливает пользовательский affinity-преобразователь | `AffinityKeyMapper` | Реализация `AffinityKeyMapper` по умолчанию | — |
| `atomicityMode` | Устанавливает атомарный режим кешей | `CacheAtomicityMode` | `DFLT_CACHE_ATOMICITY_MODE = CacheAtomicityMode.ATOMIC` | — |
| `backups` | Устанавливает количество резервных копий в режиме кеширования `PARTITIONED` | int | `DFLT_BACKUPS = 0` | — |
| `cacheLoaderFactory` | Устанавливает фабрику для создания экземпляра загрузчика кеша (`CacheLoader`) для заданного типа ключей `K` и значений `V` | `javax.cache.configuration.Factory<? extends javax.cache.integration.CacheLoader<K,V>>` | — | — |
| `cacheMode` | Устанавливает режим кеширования | `CacheMode` | `DFLT_CACHE_MODE = CacheMode.PARTITIONED` | — |
| `cacheStoreFactory` | Устанавливает фабрику для хранения данных кеша в постоянном хранилище | `javax.cache.configuration.Factory<? extends CacheStore<? super K,? super V>>` | — | — |
| `cacheStoreSessionListenerFactories` | Устанавливает фабрики слушателей сеансов реализации `CacheStore` | `javax.cache.configuration.Factory<? extends CacheStoreSessionListener>...` | — | — |
| `cacheWriterFactory` | Устанавливает фабрику для создания экземпляра записывающего устройства кеша (`CacheWriter`) для заданного типа ключей `K` и значений `V` | `javax.cache.configuration.Factory<? extends javax.cache.integration.CacheWriter<? super K,? super V>>` | — | — |
| `copyOnRead` | Устанавливает флаг копирования при чтении | boolean | `DFLT_COPY_ON_READ = true` | — |
| `dataRegionName` | Устанавливает имя конфигурации региона данных для данного кеша | String | `DFLT_DATA_REG_DEFAULT_NAME = "default"` | — |
| `diskPageCompression` | Устанавливает алгоритм сжатия дисковых страниц | `DiskPageCompression` | `IgniteSystemProperties.getEnum(DiskPageCompression.class, IGNITE_DEFAULT_DISK_PAGE_COMPRESSION);`<br>`IGNITE_DEFAULT_DISK_PAGE_COMPRESSION = "IGNITE_DEFAULT_DISK_PAGE_COMPRESSION"` | — |
| `diskPageCompressionLevel` | Устанавливает уровень сжатия дисковых страниц, специфичный для выбранного алгоритма | Integer | Если у `diskPageCompressionLevel` установлено значение `null`, будет использоваться значение по умолчанию: `Zstd` — от `-131072` до `22` (по умолчанию `3`), `LZ4` — от `0` до `17` (по умолчанию `0`) | — |
| `eagerTtl` | Устанавливает поведение, при котором устаревшие записи можно удалять из кеша сразу или при первом обращении к ним во время кеш-операции | boolean | `DFLT_EAGER_TTL = true` | — |
| `encryptionEnabled` | Используется для включения или отключения шифрования данных в кеше | boolean | — | — |
| `eventsDisabled` | Устанавливает флаг отключения генерации событий в кеше | boolean | `DFLT_EVENTS_DISABLED = false` | — |
| `evictionFilter` | Используется для установки фильтра `EvictionFilter` для вытеснения элементов из кеша. `EvictionFilter` определяет, какие элементы подлежат удалению из кеша при достижении определенного порога заполнения | `EvictionFilter<K,V>` | `null` | — |
| `evictionPolicy` | Устарел, используйте параметр `setEvictionPolicyFactory(Factory)` | `EvictionPolicy` | `null` | — |
| `evictionPolicyFactory` | Устанавливает фабрику, которая создает политику вытеснения элементов из кеша | `javax.cache.configuration.Factory<? extends EvictionPolicy<? super K,? super V>>` | `null` | — |
| `expiryPolicyFactory` | Устанавливает фабрику, которая создает политику истечения срока действия элементов в кеше | `javax.cache.configuration.Factory<? extends javax.cache.expiry.ExpiryPolicy>` | — | — |
| `groupName` | Устанавливает объединение кешей в группы | String | — | — |
| `indexedTypes` | Устанавливает массив пар типов ключей и значений, которые подлежат индексации (поэтому у массива `indexedTypes` всегда должна быть четная длина) | `Class<?>...` | — | — |
| `interceptor` | Устанавливает перехватчик для кеша | `CacheInterceptor<K,V>` | — | — |
| `invalidate` | Используется для настройки поведения кеша относительно устаревших данных. Если у параметра `invalidate` установлено значение `true`, при выполнении транзакции данные в кеше будут помечены как устаревшие (недействительные) и впоследствии обновлены или удалены. Если установлено значение `false`, данные останутся актуальными | boolean | `false` | — |
| `cacheKeyConfiguration` | Устанавливает конфигурацию ключей кеша | `CacheKeyConfiguration...` | — | — |
| `loadPreviousValue` | Устанавливает флаг, который указывает, нужно ли загружать значение из хранилища, если оно отсутствует в кеше для операций с кешем: `IgniteCache.putIfAbsent(Object, Object)`, `IgniteCache.replace(Object, Object)`, `IgniteCache.replace(Object, Object, Object)`, `IgniteCache.remove(Object, Object)`, `IgniteCache.getAndPut(Object, Object)`, `IgniteCache.getAndRemove(Object)`, `IgniteCache.getAndReplace(Object, Object)`, `IgniteCache.getAndPutIfAbsent(Object, Object)` | boolean | `DFLT_LOAD_PREV_VAL = false` | — |
| `longQueryWarningTimeout` | Устарел, используйте параметр `IgniteConfiguration.setLongQueryWarningTimeout(long)` | long | `DFLT_LONG_QRY_WARN_TIMEOUT = 3000` | мс |
| `managementEnabled` | Устанавливает флаг включения или отключения функций управления кешем | boolean | `false` | — |
| `maxConcurrentAsyncOperations` | Устанавливает максимальное количество параллельных асинхронных операций | int | `DFLT_MAX_CONCURRENT_ASYNC_OPS = 500` | — |
| `maxQueryIteratorsCount` | Устанавливает максимальное количество хранимых итераторов запросов | int | `DFLT_MAX_QUERY_ITERATOR_CNT = 1024` | — |
| `memoryPolicyName` | Устарел, используйте параметр `setDataRegionName(String)` | String | `DFLT_DATA_REG_DEFAULT_NAME = "default"` | — |
| `name` | Устанавливает имя кеша | String | — | — |
| `nearConfiguration` | Устанавливает конфигурацию near-кеша, которая будет использоваться на всех узлах кеша | `NearCacheConfiguration<K,V>` | — | — |
| `nodeFilter` | Устанавливает `NodeFilter`, который определяет, на каких узлах должны храниться записи | `IgnitePredicate<ClusterNode>` | — | — |
| `onheapCacheEnabled` | Устанавливает включение/отключение дополнительного кеширования в Java Heap.<br><br>Кеширование в heap-памяти пригодится при большом количестве операций чтения кеша на серверных узлах, которые работают с записями кеша в бинарном формате или вызывают их десериализацию. Например, кеширование в heap-памяти пригодится при распределенных вычислениях или получении данных от кеша для дальнейшей обработки | boolean | `CacheConfiguration`: —<br>`ClientCacheConfiguration`: `onheapCacheEnabled = false` | — |
| `partitionLossPolicy` | Устанавливает политику потери партиций | `PartitionLossPolicy` | `DFLT_PARTITION_LOSS_POLICY = PartitionLossPolicy.IGNORE` | — |
| `platformCacheConfiguration` | Устанавливает конфигурацию платформенного кеша | `PlatformCacheConfiguration` | — | — |
| `cachePluginConfigurations` | Устанавливает конфигурацию подключаемых плагинов для кеша | `CachePluginConfiguration` | — | — |
| `queryDetailMetricsSize` | Устанавливает размер подробных метрик запросов, которые будут храниться в памяти для целей мониторинга | int | `DFLT_QRY_DETAIL_METRICS_SIZE = 0` | — |
| `queryEntities` | Устанавливает конфигурацию объектов сущностей запроса (Query Etities) | `Collection<QueryEntity>` | — | — |
| `queryParallelism` | Устанавливает степень параллелизма для выполнения запросов | int | `DFLT_QUERY_PARALLELISM = 1` | — |
| `readFromBackup` | Устанавливает флаг чтения из резервной копии | boolean | `DFLT_READ_FROM_BACKUP = true` | — |
| `isReadThrough` | Устанавливает режим сквозного чтения для кеша | boolean | `false` | — |
| `rebalanceBatchesPrefetchCount` | Устарел, используйте параметр `IgniteConfiguration.setRebalanceBatchesPrefetchCount(long)` | long | `DFLT_REBALANCE_BATCHES_PREFETCH_COUNT = 3` | — |
| `rebalanceBatchSize` | Устарел, используйте параметр `IgniteConfiguration.setRebalanceBatchSize(int)` | int | `DFLT_REBALANCE_BATCH_SIZE = 512 * 1024` (512 Кб) | б |
| `rebalanceDelay` | Параметр устарел, используйте функцию базовой (baseline) топологии. Данный API будет удален в будущих релизах | long | `0` | мс |
| `rebalanceMode` | Устанавливает режим ребалансировки кеша | `CacheRebalanceMode` | `DFLT_REBALANCE_MODE = CacheRebalanceMode.ASYNC` | — |
| `rebalanceOrder`<br>`StoreByValue` | Устанавливает последовательность, по которой должна выполняться ребаланcировка.<br><br>Значение больше нуля можно установить только для кешей с режимом ребалансировки `SYNC` или `ASYNC`. Ребалансировка для кешей с меньшим значением выполняется первой. По умолчанию ребалансировка не упорядочена | int | `0` | — |
| `rebalancePoolSize` | Устарел, используйте параметр `IgniteConfiguration.getRebalanceThreadPoolSize()` | int | `DFLT_REBALANCE_THREAD_POOL_SIZE = min(4, max(1, AVAILABLE_PROC_CNT / 4))`, где `AVAILABLE_PROC_CNT = Runtime.getRuntime().availableProcessors()` | — |
| `rebalanceThrottle` | Устарел, используйте параметр `IgniteConfiguration.setRebalanceThrottle(long)` | long | `DFLT_REBALANCE_THROTTLE = 0` | мс |
| `rebalanceTimeout` | Устарел, используйте параметр `IgniteConfiguration.setRebalanceTimeout(long)` | long | `DFLT_REBALANCE_TIMEOUT = 10000` | мс |
| `sqlEscapeAll` | Если установлено значение `true`, все имена таблиц и полей SQL будут заключены в двойные кавычки, например `{@code "tableName"}`. Настройка обеспечивает чувствительность к регистру имен полей и позволяет использовать специальные символы в именах таблиц и полей | boolean | — | — |
| `sqlFunctionClasses` | Устанавливает классы с методами, которые аннотированы как `QuerySqlFunction`, чтобы использовать их в качестве пользовательских функций в SQL-запросах | `Class<?>...` | — | — |
| `sqlIdxMaxInlineSize` | Устанавливает максимальный встроенный размер индекса для SQL-запросов | int | `DFLT_SQL_INDEX_MAX_INLINE_SIZE = -1` | — |
| `sqlOnheapCacheEnabled` | Устанавливает, включено ли кеширование в Java Heap для SQL-запросов | boolean | — | — |
| `sqlOnheapCacheMaxSize` | Устанавливает максимальный размер кеша SQL в Java Heap | int | `DFLT_SQL_ONHEAP_CACHE_MAX_SIZE = 0` | — |
| `sqlSchema` | Устанавливает SQL-схему для использования в текущем кеше | String | `""` | — |
| `statisticsEnabled` | Устанавливает флаг включения/отключения статистики о работе кеша | boolean | `false` | — |
| `isStoreByVal` | Устанавливает флаг хранения данных в кеше по значению вместо хранения по ссылке | boolean | `true` | — |
| `storeConcurrentLoadAllThreshold` | Устанавливает порог параллельной загрузки всех данных, который используется при одновременной загрузке значений ключей из `CacheStore` | int | `DFLT_CONCURRENT_LOAD_ALL_THRESHOLD = 5` | — |
| `storeKeepBinary` | Устанавливает флаг хранения данных в бинарном виде | boolean | `DFLT_STORE_KEEP_BINARY = false` | — |
| `topologyValidator` | Устанавливает валидатор топологии `TopologyValidator` | `TopologyValidator` | DataGrid предоставляет только интерфейс `TopologyValidator`, реализацию нужно написать самостоятельно. Если `TopologyValidator` не настроен, любая топология кластера считается корректной | — |
| `transactionManagerLookupClassName` | Устарел, используйте параметр `TransactionConfiguration.setTxManagerFactory(Factory)` | String | — | — |
| `keyType, valueType` | Указывает типы ключей и значений, которые будут храниться в кеше | `Class<K>, Class<V>` | — | — |
| `writeBehindBatchSize` | Устанавливает максимальный размер пакета для операций `CacheStore` при использовании режима write-behind | int | `DFLT_WRITE_BEHIND_BATCH_SIZE = 512` | — |
| `writeBehindCoalescing` | Устанавливает флаг объединения записей для отложенной записи в кеш | boolean | `DFLT_WRITE_BEHIND_COALESCING = true` | — |
| `writeBehindEnabled` | Устанавливает флаг, который указывает, включена ли функция отложенной записи | boolean | `DFLT_WRITE_BEHIND_ENABLED = false` | — |
| `writeBehindFlushFreq` | Устанавливает частоту загрузки write-behind-кеша в `CacheStore`. Данное значение определяет максимальный временной интервал между внесением объекта в кеш или его удалением из него и моментом, когда соответствующая операция будет отправлена в `CacheStore`.<br><br>Если установлено значение `0`, загрузка производится в соответствии со значением размера загрузки. Размеры загружаемого кеша и частоты загрузки не могут одновременно быть равны `0` | long | `DFLT_WRITE_BEHIND_FLUSH_FREQUENCY = 5000` | мс |
| `writeBehindFlushSize` | Устанавливает максимальный размер write-behind-кеша. Если размер кеша превышает данное значение, все объекты кеша загружаются в `CacheStore` и записи кеша очищаются.<br><br>Если установлено значение `0`, загрузка производится в соответствии со значением интервала загрузки. Размеры загружаемого кеша и частоты загрузки не могут одновременно быть равны `0` | int | `DFLT_WRITE_BEHIND_FLUSH_SIZE = 10240` | б |
| `writeBehindFlushThreadCnt` | Устанавливает количество потоков, которые производят очистку кеша | int | `DFLT_WRITE_FROM_BEHIND_FLUSH_THREAD_CNT = 1` | — |
| `writeSync` | Устанавливает режим синхронизации записи | `CacheWriteSynchronizationMode` | `CacheWriteSynchronizationMode.PRIMARY_SYNC` | — |

## IgniteSystemProperties

| Название параметра | Описание | Значение по умолчанию | Единицы измерения |
|---|---|---|---|
| `CHECKPOINT_PARALLEL_SORT_THRESHOLD` | Если выбран последовательный порядок записи контрольной точки (`CheckpointWriteOrder.SEQUENTIAL`), при достижении данного количества «грязных» страниц в контрольной точке массив будет пересортирован с помощью `Arrays.parallelSort(Comparable[])` | `512 * 1024` | б |
| `CLIENT_THROTTLE_RECONNECT_RESET_TIMEOUT_INTERVAL` | Временной интервал, после которого ограничение на повторное соединение клиента будет сброшено до нуля | `DFLT_THROTTLE_RECONNECT_RESET_TIMEOUT_INTERVAL = 2 * 60_000` | мс |
| `IGNITE_AFFINITY_BACKUPS_THRESHOLD` | Пороговый размер для выделения и поддержания дополнительного объекта `HashMap`, который улучшает работу метода `contains()`, но увеличивает потребление памяти | `DFLT_AFFINITY_BACKUPS_THRESHOLD = 5` | — |
| `IGNITE_AFFINITY_HISTORY_SIZE` | Максимальный размер истории назначений affinity-функции | `DFLT_AFFINITY_HISTORY_SIZE = 25` | — |
| `IGNITE_ALLOW_DML_INSIDE_TRANSACTION` | Если у параметра установлено значение `true`, DataGrid разрешит выполнение DML-операции (`MERGE\|INSERT\|UPDATE\|DELETE`) внутри транзакции в режиме без MVCC | `false` | — |
| `IGNITE_ALLOW_MIXED_CACHE_GROUPS` | Флаг, который указывает, разрешено ли совместное использование атомарных и транзакционных кешей в пределах одной кеш-группы | `false` | — |
| `IGNITE_ALLOW_START_CACHES_IN_PARALLEL` | Разрешает параллельный запуск кешей | `DFLT_ALLOW_START_CACHES_IN_PARALLEL = true` | — |
| `IGNITE_ATOMIC_CACHE_DELETE_HISTORY_SIZE` | Максимальное количество записей в очереди истории удаления для атомарного кеша (на партицию) | `DFLT_ATOMIC_CACHE_DELETE_HISTORY_SIZE = 200_000` (на партицию) | — |
| `IGNITE_ATOMIC_CACHE_QUEUE_RETRY_TIMEOUT` | Время ожидания отложенного обновления атомарного кеша | `DFLT_ATOMIC_CACHE_QUERY_RETRY_TIMEOUT = 10000` | мс |
| `IGNITE_ATOMIC_DEFERRED_ACK_BUFFER_SIZE` | Размер буфера отклика для отложенных обновлений атомарного кеша | `DFLT_ATOMIC_DEFERRED_ACK_BUFFER_SIZE = 256` | — |
| `IGNITE_ATOMIC_DEFERRED_ACK_TIMEOUT` | Тайм-аут для отложенных обновлений атомарного кеша | `DFLT_ATOMIC_DEFERRED_ACK_TIMEOUT = 500` | мс |
| `IGNITE_BASELINE_AUTO_ADJUST_LOG_INTERVAL` | Интервал между записями в лог автоматического обновления базовой топологии | `DFLT_BASELINE_AUTO_ADJUST_LOG_INTERVAL = 60_000` | мс |
| `IGNITE_BINARY_MARSHALLER_USE_STRING_SERIALIZATION_VER_2` | Управляет выбором механизма сериализации для типа String, который обрабатывается `BinaryMarshaller` | — | — |
| `IGNITE_BINARY_SORT_OBJECT_FIELDS` | Если у параметра установлено значение `true`, поля записываются c помощью `BinaryMarshaller` в отсортированном порядке | Должен стать поведением по умолчанию в одном из будущих релизов DataGrid | — |
| `IGNITE_BPLUS_TREE_DISABLE_METRICS` | Отключает метрики B+ дерева для вторичных индексов | `false` | — |
| `IGNITE_BPLUS_TREE_LOCK_RETRIES` | Количество попыток захвата блокировки в B+ дереве | `IGNITE_BPLUS_TREE_LOCK_RETRIES_DEFAULT = 1000` | — |
| `IGNITE_CACHE_CLIENT` | Определяет поведение по умолчанию для клиентского кеша | — | — |
| `IGNITE_CACHE_REMOVED_ENTRIES_TTL` | Время жизни (TTL — time to live) удаленных записей кеша | `DFLT_CACHE_REMOVE_ENTRIES_TTL = 10_000` | мс |
| `IGNITE_CACHE_RETRIES_COUNT` | Количество повторных попыток выполнения операций с кешем в случае возникновения исключений, которые связаны с топологией | `DFLT_CACHE_RETRIES_COUNT = 100` | — |
| `IGNITE_CACHE_START_SIZE` | Начальный размер кеша для карт, которые размещаются в Heap | `DFLT_CACHE_START_SIZE = 4096` | — |
| `IGNITE_CALCITE_EXEC_IN_BUFFER_SIZE` | SQL-движок на основе Apache Calcite. Размер буфера (количество строк) для узлов выполнения запросов | — | — |
| `IGNITE_CALCITE_EXEC_IO_BATCH_CNT` | SQL-движок на основе Apache Calcite. Максимальное количество ожидающих отправки сообщений с данными для каждой исходящей очереди | — | — |
| `IGNITE_CALCITE_EXEC_IO_BATCH_SIZE` | SQL-движок на основе Apache Calcite. Размер пакета (количество строк) для исходящего сообщения с данными | — | — |
| `IGNITE_CALCITE_EXEC_MODIFY_BATCH_SIZE` | SQL-движок на основе Apache Calcite. Размер пакета (количество строк) для узлов, которые выполняют операции с кешем | — | — |
| `IGNITE_CALCITE_REL_JSON_PRETTY_PRINT` | SQL-движок на основе Apache Calcite. Форматирует сериализованный в JSON план в удобочитаемом виде перед передачей его на удаленные узлы | — | — |
| `IGNITE_CHECKPOINT_MAP_SNAPSHOT_THRESHOLD` | Пороговое значение количества контрольных точек, начиная с последнего самого раннего снимка карты контрольных точек | `DFLT_IGNITE_CHECKPOINT_MAP_SNAPSHOT_THRESHOLD = 5` | — |
| `IGNITE_CHECKPOINT_READ_LOCK_TIMEOUT` | Тайм-аут для получения блокировок чтения контрольной точки | — | мс |
| `IGNITE_CHECKPOINT_TRIGGER_ARCHIVE_SIZE_PERCENTAGE` | Свойство для настройки размера архива для запуска контрольной точки | `DFLT_CHECKPOINT_TRIGGER_ARCHIVE_SIZE_PERCENTAGE = 0.25` (25%) | — |
| `IGNITE_CLIENT_CACHE_CHANGE_MESSAGE_TIMEOUT` | При запуске или остановке клиентского кеша отправляется специальное discovery-сообщение, которое уведомляет кластер. Например, это необходимо для API `ClusterGroup.forCacheNodes(String)` | `DFLT_CLIENT_CACHE_CHANGE_MESSAGE_TIMEOUT = 10_000` | мс |
| `IGNITE_CLUSTER_NAME` | Имя кластера DataGrid. Используется по умолчанию как идентификатор развертывания служебного кеша | — | — |
| `IGNITE_CONFIG_URL` | Системное свойство, которое содержит опциональный URL конфигурации | — | — |
| `IGNITE_CONFIGURATION_VIEW_PACKAGES` | Перечень пакетов, которые разделены запятыми, для показа в представлении конфигурации | `null` | — |
| `IGNITE_CONSISTENT_ID_BY_HOST_WITHOUT_PORT` | Если у параметра установлено значение `true`, согласованный идентификатор (consistent ID) будет рассчитываться по имени хоста без порта. Таким образом в кластере допускается наличие лишь одного узла на каждый хост | — | — |
| `IGNITE_CONSOLE_APPENDER` | Если у параметра установлено значение `true` (по умолчанию), в DataGrid настроен режим расширенного вывода (подробнее написано ниже в графе `IGNITE_QUIET`) и в конфигурации не настроен консольный вывод, будет использоваться стандартная запись в консоль | `true` | — |
| `IGNITE_DATA_STORAGE_FOLDER_BY_CONSISTENT_ID` | Если у параметра установлено значение `true`, папки хранилища данных создаются исключительно на основе согласованного идентификатора (consistent ID). В то же время согласованный идентификатор не будет установлен на основе существующих папок хранилища данных | — | — |
| `IGNITE_DATA_STREAMING_EXECUTOR_SERVICE_TASKS_STEALING_THRESHOLD` | Перехват задач (tasks stealing) начнется, если размер очереди задач на поток `DataStreamer` превысит данное пороговое значение | `DFLT_DATA_STREAMING_EXECUTOR_SERVICE_TASKS_STEALING_THRESHOLD = 4` | — |
| `IGNITE_DEFAULT_DATA_STORAGE_PAGE_SIZE` | Устанавливает значение по умолчанию для размера страницы хранилища | `DFLT_PAGE_SIZE = 4 * 1024` | б |
| `IGNITE_DEFAULT_DISK_PAGE_COMPRESSION` | Устанавливает значение по умолчанию для сжатия страниц диска для кеша | — | — |
| `IGNITE_DEFERRED_ONE_PHASE_COMMIT_ACK_REQUEST_BUFFER_SIZE` | Количество отложенных запросов на подтверждение, которые могут одновременно находиться в буфере при использовании однофазного коммита | `DFLT_DEFERRED_ONE_PHASE_COMMIT_ACK_REQUEST_BUFFER_SIZE = 256` | Количество запросов, которые могут одновременно находиться в буфере |
| `IGNITE_DEFERRED_ONE_PHASE_COMMIT_ACK_REQUEST_TIMEOUT` | Тайм-аут для отложенных запросов на подтверждение при использовании однофазного коммита | `DFLT_DEFERRED_ONE_PHASE_COMMIT_ACK_REQUEST_TIMEOUT = 500` | мс |
| `IGNITE_DEFRAGMENTATION_REGION_SIZE_PERCENTAGE` | Процент размера региона данных, который будет использоваться для дефрагментации | `DFLT_DEFRAGMENTATION_REGION_SIZE_PERCENTAGE = 60` | % |
| `IGNITE_DELAYED_REPLACED_PAGE_WRITE` | Позволяет записывать замененные страницы (replaced pages) в хранилище страниц с задержкой, не удерживая блокировку сегмента | `DFLT_DELAYED_REPLACED_PAGE_WRITE = true` | — |
| `IGNITE_DEP_MODE_OVERRIDE` | Системное свойство для переопределения параметра конфигурации режима развертывания | — | — |
| `IGNITE_DEV_ONLY_LOGGING_DISABLED` | Если у параметра установлено значение `true`, предупреждения от сред разработки и не подходящие для производства ошибки (ошибки кодирования в коде, который использует DataGrid), регистрироваться не будут | — | — |
| `IGNITE_DIAGNOSTIC_ENABLED` | Параметр включает диагностику в DataGrid. Если у параметра установлено значение `true` (по умолчанию), различные диагностические инструменты и механизмы активируются, помогая выявлять проблемы и анализировать состояние кластера | `DFLT_DIAGNOSTIC_ENABLED = true` | — |
| `IGNITE_DIAGNOSTIC_WARN_LIMIT` | Максимальное количество предупреждающих диагностических сообщений для каждой категории при ожидании процесса обмена картами партиций (PME — Partition Map Exchange) | `DFLT_DIAGNOSTIC_WARN_LIMIT = 10` | — |
| `IGNITE_DIRECT_IO_ENABLED` | Если у параметра установлено значение `true`, возможно включение прямого ввода-вывода (direct I/O) | `true` | — |
| `IGNITE_DISABLE_AFFINITY_MEMORY_OPTIMIZATION` | Позволяет отключить оптимизацию памяти, так как для хранения партиций будут использоваться битовые множества (`BitSet`) вместо хеш-множества (`HashSet`)  | — | — |
| `IGNITE_DISABLE_GRP_STATE_LAZY_STORE` | Позволяет отключить ленивое хранение (lazy store) состояния группы | `false` | — |
| `IGNITE_DISABLE_HOSTNAME_VERIFIER` | Системное свойство для отключения проверки имени хоста (`HostNameVerifier`) для SSL-соединений | `false` | — |
| `IGNITE_DISABLE_ONHEAP_CACHE` | Если у параметра установлено значение `true`, кеширование в Heap включить нельзя | `false` | — |
| `IGNITE_DISABLE_REBALANCING_CANCELLATION_OPTIMIZATION` | Если у параметра установлено значение `false`, каждая следующая операция обмена будет пытаться провести сравнение с предыдущей | `false` | — |
| `IGNITE_DISABLE_TRIGGERING_CACHE_INTERCEPTOR_ON_CONFLICT` | Отключает вызов перехватчика кеша (cache interceptor) в случае конфликтов | `false` | — |
| `IGNITE_DISABLE_WAL_DURING_REBALANCING` | Eсли у параметра установлено значение `false`, WAL (журнал предзаписи) не будет автоматически отключаться во время ребалансировки (если ни одна из партиций не находится состоянии `OWNING`) | `DFLT_DISABLE_WAL_DURING_REBALANCING = true` | — |
| `IGNITE_DISCO_FAILED_CLIENT_RECONNECT_DELAY` | Определяет задержку перед попыткой повторного подключения клиентского узла к серверу после того, как подключение было принудительно отключено | `DFLT_DISCO_FAILED_CLIENT_RECONNECT_DELAY = 10_000` | мс |
| `IGNITE_DISCOVERY_CLIENT_RECONNECT_HISTORY_SIZE` | Максимальное количество сохраняемых discovery-сообщений, которые используются для восстановления подключения клиентов | `DFLT_DISCOVERY_CLIENT_RECONNECT_HISTORY_SIZE = 512` | — |
| `IGNITE_DISCOVERY_DISABLE_CACHE_METRICS_UPDATE` | Если у параметра установлено значение `true`, метрики кеша не включаются в discovery-сообщение об обновлении метрик (в этом случае сообщение содержит только кластерные метрики) | `false` | — |
| `IGNITE_DISCOVERY_HISTORY_SIZE` | Максимальный размер истории discovery-сообщений | `DFLT_DISCOVERY_HISTORY_SIZE = 500` | — |
| `IGNITE_DISCOVERY_METRICS_QNT_WARN` | Логирование предупреждающего `WARN`-сообщения, если количество метрик превысит определенное значение | `DFLT_DISCOVERY_METRICS_QNT_WARN = 500` | — |
| `IGNITE_DUMP_PAGE_LOCK_ON_FAILURE` | Включает сохранение дампа блокировок потоков при возникновении критической ошибки на узле | `DFLT_DUMP_PAGE_LOCK_ON_FAILURE = true` | — |
| `IGNITE_DUMP_THREADS_ON_FAILURE` | Включает создание дампа потоков при появлении критической ошибки на узле | `true` | — |
| `IGNITE_DUMP_THREADS_ON_FAILURE_THROTTLING_TIMEOUT` | Тайм-аут для генерации дампа потоков во время обработки сбоев (не задается пользователем) | Failure detection timeout для серверных узлов — 10 000 мс, для клиентских узлов — 30 000 мс | мс |
| `IGNITE_DUMP_TX_COLLISIONS_INTERVAL` | Устанавливает интервал, по прошествии которого будут выводиться коллизии ключей транзакций. Если значение больше нуля, коллизии будут выводиться с указанной периодичностью | `DFLT_DUMP_TX_COLLISIONS_INTERVAL = 1000` | мс |
| `IGNITE_ENABLE_EXPERIMENTAL_COMMAND` | Устарел, используйте параметр `--enable-experimental` | — | — |
| `IGNITE_ENABLE_EXTRA_INDEX_REBUILD_LOGGING` | Включает расширенное логирование создания/перестроения индексов | `false` | — |
| `IGNITE_ENABLE_FORCIBLE_NODE_KILL` | Если параметр установлен, узел принудительно завершит работу удаленного (remote) узла (серверного или клиентского), если не сможет установить с ним соединение | — | — |
| `IGNITE_ENABLE_SUBQUERY_REWRITE_OPTIMIZATION` | Включает оптимизацию переписывания подзапросов | `true` | — |
| `IGNITE_EVICTION_PERMITS` | Устарел, для управления выполнением операций вытеснения данных из кеша используйте параметр `IgniteConfiguration.setRebalanceThreadPoolSize(int)` | — | — |
| `IGNITE_EXCEPTION_REGISTRY_MAX_SIZE` | Определяет максимальное количество последних исключений, которые хранятся в буфере | `DEFAULT_QUEUE_SIZE = 1000` | — |
| `IGNITE_EXCHANGE_HISTORY_SIZE` | Максимальный размер истории операций обмена картами партиций (PME — Partition Map Exchange) | `DFLT_EXCHANGE_HISTORY_SIZE = 1_000` | — |
| `IGNITE_EXCHANGE_MERGE_DELAY` | Определяет задержку перед началом слияния обменов картами партиций (PME — Partition Map Exchange) | `DFLT_EXCHANGE_MERGE_DELAY = 0` | мс |
| `IGNITE_FAIL_NODE_ON_UNRECOVERABLE_PARTITION_INCONSISTENCY` | Позволяет активировать обработчик ошибок (failure handler) для узла в случае обнаружения не подлежащей восстановлению несогласованности партиций во время обмена обновлениями счетчиков партиций (partition update counter) | — | — |
| `IGNITE_FAILURE_HANDLER_RESERVE_BUFFER_SIZE` | Определяет размер буфера, который резервируется в Heap при запуске узла и который может быть освобожден для увеличения шансов успешной обработки возможных ошибок при нехватки памяти (`OutOfMemoryError`) | `DFLT_FAILURE_HANDLER_RESERVE_BUFFER_SIZE = 64 * 1024` | б |
| `IGNITE_GLOBAL_METASTORAGE_HISTORY_MAX_BYTES` | Максимальное количество байтов, которое может храниться в истории обновлений `DistributedMetaStorage` | `DFLT_MAX_HISTORY_BYTES = 100 * 1024 * 1024` | б |
| `IGNITE_GRID_CLIENT_LOG_ENABLED` | Если у параметра установлено значение `true`, включается логирование в `GridClient` | — | — |
| `IGNITE_H2_INDEXING_CACHE_CLEANUP_PERIOD` | Указывает период между вызовами задачи очистки кеша SQL-запросов | `10,000` | мс |
| `IGNITE_H2_INDEXING_CACHE_THREAD_USAGE_TIMEOUT` | Указывает тайм-аут, по истечении которого кеш SQL-запросов потока будет очищен задачей очистки, если поток не выполняет никаких запросов | `600,000` | мс |
| `IGNITE_HOME` | Определяет папку установки DataGrid | `""` | — |
| `IGNITE_IGNORE_LOCAL_HOST_NAME` | Позволяет игнорировать чтение имени хоста для локального адреса | `true` | — |
| `IGNITE_INDEX_REBUILD_BATCH_SIZE` | Количество строк, которые обрабатываются за одну операцию блокировки контрольной точки при перестроении индексов | `DFLT_IGNITE_INDEX_REBUILD_BATCH_SIZE = 1_000` | — |
| `IGNITE_INDEXING_DISCOVERY_HISTORY_SIZE` | Размер истории индексирования discovery-сообщений. Защищает от дублирующихся сообщений с помощью списка идентификаторов недавно полученных discovery-сообщений | `DFLT_INDEXING_DISCOVERY_HISTORY_SIZE = 1000` | — |
| `IGNITE_IO_BALANCE_PERIOD` | Период балансировки ввода-вывода | `DFLT_IO_BALANCE_PERIOD = 5000` | мс |
| `IGNITE_IO_DUMP_ON_TIMEOUT` | Включает запись статистики SPI в диагностическом журнале | — | — |
| `IGNITE_JCACHE_DEFAULT_ISOLATED` | Контролирует поведение `CacheManager` при запуске кластера с изолированным поиском IP-адресов и передаче URL по умолчанию | `DFLT_JCACHE_DEFAULT_ISOLATED = true` | — |
| `IGNITE_JDBC_DRIVER_CURSOR_REMOVE_DELAY` | Определяет задержку перед удалением курсора в JDBC-драйвере | `600,000` (10 минут) | мс |
| `IGNITE_JETTY_HOST` | Позволяет переопределить хост Jetty для REST-процессора | — | — |
| `IGNITE_JETTY_LOG_NO_OVERRIDE` | Запрещает DataGrid менять конфигурацию логирования Jetty для REST-процессора | — | — |
| `IGNITE_JETTY_PORT` | Позволяет переопределить локальный порт Jetty для REST-процессора | — | — |
| `IGNITE_JOBS_HISTORY_SIZE` | Системное свойство для изменения стандартных размеров карт процессора для выполненных задач и запросов на отмену | `DFLT_JOBS_HISTORY_SIZE = 10240` | — |
| `IGNITE_JOBS_METRICS_CONCURRENCY_LEVEL` | Устарел, используйте параметр `ReadOnlyMetricRegistry` с `name=compute.jobs` | `DFLT_JOBS_METRICS_CONCURRENCY_LEVEL = 64` | — |
| `IGNITE_JVM_PAUSE_DETECTOR_DISABLED` | Отключает детектор JVM-пауз | — | — |
| `IGNITE_JVM_PAUSE_DETECTOR_LAST_EVENTS_COUNT` | Устанавливает количество последних зафиксированных событий детектора JVM-пауз | `DFLT_JVM_PAUSE_DETECTOR_LAST_EVENTS_COUNT = 20` | — |
| `IGNITE_JVM_PAUSE_DETECTOR_PRECISION` | Определяет точность работы детектора JVM-пауз. Чем выше значение, тем точнее детектор будет определять продолжительность пауз, которые вызваны сборщиком мусора и другими причинами | `DFLT_JVM_PAUSE_DETECTOR_PRECISION = 50` | — |
| `IGNITE_JVM_PAUSE_DETECTOR_THRESHOLD` | Устанавливает порог срабатывания детектора JVM-пауз | `EFAULT_JVM_PAUSE_DETECTOR_THRESHOLD = 500` | — |
| `IGNITE_KEEP_STATIC_CACHE_CONFIGURATION` | Указывает, следует ли сохранять статическую конфигурацию кеша, даже если сохраненные данные кеша отличаются от этой конфигурации | — | — |
| `IGNITE_LOADED_PAGES_BACKWARD_SHIFT_MAP` | Если у параметра установлено значение `false`, реализация загруженных страниц переключается на предыдущую версию реализации — `FullPageIdTable` | `DFLT_LOADED_PAGES_BACKWARD_SHIFT_MAP = true` | — |
| `IGNITE_LOCAL_HOST` | Определяет локальный IP-адрес или имя хоста, которое будет использоваться сетевыми компонентами для сетевого взаимодействия внутри кластера. Это особенно полезно в средах с несколькими сетевыми интерфейсами | — | — |
| `IGNITE_LOCAL_STORE_KEEPS_PRIMARY_ONLY` | Указывает, сохраняет ли локальное хранилище только основные (primary) партиции | — | — |
| `IGNITE_LOG_CLASSPATH_CONTENT_ON_STARTUP` | Сканирует `classpath` при запуске и записывает в лог все содержащиеся в нем файлы | `DFLT_LOG_CLASSPATH_CONTENT_ON_STARTUP = true` | — |
| `IGNITE_LOG_DIR` | Переменная окружения для переопределения каталога логирования, который был задан в конфигурации логера | — | — |
| `IGNITE_LOG_GRID_NAME` | Устарел, используйте параметр `IGNITE_LOG_INSTANCE_NAME` | — | — |
| `IGNITE_LOG_INSTANCE_NAME` | При наличии данной системной переменной имя экземпляра будет выводиться в подробном выводе логирования | — | — |
| `IGNITE_LOG_THROTTLE_CAPACITY` | Максимальное количество ошибок, которые будут запоминаться с помощью механизма ограничения частоты записей в журнале (`GridLogThrottle`) | `DFLT_LOG_THROTTLE_CAPACITY = 128` | — |
| `IGNITE_LONG_LONG_HASH_MAP_LOAD_FACTOR` | Коэффициент загрузки карты вне Heap (off-heap) c ключами и значениями типа long | `DFLT_LONG_LONG_HASH_MAP_LOAD_FACTOR = 2.5f` | — |
| `IGNITE_LONG_OPERATIONS_DUMP_TIMEOUT` | Операции с кешем, длительность которых превышает значение этого свойства, будут регистрироваться в логе | `DFLT_LONG_OPERATIONS_DUMP_TIMEOUT = 60_000L` | мс |
| `IGNITE_LONG_OPERATIONS_DUMP_TIMEOUT_LIMIT` | Максимальный интервал времени между созданием отладочных дампов для продолжительных или зависших операций | `DFLT_LONG_OPERATIONS_DUMP_TIMEOUT_LIMIT = 30 * 60_000` | мс |
| `IGNITE_LONG_TRANSACTION_TIME_DUMP_THRESHOLD` | Предельное время для долгих транзакций. Если транзакция превышает данный лимит, она будет записана в лог вместе с информацией о затраченном времени на системные операции (например, захват блокировок, подготовку, фиксацию и так далее) и на выполнение пользовательских операций (время выполнения клиентским узлом некоторого кода в рамках транзакции без ожидания завершения) | `0` | мс |
| `IGNITE_MARSHAL_BUFFERS_PER_THREAD_POOL_SIZE` | Определяет размер пула фрагментов распределителя памяти двоичных данных для каждого потока | `DFLT_MARSHAL_BUFFERS_PER_THREAD_POOL_SIZE = 32` | — |
| `IGNITE_MARSHAL_BUFFERS_RECHECK` | Определяет интервал, спустя который происходит повторная проверка и возможное освобождение фрагментов распределителя памяти двоичных данных | `DFLT_MARSHAL_BUFFERS_RECHECK = 10000` | мс |
| `IGNITE_MARSHALLER_BLACKLIST` | Задает путь к файлу, который содержит список классов, недоступных для безопасной десериализации | — | — |
| `IGNITE_MARSHALLER_WHITELIST` | Задает путь к файлу, который содержит список классов, разрешенных для безопасной десериализации | — | — |
| `IGNITE_MASTER_KEY_NAME_TO_CHANGE_BEFORE_STARTUP` | Имя мастер-ключа, которое узел будет использовать во время восстановления | — | — |
| `IGNITE_MAX_COMPLETED_TX_COUNT` | Определяет максимальный размер буфера, в котором хранятся завершенные версии транзакций | `DFLT_MAX_COMPLETED_TX_CNT = 262144` (2^18) | — |
| `IGNITE_MAX_INDEX_PAYLOAD_SIZE` | Системное свойство для указания максимального размера полезной нагрузки для индекса `H2TreeIndex` | `64` | б |
| `IGNITE_MAX_NESTED_LISTENER_CALLS` | Максимальное количество вложенных вызовов слушателей, после достижения которого уведомления слушателя начинают выполняться асинхронно | `DFLT_MAX_NESTED_LISTENER_CALLS = 5` | — |
| `IGNITE_MBEAN_APPEND_CLASS_LOADER_ID` | Определяет, будет ли DataGrid добавлять хеш-код класса загрузчика к имени `MBean`, то есть будет ли отображаться идентификатор `Classloader` в иерархии имен `MBean` | `DFLT_MBEAN_APPEND_CLASS_LOADER_ID = true` | — |
| `IGNITE_MBEAN_APPEND_JVM_ID` | Определяет, нужно ли добавлять идентификационные данные JVM к имени `MXBean` в DataGrid. Если у параметра установлено значение `true`, хеш-код класса DataGrid в виде шестнадцатеричной строки будет добавлен к имени JVM, которое будет получено с помощью метода `RuntimeMXBean.getName()`. Это помогает идентифицировать `MBeans` в среде с несколькими виртуальными машинами Java | `false` | — |
| `IGNITE_MBEANS_DISABLED` | Если у параметра установлено значение `true`, регистрация `MBeans` в DataGrid будет отключена | `false` | — |
| `IGNITE_MEMORY_PER_BYTE_COPY_THRESHOLD` | Определяет порог, ниже которого DataGrid будет выполнять небезопасное копирование памяти побайтовым способом вместо использования метода `Unsafe.copyMemory()` | `DFLT_MEMORY_PER_BYTE_COPY_THRESHOLD = 0L` | — |
| `IGNITE_MEMORY_UNALIGNED_ACCESS` | Определяет, может ли DataGrid обращаться к невыровненным (unaligned) адресам памяти | `false` | — |
| `IGNITE_NEAR_GET_MAX_REMAPS` | Определяет максимальное количество попыток перенаправления запроса на получение данных с ближнего узла к одному и тому же основному узлу | `DFLT_MAX_REMAP_CNT = 3` | — |
| `IGNITE_NIO_RECOVERY_DESCRIPTOR_RESERVATION_TIMEOUT` | Устанавливает тайм-аут для бронирования дескриптора восстановления TCP-клиента | `DFLT_NIO_RECOVERY_DESCRIPTOR_RESERVATION_TIMEOUT = 5_000` | мс |
| `IGNITE_NO_ASCII` | Если данная системная переменная установлена (независимо от ее значения), логотип в формате `ASCII` выводиться не будет | — | — |
| `IGNITE_NO_DISCO_ORDER` | Название системной переменной, которая позволяет отключить требование корректного порядка узлов в механизме обнаружения (Discovery SPI) | — | — |
| `IGNITE_NO_SELECTOR_OPTS` | Если у параметра установлено значение `true`, в `GridNioServer` будет использован набор ключей по умолчанию, что может привести к дополнительному созданию мусора при обработке этих ключей | `false` | — |
| `IGNITE_NO_SHUTDOWN_HOOK` | Определяет, будет ли установлен обработчик завершения работы (shutdown hook). Если у параметра установлено значение `true`, обработчик не будет настроен и приложение завершится без выполнения дополнительных действий по shutdown hook при завершении работы JVM | — | — |
| `IGNITE_NODE_IDS_HISTORY_SIZE` | Максимальный размер истории серверных узлов (идентификаторы серверных узлов), которые когда-либо присоединялись к текущей топологии | `DFLT_NODE_IDS_HISTORY_SIZE = 50` | — |
| `IGNITE_OFFHEAP_LOCK_CONCURRENCY_LEVEL` | Определяет уровень параллелизма для блокировки памяти вне Heap (off-heap) | — | — |
| `IGNITE_OFFHEAP_SAFE_RELEASE` | Позволяет включить режим безопасного освобождения блоков памяти вне Heap (off-heap). При установке данного флага перед освобождением блока памяти он заполняется определенным шаблоном, что помогает выявлять ошибки использования освобожденной памяти | — | — |
| `IGNITE_OPTIMIZED_MARSHALLER_USE_DEFAULT_SUID` | Управляет поведением `OptimizedMarshaller` при вычислении значения `serialVersionUID` для классов, которые реализуют интерфейс `Serializable` | — | — |
| `IGNITE_OVERRIDE_CONSISTENT_ID` | Системное свойство для указания согласованного идентификатора (consistent ID) узла DataGrid | — | — |
| `IGNITE_OVERRIDE_MCAST_GRP` | Позволяет переопределить многоадресную группу, которая указана в конфигурации для механизма обнаружения узлов | — | — |
| `IGNITE_OVERRIDE_WRITE_THROTTLING_ENABLED` | Позволяет принудительно включить регулирование записи данных (write throttling) с помощью установки значения `true` в `DataStorageConfiguration.setWriteThrottlingEnabled(boolean)` независимо от первоначального значения в конфигурации | — | — |
| `IGNITE_PAGE_LOCK_TRACKER_CAPACITY` | Определяет объем памяти, который выражен в количестве страниц и выделяется под структуру для отслеживания заблокированных страниц (page lock tracker) | `DFLT_PAGE_LOCK_TRACKER_CAPACITY = 512` | — |
| `IGNITE_PAGE_LOCK_TRACKER_CHECK_INTERVAL` | Интервал времени между проверками трекером блокировки страниц (page lock tracker) на предмет зависших потоков | `DFLT_PAGE_LOCK_TRACKER_CHECK_INTERVAL = 60_000` | мс |
| `IGNITE_PAGE_LOCK_TRACKER_TYPE` | Тип трекера блокировки страниц | `HEAP_LOG = 2` | — |
| `IGNITE_PAGES_LIST_DISABLE_ONHEAP_CACHING` | Позволяет отключить кеширования списков страниц (списков свободных блоков (free list) и списков повторного использования (reuse list)) в Heap | `false` | — |
| `IGNITE_PART_DISTRIBUTION_WARN_THRESHOLD` | Порог уровня неравномерного распределения партиций, превышение которого приведет к записи информации о распределении партиций в лог | `DFLT_PART_DISTRIBUTION_WARN_THRESHOLD = 50f` | — |
| `IGNITE_PARTITION_RELEASE_FUTURE_DUMP_THRESHOLD` | Если `future` по освобождению партиции во время перераспределения данных между узлами длится дольше, чем определено данным порогом, содержимое `future` будет записано в лог | `DFLT_PARTITION_RELEASE_FUTURE_DUMP_THRESHOLD = 0` | — |
| `IGNITE_PARTITION_RELEASE_FUTURE_WARN_LIMIT` | Определяет максимальное количество `future`, которое включается в предупреждающее диагностическое сообщение | `DFLT_IGNITE_PARTITION_RELEASE_FUTURE_WARN_LIMIT = 10` | — |
| `IGNITE_PDS_MAX_CHECKPOINT_MEMORY_HISTORY_SIZE` | Максимальное количество записей в истории контрольных точек, которые хранятся в памяти | `DFLT_PDS_MAX_CHECKPOINT_MEMORY_HISTORY_SIZE = 100` | — |
| `IGNITE_PDS_SKIP_CRC` | Устанавливает флаг пропуска вычисления CRC | — | — |
| `IGNITE_PDS_WAL_REBALANCE_THRESHOLD` | Устарел, используйте параметр `historical.rebalance.threshold` в распределенном хранилище метаданных (distributed metastorage) | `DFLT_PDS_WAL_REBALANCE_THRESHOLD = 500` | — |
| `IGNITE_PENDING_TX_TRACKER_ENABLED` | Системное свойство для включения трекера отложенных (pending) транзакций | — | — |
| `IGNITE_PERF_STAT_BUFFER_SIZE` | Определяет размер буфера вне Heap (off-heap) для сбора статистических данных производительности | `DFLT_BUFFER_SIZE = (int)(32 * U.MB)` (32 * 1024 * 1024) | б |
| `IGNITE_PERF_STAT_CACHED_STRINGS_THRESHOLD` | Определяет максимальное количество строк, которые могут быть закешированы для статистики производительности | `DFLT_CACHED_STRINGS_THRESHOLD = 10 * 1024` | — |
| `IGNITE_PERF_STAT_FILE_MAX_SIZE` | Максимальный размер файла статистики производительности | `DFLT_FILE_MAX_SIZE = 32 * U.GB` | б |
| `IGNITE_PERF_STAT_FLUSH_SIZE` | Минимальный размер пакета данных статистики производительности для отправки в файл | `DFLT_FLUSH_SIZE = (int)(8 * U.MB)` | б |
| `IGNITE_PERFORMANCE_SUGGESTIONS_DISABLED` | Позволяет отключить вывод предложений по улучшению производительности при запуске | — | — |
| `IGNITE_PREFER_WAL_REBALANCE` | Дает возможность использовать историческую ребалансировку при наличии достаточной истории, не принимая во внимание другие эвристические методы | `false` | — |
| `IGNITE_PRELOAD_RESEND_TIMEOUT` | Системная переменная, которая задает интервал ожидания перед повторной отправкой данных для предварительно загруженных, но впоследствии вытесненных (evicted) партиций | `DFLT_PRELOAD_RESEND_TIMEOUT = 1500` | мс |
| `IGNITE_PROG_NAME` | Имя системной переменной, которое определяет имя командной программы | `DFLT_PROG_NAME = "ignite.{sh\|bat}"` | — |
| `IGNITE_QUIET` | Если у параметра установлено значение `true`, включается «тихий» (не расширенный — verbose) режим DataGrid | `true` | — |
| `IGNITE_READ_LOAD_BALANCING` | При включении балансировки нагрузки чтения запросы `get` будут распределяться между основными и резервными узлами, если это возможно и функция `CacheConfiguration.isReadFromBackup()` возвращает `true` | `DFLT_READ_LOAD_BALANCING = true` | — |
| `IGNITE_REBALANCE_STATISTICS_TIME_INTERVAL` | Устарел, используйте параметр `MetricsMxBean.configureHitRateMetric(String, long)` | `60,000` | мс |
| `IGNITE_REBALANCE_THROTTLE_OVERRIDE` | Устарел, используйте параметр `IgniteConfiguration.getRebalanceThrottle()` | `0` | мс |
| `IGNITE_RECOVERY_SEMAPHORE_PERMITS` | Ограничивает максимальное количество объектов, которые могут одновременно находиться в памяти во время процедуры восстановления | — | — |
| `IGNITE_RECOVERY_VERBOSE_LOGGING` | Включает подробное логирование информации о восстановлении партиций после этапов бинарного и логического восстановлений | `true` | — |
| `IGNITE_REFLECTION_CACHE_SIZE` | Системная переменная для изменения размера кеша по умолчанию, который связан с рефлексией (reflection) | `DFLT_REFLECTION_CACHE_SIZE = 128` | — |
| `IGNITE_REST_GETALL_AS_ARRAY` | Системное свойство, которое позволяет получить вывод в виде массива | — | — |
| `IGNITE_REST_MAX_TASK_RESULTS` | Позволяет изменить максимальное количество результатов задач, которые могут храниться на одном узле в REST-процессоре | `DFLT_MAX_TASK_RESULTS = 10240` | — |
| `IGNITE_REST_SECURITY_TOKEN_TIMEOUT` | Позволяет изменить время жизни токена безопасности REST-сессии со значения по умолчанию | `DFLT_SES_TOKEN_INVALIDATE_INTERVAL = 5 * 60` | с |
| `IGNITE_REST_SESSION_TIMEOUT` | Позволяет изменить время жизни REST-сессии со значения по умолчанию | `DFLT_SES_TIMEOUT = 30` | с |
| `IGNITE_REST_START_ON_CLIENT` | Позволяет изменить поведение по умолчанию, при котором REST-процессор не запускается на клиентском узле | — | — |
| `IGNITE_RESTART_CODE` | Используется внутренним механизмом DataGrid для передачи кода завершения (exit-кода) загрузчику при перезапуске экземпляра DataGrid | `0` | — |
| `IGNITE_REUSE_MEMORY_ON_DEACTIVATE` | Управляет возможностью повторного использования памяти при деактивации узла | — | — |
| `IGNITE_SECURITY_COMPATIBILITY_MODE` | Включает режим совместимости в DataGrid. Режим позволяет работать с версиями, которые не поддерживают разрешения для служб безопасности | `false` | — |
| `IGNITE_SKIP_CONFIGURATION_CONSISTENCY_CHECK` | Позволяет пропустить проверку согласованности конфигурации | — | — |
| `IGNITE_SKIP_PARTITION_SIZE_VALIDATION` | Если у параметра установлено значение `true`, DataGrid не будет выполнять проверку размеров партиций после завершения процесса ребалансировки | `false` | — |
| `IGNITE_SLOW_TX_WARN_TIMEOUT` | Транзакции, длительность которых превышает значение данного порога, будут фиксироваться в логе с уровнем предупреждения | `DFLT_SLOW_TX_WARN_TIMEOUT = 0` | — |
| `IGNITE_SNAPSHOT_SEQUENTIAL_WRITE` | Указывает, что записи на диск во время процесса создания снепшотов по возможности должны выполняться последовательно | `DFLT_IGNITE_SNAPSHOT_SEQUENTIAL_WRITE = true` | — |
| `IGNITE_SQL_ALLOW_KEY_VAL_UPDATES` | Разрешает использование составных столбцов `_key` и `_val` в операторах `INSERT/UPDATE/MERGE` | — | — |
| `IGNITE_SQL_DISABLE_SYSTEM_VIEWS` | Позволяет отключить системные представления SQL | — | — |
| `IGNITE_SQL_FILL_ABSENT_PK_WITH_DEFAULTS` | Позволяет принудительно заполнить отсутствующие столбцы, которые принадлежат первичному ключу, значениями `NULL` или значениями по умолчанию (если они были указаны) | `false` | — |
| `IGNITE_SQL_MAX_EXTRACTED_PARTS_FROM_BETWEEN` | Ограничивает максимальное количество различных партиций, которые могут быть извлечены из условия `BETWEEN` SQL-запроса | `16` | — |
| `IGNITE_SQL_MERGE_TABLE_MAX_SIZE` | Определяет максимальное количество строк результата SQL-запроса, которое можно поместить в объединенную таблицу в DataGrid | `10,000` | — |
| `IGNITE_SQL_MERGE_TABLE_PREFETCH_SIZE` | Определяет количество строк результата SQL-запроса, которое будет предварительно загружено в объединенную таблицу перед применением бинарного поиска для определения границ | `1024` | — |
| `IGNITE_SQL_PARSER_DISABLE_H2_FALLBACK` | Позволяет отключить использование SQL-парсера H2 в случае, если внутренний SQL-парсер не справляется с обработкой запроса | — | — |
| `IGNITE_SQL_RETRY_TIMEOUT` | Определяет тайм-аут перед повторной попыткой выполнения SQL-запроса | `30000` | мс |
| `IGNITE_SQL_SYSTEM_SCHEMA_NAME_IGNITE` | Позволяет включить режим обратной совместимости, при котором `IGNITE` используется в качестве схемы SQL-системы | — | — |
| `IGNITE_SQL_UUID_DDL_BYTE_FORMAT` | Позволяет  включить обработку UUID в формате байтов с помощью операторов определения данных (DDL) для обеспечения обратной совместимости | — | — |
| `IGNITE_SSH_HOST` | Определяет SSH-хост для узлов, которые запущены с помощью инструмента администрирования кластера Visor | — | — |
| `IGNITE_SSH_USER_NAME` | Задает имя пользователя SSH для узлов, которые запущены с помощью инструмента администрирования кластера Visor | — | — |
| `IGNITE_START_CACHES_ON_JOIN` | Позволяет автоматически запускать все существующие кеши локально на клиентском узле при его запуске | — | — |
| `IGNITE_STARVATION_CHECK_INTERVAL` | Задает интервал, спустя который DataGrid будет проверять состояние пула потоков на предмет нехватки ресурсов (starvation) | `DFLT_PERIODIC_STARVATION_CHECK_FREQ = 1000 * 30` | мс |
| `IGNITE_STREAM_TRANSFORMER_COMPATIBILITY_MODE` | Управляет режимом обратной совместимости для метода `StreamTransformer.from(CacheEntryProcessor)` | — | — |
| `IGNITE_SUCCESS_FILE` | Определяет имя файла, который создается для обозначения успешного запуска и корректного функционирования узла | — | — |
| `IGNITE_SYSTEM_WORKER_BLOCKED_TIMEOUT` | Определяет максимальный допустимый период неактивности для системного рабочего потока | — | мс |
| `IGNITE_TCP_COMM_SET_ATTR_HOST_NAMES` | Позволяет устанавливать значение атрибута `ATTR_HOST_NAMES`, когда значение `getLocalHost` является IP-адресом, обеспечивая таким образом обратную совместимость | `false` | — |
| `IGNITE_TCP_DISCOVERY_ADDRESSES` | Содержит список адресов, которые разделены запятыми, в формате: `xx.xxx.xx.xxx:xxxxx,xx.xxx.xx.xxx:xxxxx` | — | — |
| `IGNITE_TEST_ENV` | Значение параметра должно быть установлено как `true` исключительно во время проведения junit-тестов | — | — |
| `IGNITE_TEST_FEATURES_ENABLED` | Если у параметра установлено значение `true`, активируются функции тестирования | `false` | — |
| `IGNITE_THREAD_DUMP_ON_EXCHANGE_TIMEOUT` | Позволяет настроить создание дампа потоков в случае превышения тайм-аута обмена партициями. Если у параметра установлено значение `true`, при возникновении такой ситуации будет создан и сохранен дамп потоков для анализа проблемы | — | — |
| `IGNITE_THRESHOLD_WAIT_TIME_NEXT_WAL_SEGMENT` | Устанавливает пороговое время, по достижении которого в журнал будет добавлено предупреждение (если ожидание следующего WAL-сегмента займет больше времени, чем указанный порог) | `DFLT_THRESHOLD_WAIT_TIME_NEXT_WAL_SEGMENT = 1000L` | мс |
| `IGNITE_THRESHOLD_WAL_ARCHIVE_SIZE_PERCENTAGE` | Устарел, используйте параметр `IGNITE_SQL_FORCE_LAZY_RESULT_SET(long)` | — | — |
| `IGNITE_THROTTLE_INLINE_SIZE_CALCULATION` | Регулирует частоту расчетов встроенного размера строк индекса и логирования рекомендаций по размеру встроенного индекса | `DFLT_THROTTLE_INLINE_SIZE_CALCULATION = 1_000` | — |
| `IGNITE_THROTTLE_LOG_THRESHOLD` | Определяет порог для регулирования записи операций в журнал в DataGrid. Когда число записываемых операций достигает данного порога, частота их записи снижается для предотвращения перегрузки системы | `DFLT_THROTTLE_LOG_THRESHOLD = 10` | — |
| `IGNITE_TO_STRING_COLLECTION_LIMIT` | Ограничивает количество элементов коллекции (карты, массива), которые будут выводиться при преобразовании объектов в строку (например, при вызове метода `toString()`) | `DFLT_TO_STRING_COLLECTION_LIMIT = 100` | — |
| `IGNITE_TO_STRING_INCLUDE_SENSITIVE` | Определяет, должна ли конфиденциальная информация включаться в вывод метода `toString()`. Если у параметра установлено значение `true`, конфиденциальные данные будут включены в вывод | `DFLT_TO_STRING_INCLUDE_SENSITIVE = true` | — |
| `IGNITE_TO_STRING_MAX_LENGTH` | Определяет максимальную длину строки, которая будет возвращаться методом `toString()`. Если результирующая строка превышает установленное значение, она будет обрезана | `DFLT_TO_STRING_MAX_LENGTH = 10_000` | — |
| `IGNITE_TRANSACTION_TIME_DUMP_SAMPLES_COEFFICIENT` | Коэффициент выборки завершенных транзакций, которые будут записаны в лог | `0` | — |
| `IGNITE_TRANSACTION_TIME_DUMP_SAMPLES_PER_SECOND_LIMIT` | Устанавливает ограничение на количество выборок завершенных транзакций, которые будут записаны в лог каждую секунду, если значение параметра `IGNITE_TRANSACTION_TIME_DUMP_SAMPLES_COEFFICIENT` больше `0.0` | `DFLT_TRANSACTION_TIME_DUMP_SAMPLES_PER_SECOND_LIMIT = 5` | — |
| `IGNITE_TROUBLESHOOTING_LOGGER` | Если у параметра установлено значение `true`, будет включено логирование устранения неисправностей | — | — |
| `IGNITE_TTL_EXPIRE_BATCH_SIZE` | Определяет количество просроченных записей, которые будут удалены из кеша при каждой операции пользователя | `DFLT_TTL_EXPIRE_BATCH_SIZE = 5` | — |
| `IGNITE_TX_DEADLOCK_DETECTION_MAX_ITERS` | Указывает максимальное количество итераций для процедуры обнаружения взаимоблокировок (deadlock) в транзакциях | `DFLT_TX_DEADLOCK_DETECTION_MAX_ITERS = 1000` | — |
| `IGNITE_TX_DEADLOCK_DETECTION_TIMEOUT` | Указывает тайм-аут для процедуры обнаружения взаимоблокировок в транзакциях | `DFLT_TX_DEADLOCK_DETECTION_TIMEOUT = 60000` | мс |
| `IGNITE_TX_OWNER_DUMP_REQUESTS_ALLOWED` | Показывает, разрешены ли запросы на выгрузку с локального узла на ближайший (near) узел при обнаружении длительной транзакции | `DFLT_TX_OWNER_DUMP_REQUESTS_ALLOWED = true` | — |
| `IGNITE_UNWIND_THROTTLING_TIMEOUT` | Определяет тайм-аут, который предотвращает избыточный доступ к структуре `PendingTree` при откате транзакции, если ничего еще не готово для очистки | `DFLT_UNWIND_THROTTLING_TIMEOUT = 500L` | мс |
| `IGNITE_UNWRAP_BINARY_FOR_INDEXING_SPI` | Если у параметра установлено значение `{@code true}`, `BinaryObject` будет развернут перед передачей в `IndexingSpi`, чтобы сохранить старое поведение обработчика запросов с `IndexingSpi` | — | — |
| `IGNITE_UPDATE_NOTIFIER` | Если у параметра установлено значение `false`, DataGrid не будет выполнять проверки наличия новых версий программного обеспечения | `DFLT_UPDATE_NOTIFIER = true` | — |
| `IGNITE_USE_ASYNC_FILE_IO_FACTORY` | Если у параметра установлено значение `true`, DataGrid по умолчанию будет использовать фабрику асинхронного ввода-вывода файлов | `DFLT_USE_ASYNC_FILE_IO_FACTORY = true` | — |
| `IGNITE_USE_BINARY_ARRAYS` | Включает поддержку хранения массивов с типом в бинарном формате | `DFLT_IGNITE_USE_BINARY_ARRAYS = false` | — |
| `IGNITE_USE_LEGACY_NODE_COMPARATOR` | Если у параметра установлено значение `true`, DataGrid будет использовать устаревший компаратор (comparator) узлов, который основан на порядке узлов, вместо нового | `false` | — |
| `IGNITE_WAIT_FOR_BACKUPS_ON_SHUTDOWN` | Устарел, используйте параметр `shutdownPolicy` объекта `IgniteConfiguration` | — | — |
| `IGNITE_WAIT_SCHEMA_UPDATE` | Тайм-аут ожидания обновления схемы, если не найдена схема для последней принятой версии | `DFLT_WAIT_SCHEMA_UPDATE = 30_000` | мс |
| `IGNITE_WAL_COMPRESSOR_WORKER_THREAD_CNT` | Количество потоков рабочих WAL-компрессоров | `DFLT_WAL_COMPRESSOR_WORKER_THREAD_CNT = 4` | — |
| `IGNITE_WAL_FSYNC_WITH_DEDICATED_WORKER` | Управляет использованием специализированного рабочего потока для реализации WAL даже в режиме синхронизации файловой системы (`FSYNC`). Если у параметра установлено значение `true`, выделенный рабочий поток будет обрабатывать запись в WAL | `false` | — |
| `IGNITE_WAL_MMAP` | Определяет, следует ли использовать отображаемые в памяти файлы (`MMAP`) для реализации WAL | `DFLT_WAL_MMAP = true` | — |
| `IGNITE_WAL_SEGMENT_SYNC_TIMEOUT` | Определяет тайм-аут синхронизации сегмента WAL-журнала | `DFLT_WAL_SEGMENT_SYNC_TIMEOUT = 500L` | мс |
| `IGNITE_WAL_SERIALIZER_VERSION` | Определяет версию WAL-сериализатора | `LATEST_SERIALIZER_VERSION = 2` | — |
| `IGNITE_WORK_DIR` | Переменная окружения для установки рабочей директории | — | — |
| `IGNITE_ZOOKEEPER_DISCOVERY_MAX_RETRY_COUNT` | Максимальное количество попыток повторного подключения к ZooKeeper в механизме обнаружения узлов | `10` | — |
| `IGNITE_ZOOKEEPER_DISCOVERY_RETRY_TIMEOUT` | Определяет интервал времени между попытками повторного подключения к ZooKeeper в механизме обнаружения узлов | `2000` | мс |

## Прочие свойства

| Название параметра | Описание | Значение по умолчанию | Единицы измерения |
|---|---|---|---|
| `baselineAutoAdjustEnabled` | Указывает, включена ли функция автоматической регулировки базовых показателей для кластера. Если у параметра установлено значение `true`, кластер работает в режиме автонастройки. Если у параметра установлено значение `false`, управление осуществляется вручную | — | — |
| `baselineAutoAdjustTimeout` | Определяет время, в течение которого система ожидает внесения изменений в топологию кластера после последних изменений топологии сервера, например, присоединения, выхода или отказа узла | — | мс |
| `collisionsDumpInterval` | Устанавливает интервал, в течение которого собираются статистические данные о коллизиях ключей транзакций. Если у параметра установлено значение больше нуля, информация о коллизиях будет выводиться с указанной периодичностью. Каждая транзакция, кроме `OPTIMISTIC SERIALIZABLE`, захватывает блокировки на всех задействованных ключах, и иногда очередь блокировок для каждого ключа может расти | `DFLT_DUMP_TX_COLLISIONS_INTERVAL = 1000` | мс |
| `computeJobWorkerInterruptTimeout` | Распределенное свойство задает тайм-аут, по истечении которого работа будет прервана после ее отмены | — | мс |
| `longOperationsDumpTimeout` | Операции с кешем, которые занимают больше времени, чем значение данного свойства, будут записываться в лог. Чтобы отключить функциональность, установите значение параметра равным нулю | `DFLT_LONG_OPERATIONS_DUMP_TIMEOUT = 60_000L` | мс |
| `longTransactionTimeDumpSamplesPerSecondLimit` | Определяет количество записей о завершенных транзакциях, которые будут сохраняться в логе каждую секунду, если коэффициент `transactionTimeDumpSamplesCoefficient` больше `0.0`. Значение должно быть целым числом больше нуля | `DFLT_TRANSACTION_TIME_DUMP_SAMPLES_PER_SECOND_LIMIT = 5` | — |
| `longTransactionTimeDumpThreshold` | Пороговое значение тайм-аута для длительных транзакций. Если транзакция превышает данное значение, она будет записана в лог вместе с информацией о времени, которые было затрачено на системные операции (например, получение блокировок, подготовка, фиксация (commit) и другие), и на выполнение кода клиентом (время, когда клиентский узел выполняет код, удерживая транзакцию и не ожидая ее завершения). Если значение параметра не установлено, оно считается равным `0` | `0` | мс |
| `shutdown.policy` | Политика отключения определяет гарантии безопасности данных при штатном выключении одного или нескольких узлов кластера. `IMMEDIATE` — остановка произойдет настолько быстро, насколько возможно. `GRACEFUL` — остановка произойдет в том случае, если в кластере останется хотя бы одна копия партиции | — | — |
| `snapshotTransferRate` | Ограничивает скорость снятия дампа. Если у параметра установлено значение `0`, ограничений нет | `0` | б/сек |
| `sql.defaultQueryTimeout` | Определяет время ожидания выполнения запроса | — | мс |
| `sql.disableCreateLuceneIndexForStringValueType` | Флаг позволяет отключить автоматическое создание индекса `Lucene` для строковых значений по умолчанию | `false` | — |
| `sql.disabledFunctions` | Список отключенных SQL-функций. Для задания значения перечислите функции через запятую | — | — |
| `statistics.usage.state` | Режим использования статистики. `OFF` — статистика не используется. `NO_UPDATE` — статистика используется без обновлений. `ON` — статистика используется и обновляется после каждого изменения (по умолчанию) | `ON` | — |
| `thinClientProperty.showStackTrace` | Если у параметра установлено значение `true`, в ответ тонкого клиента будет включена полная трассировка стека в случае возникновения исключения. Если у параметра установлено значение `false`, будет включено только сообщение об исключении верхнего уровня | — | — |
| `tr.config` | Определяет ключ, который используется для хранения конфигурационных данных трассировки во внутреннем распределенном хранилище DataGrid (distributed metastorage), данные в котором синхронизированы между узлами в кластере и недоступны внешним пользователям через общедоступный API DataGrid | — | — |
| `transactionTimeDumpSamplesCoefficient` | Определяет долю завершенных транзакций, информация о которых будет сохранена в логе. Значение должно быть дробным числом в диапазоне от `0.0` до `1.0` включительно | `0` | — |
| `txOwnerDumpRequestsAllowed` | Устанавливает, разрешено ли отправлять запросы с локального узла на ближайший (near) узел при обнаружении долго выполняющейся транзакции. Если разрешение получено, запрос на вычисление будет направлен ближайшему узлу для получения дампа потока владельца транзакции. Возвращаемое значение:<br>`true`, если разрешено; иначе `false` | `DFLT_TX_OWNER_DUMP_REQUESTS_ALLOWED = true` | — |