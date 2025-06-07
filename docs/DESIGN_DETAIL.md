# 日本株日次データ自動取得アプリ 詳細設計書

## 1. システムアーキテクチャ

### 1.1. 全体構成図

```
Cloud Scheduler → Pub/Sub → Cloud Run → BigQuery
                               ↓
                         Secret Manager
                               ↓
                          J-Quants API
```

### 1.2. コンポーネント詳細

#### 1.2.1. Cloud Scheduler
- **目的**: 日次データ取得の定期実行トリガー
- **スケジュール**: 平日16:30 JST（市場クローズ後30分）
- **メッセージ内容**: データ取得日付を含むJSON

#### 1.2.2. Pub/Sub
- **Topic名**: `stock-data-trigger`
- **Subscription名**: `stock-data-processor`
- **メッセージ保持期間**: 7日間
- **配信確認**: プッシュ配信（Cloud Runエンドポイント）

#### 1.2.3. Cloud Run
- **サービス名**: `stock-data-collector`
- **コンテナイメージ**: `gcr.io/{project-id}/stock-data-collector`
- **メモリ**: 1GB
- **CPU**: 1vCPU
- **最大実行時間**: 30分
- **最大インスタンス数**: 1（並行実行制御）

#### 1.2.4. BigQuery
- **データセット**: `stock_data`
- **テーブル**: `daily_stock_prices`
- **ロケーション**: asia-northeast1（東京）

## 2. アプリケーション設計

### 2.1. ディレクトリ構造

```
src/
├── main.py                    # Cloud Runエントリーポイント
├── config/
│   ├── __init__.py
│   └── settings.py           # 設定管理
├── services/
│   ├── __init__.py
│   ├── jquants_client.py     # J-Quants API クライアント
│   ├── bigquery_client.py    # BigQuery クライアント
│   └── secret_manager.py     # Secret Manager クライアント
├── models/
│   ├── __init__.py
│   └── stock_data.py         # データモデル定義
├── utils/
│   ├── __init__.py
│   ├── logger.py             # ロギング設定
│   ├── retry.py              # リトライ機能
│   └── date_utils.py         # 日付ユーティリティ
└── tests/
    ├── __init__.py
    ├── test_jquants_client.py
    ├── test_bigquery_client.py
    └── test_models.py
```

### 2.2. データフロー

```
1. Cloud Scheduler → Pub/Sub (トリガーメッセージ)
2. Cloud Run起動 → メッセージ受信
3. 日付検証（営業日判定）
4. Secret Manager → APIキー取得
5. J-Quants API → 認証
6. J-Quants API → 株価データ取得
7. データ変換・検証
8. BigQuery → データ投入（MERGE）
9. ログ出力・処理完了
```

## 3. データ設計

### 3.1. BigQueryテーブル設計

#### 3.1.1. daily_stock_prices テーブル

```sql
CREATE TABLE `{project}.stock_data.daily_stock_prices` (
  date DATE NOT NULL,
  security_code STRING NOT NULL,
  security_name STRING,
  market_code STRING,
  open_price NUMERIC,
  high_price NUMERIC,
  low_price NUMERIC,
  close_price NUMERIC,
  volume INTEGER,
  turnover_value NUMERIC,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY date
CLUSTER BY security_code
OPTIONS(
  description="日次株価データテーブル",
  labels=[("env", "production"), ("data_type", "stock_prices")]
);
```

#### 3.1.2. データ投入用MERGE文

```sql
MERGE `{project}.stock_data.daily_stock_prices` AS target
USING (
  SELECT * FROM UNNEST(@stock_data_array)
) AS source
ON target.date = source.date AND target.security_code = source.security_code
WHEN MATCHED THEN
  UPDATE SET
    security_name = source.security_name,
    market_code = source.market_code,
    open_price = source.open_price,
    high_price = source.high_price,
    low_price = source.low_price,
    close_price = source.close_price,
    volume = source.volume,
    turnover_value = source.turnover_value,
    updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (
    date, security_code, security_name, market_code,
    open_price, high_price, low_price, close_price,
    volume, turnover_value, created_at, updated_at
  )
  VALUES (
    source.date, source.security_code, source.security_name, source.market_code,
    source.open_price, source.high_price, source.low_price, source.close_price,
    source.volume, source.turnover_value, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
  );
```

### 3.2. データモデル（Python）

```python
@dataclass
class StockPrice:
    date: str
    security_code: str
    security_name: str
    market_code: str
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Optional[Decimal]
    volume: Optional[int]
    turnover_value: Optional[Decimal]
```

## 4. API設計

### 4.1. J-Quants API統合

#### 4.1.1. 認証フロー
1. Secret Managerからリフレッシュトークン取得
2. トークンエンドポイントでアクセストークン取得
3. APIリクエストにBearerトークン設定

#### 4.1.2. データ取得エンドポイント
- **エンドポイント**: `/prices/daily_quotes`
- **パラメータ**: 
  - `date`: 取得対象日（YYYY-MM-DD）
  - `code`: 銘柄コード（空の場合は全銘柄）
- **レスポンス形式**: JSON配列

#### 4.1.3. レート制限対応
- **制限**: 10リクエスト/秒
- **対応**: 指数バックオフによるリトライ
- **最大リトライ回数**: 3回

### 4.2. Cloud Runエンドポイント

#### 4.2.1. Pub/Subハンドラー
```python
@app.route('/', methods=['POST'])
def handle_pubsub_message():
    # Pub/Subメッセージデコード
    # 営業日判定
    # データ取得・保存処理
    # レスポンス返却
```

#### 4.2.2. ヘルスチェックエンドポイント
```python
@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

## 5. エラーハンドリング設計

### 5.1. エラー分類

#### 5.1.1. 一時的エラー（リトライ対象）
- ネットワークタイムアウト
- HTTP 5xx エラー
- BigQuery一時的エラー
- レート制限エラー

#### 5.1.2. 永続的エラー（リトライ非対象）
- 認証エラー（401, 403）
- 不正なリクエスト（400）
- データ形式エラー

### 5.2. リトライ戦略

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ConnectionError, HTTPError))
)
def api_request_with_retry():
    pass
```

### 5.3. ログ設計

#### 5.3.1. ログレベル
- **INFO**: 処理開始・終了、主要ステップ
- **WARNING**: リトライ実行、データ異常
- **ERROR**: 処理失敗、予期しないエラー

#### 5.3.2. ログ出力形式
```json
{
  "timestamp": "2025-06-03T16:30:00Z",
  "severity": "INFO",
  "message": "Stock data collection started",
  "labels": {
    "component": "stock-data-collector",
    "process_date": "2025-06-03"
  },
  "trace": "projects/PROJECT_ID/traces/TRACE_ID"
}
```

## 6. 設定管理

### 6.1. 環境変数

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=my-project-id
BIGQUERY_DATASET=stock_data
BIGQUERY_TABLE=daily_stock_prices

# J-Quants API
JQUANTS_REFRESH_TOKEN_SECRET=jquants-refresh-token
JQUANTS_BASE_URL=https://api.jquants.com

# 設定
LOG_LEVEL=INFO
RETRY_MAX_ATTEMPTS=3
TIMEOUT_SECONDS=30
```

### 6.2. 設定ファイル管理

#### 6.2.1. .envファイル構成

開発環境では`.env`ファイルを使用して環境変数を管理します。本番環境ではCloud Runの環境変数設定やSecret Managerを使用します。

```bash
# .env.example
# Google Cloud設定
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET=stock_data
BIGQUERY_TABLE=daily_stock_prices
BIGQUERY_LOCATION=asia-northeast1

# J-Quants API設定
JQUANTS_BASE_URL=https://api.jquants.com
JQUANTS_REFRESH_TOKEN_SECRET=jquants-refresh-token
JQUANTS_EMAIL=your-email@example.com
JQUANTS_PASSWORD=your-password

# アプリケーション設定
LOG_LEVEL=INFO
RETRY_MAX_ATTEMPTS=3
TIMEOUT_SECONDS=30

# 開発環境設定
DEBUG=false
PORT=8080
```

#### 6.2.2. 設定読み込み実装

```python
# src/config/settings.py
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# .envファイルを読み込み（開発環境のみ）
if os.getenv("ENVIRONMENT", "development") == "development":
    load_dotenv()

@dataclass
class Settings:
    """アプリケーション設定"""
    # Google Cloud
    project_id: str
    bigquery_dataset: str
    bigquery_table: str
    bigquery_location: str
    
    # J-Quants API
    jquants_base_url: str
    jquants_refresh_token_secret: str
    jquants_email: Optional[str] = None
    jquants_password: Optional[str] = None
    
    # アプリケーション設定
    log_level: str = "INFO"
    retry_max_attempts: int = 3
    timeout_seconds: int = 30
    
    # 開発環境設定
    debug: bool = False
    port: int = 8080
    
    @classmethod
    def from_env(cls) -> "Settings":
        """環境変数から設定を読み込み"""
        return cls(
            project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            bigquery_dataset=os.environ["BIGQUERY_DATASET"],
            bigquery_table=os.environ["BIGQUERY_TABLE"],
            bigquery_location=os.getenv("BIGQUERY_LOCATION", "asia-northeast1"),
            jquants_base_url=os.environ["JQUANTS_BASE_URL"],
            jquants_refresh_token_secret=os.environ["JQUANTS_REFRESH_TOKEN_SECRET"],
            jquants_email=os.getenv("JQUANTS_EMAIL"),
            jquants_password=os.getenv("JQUANTS_PASSWORD"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            port=int(os.getenv("PORT", "8080"))
        )

# シングルトンインスタンス
settings = Settings.from_env()
```

#### 6.2.3. .gitignore設定

```bash
# .gitignore
# 環境変数ファイル
.env
.env.local
.env.*.local

# 秘密情報
*.pem
*.key
secrets/
```

#### 6.2.4. 環境別設定の管理

- **開発環境**: `.env`ファイルによるローカル設定
- **CI/CD環境**: GitHub Secrets等による設定注入
- **本番環境**: Cloud Run環境変数とSecret Managerによる設定管理

### 6.3. Secret Manager構成

```yaml
secrets:
  - name: jquants-refresh-token
    value: "${JQUANTS_REFRESH_TOKEN}"
  - name: jquants-mail-address
    value: "${JQUANTS_EMAIL}"
  - name: jquants-password
    value: "${JQUANTS_PASSWORD}"
```

## 7. テスト設計

### 7.1. テスト分類

#### 7.1.1. 単体テスト
- J-Quants APIクライアント
- BigQueryクライアント
- データモデル変換
- ユーティリティ関数

#### 7.1.2. 統合テスト
- エンドツーエンドデータフロー
- 外部サービス連携（モック使用）

### 7.2. テストデータ

```python
SAMPLE_STOCK_DATA = [
    {
        "Date": "2025-06-03",
        "Code": "7203",
        "CompanyName": "トヨタ自動車",
        "MarketCode": "0111",
        "Open": 2500.0,
        "High": 2520.0,
        "Low": 2480.0,
        "Close": 2510.0,
        "Volume": 1000000,
        "TurnoverValue": 2505000000
    }
]
```

## 8. デプロイメント設計

### 8.1. Docker設定

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
EXPOSE 8080

CMD ["python", "src/main.py"]
```

### 8.2. Cloud Build設定

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/stock-data-collector:$SHORT_SHA', '.']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/stock-data-collector:$SHORT_SHA']
  
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'stock-data-collector',
      '--image', 'gcr.io/$PROJECT_ID/stock-data-collector:$SHORT_SHA',
      '--platform', 'managed',
      '--region', 'asia-northeast1',
      '--allow-unauthenticated'
    ]
```

## 9. 運用設計

### 9.1. モニタリング

#### 9.1.1. メトリクス
- Cloud Run実行回数・成功率
- データ取得件数
- 処理時間
- エラー発生率

#### 9.1.2. アラート（将来拡張）
- 3日連続でデータ取得失敗
- API認証エラー
- BigQuery書き込みエラー

### 9.2. 運用手順

#### 9.2.1. 日次確認
1. Cloud Loggingでの実行ログ確認
2. BigQueryでのデータ投入確認
3. エラーログの有無確認

#### 9.2.2. 障害対応
1. ログ確認によるエラー原因特定
2. 必要に応じて手動再実行
3. APIキー更新（認証エラー時）

## 10. Terraformインフラ設計

### 10.1. ディレクトリ構造

```
terraform/
├── main.tf                   # プロバイダー設定・メインリソース
├── variables.tf              # 変数定義
├── outputs.tf               # 出力値定義
├── terraform.tfvars.example # 環境設定テンプレート
├── modules/
│   ├── bigquery/
│   │   ├── main.tf          # BigQueryリソース
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cloud_run/
│   │   ├── main.tf          # Cloud Runリソース
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── scheduler/
│   │   ├── main.tf          # Cloud Scheduler・Pub/Sub
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf          # サービスアカウント・IAM
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf          # 開発環境設定
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf          # 本番環境設定
│       ├── terraform.tfvars
│       └── backend.tf
└── scripts/
    ├── init.sh              # 初期セットアップスクリプト
    └── deploy.sh            # デプロイスクリプト
```

### 10.2. メインリソース設計

#### 10.2.1. プロバイダー設定
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "terraform-state-${var.project_id}"
    prefix = "stock-data-collector"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

#### 10.2.2. BigQueryモジュール
```hcl
# modules/bigquery/main.tf
resource "google_bigquery_dataset" "stock_data" {
  dataset_id                  = var.dataset_id
  friendly_name              = "Stock Data Dataset"
  description                = "Dataset for Japanese stock market data"
  location                   = var.location
  default_table_expiration_ms = var.table_expiration_ms

  labels = var.labels

  access {
    role          = "OWNER"
    user_by_email = var.dataset_owner_email
  }

  access {
    role         = "WRITER"
    special_group = "projectWriters"
  }
}

resource "google_bigquery_table" "daily_stock_prices" {
  dataset_id = google_bigquery_dataset.stock_data.dataset_id
  table_id   = var.table_id

  description = "Daily stock prices for Japanese market"
  labels      = var.labels

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  clustering = ["security_code"]

  schema = jsonencode([
    {
      name = "date"
      type = "DATE"
      mode = "REQUIRED"
      description = "Trading date"
    },
    {
      name = "security_code"
      type = "STRING"
      mode = "REQUIRED"
      description = "Security code"
    },
    {
      name = "security_name"
      type = "STRING"
      mode = "NULLABLE"
      description = "Security name"
    },
    {
      name = "market_code"
      type = "STRING"
      mode = "NULLABLE"
      description = "Market code"
    },
    {
      name = "open_price"
      type = "NUMERIC"
      mode = "NULLABLE"
      description = "Opening price"
    },
    {
      name = "high_price"
      type = "NUMERIC"
      mode = "NULLABLE"
      description = "Highest price"
    },
    {
      name = "low_price"
      type = "NUMERIC"
      mode = "NULLABLE"
      description = "Lowest price"
    },
    {
      name = "close_price"
      type = "NUMERIC"
      mode = "NULLABLE"
      description = "Closing price"
    },
    {
      name = "volume"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Trading volume"
    },
    {
      name = "turnover_value"
      type = "NUMERIC"
      mode = "NULLABLE"
      description = "Turnover value"
    },
    {
      name = "created_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Record creation timestamp"
    },
    {
      name = "updated_at"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Record update timestamp"
    }
  ])
}
```

#### 10.2.3. Cloud Runモジュール
```hcl
# modules/cloud_run/main.tf
resource "google_cloud_run_v2_service" "stock_data_collector" {
  name     = var.service_name
  location = var.region

  template {
    service_account = var.service_account_email
    
    containers {
      image = var.container_image
      
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset
      }

      env {
        name  = "BIGQUERY_TABLE"
        value = var.bigquery_table
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name = "JQUANTS_REFRESH_TOKEN_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.jquants_secret_id
            version = "latest"
          }
        }
      }

      ports {
        container_port = 8080
      }
    }

    timeout = "${var.timeout_seconds}s"
    
    scaling {
      max_instance_count = 1
    }
  }

  labels = var.labels
}

resource "google_cloud_run_service_iam_binding" "pubsub_invoker" {
  location = google_cloud_run_v2_service.stock_data_collector.location
  service  = google_cloud_run_v2_service.stock_data_collector.name
  role     = "roles/run.invoker"
  members  = [
    "serviceAccount:${var.pubsub_service_account_email}"
  ]
}
```

#### 10.2.4. Schedulerモジュール
```hcl
# modules/scheduler/main.tf
resource "google_pubsub_topic" "stock_data_trigger" {
  name = var.topic_name

  labels = var.labels
}

resource "google_pubsub_subscription" "stock_data_processor" {
  name  = var.subscription_name
  topic = google_pubsub_topic.stock_data_trigger.name

  ack_deadline_seconds = 600
  message_retention_duration = "604800s" # 7 days

  push_config {
    push_endpoint = var.cloud_run_endpoint
    
    oidc_token {
      service_account_email = var.pubsub_service_account_email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  labels = var.labels
}

resource "google_cloud_scheduler_job" "daily_stock_data" {
  name        = var.job_name
  description = "Daily stock data collection trigger"
  schedule    = var.schedule
  time_zone   = "Asia/Tokyo"

  pubsub_target {
    topic_name = google_pubsub_topic.stock_data_trigger.id
    data       = base64encode(jsonencode({
      trigger_type = "daily"
      date         = ""
    }))
  }

  labels = var.labels
}
```

#### 10.2.5. IAMモジュール
```hcl
# modules/iam/main.tf
resource "google_service_account" "cloud_run_sa" {
  account_id   = var.cloud_run_sa_id
  display_name = "Cloud Run Service Account for Stock Data Collector"
  description  = "Service account for Cloud Run stock data collector"
}

resource "google_service_account" "pubsub_sa" {
  account_id   = var.pubsub_sa_id
  display_name = "Pub/Sub Service Account"
  description  = "Service account for Pub/Sub to invoke Cloud Run"
}

# BigQuery permissions
resource "google_bigquery_dataset_iam_member" "cloud_run_bigquery_writer" {
  dataset_id = var.bigquery_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Secret Manager permissions
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_accessor" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run invoker permission for Pub/Sub
resource "google_project_iam_member" "pubsub_cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.pubsub_sa.email}"
}
```

### 10.3. 環境分離設計

#### 10.3.1. 開発環境
```hcl
# environments/dev/terraform.tfvars
project_id = "stock-data-dev"
region     = "asia-northeast1"
environment = "dev"

# BigQuery
bigquery_dataset_id = "stock_data_dev"
bigquery_table_id   = "daily_stock_prices"

# Cloud Run
cloud_run_service_name = "stock-data-collector-dev"
container_image = "gcr.io/stock-data-dev/stock-data-collector:latest"
cpu_limit = "1"
memory_limit = "1Gi"

# Scheduler
schedule = "30 16 * * 1-5"  # Dev: weekdays 16:30 JST

labels = {
  environment = "dev"
  project     = "stock-data-collector"
  managed_by  = "terraform"
}
```

#### 10.3.2. 本番環境
```hcl
# environments/prod/terraform.tfvars
project_id = "stock-data-prod"
region     = "asia-northeast1"
environment = "prod"

# BigQuery
bigquery_dataset_id = "stock_data"
bigquery_table_id   = "daily_stock_prices"

# Cloud Run
cloud_run_service_name = "stock-data-collector"
container_image = "gcr.io/stock-data-prod/stock-data-collector:latest"
cpu_limit = "2"
memory_limit = "2Gi"

# Scheduler
schedule = "30 16 * * 1-5"  # Prod: weekdays 16:30 JST

labels = {
  environment = "prod"
  project     = "stock-data-collector"
  managed_by  = "terraform"
}
```

### 10.4. State管理

#### 10.4.1. Backend設定
```hcl
# environments/dev/backend.tf
terraform {
  backend "gcs" {
    bucket = "terraform-state-stock-data-dev"
    prefix = "stock-data-collector/dev"
  }
}

# environments/prod/backend.tf
terraform {
  backend "gcs" {
    bucket = "terraform-state-stock-data-prod"
    prefix = "stock-data-collector/prod"
  }
}
```

### 10.5. デプロイメントスクリプト

#### 10.5.1. 初期セットアップ
```bash
#!/bin/bash
# scripts/init.sh

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${2}

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <environment> <project_id>"
  exit 1
fi

echo "Initializing Terraform for environment: $ENVIRONMENT"

# Create state bucket
gsutil mb -p $PROJECT_ID gs://terraform-state-$PROJECT_ID || true
gsutil versioning set on gs://terraform-state-$PROJECT_ID

# Enable required APIs
gcloud services enable --project=$PROJECT_ID \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com

# Initialize Terraform
cd environments/$ENVIRONMENT
terraform init
terraform plan -var="project_id=$PROJECT_ID"

echo "Terraform initialized successfully for $ENVIRONMENT environment"
```

#### 10.5.2. デプロイスクリプト
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${2}
ACTION=${3:-plan}

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <environment> <project_id> [plan|apply|destroy]"
  exit 1
fi

cd environments/$ENVIRONMENT

case $ACTION in
  plan)
    terraform plan -var="project_id=$PROJECT_ID"
    ;;
  apply)
    terraform apply -var="project_id=$PROJECT_ID" -auto-approve
    ;;
  destroy)
    terraform destroy -var="project_id=$PROJECT_ID" -auto-approve
    ;;
  *)
    echo "Invalid action: $ACTION. Use plan, apply, or destroy."
    exit 1
    ;;
esac
```

### 10.6. CI/CD統合

#### 10.6.1. Cloud Build Terraform設定
```yaml
# cloudbuild-terraform.yaml
steps:
  # Terraform validation
  - name: 'hashicorp/terraform:1.5'
    dir: 'terraform/environments/${_ENVIRONMENT}'
    entrypoint: 'sh'
    args:
    - '-c'
    - |
      terraform init
      terraform validate
      terraform plan -var="project_id=${PROJECT_ID}"

  # Terraform apply (only on main branch)
  - name: 'hashicorp/terraform:1.5'
    dir: 'terraform/environments/${_ENVIRONMENT}'
    entrypoint: 'sh'
    args:
    - '-c'
    - |
      if [ "${BRANCH_NAME}" = "main" ]; then
        terraform apply -var="project_id=${PROJECT_ID}" -auto-approve
      fi

substitutions:
  _ENVIRONMENT: 'dev'

options:
  logging: CLOUD_LOGGING_ONLY
```

## 11. セキュリティ設計

### 11.1. 認証・認可
- Cloud RunサービスアカウントによるGCPリソースアクセス
- Secret Manager読み取り権限の最小化
- BigQuery書き込み権限の限定

### 11.2. ネットワークセキュリティ
- VPC Connectorの使用（必要に応じて）
- HTTPSでの外部API通信
- プライベートGoogleアクセス

### 11.3. データ保護
- 転送中暗号化（HTTPS/TLS）
- 保存時暗号化（BigQuery標準）
- 個人情報の非保存（株価データのみ）