# Crocoblock Smart Ticket Classifier

**[English](#english)** · **[Українська](#українська)** · **[Русский](#русский)**

---

## English

A small Python service that reads a raw support ticket and classifies it on four axes so
it can be triaged and routed automatically:

| Axis | Values |
|------|--------|
| **category** | `bug` · `feature_request` · `how_to` |
| **priority** | `low` · `medium` · `high` · `urgent` |
| **plugin** | the primary Jet/Crocoblock plugin (JetEngine, JetFormBuilder, JetBooking, …) |
| **sentiment** | `positive` · `neutral` · `frustrated` · `angry` |

It also returns a **confidence** score and one-sentence **reasoning** for each decision.

Built on the **Google Gemini API** (free tier) using **few-shot prompting** and
**structured output** (`response_schema`), so the response is a validated, typed object —
never a raw string that has to be parsed and hope-checked.

### Why this exists

A support queue for a plugin ecosystem like Crocoblock's mixes urgent regressions
("site down after update") with simple how-to questions and feature requests. Reading and
tagging each ticket by hand is slow. This service does the first pass in ~1 second per
ticket, producing a structured label that a workflow (n8n, Zapier, a webhook) can route:
urgent bugs to on-call, how-tos to docs/self-service, feature requests to the roadmap board.

### How it works

```
ticket text
    │
    ▼
system instruction (triage rules + 3 worked examples)  +  the ticket
    │
    ▼
client.models.generate_content(response_schema=TicketClassification)   ← schema enforced
    │
    ▼
response.parsed  ->  TicketClassification  (Pydantic object, guaranteed valid enums)
```

Two techniques do the work:

- **Few-shot prompting** — three hand-labelled tickets are embedded in the system
  instruction so the model learns *our* conventions for priority and sentiment instead of
  guessing them.
- **Structured output** — the Pydantic schema in `schema.py` is passed as `response_schema`
  with `response_mime_type="application/json"`. Gemini constrains generation to the schema
  and the SDK hands back a parsed Pydantic object via `response.parsed`. The model can't
  return an invalid category or malformed JSON.

**Gemini-specific design note:** Google recommends *not* dumping example JSON that
duplicates the response schema into the prompt (it lowers output quality). So the few-shot
examples are written as compact shorthand (`ticket -> bug | urgent | JetEngine | frustrated`)
rather than full JSON objects. Still few-shot — it just anchors the decision boundaries
without repeating the schema the API already enforces.

### Project layout

```
schema.py       Pydantic models + enums (the contract)
prompts.py      system instruction + few-shot worked examples
classifier.py   classify_ticket() — the core function
main.py         CLI (single ticket / file / batch)
examples/
  tickets.json  5 real-world support tickets
```

### Setup

```bash
git clone https://github.com/igorshkov93/crocoblock-ticket-classifier
cd crocoblock-ticket-classifier

python -m venv .venv
.venv\Scripts\activate          # Windows / PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # then paste your GEMINI_API_KEY into .env
```

Get a free Gemini API key at <https://aistudio.google.com/apikey> — no credit card required.

### Usage

```bash
# Classify one ticket
python main.py "After updating JetEngine my dynamic fields are all blank and the site is live!"

# Classify a ticket stored in a file
python main.py --file ticket.txt

# Run the 5 bundled real-world examples and print a summary table
python main.py --examples
```

#### Example output

```
[TCK-1042] JetBooking allowing double bookings on the same dates
-----------------------------------------------------------------
  category   : bug
  priority   : urgent
  plugin     : JetBooking
  sentiment  : frustrated
  confidence : 0.96
  reasoning  : Overlapping reservations indicate the availability check is broken, costing live revenue.
  (gemini-2.5-flash, 910 ms, 512 in / 70 out tokens)
```

*(Exact scores and latency vary per run and model.)*

### Design decisions

- **Structured output over "parse the text".** `response_schema` guarantees a schema-valid
  object, so downstream automation can trust the fields without validation retries.
- **Enums for `plugin`.** Constraining the plugin field to the real Jet product list keeps the
  labels clean and routable, with `unknown`/`other` as safe fallbacks.
- **`temperature=0`** for deterministic triage.
- **Free tier.** Runs at zero cost on `gemini-2.5-flash`. Model is configurable via
  `GEMINI_MODEL` (`gemini-2.5-flash-lite` for higher RPM, `gemini-3.5-flash` for newer).
  Note: on the free tier Google may use prompts to improve its products — fine for a demo,
  but use a billed project for anything with customer data.

### Possible extensions

- Wire `classify_ticket()` into an **n8n / webhook** flow: HTTP node → classifier → Switch
  node that routes by `category` + `priority` (Slack for urgent bugs, Notion for feature
  requests, docs autoresponder for how-tos).
- Add a small eval set of labelled tickets and measure per-field accuracy.
- Disable "thinking" on 2.5 Flash (`thinking_config`) to shave latency/tokens for this
  simple classification task.

---

## Русский

Небольшой Python-сервис, который читает текст тикета поддержки и классифицирует его по
четырём осям, чтобы тикет можно было автоматически сортировать и маршрутизировать:

| Ось | Значения |
|-----|----------|
| **category** (категория) | `bug` · `feature_request` · `how_to` |
| **priority** (приоритет) | `low` · `medium` · `high` · `urgent` |
| **plugin** (плагин) | основной плагин Jet/Crocoblock (JetEngine, JetFormBuilder, JetBooking, …) |
| **sentiment** (тональность) | `positive` · `neutral` · `frustrated` · `angry` |

Дополнительно по каждому решению возвращаются оценка уверенности **confidence** и краткое
обоснование **reasoning** одним предложением.

Построен на **Google Gemini API** (бесплатный тариф) с использованием **few-shot
prompting** и **структурированного вывода** (`response_schema`), поэтому ответ приходит как
валидированный типизированный объект, а не как сырая строка, которую нужно парсить и на
которую остаётся только надеяться.

### Зачем это нужно

Очередь поддержки экосистемы плагинов вроде Crocoblock смешивает срочные регрессии
(«сайт лёг после обновления») с простыми how-to вопросами и фича-реквестами. Читать и
размечать каждый тикет вручную медленно. Этот сервис делает первый проход примерно за
секунду на тикет и выдаёт структурированную метку, которую воркфлоу (n8n, Zapier, вебхук)
может маршрутизировать: срочные баги — на дежурного, how-to — в документацию/самообслуживание,
фича-реквесты — на доску роадмапа.

### Как это работает

```
текст тикета
    │
    ▼
системная инструкция (правила триажа + 3 разобранных примера)  +  тикет
    │
    ▼
client.models.generate_content(response_schema=TicketClassification)   ← схема навязана
    │
    ▼
response.parsed  ->  TicketClassification  (объект Pydantic, гарантированно валидные enum)
```

Работают два приёма:

- **Few-shot prompting** — три размеченных вручную тикета встроены в системную инструкцию,
  чтобы модель усвоила *наши* конвенции по приоритету и тональности, а не угадывала их.
- **Структурированный вывод** — Pydantic-схема из `schema.py` передаётся как
  `response_schema` вместе с `response_mime_type="application/json"`. Gemini ограничивает
  генерацию этой схемой, а SDK возвращает готовый объект Pydantic через `response.parsed`.
  Модель физически не может вернуть невалидную категорию или битый JSON.

**Замечание по специфике Gemini:** Google рекомендует *не* дублировать в промпте пример
JSON, повторяющий схему ответа — это снижает качество вывода. Поэтому few-shot примеры
записаны в компактной форме (`тикет -> bug | urgent | JetEngine | frustrated`), а не как
полные JSON-объекты. Это всё ещё few-shot — просто он задаёт границы решений, не повторяя
схему, которую API и так навязывает.

### Структура проекта

```
schema.py       модели и enum'ы Pydantic (контракт)
prompts.py      системная инструкция + few-shot примеры
classifier.py   classify_ticket() — основная функция
main.py         CLI (один тикет / файл / пакетный прогон)
examples/
  tickets.json  5 реальных тикетов поддержки
```

### Установка

```bash
git clone https://github.com/igorshkov93/crocoblock-ticket-classifier
cd crocoblock-ticket-classifier

python -m venv .venv
.venv\Scripts\activate          # Windows / PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # затем вставь свой GEMINI_API_KEY в .env
```

Бесплатный ключ Gemini берётся на <https://aistudio.google.com/apikey> — карта не нужна.

### Использование

```bash
# Классифицировать один тикет
python main.py "После обновления JetEngine динамические поля пустые, а сайт живой!"

# Классифицировать тикет из файла
python main.py --file ticket.txt

# Прогнать 5 встроенных реальных примеров и вывести сводную таблицу
python main.py --examples
```

#### Пример вывода

```
[TCK-1042] JetBooking allowing double bookings on the same dates
-----------------------------------------------------------------
  category   : bug
  priority   : urgent
  plugin     : JetBooking
  sentiment  : frustrated
  confidence : 0.96
  reasoning  : Overlapping reservations indicate the availability check is broken, costing live revenue.
  (gemini-2.5-flash, 910 ms, 512 in / 70 out tokens)
```

*(Точные оценки и задержка меняются от запуска к запуску и зависят от модели.)*

### Проектные решения

- **Структурированный вывод вместо «парсить текст».** `response_schema` гарантирует
  валидный по схеме объект, поэтому автоматизация ниже по цепочке может доверять полям без
  повторных проверок.
- **Enum для `plugin`.** Ограничение поля плагина реальным списком продуктов Jet держит
  метки чистыми и маршрутизируемыми, с `unknown`/`other` как безопасными запасными вариантами.
- **`temperature=0`** для детерминированного триажа.
- **Бесплатный тариф.** Работает без затрат на `gemini-2.5-flash`. Модель настраивается через
  `GEMINI_MODEL` (`gemini-2.5-flash-lite` для более высокого RPM, `gemini-3.5-flash` для новее).
  Важно: на бесплатном тарифе Google может использовать промпты для улучшения своих продуктов —
  нормально для демо, но для данных клиентов используй billed-проект.

### Возможные расширения

- Встроить `classify_ticket()` в **n8n / webhook**-поток: HTTP-нода → классификатор → Switch-нода,
  маршрутизирующая по `category` + `priority` (Slack для срочных багов, Notion для фича-реквестов,
  автоответ из документации для how-to).
- Добавить небольшой набор размеченных тикетов для оценки и измерить точность по каждому полю.
- Отключить «thinking» у 2.5 Flash (`thinking_config`), чтобы срезать задержку/токены для этой
  простой задачи классификации.

---

## Українська

Невеликий Python-сервіс, який читає текст тікета підтримки й класифікує його за чотирма
осями, щоб тікет можна було автоматично сортувати та маршрутизувати:

| Ось | Значення |
|-----|----------|
| **category** (категорія) | `bug` · `feature_request` · `how_to` |
| **priority** (пріоритет) | `low` · `medium` · `high` · `urgent` |
| **plugin** (плагін) | основний плагін Jet/Crocoblock (JetEngine, JetFormBuilder, JetBooking, …) |
| **sentiment** (тональність) | `positive` · `neutral` · `frustrated` · `angry` |

Додатково для кожного рішення повертаються оцінка впевненості **confidence** і коротке
обґрунтування **reasoning** одним реченням.

Побудований на **Google Gemini API** (безкоштовний тариф) з використанням **few-shot
prompting** і **структурованого виводу** (`response_schema`), тож відповідь приходить як
валідований типізований об'єкт, а не як сирий рядок, який доводиться парсити й на який
лишається тільки сподіватися.

### Навіщо це потрібно

Черга підтримки екосистеми плагінів на кшталт Crocoblock змішує термінові регресії
(«сайт ліг після оновлення») з простими how-to питаннями та запитами на нові функції.
Читати й розмічати кожен тікет вручну повільно. Цей сервіс робить перший прохід приблизно
за секунду на тікет і видає структуровану мітку, яку воркфлоу (n8n, Zapier, вебхук) може
маршрутизувати: термінові баги — на чергового, how-to — у документацію/самообслуговування,
запити на функції — на дошку роадмапу.

### Як це працює

```
текст тікета
    │
    ▼
системна інструкція (правила тріажу + 3 розібрані приклади)  +  тікет
    │
    ▼
client.models.generate_content(response_schema=TicketClassification)   ← схема нав'язана
    │
    ▼
response.parsed  ->  TicketClassification  (об'єкт Pydantic, гарантовано валідні enum)
```

Працюють два прийоми:

- **Few-shot prompting** — три розмічені вручну тікети вбудовані в системну інструкцію,
  щоб модель засвоїла *наші* конвенції щодо пріоритету й тональності, а не вгадувала їх.
- **Структурований вивід** — Pydantic-схема зі `schema.py` передається як `response_schema`
  разом із `response_mime_type="application/json"`. Gemini обмежує генерацію цією схемою, а
  SDK повертає готовий об'єкт Pydantic через `response.parsed`. Модель фізично не може
  повернути невалідну категорію чи побитий JSON.

**Зауваження щодо специфіки Gemini:** Google рекомендує *не* дублювати в промпті приклад
JSON, що повторює схему відповіді — це знижує якість виводу. Тому few-shot приклади записані
в компактній формі (`тікет -> bug | urgent | JetEngine | frustrated`), а не як повні
JSON-об'єкти. Це все ще few-shot — просто він задає межі рішень, не повторюючи схему, яку
API й так нав'язує.

### Структура проєкту

```
schema.py       моделі та enum'и Pydantic (контракт)
prompts.py      системна інструкція + few-shot приклади
classifier.py   classify_ticket() — основна функція
main.py         CLI (один тікет / файл / пакетний прогін)
examples/
  tickets.json  5 реальних тікетів підтримки
```

### Встановлення

```bash
git clone https://github.com/igorshkov93/crocoblock-ticket-classifier
cd crocoblock-ticket-classifier

python -m venv .venv
.venv\Scripts\activate          # Windows / PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # потім встав свій GEMINI_API_KEY у .env
```

Безкоштовний ключ Gemini береться на <https://aistudio.google.com/apikey> — картка не потрібна.

### Використання

```bash
# Класифікувати один тікет
python main.py "Після оновлення JetEngine динамічні поля порожні, а сайт живий!"

# Класифікувати тікет із файлу
python main.py --file ticket.txt

# Прогнати 5 вбудованих реальних прикладів і вивести зведену таблицю
python main.py --examples
```

#### Приклад виводу

```
[TCK-1042] JetBooking allowing double bookings on the same dates
-----------------------------------------------------------------
  category   : bug
  priority   : urgent
  plugin     : JetBooking
  sentiment  : frustrated
  confidence : 0.96
  reasoning  : Overlapping reservations indicate the availability check is broken, costing live revenue.
  (gemini-2.5-flash, 910 ms, 512 in / 70 out tokens)
```

*(Точні оцінки й затримка змінюються від запуску до запуску та залежать від моделі.)*

### Проєктні рішення

- **Структурований вивід замість «парсити текст».** `response_schema` гарантує валідний за
  схемою об'єкт, тож автоматизація далі по ланцюжку може довіряти полям без повторних перевірок.
- **Enum для `plugin`.** Обмеження поля плагіна реальним списком продуктів Jet тримає мітки
  чистими й придатними до маршрутизації, з `unknown`/`other` як безпечними запасними варіантами.
- **`temperature=0`** для детермінованого тріажу.
- **Безкоштовний тариф.** Працює без витрат на `gemini-2.5-flash`. Модель налаштовується через
  `GEMINI_MODEL` (`gemini-2.5-flash-lite` для вищого RPM, `gemini-3.5-flash` для новішого).
  Важливо: на безкоштовному тарифі Google може використовувати промпти для покращення своїх
  продуктів — нормально для демо, але для даних клієнтів використовуй billed-проєкт.

### Можливі розширення

- Вбудувати `classify_ticket()` у **n8n / webhook**-потік: HTTP-нода → класифікатор → Switch-нода,
  що маршрутизує за `category` + `priority` (Slack для термінових багів, Notion для запитів на
  функції, автовідповідь із документації для how-to).
- Додати невеликий набір розмічених тікетів для оцінки й виміряти точність за кожним полем.
- Вимкнути «thinking» у 2.5 Flash (`thinking_config`), щоб зрізати затримку/токени для цієї
  простої задачі класифікації.
