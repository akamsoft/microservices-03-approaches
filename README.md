# Домашнее задание к занятию «Микросервисы: подходы»

Вы работаете в крупной компании, которая строит систему на основе микросервисной архитектуры.
Вам как DevOps-специалисту необходимо выдвинуть предложение по организации инфраструктуры для разработки и эксплуатации.


## Задача 1: Обеспечить разработку

Предложите решение для обеспечения процесса разработки: хранение исходного кода, непрерывная интеграция и непрерывная поставка. 
Решение может состоять из одного или нескольких программных продуктов и должно описывать способы и принципы их взаимодействия.

Решение должно соответствовать следующим требованиям:
- облачная система;
- система контроля версий Git;
- репозиторий на каждый сервис;
- запуск сборки по событию из системы контроля версий;
- запуск сборки по кнопке с указанием параметров;
- возможность привязать настройки к каждой сборке;
- возможность создания шаблонов для различных конфигураций сборок;
- возможность безопасного хранения секретных данных (пароли, ключи доступа);
- несколько конфигураций для сборки из одного репозитория;
- кастомные шаги при сборке;
- собственные докер-образы для сборки проектов;
- возможность развернуть агентов сборки на собственных серверах;
- возможность параллельного запуска нескольких сборок;
- возможность параллельного запуска тестов.

Обоснуйте свой выбор.

### Выбранное решение

**GitLab + GitLab Runner + GitLab Container Registry + HashiCorp Vault.**

GitLab используется как облачная платформа для хранения исходного кода, CI/CD, управления доступом, контейнерного реестра и секретов. GitLab Runner разворачивается на собственных серверах компании и выполняет сборки в Docker-контейнерах.

### Архитектура

```text
Разработчик
   │ git push / merge request
   ▼
GitLab
   ├── Git-репозиторий сервиса
   ├── .gitlab-ci.yml
   ├── CI/CD pipeline
   ├── Container Registry
   └── Секреты / интеграция с Vault
          │
          ▼
GitLab Runner на собственных серверах
   ├── Сборка Docker-образа
   ├── Запуск unit- и integration-тестов
   ├── Параллельное выполнение задач
   └── Публикация образа в Registry
```

### Как закрываются требования

| Требование | Реализация |
|---|---|
| Облачная система | GitLab SaaS или self-managed GitLab в облачной инфраструктуре |
| Система контроля версий Git | Встроенный Git, ветки, merge requests, защита веток |
| Репозиторий на каждый сервис | Отдельный проект GitLab для каждого микросервиса |
| Сборка по событию из SCM | Пайплайн запускается на `push`, merge request или создание тега |
| Сборка по кнопке с параметрами | Ручной запуск pipeline с переменными окружения |
| Настройки для каждой сборки | Переменные проекта, группы, окружения и pipeline |
| Шаблоны конфигураций | Общие CI-шаблоны через `include`, `extends` и CI/CD Components |
| Безопасное хранение секретов | Masked/protected variables, интеграция с HashiCorp Vault |
| Несколько конфигураций из одного репозитория | Условные правила, переменные, `parallel:matrix` |
| Кастомные шаги | `before_script`, `script`, `after_script`, собственные скрипты |
| Собственные Docker-образы | Параметр `image` в job и собственные образы в Registry |
| Агенты на собственных серверах | GitLab Runner с Docker- или Kubernetes-executor |
| Параллельные сборки | Несколько Runner’ов и `parallel: N` |
| Параллельные тесты | `parallel:matrix`, шардирование тестов, JUnit-отчёты |

### Пример `.gitlab-ci.yml`

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  SERVICE_NAME: security

lint:
  stage: lint
  image: python:3.11-slim
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.11-slim
  parallel: 4
  script:
    - pip install -r requirements.txt
    - pytest --splits 4 --group $CI_NODE_INDEX --junitxml=report.xml
  artifacts:
    when: always
    reports:
      junit: report.xml

build:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  parallel:
    matrix:
      - BUILD_ENV: [dev, stage, prod]
  script:
    - docker build
      --build-arg ENV=$BUILD_ENV
      -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA-$BUILD_ENV .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA-$BUILD_ENV

deploy:
  stage: deploy
  when: manual
  script:
    - echo "Deploying $SERVICE_NAME to $DEPLOY_ENV"
  environment:
    name: $DEPLOY_ENV
```

### Обоснование

GitLab выбран, поскольку он объединяет Git, CI/CD, реестр образов, переменные окружения и секреты в единой платформе. Это упрощает эксплуатацию и не требует связывать несколько независимых инструментов.

GitLab Runner позволяет выполнять сборки на серверах компании, что важно для приватных зависимостей, внутренних сетей и контроля над вычислительными ресурсами. Поддержка `parallel:matrix` и нескольких Runner’ов обеспечивает параллельное выполнение сборок и тестов.

Альтернативы:

- **GitHub Actions** — удобен, если компания уже использует GitHub, но требует отдельных решений для Container Registry и управления секретами.
- **Jenkins** — очень гибкий, но требует больше усилий на поддержку плагинов, агентов и инфраструктуры.
- **TeamCity** — удобный CI, но не является полноценной системой контроля версий.

## Задача 2: Логи

Предложите решение для обеспечения сбора и анализа логов сервисов в микросервисной архитектуре.
Решение может состоять из одного или нескольких программных продуктов и должно описывать способы и принципы их взаимодействия.

Решение должно соответствовать следующим требованиям:
- сбор логов в центральное хранилище со всех хостов, обслуживающих систему;
- минимальные требования к приложениям, сбор логов из stdout;
- гарантированная доставка логов до центрального хранилища;
- обеспечение поиска и фильтрации по записям логов;
- обеспечение пользовательского интерфейса с возможностью предоставления доступа разработчикам для поиска по записям логов;
- возможность дать ссылку на сохранённый поиск по записям логов.

Обоснуйте свой выбор.

### Выбранное решение

**Vector + Elasticsearch + Kibana.**

- **Vector** — агент сбора логов, устанавливаемый на каждом хосте.
- **Elasticsearch** — центральное хранилище и поисковый движок.
- **Kibana** — веб-интерфейс для поиска, фильтрации и сохранения поисковых запросов.

### Архитектура

```text
Приложение
   │ stdout / stderr
   ▼
Docker / containerd
   │
   ▼
Vector на каждом хосте
   ├── Чтение логов контейнеров
   ├── Нормализация полей
   ├── Дисковый буфер
   └── Отправка в Elasticsearch
          │
          ▼
Elasticsearch
   │
   ▼
Kibana
   └── Поиск, фильтры, сохранённые запросы
```

### Как закрываются требования

| Требование | Реализация |
|---|---|
| Центральное хранилище | Elasticsearch |
| Сбор со всех хостов | Vector разворачивается на каждом хосте или как DaemonSet в Kubernetes |
| Минимальные требования к приложениям | Сервисы пишут только в `stdout`/`stderr` |
| Сбор логов из stdout | Vector читает Docker-логи через Docker API |
| Гарантированная доставка | Дисковый буфер Vector, повторные попытки отправки, подтверждение записи в Elasticsearch |
| Поиск и фильтрация | Полнотекстовый поиск Elasticsearch, KQL и фильтры Kibana |
| UI для разработчиков | Kibana с ролями и разделением доступа |
| Ссылка на сохранённый поиск | Saved Search в Kibana с возможностью поделиться ссылкой |

### Пример конфигурации Vector

```yaml
sources:
  docker_logs:
    type: docker_logs
    include_containers:
      - security
      - uploader
      - api-gateway

transforms:
  enrich:
    type: remap
    inputs:
      - docker_logs
    source: |
      .service = .container_name
      .host = get_hostname!()
      .received_at = now()

sinks:
  elasticsearch:
    type: elasticsearch
    inputs:
      - enrich
    endpoints:
      - "http://elasticsearch:9200"
    bulk:
      index: logs-%{Y.%m.%d}
    buffer:
      type: disk
      max_size: 1073741824
      when_full: block
    request:
      retry_attempts: 10
      retry_max_duration_secs: 60
```

### Обоснование

Vector выбран как агент, потому что он потребляет меньше ресурсов, чем Logstash, поддерживает чтение Docker-логов, преобразование событий и надёжную буферизацию на диске. Это позволяет не потерять логи при временной недоступности Elasticsearch.

Elasticsearch обеспечивает быстрый полнотекстовый поиск и гибкую фильтрацию по полям: сервису, хосту, уровню логирования, идентификатору запроса и времени. Kibana даёт разработчикам удобный интерфейс и позволяет сохранять поисковые запросы, которыми можно делиться ссылкой.

Альтернативы:

- **EFK**: Fluent Bit + Elasticsearch + Kibana. Зрелое решение, но Vector удобнее в настройке маршрутизации и буферизации.
- **Loki + Grafana**: дешевле по ресурсам, но полнотекстовый поиск по содержимому логов ограничен.
- **Splunk / Datadog**: удобные SaaS-решения, но дороже и создают зависимость от внешнего вендора.

## Задача 3: Мониторинг

Предложите решение для обеспечения сбора и анализа состояния хостов и сервисов в микросервисной архитектуре.
Решение может состоять из одного или нескольких программных продуктов и должно описывать способы и принципы их взаимодействия.

Решение должно соответствовать следующим требованиям:
- сбор метрик со всех хостов, обслуживающих систему;
- сбор метрик состояния ресурсов хостов: CPU, RAM, HDD, Network;
- сбор метрик потребляемых ресурсов для каждого сервиса: CPU, RAM, HDD, Network;
- сбор метрик, специфичных для каждого сервиса;
- пользовательский интерфейс с возможностью делать запросы и агрегировать информацию;
- пользовательский интерфейс с возможностью настраивать различные панели для отслеживания состояния системы.

Обоснуйте свой выбор.

### Выбранное решение

**Prometheus + Node Exporter + cAdvisor + Grafana + Alertmanager.**

- **Prometheus** собирает и хранит метрики.
- **Node Exporter** собирает метрики хостов.
- **cAdvisor** собирает метрики контейнеров и сервисов.
- **Grafana** предоставляет интерфейс для запросов и дашбордов.
- **Alertmanager** отправляет уведомления о проблемах.

### Архитектура

```text
Node Exporter ──────┐
cAdvisor ───────────┤
security /metrics ──┤
uploader /metrics ──┼──► Prometheus ──► Alertmanager
MinIO /metrics ─────┤        │
nginx-exporter ─────┘        ▼
                          Grafana
```

### Как закрываются требования

| Требование | Реализация |
|---|---|
| Метрики со всех хостов | Node Exporter на каждом хосте |
| CPU, RAM, HDD, Network хоста | Метрики Node Exporter |
| Ресурсы каждого сервиса | cAdvisor: CPU, память, файловая система, сеть контейнера |
| Специфичные метрики сервисов | `/metrics` каждого приложения и экспортеры зависимостей |
| Запросы и агрегация | PromQL и Grafana Explore |
| Настраиваемые панели | Grafana Dashboards, переменные, шаблоны, dashboard-as-code |

### Пример `prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - "localhost:9090"

  - job_name: node-exporter
    static_configs:
      - targets:
          - "node-exporter:9100"

  - job_name: cadvisor
    static_configs:
      - targets:
          - "cadvisor:8080"

  - job_name: security
    metrics_path: /metrics
    static_configs:
      - targets:
          - "security:8000"

  - job_name: uploader
    metrics_path: /metrics
    static_configs:
      - targets:
          - "uploader:8001"

  - job_name: minio
    metrics_path: /minio/v2/metrics/cluster
    static_configs:
      - targets:
          - "minio:9000"
```

### Полезные PromQL-запросы

```promql
# Загрузка CPU хоста, %
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))

# Свободное место на диске, %
100 * node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
  / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}

# Использование CPU контейнером
sum by (container_label_com_docker_compose_service) (
  rate(container_cpu_usage_seconds_total[5m])
)

# Использование RAM контейнером
sum by (container_label_com_docker_compose_service) (
  container_memory_working_set_bytes
)

# Распределение запросов по сервисам
sum by (service) (rate(http_requests_total[5m]))
```

### Обоснование

Prometheus является стандартом де-факто для мониторинга микросервисов и Kubernetes. Его pull-модель позволяет сервису просто предоставлять endpoint `/metrics`, а Prometheus самостоятельно опрашивает цели по расписанию.

Grafana выбрана как единый интерфейс для PromQL-запросов, визуализации и настраиваемых дашбордов. Дашборды можно хранить в Git и автоматически провижинить при запуске Grafana.

Альтернативы:

- **Zabbix** — хорош для классической инфраструктуры, но менее удобен для динамических контейнерных сред.
- **VictoriaMetrics** — подходит для долгого хранения метрик и высоких нагрузок, может использоваться как backend для Prometheus.
- **Datadog / New Relic** — удобные SaaS-решения, но дороже и создают vendor lock-in.

## Задача 4: Логи * (необязательная)

Продолжить работу по задаче API Gateway: сервисы, используемые в задаче, пишут логи в stdout. 

Добавить в систему сервисы для сбора логов Vector + ElasticSearch + Kibana со всех сервисов, обеспечивающих работу API.

### Результат выполнения: 

docker compose файл, запустив который можно перейти по адресу http://localhost:8081, по которому доступна Kibana.
Логин в Kibana должен быть admin, пароль qwerty123456.

### Состав решения

- **Vector** — собирает логи из stdout контейнеров.
- **Elasticsearch** — хранит и индексирует логи.
- **Kibana** — предоставляет интерфейс поиска.
- **Nginx** — проксирует Kibana на порт `8081`.

### `docker-compose.yml`

```yaml
version: "3.8"

services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "8081:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - kibana

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "true"
      ELASTIC_PASSWORD: qwerty123456
      ES_JAVA_OPTS: "-Xms1g -Xmx1g"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS -u elastic:qwerty123456 http://localhost:9200/_cluster/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 30

  kibana:
    image: docker.elastic.co/kibana/kibana:8.15.0
    environment:
      ELASTICSEARCH_HOSTS: "http://elasticsearch:9200"
      ELASTICSEARCH_USERNAME: elastic
      ELASTICSEARCH_PASSWORD: qwerty123456
    depends_on:
      elasticsearch:
        condition: service_healthy

  vector:
    image: timberio/vector:0.41.1-debian
    command: ["--config", "/etc/vector/vector.yaml"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./vector/vector.yaml:/etc/vector/vector.yaml:ro
    depends_on:
      - elasticsearch

  security:
    build:
      context: ./security
    environment:
      SERVICE_NAME: security
    ports:
      - "8000:8000"

  uploader:
    build:
      context: ./uploader
    environment:
      SERVICE_NAME: uploader
    ports:
      - "8001:8001"

volumes:
  es_data:
```

### `nginx.conf`

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://kibana:5601;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### `vector/vector.yaml`

```yaml
sources:
  docker_logs:
    type: docker_logs
    include_containers:
      - security
      - uploader

transforms:
  enrich:
    type: remap
    inputs:
      - docker_logs
    source: |
      .service = .container_name
      .host = get_hostname!()
      .received_at = now()

sinks:
  elasticsearch:
    type: elasticsearch
    inputs:
      - enrich
    endpoints:
      - "http://elasticsearch:9200"
    bulk:
      index: logs-%{Y.%m.%d}
    auth:
      strategy: basic
      user: elastic
      password: qwerty123456
    buffer:
      type: disk
      max_size: 268435456
      when_full: block
```

### Запуск

```bash
docker compose up -d
```

После запуска Kibana будет доступна по адресу:

```text
http://localhost:8081
```

Логин:

```text
Логин: admin
Пароль: qwerty123456
```

В Kibana необходимо создать Data View по индексу `logs-*`, после чего станут доступны поиск, фильтрация и сохранённые поисковые запросы.

## Задача 5: Мониторинг * (необязательная)

Продолжить работу по задаче API Gateway: сервисы, используемые в задаче, предоставляют набор метрик в формате prometheus:

- сервис security по адресу /metrics,
- сервис uploader по адресу /metrics,
- сервис storage (minio) по адресу /minio/v2/metrics/cluster.

Добавить в систему сервисы для сбора метрик (Prometheus и Grafana) со всех сервисов, обеспечивающих работу API.
Построить в Graphana dashboard, показывающий распределение запросов по сервисам.

### Результат выполнения: 

docker compose файл, запустив который можно перейти по адресу http://localhost:8081, по которому доступна Grafana с настроенным Dashboard.
Логин в Grafana должен быть admin, пароль qwerty123456.

### Состав решения

- **Prometheus** — собирает метрики сервисов.
- **Grafana** — визуализирует метрики и содержит dashboard.
- **Nginx** — проксирует Grafana на порт `8081`.

### `docker-compose.yml`

```yaml
version: "3.8"

services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "8081:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - grafana

  prometheus:
    image: prom/prometheus:v2.54.1
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:11.2.0
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: qwerty123456
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    depends_on:
      - prometheus

  security:
    build:
      context: ./security
    ports:
      - "8000:8000"

  uploader:
    build:
      context: ./uploader
    ports:
      - "8001:8001"

  minio:
    image: minio/minio:RELEASE.2024-08-17T01-24-54Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  grafana_data:
  minio_data:
```

### `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - "localhost:9090"

  - job_name: security
    metrics_path: /metrics
    static_configs:
      - targets:
          - "security:8000"

  - job_name: uploader
    metrics_path: /metrics
    static_configs:
      - targets:
          - "uploader:8001"

  - job_name: minio
    metrics_path: /minio/v2/metrics/cluster
    static_configs:
      - targets:
          - "minio:9000"
```

### `grafana/provisioning/datasources/datasource.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### `grafana/provisioning/dashboards/dashboards.yml`

```yaml
apiVersion: 1

providers:
  - name: default
    folder: API Gateway
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

### Dashboard: распределение запросов по сервисам

В Grafana создаётся dashboard с панелью **Time series** и запросом:

```promql
sum by (service) (
  rate(http_requests_total[5m])
)
```

Если сервисы экспортируют метрики с меткой `service`, график покажет распределение запросов между `security`, `uploader` и `minio`.

### Запуск

```bash
docker compose up -d
```

Grafana будет доступна по адресу:

```text
http://localhost:8081
```

Логин:

```text
Логин: admin
Пароль: qwerty123456
```

## Итоговая архитектура

```text
GitLab
  ├── Git-репозитории сервисов
  ├── CI/CD pipeline
  ├── Container Registry
  └── Секреты / Vault

Приложения
  ├── stdout → Vector → Elasticsearch → Kibana
  └── /metrics → Prometheus → Grafana → Alertmanager
```

Такая инфраструктура обеспечивает независимую разработку и выпуск микросервисов, централизованный поиск по логам и единое наблюдение за состоянием хостов, контейнеров и бизнес-метрик сервисов.