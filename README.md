# 日本株日次データ自動取得アプリケーション

## 概要

J-Quants APIから日本株の日次OHLCV（始値・高値・安値・終値・出来高）データを自動取得し、Google Cloud BigQueryに保存するシステムです。

## 機能

- J-Quants APIからの日次株価データ取得
- BigQueryへのデータ保存（重複排除対応）
- 営業日判定による自動スキップ
- Cloud Schedulerによる定期実行
- エラーハンドリングとリトライ機能

## アーキテクチャ

```
Cloud Scheduler → Pub/Sub → Cloud Run → BigQuery
                              ↓
                        Secret Manager
                              ↓
                         J-Quants API
```

## セットアップ

### 1. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、必要な値を設定します：

```bash
cp .env.example .env
```

### 2. 依存関係のインストール

```bash
make install
```

### 3. ローカル実行

```bash
make run
```

## 開発

### コードフォーマット

```bash
make format
```

### Linting

```bash
make lint
```

### テスト実行

```bash
make test
```

## Docker

### ビルド

```bash
make docker-build
```

### 実行

```bash
make docker-run
```

## デプロイ

Cloud Buildを使用してGoogle Cloud Runにデプロイします：

```bash
gcloud builds submit --config cloudbuild.yaml
```

## API エンドポイント

- `POST /` - Pub/Subメッセージハンドラー（本番用）
- `GET /health` - ヘルスチェック
- `POST /process` - 手動実行（開発・テスト用）

## 環境変数

- `GOOGLE_CLOUD_PROJECT` - GCPプロジェクトID
- `BIGQUERY_DATASET` - BigQueryデータセット名
- `BIGQUERY_TABLE` - BigQueryテーブル名
- `JQUANTS_BASE_URL` - J-Quants API URL
- `JQUANTS_REFRESH_TOKEN_SECRET` - Secret Manager内のリフレッシュトークン名
- `LOG_LEVEL` - ログレベル（INFO/WARNING/ERROR）

## ライセンス

MIT License