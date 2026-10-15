# راهنمای جامع کاربر — clean-architecture

> این راهنما برای **کاربر تازه‌کار** نوشته شده: کسی که تازه با این پروژه آشنا شده و
> می‌خواهد قدم‌به‌قدم یاد بگیرد چطور آن را بالا بیاورد، با کامندهای ترمینال کار کند،
> و از ایجنت‌ها و کامندهای opencode استفاده کند. هیچ پیش‌فرضی دربارهٔ دانسته‌های قبلی
> تو (جز آشنایی اولیه با ترمینال لینوکس و پایتون) وجود ندارد.

**قراردادهای این راهنما:**

- متن `monospace` یعنی چیزی که دقیقاً تایپ یا خوانده می‌شود (کامند، فایل، کلید).
- همهٔ کامندها را از **ریشهٔ پروژه** (جایی که `pyproject.toml` هست) اجرا کن.
- خروجی‌های نمونه، خروجی واقعی همین پروژه‌اند.

## فهرست

- [۱. پروژه در یک نگاه](#۱-پروژه-در-یک-نگاه)
- [۲. پیش‌نیازها](#۲-پیشنیازها)
- [۳. راه‌اندازی قدم‌به‌قدم (اولین بار)](#۳-راهاندازی-قدمبهقدم-اولین-بار)
- [۴. کامندهای ترمینال — Makefile](#۴-کامندهای-ترمینال--makefile)
- [۵. اسکریپت‌ها و همهٔ فلگ‌هایشان](#۵-اسکریپتها-و-همهٔ-فلگهایشان)
- [۶. CLI یکپارچهٔ fastddd](#۶-cli-یکپارچهٔ-fastddd)
- [۷. کار با opencode (ایجنت‌ها و کامندها)](#۷-کار-با-opencode-ایجنتها-و-کامندها)
- [۸. دستورالعمل‌های قدم‌به‌قدم رایج](#۸-دستورالعملهای-قدمبهقدم-رایج)
- [۹. نقشهٔ پروژه: هر چیز کجاست](#۹-نقشهٔ-پروژه-هر-چیز-کجاست)
- [۱۰. عیب‌یابی](#۱۰-عیبیابی)
- [۱۱. واژه‌نامه](#۱۱-واژهنامه)

---

## ۱. پروژه در یک نگاه

این پروژه دو چهره دارد که هردو را همین‌جا یاد می‌گیری:

1. **یک وب‌اپلیکیشن واقعی** با FastAPI: ورود/خروج کاربر، نقش‌ها (`admin/manager/user`)،
   کلید API، اعلان‌ها، WebSocket، کش Redis و دیتابیس PostgreSQL — همه روی معماری تمیز
   چهارلایه (`domain → application → infrastructure → presentation`).
2. **یک جعبه‌ابزار** که خودش را می‌سازد و نگه می‌دارد: اسکریپت‌های راه‌اندازی،
   دستور `fastddd`، و بستهٔ اسکیل/ایجنت/کامند برای opencode.

دو جملهٔ کلیدی که همه‌جا به کارت می‌آید:

- **هر ماژول = یک پوشه** زیر `app/modules/<نام>/` با چهار زیرپوشهٔ `domain`،
  `application`، `infrastructure` و `presentation`.
- **قانون طلایی:** منطق کسب‌وکار فقط در use case؛ همه‌چیز idempotent (اجرای دوباره،
  اثر دوباره ندارد).

---

## ۲. پیش‌نیازها

| ابزار | نسخه | نصب / بررسی |
|---|---|---|
| Python | 3.14+ | `python3 --version` (پین‌شده در `.python-version`) |
| [uv](https://docs.astral.sh/uv/) | آخرین | `curl -LsSf astral.sh/uv/install.sh \| sh` سپس `uv --version` |
| PostgreSQL | 17 (یا Docker) | `psql --version` — یا فقط Docker داشته باش |
| Redis | 8 (یا Docker) | `redis-cli --version` — یا فقط Docker داشته باش |
| Docker + Compose | اختیاری | فقط اگر می‌خواهی دیتابیس/کش را با Docker بالا بیاوری: `docker ps` |
| opencode | اختیاری | فقط برای ایجنت‌ها (بخش ۷) |

> Docker **اجباری نیست**. اگر PostgreSQL و Redis را native روی سیستم داری کافی است.
> اسکریپت‌ها خودشان تشخیص می‌دهند چه چیزی در دسترس است.

بررسی سریع پیش‌نیازها:

```bash
python3 --version   # باید 3.14.x باشد
uv --version        # باید نسخه چاپ کند
```

---

## ۳. راه‌اندازی قدم‌به‌قدم (اولین بار)

### گام ۰ — کلون

```bash
git clone https://github.com/Elmino-19/clean-architecture.git my-project
cd my-project
```

### گام ۱ — تغییر نام (اختیاری ولی توصیه‌شده)

نام template در چند جا hardcode شده (نام پکیج، پیشوند جدول‌ها، عنوان OpenAPI، اطلاعات
تماس). اول ببین چه چیزی عوض می‌شود، بعد اعمال کن:

```bash
# فقط نمایش، بدون نوشتن
uv run python scripts/rebrand.py "Acme CRM" --dry-run

# اعمال واقعی
make rebrand name="Acme CRM" author="Your Name" email="you@acme.io"
```

> `rebrand.py` به‌عمد `README.md` را دست نمی‌زند (مستندات معماری را می‌خواهی نگه داری).
> اگر می‌خواهی markdownها هم بازنویسی شوند `--docs` را اضافه کن. جزئیات همهٔ فلگ‌ها در
> بخش ۵ آمده.

### گام ۲ — نصب وابستگی‌ها

```bash
uv sync
```

این کار یک virtualenv به نام `.venv` می‌سازد و همهٔ وابستگی‌ها را نصب می‌کند. از این
به بعد هر کامند پایتونی را با `uv run ...` اجرا کن تا از همین محیط استفاده شود.
(هیچ‌وقت لازم نیست `.venv` را دستی `activate` کنی.)

### گام ۳ — نصب کامل با ویزارد

```bash
make install
```

چند سؤال ساده می‌پرسد (نام پروژه، مشخصات دیتابیس، ایمیل/پسورد ادمین — بقیه با Enter
قبول می‌شوند)، بعد ۵ گام را پشت سر هم انجام می‌دهد:

| گام | چه می‌کند |
|---|---|
| ۱. opencode | `opencode.jsonc` را می‌سازد/اعتبارسنجی می‌کند |
| ۲. `.env` | هر ۸۳ کلید را می‌نویسد (secret تصادفی + مقادیر مشتق از نام پروژه) |
| ۳. توکن‌ها | جفت‌کلیدهای JWT (Ed25519 + X25519) در `secrets/keys/` |
| ۴. دیتابیس | ساخت role + database، اجرای مهاجرت، ساخت کاربر ادمین |
| ۵. جمع‌بندی | چاپ اطلاعات ورود و گام‌های بعدی |

> اگر `sudo` برای ساخت role رمز بخواهد و ترمینال تعاملی نباشد، اسکریپت متوقف
> نمی‌شود؛ دستورهای آمادهٔ کپی را چاپ می‌کند و بقیهٔ گام‌ها را ادامه می‌دهد. آن
> دستورها را در یک ترمینال تعاملی اجرا کن و دوباره `make provision` بزن.

حالت بدون سؤال (برای CI یا اسکریپت):

```bash
make install-yes p="Acme CRM"
```

### گام ۴ — اجرا و اولین ورود

```bash
make dev
```

بعد این آدرس‌ها را باز کن:

| سرویس | آدرس |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health/ |

ورود ادمین همان ایمیل/پسوردی است که در ویزارد دادی. ورود **form-encoded** است نه JSON:

```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$SECURITY_ADMIN_EMAIL&password=$SECURITY_ADMIN_PASSWORD" \
  -c cookies.txt

curl http://localhost:8000/api/v1/user/me/ -b cookies.txt
```

### بعد از هر تغییر کد

```bash
make test        # اجرای تست‌ها — باید سبز بماند
make lint        # بررسی کیفیت کد (Ruff)
make format      # فرمت خودکار (Ruff)
```

---

## ۴. کامندهای ترمینال — Makefile

`make <نام>` فقط یک میان‌بر خوانا برای یک دستور طولانی است. با `make help` فهرست کامل
را ببین (۲۹ تارگت). جدول زیر هر تارگت را با **دستور معادل** و **موقع استفاده** نشان
می‌دهد:

### راه‌اندازی اولیه

| کامند | دستور معادل | کی استفاده کن |
|---|---|---|
| `make install` | `uv run python scripts/install.py` | اولین بار؛ ویزارد کامل |
| `make install-yes p="..."` | `.../install.py --yes --project "$(p)"` | نصب بدون سؤال (CI) |
| `make opencode` | `.../opencode_setup.py --global` | نصب سراسری اسکیل/کامندهای opencode |
| `make setup` | `.../setup_env.py` | فقط ساخت `.env` |
| `make setup-yes p="..."` | `.../setup_env.py --yes --project "$(p)"` | ساخت `.env` بدون سؤال |
| `make env-check` | `.../setup_env.py --check` | بررسی کامل‌بودن `.env` (کد خروج ۱ اگر کلیدی خالی باشد) |
| `make provision` | `.../provision.py` | ساخت role/database، مهاجرت، ادمین، چک Redis |
| `make provision-check` | `.../provision.py --check` | فقط گزارش وضعیت، بدون ساختن چیزی |
| `make bootstrap` | `setup` سپس `provision` | مثل `install` ولی بدون گام opencode |
| `make rebrand name=... author=... email=...` | `.../rebrand.py "$(name)" --author ... --email ...` | تغییر نام پروژه |
| `make doctor` | `.../doctor.py` | گزارش سلامت کامل، فقط-خواندنی |

### اجرا و دیتابیس و Docker

| کامند | دستور معادل | کی استفاده کن |
|---|---|---|
| `make dev` | `uv run uvicorn app.app:app --reload` | اجرای محلی با reload خودکار |
| `make migrate` | `uv run alembic upgrade head` | اعمال مهاجرت‌ها تا head |
| `make migration m="create_x"` | `uv run alembic revision --autogenerate -m "$(m)"` | ساخت مهاجرت جدید |
| `make start` / `make start-silent` | `docker compose up -d --build ...` | بالا آوردن کل استک (+دنبال‌کردن لاگ / detached) |
| `make stop` | `docker compose down` | توقف استک |
| `make delete` | `docker compose down -v` | توقف **و حذف volumeها** (داده‌ها پاک می‌شوند!) |
| `make dependencies-up[-silent]` | `docker compose up -d ... database database-admin cache cache-admin` | فقط Postgres/pgAdmin/Redis/RedisInsight |
| `make dependencies-down` | `docker compose down` | توقف وابستگی‌ها |
| `make logs` | `docker compose logs -f` | دنبال‌کردن لاگ |
| `make view-processes` | `docker ps -a` | دیدن کانتینرها |

### کیفیت و تست

| کامند | دستور معادل | کی استفاده کن |
|---|---|---|
| `make test` | `uv run pytest` | اجرای کل تست‌ها |
| `make test-watch` | `uv run pytest -f -q` | ⚠️ **فعلاً خراب است** — به پلاگین `pytest-watch` نیاز دارد که نصب نیست (`unrecognized arguments: -f`). تا نصب نشده از `make test` استفاده کن |
| `make lint` | `uv run ruff check .` | بررسی کیفیت کد |
| `make format` | `uv run ruff format .` | فرمت خودکار |

---

## ۵. اسکریپت‌ها و همهٔ فلگ‌هایشان

همه زیر `scripts/` هستند و هم با `make` و هم مستقیم (`uv run python scripts/<name>.py
...`) اجرا می‌شوند. فلگ‌های زیر عین خروجی `--help` هر اسکریپت‌اند.

### `install.py` — نصب‌کنندهٔ یکپارچه

```
--project, --db-name, --db-user, --db-password, --db-host, --db-port
--admin-name, --admin-email, --admin-password
--environment {development,homolog,production}
--yes            همهٔ پیش‌فرض‌ها، بدون هیچ سؤالی
--global-assets  کپی اسکیل/کامندها در ~/.config/opencode
--force          چرخاندن secretها
--skip-opencode  رد کردن گام opencode
--skip-database  فقط .env و توکن‌ها؛ دست به Postgres نزن
```

مثال‌ها:

```bash
uv run python scripts/install.py --yes --project "Acme CRM"
uv run python scripts/install.py --skip-database --global-assets
```

### `setup_env.py` — سازندهٔ خودکار `.env`

مسئله‌اش این است: `.env.example` حدود ۸۳ کلیدِ خالی دارد. این اسکریپت در سه لایه پرشان
می‌کند: **تولیدی** (مثل `REDIS_PASSWORD` → تصادفی امن)، **مشتق‌شده** (مثل
`APPLICATION_TABLE_PREFIX` → از نام پروژه)، **حفظ‌شده** (مقدار موجود دست نمی‌خورد).
Idempotent است و اگر پورت ۸۰۰۰/۵۴۳۲/۶۳۷۹ اشغال باشد خودش پورت آزاد بعدی را برمی‌دارد.

```
--project, --title (بازنویسی APPLICATION_TITLE), --host (پیش‌فرض localhost)
--environment {development,homolog,production}
--cookie-samesite {lax,strict,none}
--admin-email, --admin-password, --contact-phone
--db-name, --db-user, --db-password, --db-host, --db-port
--yes, --force, --check (فقط گزارش کمبودها)
```

### `provision.py` — دیتابیس، ادمین، مهاجرت

به ترتیب `role + database → migrations → admin user` (و چک Redis). هر گام idempotent.

```
--skip-redis, --skip-migrations, --skip-admin
--admin-name "Sara Ahmadi"
--check   فقط گزارش وضعیت، بدون ساختن چیزی
```

### `doctor.py` — پزشک پروژه (فقط-خواندنی)

هیچ فلگی ندارد؛ فقط اجرا کن:

```bash
make doctor
```

خروجی واقعی‌اش شبیه این است (بخش‌بخش، با `[ok]` یا `[FAIL]`):

```text
=== Environment ===
  .env looks complete: 83 keys.
=== Services ===
  [ok]   postgres  reachable at localhost:5433
  [ok]   redis     reachable at localhost:6379
=== JWT keys ===
  [ok]   signing private      signing-private.pem
  ...
```

کد خروج ۱ اگر هر بررسی شکست بخورد — برای CI مناسب است.

### `rebrand.py` — تغییر نام template

```
project (positional, مثل 'Acme CRM')
--author, --email, --url
--docs      README و markdownها را هم بازنویسی کن
--dry-run   فقط نمایش، بدون نوشتن
```

> پیش‌فرض `README.md` را دست نمی‌زند.

### `opencode_setup.py` — کانفیگ opencode

```
--global   کپی skills/commands به ~/.config/opencode
--no-fix   به‌جای تعمیر opencode.jsonc خراب، فقط گزارش بده
```

### بقیهٔ اسکریپت‌ها

| اسکریپت | اجرا | خروجی |
|---|---|---|
| `create_module.py` | `uv run python scripts/create_module.py [billing]` | اسکلت چهارلایهٔ ماژول + پوشهٔ تست (بدون آرگومان، نام را می‌پرسد) |
| `generate_secret.py` | `uv run python scripts/generate_secret.py` | یک secret هگز ۳۲ بایتی |
| `generate_fernet.py` | `uv run python scripts/generate_fernet.py` | یک کلید Fernet |
| `directory_tree.py` | `uv run python scripts/directory_tree.py` | درخت پروژه در `scripts/directory_tree.txt` |

---

## ۶. CLI یکپارچهٔ `fastddd`

`fastddd` همان اسکریپت‌های بالا را در یک دستور جمع کرده. چهار راه اجرا:

```bash
uv run fastddd <command> [options]   # داخل همین پروژه (توسعه)
pip install .                        # نصب با pip از روی همین پوشه
uv tool install .                    # نصب سراسری با uv از روی همین پوشه
fastddd <command>                    # بعد از نصب، در هر پروژه‌ای
python -m fastddd <command>          # راه جایگزین
```

`fastddd` روی PyPI هم قابل انتشار است؛ بعد از انتشار با `pip install clean-architecture`
یا `uv tool install clean-architecture` نصب می‌شود. برای نصب ویرایشی (توسعهٔ خودِ CLI)
`pip install -e .` بزن.

فهرست دستورها (`fastddd --help`):

| دستور | معادل | توضیح |
|---|---|---|
| `install` | `install.py` | ویزارد سرتاسری |
| `opencode` | `opencode_setup.py` | اسکیل‌ها و کانفیگ opencode |
| `setup` | `setup_env.py` | ساخت `.env` |
| `db` | `provision.py` | role/database، مهاجرت، ادمین |
| `doctor` | `doctor.py` | بررسی سلامت |
| `rebrand` | `rebrand.py` | تغییر نام |
| `new-module` | `create_module.py` | اسکلت ماژول جدید |
| `tree` | `directory_tree.py` | درخت پروژه |
| `secret` / `fernet` | `generate_secret.py` / `generate_fernet.py` | تولید secret/کلید |
| `list`, `version`, `--help` | — | فهرست و نسخه |

دو نکتهٔ مهم که باید بدانی:

1. **ریشهٔ پروژه را خودش پیدا می‌کند:** از دایرکتوری فعلی به بالا می‌گردد تا
   `pyproject.toml` را پیدا کند. اگر خواستی دستی بده:
   `FASTDDD_PROJECT_ROOT=/path/to/project fastddd doctor`.
2. **دستورهای سبک و سنگین فرق دارند:** دستورهایی که کد خود پروژه را import می‌کنند
   (`install`, `db`, `doctor`) از طریق `uv run` اجرا می‌شوند تا از وابستگی‌های خود
   پروژه استفاده شود؛ بقیه با interpreter خودِ تول اجرا می‌شوند. اگر جایی `.opencode/`
   نبود، دارایی‌های opencodeِ داخل خودِ پکیج استفاده می‌شود (`FASTDDD_OPENCODE_DIR`).

مثال واقعی (ساخت ماژول `billing` در یک پروژهٔ دیگر):

```bash
cd /tmp/opencode/proj2
fastddd new-module billing
# Module 'billing' created at /tmp/opencode/proj2/app/modules/billing
# Test folder created at /tmp/opencode/proj2/test/modules/billing
```

---

## ۷. کار با opencode (ایجنت‌ها و کامندها)

### opencode چیست؟

opencode یک **ایجنت برنامه‌نویسی داخل ترمینال** است: در ریشهٔ پروژه اجرایش می‌کنی، به
او به زبان ساده می‌گویی چه می‌خواهی، و او فایل‌ها را می‌خواند/می‌سازد/ویرایش می‌کند.
این پروژه برای او یک بستهٔ آماده دارد تا «قواعد خانه» را بلد باشد.

پیش‌نیاز: opencode نصب‌شده باشد و فایل `opencode.jsonc` معتبر در ریشهٔ پروژه باشد
(`make opencode` آن را می‌سازد/تعمیر می‌کند و اتصال CodeGraph را فعال می‌کند).

```bash
cd /path/to/project
opencode
```

### سه مفهوم: skill، agent، command

| مفهوم | به زبان ساده | مثال |
|---|---|---|
| **Skill** | کتاب قانونِ یک کار؛ خودش اجرا نمی‌شود، ولی ایجنت‌ها آن را می‌خوانند | `backend-development` (قواعد لایه‌ها)، `software-design-document` (قواعد سند طراحی) |
| **Agent** | یک نقش تخصصی با دسترسی و سقف قدم مشخص | `backend-developer` (کدنویس)، `code-auditor` (بازبین فقط-خواندنی) |
| **Command** | میان‌بر `/...` که یک ایجنت را در یک **دامنهٔ مشخص** صدا می‌زند | `/audit-module knowledge`، `/develop-module billing` |

فایل‌ها این‌جاهستند: اسکیل‌ها در `.opencode/skills/*/`، ایجنت‌ها در
`.opencode/agent/`، کامندها در `.opencode/command/`.

### ایجنت‌ها — هرکدام چه کاره‌اند

| ایجنت | نقش | دسترسی | سقف قدم |
|---|---|---|---|
| `backend-developer` | پیاده‌سازی کد (ماژول، use case، repository، router، تست) | ویرایش آزاد | ۴۰ |
| `code-auditor` | بازبینی کد در برابر قوانین؛ فقط **گزارش** می‌دهد، درست نمی‌کند | فقط-خواندنی | ۲۰ |
| `code-explorer` | کاوش و توضیح کد (معماری، جریان، «کجاست؟»، blast radius) | فقط-خواندنی | ۱۲ |
| `sdd-writer` | نوشتن سند طراحی `docs/sdd.md`؛ هرگز کد تولید نمی‌کند | ویرایش آزاد | ۲۵ |

### کامندها — هرکدام چه کاره‌اند (۱۶ عدد)

الگو ثابت است: `/<کار>-<دامنه> <آرگومان>`. اگر آرگومان ندهی، خودش می‌پرسد.

| خانواده | ایجنت | فایل | ماژول | لایه (همهٔ ماژول‌ها) | همهٔ ماژول‌ها |
|---|---|---|---|---|---|
| `audit-*` | code-auditor | `/audit-file app/modules/key/domain/entities.py` | `/audit-module knowledge` | `/audit-layer domain` | `/audit-all` |
| `explore-*` | code-explorer | `/explore-file app/core/security.py` | `/explore-module key` | `/explore-layer infrastructure` | `/explore-all` |
| `develop-*` | backend-developer | `/develop-file app/modules/key/domain/entities.py` | `/develop-module billing` | `/develop-layer application` | `/develop-all` |
| `design-*` | sdd-writer | `/design-file rate-limiting` | `/design-module billing` | `/design-layer caching` | `/design-all` |

مقدار مجاز `<layer>`: `domain` \| `application` \| `infrastructure` \| `presentation`.

### سه قانونی که باید بدانی

1. **subtask یعنی چه:** کامندهای `audit-*` و `explore-*` در یک نشست جدا اجرا می‌شوند و
   فقط خلاصه برمی‌گردد تا کانتکست اصلی شلوغ نشود. `develop-*` و `design-*` در همان
   نشست می‌مانند تا تعاملی باشی.
2. **سقف قدم (step budget):** هر ایجنت سقف مشخصی دارد. اگر کار بزرگ‌تر باشد، وسط راه
   می‌ایستد، گزارش می‌دهد و می‌پرسد «continue؟» — با تأیید تو ادامه می‌دهد.
3. **بعد از تغییر بسته، restart:** اگر `.opencode/` یا `opencode.jsonc` را عوض کردی،
   opencode را quit و restart کن؛ نشستِ در حال اجرا کانفیگ قبلی را نگه می‌دارد.

> قرارداد CodeGraph: اولین ابزار ایجنت باید `codegraph_explore` باشد و `grep` ممنوع
> است. لازم نیست حفظش کنی؛ فقط بدان اگر ایجنت گفت «ابزار در دسترس نیست»، مشکل از
> MCP/ایندکس است، نه از تو.

### پروژه‌ای در برابر سراسری (project vs global)

- **پروژه‌ای (خودکار):** هرچه در `.opencode/` است وقتی همین پروژه دایرکتوری کاری است،
  خودکار لود می‌شود. چیزی نصب لازم نیست.
- **سراسری:** `make opencode` همان دارایی‌ها را در `~/.config/opencode/` کپی می‌کند تا
  در همهٔ پروژه‌های روی سیستم در دسترس باشند. (بعدش restart لازم است.)

### یک مکالمهٔ نمونهٔ کامل

```text
تو:  /explore-module key
ایجنت: (نقشهٔ چهار لایه، پورت‌ها، جریان router تا database، وابستگی‌ها — با file:line)

تو:  /audit-module key
ایجنت: (جدول یافته‌ها با Severity + verdict: Pass / Needs work / Fail)

تو:  /develop-module billing
ایجنت: (scaffold، چهار لایه، migration، ثبت router، تست، و در پایان make test و make lint تا سبز)
```

---

## ۸. دستورالعمل‌های قدم‌به‌قدم رایج

### R1 — ساخت یک ماژول جدید از صفر تا تست سبز

```bash
# ۱. اسکلت
uv run python scripts/create_module.py billing     # یا: fastddd new-module billing

# ۲. لایه‌ها را به ترتیب بنویس (یا به ایجنت بسپار):
#    domain → application → infrastructure → presentation
#    راهنمای هر فایل: .opencode/skills/backend-development/references/layers.md

# ۳. ثبت مدل و ساخت مهاجرت
#    (مدل را در migrations/env.py به لیست _ = [...] اضافه کن)
make migration m="create_billing"
make migrate

# ۴. ثبت router در app/app.py (هر دو شکل با/بدون اسلش پایانی)

# ۵. تست با fake در test/fakes.py، بعد:
make test && make lint
```

میان‌بر با ایجنت: `/develop-module billing` همین ۵ قدم را برایت انجام می‌دهد.

### R2 — افزودن یک endpoint به ماژول موجود

1. اسکیما در `presentation/schemas.py`، مستندات در `presentation/docs.py`.
2. mapper در `application/mappers.py`، متد use case در `application/use_cases.py`
   (منطق کسب‌وکار **فقط** این‌جا).
3. هندلر در `presentation/routers.py` با بدنهٔ ثابت `payload → mapper → use case →
   mapper → return` و **هر دو شکل مسیر** (`@router.post("/")` + `@router.post("")`).
4. تست + `make test && make lint`.

### R3 — ساخت migration برای مدل جدید

```bash
# مدل را در migrations/env.py ثبت کن، بعد:
make migration m="create_my_entity_model"
make migrate
```

> ⚠️ autogenerate فقط مدل‌های ثبت‌شده را می‌بیند؛ برای جدول ثبت‌نشده `drop_table`
> صادر می‌کند. همیشه `migrations/env.py` را چک کن.

### R4 — دیباگ «در Swagger کار می‌کند، از کلاینت 403 می‌دهد»

علت شایع: فقط شکل اسلش‌دار مسیر ثبت شده. هر دو شکل را ثبت کن:

```python
@router.post("/", **create_docs)
@router.post("", include_in_schema=False)
```

و مسیر را در پایین‌ترین tier مجاز در تنظیمات `SECURITY_*_ALLOWED_PATHS` هم ثبت کن.

### R5 — چرخاندن secretها

```bash
uv run python scripts/setup_env.py --force   # همهٔ secretهای تولیدی می‌چرخند
make provision                               # اگر مربوط به دیتابیس/ادمین است
```

### R6 — شروع کاملاً تازه (ریست محیط)

```bash
make delete            # ⚠️ توقف + حذف volumeهای Docker (داده‌ها می‌روند)
make install           # از نو: .env، کلیدها، دیتابیس، ادمین
```

### R7 — «چیزی کار نمی‌کند، از کجا شروع کنم؟»

```bash
make doctor            # فقط-خواندنی؛ دقیقاً می‌گوید کجا خراب است
make env-check         # فقط .env
make provision-check   # فقط role/database
```

---

## ۹. نقشهٔ پروژه: هر چیز کجاست

```text
.
├── app/
│   ├── app.py            نقطهٔ ورود FastAPI + ثبت routerها
│   ├── core/             settings، security، database، cache، middleware، logging
│   └── modules/
│       ├── shared/       تایپ‌های پایه (بدون route): BaseEntity، UNSET، ResponseMessages...
│       ├── authentication/ user/ key/ knowledge/ notification/ websocket/ health/ example/
├── migrations/           Alembic (اولین مهاجرت کل اسکیما را می‌سازد)
├── scripts/              همهٔ اسکریپت‌های بخش ۵
├── fastddd/              CLI یکپارچه (بخش ۶)
├── test/                 تست‌ها + fakes.py (آینهٔ app/modules)
├── docs/                 همین راهنما + کالکشن Postman
├── .opencode/           skills / agent / command (بخش ۷)
├── .me/                  کپی فارسی شخصی (commit نمی‌شود)
├── Makefile              همهٔ کامندهای بخش ۴
├── pyproject.toml        وابستگی‌ها + کانفیگ pytest/ruff
├── docker-compose.yaml   Postgres + Redis + pgAdmin + RedisInsight (+ api)
├── opencode.jsonc        کانفیگ opencode (اتصال CodeGraph)
└── .env / .env.example   تنظیمات واقعی / قالب (`.env` commit نمی‌شود)
```

مرجع طلایی کد: `app/modules/key/` (تنها ماژولی که همهٔ لایه‌ها را تمرین می‌کند) و برای
CRUD ساده، `knowledge`.

---

## ۱۰. عیب‌یابی

| علامت | علت محتمل | راه‌حل |
|---|---|---|
| `sudo needs a password` در provision | ساخت role/database به superuser نیاز دارد | دستورهای چاپ‌شده را در ترمینال تعاملی اجرا کن، بعد `make provision` |
| `ValidationError` با نام کلید در استارت | آن کلید در `.env` خالی است | `make doctor` بزن؛ بعد `make setup` |
| 403 از کلاینت ولی 200 در Swagger | شکل بدون اسلش ثبت نشده | R4 |
| `greenlet` missing | حذف دستی وابستگی | `uv sync` |
| دادهٔ قدیمی از کش | فرمت payload عوض شده | `REDIS_CACHE_VERSION` را bump کن (نه flush) |
| پورت اشغال است | ۸۰۰۰/۵۴۳۲/۶۳۷۹ پر است | `setup_env` خودش پورت آزاد برمی‌دارد؛ یا دستی عوض کن و `make provision` |
| کلیدهای JWT نیست | اولین بوت | خودکار ساخته می‌شوند (`JWT_AUTO_GENERATE_KEYS`)؛ با `make doctor` چک کن |
| `make test-watch` خطای `unrecognized arguments: -f` | پلاگین `pytest-watch` نصب نیست | فعلاً فقط `make test`؛ یا `uv add --dev pytest-watch` |
| ایجنت می‌گوید ابزار CodeGraph نیست | MCP قطع یا `.codegraph/` نیست | یک خط گزارش بده و ادامه نده با grep (طبق قرارداد محیط) |
| کامند opencode اثر نکرد | نشست قدیمی | quit + restartِ opencode |

---

## ۱۱. واژه‌نامه

| واژه | یعنی چه |
|---|---|
| ماژول (module) | یک پوشه زیر `app/modules/` = یک bounded context (مثل `key`) |
| لایه (layer) | یکی از `domain/application/infrastructure/presentation`؛ وابستگی فقط به داخل |
| Use case | کلاس `{Module}UseCases`؛ تنها جای مجاز منطق کسب‌وکار |
| Port / Adapter | قرارداد (`typing.Protocol` در `interfaces.py`) / پیاده‌سازی (`Postgres*`، `Redis*`) |
| Mapper | تابع مرزی `application/mappers.py` که بین schema/entity/model تبدیل می‌کند |
| SDD | سند طراحی نرم‌افزار (`docs/sdd.md`)؛ خروجی ایجنت `sdd-writer` |
| Subtask | اجرای ایزولهٔ کامندهای `audit-*`/`explore-*` با برگرداندن خلاصه |
| Step budget | سقف قدم هر ایجنت (۴۰/۲۰/۱۲/۲۵)؛ تهش می‌پرسد «continue؟» |
| Idempotent | اجرای دوباره اثر دوباره ندارد (همهٔ اسکریپت‌های راه‌اندازی) |
| Slug | نام کوچک خط‌تیره‌ای/زیرخطی پروژه که در نام جدول‌ها و کلیدها می‌نشیند |
| Soft delete | حذف منطقی با `is_active=false`؛ هرگز `DELETE` فیزیکی |
| UNSET | نگهبان «فیلد نفرستاده» در برابر «صریحاً null»؛ همیشه با `is` مقایسه کن |
| Envelope | پوشش استاندارد پاسخ (`StandardResponse`) که middleware می‌سازد، نه هندلر |
| DAG | گراف بدون چرخهٔ وابستگی بین ماژول‌ها |

---

*سند زنده است: اگر کامند یا رفتاری عوض شد و این راهنما عقب ماند، اول همین فایل را
به‌روز کن. نسخهٔ انگلیسی راهنمای اصلی در `README.md` است.*
