# Выручка в админ-API

Агрегация: `services/revenue_aggregation.py` + `MetricsService`, `UtmService`.

- Подтверждённые покупки: суммы по **RUB** и **USD** считаются **отдельно** (поля `purchase.amount` / `purchase.currency`). Конвертации нет.
- Legacy без `amount`: только в **RUB** через цену пакета.
- В дашборде и UTM **EUR в отчётах не используется** (только ₽ и $).

Подробности для фронта: репозиторий genweb, `docs/admin-revenue-api.md`.
