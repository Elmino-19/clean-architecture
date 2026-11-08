# راهنمای استفاده از بستهٔ OpenCode V2

> این راهنما مخصوص **بستهٔ `.opencode/` همین پروژه** است و با ساختار بومی
> **OpenCode V2** (نسخهٔ `2.2.x`) نوشته شده. هدفش این است که دقیقاً بدانی چه
> چیزی نصب می‌شود، چه کامندهایی وجود دارد، هر ایجنت چه اختیاری دارد، و چطور
> بدون آزمون‌وخطا از آن استفاده کنی.

---

## ۱. این بسته چه چیزهایی دارد؟

| نوع | مسیر پروژه | مسیر سراسری | تعداد |
|---|---|---|---|
| Skill | `.opencode/skills/<name>/SKILL.md` | `~/.config/opencode/skills/<name>/` | ۲ |
| Agent | `.opencode/agents/<name>.md` | `~/.config/opencode/agents/<name>.md` | ۷ |
| Command | `.opencode/commands/<name>.md` | `~/.config/opencode/commands/<name>.md` | ۸ |
| Config | `opencode.jsonc` | `~/.config/opencode/opencode.jsonc` | ۱ |

اسکیل‌ها:

| اسکیل | کاربرد |
|---|---|
| `backend-development` | قواعد پیاده‌سازی: چهار لایه، خطاها، تراکنش، نام‌گذاری |
| `software-design-document` | قواعد نوشتن سند طراحی `docs/sdd.md` |

ایجنت‌ها (۵ کارگر + منشی + نویسندهٔ سند):

`orchestrator` · `analyzer` · `planner` · `coder` · `editor` · `reviewer` · `sdd-writer`

کامندها (۸ عدد):

`/go` · `/scan` · `/explore` · `/plan` · `/craft` · `/mend` · `/review` · `/design`

---

## ۲. نصب و همگام‌سازی

### حالت پروژه‌ای (پیش‌فرض)

وقتی پوشهٔ کاری ترمینال ریشهٔ همین پروژه باشد، OpenCode خودش `.opencode/` را
می‌خواند. هیچ نصب اضافه‌ای لازم نیست:

```bash
cd /path/to/clean-architecture
opencode
```

### حالت سراسری (همهٔ پروژه‌های سیستم)

```bash
make opencode
# معادل:
uv run python scripts/opencode_setup.py --global
```

این دستور سه پوشه را در `~/.config/opencode/` می‌سازد/به‌روز می‌کند:

```text
~/.config/opencode/
├── skills/backend-development/
├── skills/software-design-document/
├── agents/*.md          (۷ فایل)
├── commands/*.md        (۸ فایل)
└── opencode.jsonc
```

> ترتیب اولویت: نسخهٔ پروژه بر نسخهٔ سراسری مقدم است. اگر هم در ریپو و هم در
> `~/.config/opencode/` کامند هم‌نام باشد، نسخهٔ `.opencode/commands/` اجرا می‌شود.

### بررسی سلامت نصب

```bash
# اعتبارسنجی کانفیگ (بدون تغییر)
uv run python scripts/opencode_setup.py

# آنچه OpenCode واقعاً بارگذاری کرده
opencode debug config
opencode debug agents | jq 'length'     # باید ۱۴ باشد: ۷ پروژه + ۷ built-in
```

---

## ۳. سه مفهوم پایه

| مفهوم | خودش اجرا می‌شود؟ | چه کسی صدا می‌زند؟ | مثال |
|---|---|---|---|
| **Skill** | نه | ایجنت با ابزار `skill` | `backend-development` |
| **Agent** | بله، به‌عنوان یک نقش | کاربر یا ابزار `subagent` | `coder` |
| **Command** | بله | کاربر با `/...` | `/craft --modules billing` |

### تفاوت `subtask` و `subagent`

در V1 فیلد `subtask: true` بود؛ در V2 نامش **`subagent`** است. هر ۸ کامند این
پروژه `subagent: true` دارند، یعنی در یک **نشست فرزند** اجرا می‌شوند و فقط خلاصه
به نشست اصلی برمی‌گردد. `subtask` هنوز به‌عنوان alias پذیرفته می‌شود، ولی در این
بسته استفاده نمی‌شود.

چون `orchestrator` خودش `mode: subagent` است و کارگرها را با ابزار `subagent`
صدا می‌زند، در `opencode.jsonc` این تنظیم لازم است:

```jsonc
{
  "experimental": {
    "subagent_depth": 2
  }
}
```

بدون آن، عمق پیش‌فرض `1` است و منشی نمی‌تواند کارگر بسازد.

---

## ۴. کامندها و گرامر

### گرامر کامل

```text
/go <verbs> [--app be|both] [--scope all|module|layer|file]
            [--modules a,b] [--layers domain,application,infrastructure,presentation]
            [--files path,…] [--kind word,…] [-n N] [-- متن آزادِ هدف]
```

| توکن | مقدار | معنی |
|---|---|---|
| `verbs` | `explore`, `scan`, `plan`, `craft`, `mend`, `review`, `design` | مرحله‌ها، به همان ترتیب |
| `--app` | `be` \| `both` | سمت پروژه؛ این ریپو فقط بک‌اند دارد |
| `--scope` | `all` \| `module` \| `layer` \| `file` | واحد کار |
| `--modules` | فهرست با کاما | ماژول‌های زیر `app/modules/` |
| `--layers` | فهرست با کاما | چهار لایهٔ DDD |
| `--files` | فهرست با کاما | مسیرهای صریح |
| `--kind` | فهرست با کاما | محدودکردن اسکن به دسته‌های خاص |
| `-n` | عدد | تعداد کارگر موازی (پیش‌فرض ۳) |
| `-- …` | متن آزاد | هدف؛ هرگز به‌عنوان flag پارس نمی‌شود |

### هشت کامند

| کامند | verbهای ثابت | چه می‌کند | خروجی |
|---|---|---|---|
| `/go` | هر ترکیبی که بنویسی | خط فرمان را کامل پارس و اجرا می‌کند | همهٔ مراحل درخواستی |
| `/scan` | `scan` | انحراف از معماری و دادهٔ hard-coded را پیدا می‌کند | گزارش، بدون تغییر |
| `/explore` | `explore` | معماری، جریان درخواست و blast radius را توضیح می‌دهد | نقشه، بدون تغییر |
| `/plan` | `plan` | تسک‌لیست مرتب و یک فایل برای هر کارگر می‌سازد | `.me/runs/<run>/` |
| `/craft` | `plan,craft,review` | کد جدید را طبق تسک‌لیست می‌نویسد و بازبینی می‌کند | کد + گزارش |
| `/mend` | `scan,plan,mend,review` | فقط موارد فهرست‌شده را اصلاح می‌کند | اصلاح حداقلی + گزارش |
| `/review` | `review` | تسک‌ها و دیف را بررسی و تست/لینت را یک بار اجرا می‌کند | وضعیت done/open |
| `/design` | `design` | فقط `docs/sdd.md` را می‌نویسد | سند طراحی |

### پیش‌فرض‌ها

| نامشخص | پیش‌فرض |
|---|---|
| verb | یک سؤال می‌پرسد |
| `--scope` | `all` |
| `--modules` | همهٔ ماژول‌ها |
| `--layers` | هر چهار لایه |
| `--kind` | همهٔ دسته‌ها |
| `-n` | `3` |
| هدفِ `scan` / `explore` / `review` | از روی scope مشتق می‌شود |
| هدفِ `craft` / `mend` / `plan` | یک سؤال با پیش‌نویس مشتق‌شده |
| نبود `.codegraph/` | یک خط گزارش، سپس توقف |

مرحله‌های خودکار همیشه در گزارش اعلام می‌شوند:

- `craft` یا `mend` بدون `plan` → `plan` اضافه می‌شود.
- `craft` یا `mend` بدون `review` → `review` اضافه می‌شود.
- `mend` بدون `scan` → `scan` اضافه می‌شود.

### مثال‌های واقعی

```text
/scan --modules key,example
/explore --scope layer --layers domain -- مرزهای دامنه چیست
/plan --modules user -n 2 -- هدف آزاد
/craft --modules billing -n 2 -- ماژول billing را کامل کن
/mend --modules key -- اصل commit در لایهٔ application
/review --modules key
/design -- محصول جدید با ماژول‌های auth و key
/go scan,plan,mend,review --modules key -- اصل commit در یوزکیس‌ها
```

---

## ۵. ایجنت‌ها و اختیارات

| ایجنت | نقش | `steps` | نوشتن مجاز | تست | ممنوع |
|---|---|---|---|---|---|
| `orchestrator` | پارس، توزیع، گزارش | ۲۵ | `.me/**` | خیر | خواندن کد، نوشتن کد، بارگذاری اسکیل |
| `analyzer` | بررسی و نقشه، فقط‌خواندنی | ۲۰ | `.me/**` | خیر | اصلاح، dispatch |
| `planner` | تسک‌لیست و مالکیت فایل | ۱۵ | `.me/**` | خیر | نوشتن کد |
| `coder` | کد جدید طبق تسک‌فایل | ۴۰ | `app/**`, `test/**`, `migrations/versions/**`, `migrations/env.py`, `.me/**` | خیر | هر چیز بیرون از تسک‌فایل |
| `editor` | اصلاح حداقلی طبق تسک‌فایل | ۳۰ | مثل `coder` | خیر | گسترش دامنه، اصلاح فهرست‌نشده |
| `reviewer` | بررسی + `make test` و `make lint` | ۲۰ | `.me/**` | **بله، یک‌بار** | هرگونه اصلاح |
| `sdd-writer` | فقط `docs/sdd.md` | ۲۵ | `docs/**` | خیر | کد تولیدی |

نکات مهم:

- `orchestrator` هیچ‌وقت کد نمی‌خواند و نمی‌نویسد. فقط کاتالوگ را می‌شناسد.
- `analyzer` و `planner` و `reviewer` فقط‌خواندنی‌اند (به‌جز نوشتن گزارش در `.me/`).
- `coder` و `editor` فقط فایل‌های تسک‌فایل خودشان را لمس می‌کنند.
- `make test` و `make lint` **یک بار در هر اجرا** و فقط توسط `reviewer` اجرا می‌شود.
- هر ایجنت سقف `steps` دارد. اگر کار بزرگ‌تر بود، می‌ایستد، گزارش می‌دهد و
  «continue؟» می‌پرسد.

---

## ۶. مدل مجوزها (Permissions)

در V2 مجوزها یک **آرایهٔ مرتب** از قواعد هستند:

```yaml
permissions:
  - action: shell
    resource: "*"
    effect: deny
  - action: shell
    resource: "make test"
    effect: allow
```

قاعدهٔ طلایی: **آخرین قاعدهٔ منطبق برنده است.** یعنی قاعده‌های کلی را اول و
استثناها را بعد بنویس.

اکشن‌های رایج:

| action | چه چیزی را کنترل می‌کند |
|---|---|
| `read` | خواندن فایل |
| `edit` | ویرایش/نوشتن/patch |
| `glob` | یافتن فایل |
| `grep` | جست‌وجوی متنی |
| `shell` | اجرای دستور شل |
| `subagent` | صدا زدن ایجنت فرزند |
| `skill` | بارگذاری اسکیل |
| `webfetch` / `websearch` | دسترسی وب |
| `question` | پرسیدن سؤال از کاربر |
| `external_directory` | دسترسی بیرون از پروژه |

در این بسته:

- `read *` برای کارگرها `allow` است، ولی `.env`، `.env.*` و `secrets/**` بعد از
  آن `ask` می‌شوند تا رازها بی‌صدا خوانده نشوند.
- `grep` برای همهٔ ایجنت‌ها `deny` است؛ جست‌وجو با CodeGraph انجام می‌شود.
- `shell` فقط برای دستورهای مشخص (`ls`, `make test`, `make lint`,
  `codegraph explore*`, `uv run python scripts/create_module.py*`) باز است.
- `subagent` فقط برای `orchestrator` و فقط برای شش نقش مشخص باز است.

---

## ۷. قانون CodeGraph

اولین فراخوانی ابزار در هر نقش باید `codegraph_explore` باشد. اگر MCP در دسترس
نبود، معادل شل آن مجاز است:

```bash
codegraph explore "<سؤال یا نام نمادها>"
```

`grep`/`rg` ممنوع است و `read`/`glob` فقط برای فایل‌هایی است که CodeGraph نام
برده. `orchestrator` در کل هر اجرا **دقیقاً یک** بار CodeGraph را صدا می‌زند.

اگر `.codegraph/` وجود نداشته باشد، اجرا با یک خط گزارش متوقف می‌شود؛ بازگشت
خاموش به جست‌وجوی متنی وجود ندارد.

---

## ۸. کانفیگ `opencode.jsonc`

```jsonc
{
  "$schema": "https://opencode.ai/config.json",

  // منشی در عمق ۱ اجرا می‌شود و کارگرها را در عمق ۲ می‌سازد.
  "experimental": {
    "subagent_depth": 2
  },

  "mcp": {
    "servers": {
      "codegraph": {
        "type": "local",
        "command": ["codegraph", "serve", "--mcp"]
      }
    }
  }
}
```

نکته‌های V2:

- MCP زیر `mcp.servers` تعریف می‌شود (نه `mcp.<name>`).
- فیلد `enabled: true` لازم نیست؛ نبودنش یعنی فعال.
- در ایجنت‌ها از `permissions` (آرایه) استفاده می‌شود، نه `permission` (map).
- رنگ ایجنت باید هگز شش‌رقمی باشد، مثل `"#3B82F6"`.

---

## ۹. Reload

OpenCode V2 کانفیگ، ایجنت، کامند و اسکیل را **خودکار reload می‌کند**. بعد از
ذخیرهٔ یک فایل زیر `.opencode/` یا `opencode.jsonc` نیازی به بستن و بازکردن
برنامه نیست.

اگر تغییری اعمال نشد:

```text
/reload
```

از `/reload` فقط برای reload کامل دستی استفاده کن.

---

## ۱۰. جریان‌های کاری پیشنهادی

### الف) فقط بفهمم و بررسی کنم (بدون تغییر)

```text
/explore --modules knowledge
/scan --modules key,example
```

### ب) یک قابلیت جدید اضافه کنم

```text
/plan --modules billing -n 2 -- افزودن CRUD برای billing
/craft --modules billing -n 2 -- همان هدف
```

یا یک‌مرحله‌ای:

```text
/craft --modules billing -n 2 -- افزودن CRUD برای billing
```

`/craft` خودش `plan` و `review` را اضافه می‌کند.

### ج) فقط موارد مشخص را اصلاح کنم

```text
/mend --modules key -- اصل commit در لایهٔ application
```

`/mend` اول `scan` و بعد `plan` را اضافه می‌کند تا فقط یافته‌های نام‌برده اصلاح
شوند؛ بقیه فقط گزارش می‌شوند.

### د) سند طراحی بنویسم

```text
/design -- محصول جدید با ماژول‌های auth و key
```

خروجی فقط `docs/sdd.md` است؛ هیچ کد تولیدی ندارد.

### ه) فقط راستی‌آزمایی کنم

```text
/review --modules key
```

---

## ۱۱. عیب‌یابی

| نشانه | علت | راه‌حل |
|---|---|---|
| کامند در پالت نیست | فایل در `.opencode/commands/` نیست | همان‌جا ذخیره کن و `/reload` بزن |
| «کدام کار؟» پرسیده شد | به `/go` verb ندادی | verb بده یا از پریست استفاده کن |
| ۳ کارگر اجرا شد | `-n` ندادی (پیش‌فرض ۳) | `-n N` را انتهای خط بگذار |
| مرحله‌ای اجرا شد که نخواستم | اضافه‌شدن خودکار مرحله | در گزارش اعلام می‌شود؛ با پریست verbها را ثابت کن |
| منشی از خواندن فایل طفره رفت | عمدی است؛ او کد نمی‌خواند | از کارگر جزئیات بخواه |
| خطای «subagent depth» | `subagent_depth` تنظیم نشده | مقدار `2` را در `experimental` بگذار |
| `make test` دو بار اجرا شد | کارگر آن را اجرا کرده (کانفیگ قدیمی) | `/reload` و بررسی مجوز `shell` کارگر |
| ایجنت اسکیل را لود نمی‌کند | `skill *` روی `deny` است و استثنا ندارد | برای همان اسکیل یک قاعدهٔ `allow` بعد از `deny` بگذار |
| تغییر کانفیگ اعمال نشد | کش نشست | `/reload` بزن؛ نیازی به restart نیست |
| CodeGraph پاسخ نمی‌دهد | `.codegraph/` یا MCP نیست | `codegraph init` یا بررسی `opencode debug config` |

---

## ۱۲. چک‌لیست تأیید پس از هر تغییر

```bash
# ۱. سینتکس و اعتبار کانفیگ
uv run python scripts/opencode_setup.py

# ۲. فرانت‌متر ایجنت‌ها و کامندها
python3 - <<'PY'
import pathlib, re, yaml
for f in sorted(pathlib.Path('.opencode/agents').glob('*.md')) + \
         sorted(pathlib.Path('.opencode/commands').glob('*.md')):
    t = f.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', t, re.S)
    assert m, f
    yaml.safe_load(m.group(1))
print('frontmatter OK')
PY

# ۳. آنچه OpenCode دیده است
opencode debug agents | jq 'length'          # ۱۴
opencode debug config | jq '[.[] | select(.type=="document") | .info.experimental]'

# ۴. همگام‌سازی سراسری
make opencode
```

---

## ۱۳. قواعد طلایی

1. **همیشه از orchestrator شروع کن، نه از کد دستی.**
2. **verb و فلگ‌ها را دقیق بده**؛ مبهم بگذاری، یک سؤال می‌پرسد.
3. **بعد از `--` هرچه بنویسی هدف است**، حتی اگر شبیه flag باشد.
4. **تست و لینت یک بار، توسط reviewer.** کارگرها هرگز اجرا نمی‌کنند.
5. **مالکیت فایل مقدس است.** هر کارگر فقط تسک‌فایل خودش را لمس می‌کند.
6. **رازها را به ایجنت نده.** `.env` و `secrets/` عمداً `ask` هستند.
7. **برای فهم کد از CodeGraph استفاده کن**، نه grep.
8. **بعد از تغییر بسته، `/reload`** (و اگر نشد، یک reload کامل).
