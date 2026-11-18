[English](README.md) | **فارسی**

# سامانه پرسش و پاسخ مبتنی بر اسناد (RAG)

یک سامانه پرسش و پاسخ مبتنی بر اسناد که با استفاده از Django REST Framework و معماری تولید افزوده با بازیابی (Retrieval-Augmented Generation یا RAG) توسعه داده شده است.

این سامانه امکان بارگذاری اسناد DOCX، بازیابی اطلاعات مرتبط از طریق جستجوی معنایی و طرح پرسش بر اساس محتوای اسناد بارگذاری‌شده را فراهم می‌کند. پاسخ‌ها با استفاده از یک مدل زبانی بزرگ (LLM) و بر اساس محتوای بازیابی‌شده تولید می‌شوند و منابع مرتبط نیز در کنار هر پاسخ ارائه می‌شوند.

## 📑 فهرست مطالب

- [قابلیت‌های اصلی](#readme-fa-key-features)
- [معماری سیستم](#readme-fa-system-architecture)
- [مراحل پردازش RAG](#readme-fa-rag-pipeline)
- [فناوری‌های استفاده‌شده](#readme-fa-technology-stack)
- [ساختار پروژه](#readme-fa-project-structure)
- [پیش‌نیازها](#readme-fa-requirements)
- [شروع به کار](#readme-fa-getting-started)
- [مسیرهای API](#readme-fa-api-endpoints)
- [مستندات API](#readme-fa-api-documentation)
- [اسناد و پرسش‌های نمونه](#readme-fa-sample-documents)
- [اجرای تست‌ها](#readme-fa-running-tests)
- [تنظیمات پروژه](#readme-fa-configuration)
- [محدودیت‌ها و نکات امنیتی](#readme-fa-limitations)
- [مجوز](#readme-fa-license)

---

<a name="readme-fa-key-features"></a>
## ✨ قابلیت‌های اصلی

- بارگذاری و اعتبارسنجی اسناد DOCX
- مشاهده، ویرایش و حذف اسناد
- استخراج متن از پاراگراف‌ها و جدول‌های اسناد
- تقسیم متن به بخش‌های کوچک‌تر بر اساس تعداد توکن و با هم‌پوشانی
- تولید بردارهای معنایی چندزبانه با FastEmbed
- جستجوی معنایی با PostgreSQL و pgvector
- پرسش و پاسخ مبتنی بر RAG با استفاده از OpenRouter
- ارائه منابع مرتبط در کنار پاسخ‌ها
- نگهداری تاریخچه پرسش‌ها به همراه صفحه‌بندی
- پنل مدیریت Django برای مدیریت اسناد و تاریخچه پرسش‌ها
- مستندات تعاملی API با Swagger UI و ReDoc
- اجرای پروژه با Docker Compose در محیط توسعه و تست

---

<a name="readme-fa-system-architecture"></a>
## 🏗️ معماری سیستم

این برنامه از یک معماری ماژولار مبتنی بر Django استفاده می‌کند.

### اجزای اصلی

- **Django REST Framework:** ارائه قابلیت‌های مدیریت اسناد و پرسش و پاسخ از طریق REST API.
- **برنامه Documents:** مدیریت اعتبارسنجی اسناد، استخراج متن، تقسیم‌بندی، تولید embedding، ذخیره اسناد و جستجوی معنایی.
- **برنامه QA:** مدیریت پرسش‌ها، بازیابی زمینه، ارتباط با مدل زبانی، تولید پاسخ و تاریخچه پرسش‌ها.
- **PostgreSQL:** ذخیره اطلاعات برنامه و محتوای اسناد.
- **pgvector:** ذخیره و جستجوی بردارهای معنایی.
- **FastEmbed:** تولید embeddingهای چندزبانه.
- **LangChain:** اتصال محتوای بازیابی‌شده به مدل زبانی.
- **OpenRouter:** فراهم کردن دسترسی به مدل زبانی پیکربندی‌شده.
- **Django Admin:** ارائه پنل مدیریتی برای مدیریت اطلاعات ذخیره‌شده.

---

<a name="readme-fa-rag-pipeline"></a>
## 🔄 مراحل پردازش RAG

### پردازش و نمایه‌سازی سند

۱. کاربر یک سند DOCX بارگذاری می‌کند.

۲. سامانه پسوند و حجم فایل را اعتبارسنجی می‌کند.

۳. متن موجود در پاراگراف‌ها و جدول‌های سند استخراج می‌شود.

۴. متن استخراج‌شده به بخش‌هایی با حداکثر ۴۵۰ توکن و هم‌پوشانی ۶۰ توکنی تقسیم می‌شود.

۵. کتابخانه FastEmbed با پیشوند `passage:` برای هر بخش یک بردار معنایی ۳۸۴بعدی تولید می‌کند.

۶. بخش‌های متن و بردارهای مربوط به آن‌ها در PostgreSQL با استفاده از pgvector ذخیره می‌شوند.

۷. وضعیت پردازش سند به `completed` یا `failed` تغییر می‌کند.

### فرایند پرسش و پاسخ

۱. کاربر پرسش خود را از طریق REST API ارسال می‌کند.

۲. پرسش با پیشوند `query:` به یک بردار معنایی تبدیل می‌شود.

۳. pgvector مرتبط‌ترین بخش‌ها را از میان اسناد پردازش‌شده بازیابی می‌کند.

۴. نتایج بر اساس آستانه فاصله کسینوسی پیکربندی‌شده فیلتر می‌شوند.

۵. بخش‌های مرتبط به‌عنوان زمینه برای مدل زبانی آماده می‌شوند.

۶. LangChain پرسش و زمینه بازیابی‌شده را به مدل زبانی پیکربندی‌شده در OpenRouter ارسال می‌کند.

۷. مدل زبانی با استفاده از محتوای بازیابی‌شده پاسخ تولید می‌کند.

۸. پاسخ و منابع مرتبط در تاریخچه پرسش‌ها ذخیره و به کاربر بازگردانده می‌شوند.

### مدیریت نبود اطلاعات کافی

سامانه در مواجهه با نبود اطلاعات کافی، دو حالت را مدیریت می‌کند:

- **هیچ بخش مرتبطی بازیابی نشود:** اگر هیچ بخشی از اسناد به آستانه ارتباط تعیین‌شده نرسد، سامانه بدون فراخوانی مدل زبانی، پیام از پیش تعیین‌شده‌ای مبنی بر نبود اطلاعات مرتبط برمی‌گرداند. در این حالت مقدار `used_llm` برابر `false` است.
- **محتوای بازیابی‌شده کافی نباشد:** اگر بخش‌های مرتبطی بازیابی شوند، اما مدل زبانی تشخیص دهد که محتوای بازیابی‌شده برای پاسخ‌گویی کافی نیست، همان پیام از پیش تعیین‌شده پس از فراخوانی مدل زبانی برگردانده می‌شود. در این حالت مقدار `used_llm` برابر `true` است.

---

<a name="readme-fa-technology-stack"></a>
## 🧰 فناوری‌های استفاده‌شده

| بخش | فناوری |
|---|---|
| زبان برنامه‌نویسی | Python 3.13 |
| فریم‌ورک بک‌اند | Django 6.1 |
| REST API | Django REST Framework 3.18 |
| مستندسازی API | drf-spectacular 0.30 |
| پایگاه داده | PostgreSQL 16 |
| جستجوی برداری | pgvector 0.8.7 |
| مدل Embedding | intfloat/multilingual-e5-small |
| کتابخانه Embedding | FastEmbed 0.9.1 |
| ابعاد بردارها | 384 |
| یکپارچه‌سازی RAG | LangChain |
| ارائه‌دهنده مدل زبانی | OpenRouter |
| مدل زبانی پیش‌فرض | qwen/qwen3-32b:free |
| پردازش DOCX | python-docx 1.2 |
| کانتینرسازی | Docker و Docker Compose |

---

<a name="readme-fa-project-structure"></a>
## 🗂️ ساختار پروژه

```text
rag-document-system/
│
├── config/
├── core/
├── documents/
│   ├── management/
│   ├── migrations/
│   └── application files
│
├── qa/
│   ├── management/
│   ├── migrations/
│   └── application files
│
├── docs/
│   ├── API.md
│   ├── API.fa.md
│   ├── ARCHITECTURE.md
│   └── ARCHITECTURE.fa.md
│
├── sample_documents/
│   ├── generate_sample_document.py
│   ├── sample_library_guide.fa.docx
│   ├── sample_library_guide.en.docx
│   └── sample_questions.md
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── .env.example
├── .dockerignore
├── .gitignore
├── README.md
└── README.fa.md
```

اسناد بارگذاری‌شده، فایل `.env`، محیط مجازی و فایل‌های cache، داده‌های محلی یا زمان اجرای برنامه هستند و در مخزن کد قرار نمی‌گیرند.

---

<a name="readme-fa-requirements"></a>
## 📋 پیش‌نیازها

برای اجرای پروژه به موارد زیر نیاز دارید:

- Docker
- Docker Compose
- کلید API سرویس OpenRouter

تنظیمات فعلی Docker Compose برای اجرای برنامه Django و پایگاه داده PostgreSQL در محیط توسعه و تست در نظر گرفته شده است.

---

<a name="readme-fa-getting-started"></a>
## 🚀 شروع به کار

### ۱. دریافت مخزن پروژه

```bash
git clone https://github.com/MrMahdiAliakbar/rag-document-system.git
cd rag-document-system
```

### ۲. تنظیم متغیرهای محیطی

ابتدا فایل نمونه تنظیمات را به `.env` کپی کنید:

```powershell
Copy-Item .env.example .env
```

سپس مقادیر داخل فایل `.env` را تنظیم کنید:

```env
DJANGO_SECRET_KEY=replace-with-a-secure-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_NAME=rag_db
DB_USER=rag_user
DB_PASSWORD=change-this-database-password
DB_HOST=db
DB_PORT=5432

OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=qwen/qwen3-32b:free
```

تنظیمات زیر برای RAG اختیاری هستند و در صورت مشخص نکردن آن‌ها، مقادیر پیش‌فرض زیر استفاده می‌شوند:

```env
RAG_TOP_K=5
RAG_MAX_COSINE_DISTANCE=0.20
RAG_LLM_MAX_TOKENS=1024
RAG_LLM_TIMEOUT=60000
```

تمام مقادیر نمونه را با تنظیمات موردنظر خود جایگزین کنید.

فایل `.env` حاوی اطلاعات محرمانه است. آن را خصوصی نگه دارید و هرگز در مخزن Git قرار ندهید.

### ۳. ساخت و اجرای کانتینرها

```bash
docker compose up --build -d
```

برای بررسی وضعیت کانتینرها:

```bash
docker compose ps
```

برای مشاهده گزارش اجرای برنامه:

```bash
docker compose logs -f web
```

### ۴. اجرای Migrationها

```bash
docker compose exec web python manage.py migrate
```

### ۵. ساخت حساب مدیر

```bash
docker compose exec web python manage.py createsuperuser
```

سپس اطلاعات حساب مدیر را طبق راهنما وارد کنید.

### ۶. دسترسی به رابط‌های برنامه

پس از اجرای کانتینرها، مسیرهای محلی زیر در دسترس خواهند بود:

| رابط | آدرس | کاربرد |
|---|---|---|
| پنل مدیریت Django | [http://localhost:8000/admin/](http://localhost:8000/admin/) | مدیریت اسناد و تاریخچه پرسش‌ها |
| Swagger UI | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) | مشاهده Endpointها و ارسال درخواست آزمایشی |
| ReDoc | [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/) | مطالعه ساختاریافته مستندات API |
| OpenAPI Schema | [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/) | دریافت مشخصات تولیدشده OpenAPI |

این آدرس‌ها فقط تا زمانی در دسترس هستند که برنامه به‌صورت محلی در حال اجرا باشد.

---

<a name="readme-fa-api-endpoints"></a>
## 🔌 مسیرهای API

### مدیریت اسناد

مسیر پایه: `/api/documents/`

| متد | مسیر | توضیحات |
|---|---|---|
| GET | `/api/documents/` | دریافت فهرست اسناد |
| POST | `/api/documents/` | بارگذاری و پردازش سند DOCX |
| GET | `/api/documents/{id}/` | دریافت اطلاعات یک سند |
| PUT | `/api/documents/{id}/` | ویرایش اطلاعات سند |
| PATCH | `/api/documents/{id}/` | ویرایش بخشی از اطلاعات سند |
| DELETE | `/api/documents/{id}/` | حذف سند و فایل ذخیره‌شده آن |

درخواست‌های بارگذاری و ویرایش سند از نوع `multipart/form-data` هستند.

### پرسش و پاسخ

مسیر پایه: `/api/qa/`

| متد | مسیر | توضیحات |
|---|---|---|
| POST | `/api/qa/ask/` | ارسال پرسش و دریافت پاسخ |
| GET | `/api/qa/history/` | دریافت تاریخچه صفحه‌بندی‌شده پرسش‌ها |
| GET | `/api/qa/history/{id}/` | دریافت جزئیات یک رکورد تاریخچه به همراه منابع |

درخواست ارسال پرسش از نوع JSON است.

فیلد `document_id` اختیاری است. در صورت ارسال، جستجو فقط در سند مشخص‌شده انجام می‌شود.

تاریخچه پرسش‌ها از جدیدترین به قدیمی‌ترین مرتب می‌شود. مسیر فهرست از پارامترهای `page` و `page_size` برای صفحه‌بندی پشتیبانی می‌کند.

وضعیت پرسش که در پاسخ API نمایش داده می‌شود، از روی محتوای پاسخ محاسبه می‌شود و به‌عنوان یک فیلد مستقل در پایگاه داده ذخیره نمی‌شود.

برای مشاهده جزئیات درخواست‌ها و پاسخ‌ها، به [مستندات API](docs/API.fa.md) مراجعه کنید.

---

<a name="readme-fa-api-documentation"></a>
## 📖 مستندات API

مستندات API با استفاده از `drf-spectacular` به‌صورت خودکار تولید می‌شوند.

- **Swagger UI:** رابطی تعاملی برای مشاهده Endpointها، بررسی قالب درخواست‌ها و ارسال درخواست‌های آزمایشی.
- **ReDoc:** رابطی ساختاریافته و مناسب مطالعه برای مشاهده توضیحات Endpointها، پارامترها و ساختار پاسخ‌ها.
- **OpenAPI Schema:** مشخصات ماشینی API که می‌تواند توسط ابزارهای توسعه و کلاینت‌های API استفاده شود.

| نوع مستندات | مسیر محلی |
|---|---|
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI Schema | `/api/schema/` |

برای مطالعه مستندات کامل و نوشتاری:

- [مستندات API — فارسی](docs/API.fa.md)
- [API Documentation — English](docs/API.md)

برای آشنایی با اجزای داخلی و جزئیات فنی پروژه:

- [مستندات معماری — فارسی](docs/ARCHITECTURE.fa.md)
- [Architecture Documentation — English](docs/ARCHITECTURE.md)

---

<a name="readme-fa-sample-documents"></a>
## 🧪 اسناد و پرسش‌های نمونه

پوشه `sample_documents/` شامل موارد زیر است:

- یک سند نمونه فارسی با فرمت DOCX
- یک سند نمونه انگلیسی با فرمت DOCX
- اسکریپت Python برای تولید اسناد نمونه
- مجموعه‌ای از پرسش‌های نمونه برای آزمایش فرایند RAG

از این منابع می‌توان برای بارگذاری محتوای نمونه و ارزیابی عملکرد بازیابی اسناد و پاسخ‌گویی سامانه استفاده کرد.

---

<a name="readme-fa-running-tests"></a>
## 🧫 اجرای تست‌ها

برای اجرای مجموعه تست‌های خودکار در کانتینر برنامه:

```bash
docker compose exec web python manage.py test
```

در مرحله تست و اعتبارسنجی پروژه، ۵۸ تست خودکار با موفقیت اجرا شدند.

---

<a name="readme-fa-configuration"></a>
## ⚙️ تنظیمات پروژه

| متغیر | توضیحات | مقدار پیش‌فرض / رفتار |
|---|---|---|
| `DJANGO_SECRET_KEY` | کلید امنیتی Django | اجباری؛ بدون مقدار جایگزین |
| `DJANGO_DEBUG` | فعال یا غیرفعال کردن حالت Debug | در تنظیمات Django برابر `False`؛ در فایل نمونه توسعه برابر `True` |
| `DJANGO_ALLOWED_HOSTS` | فهرست میزبان‌های مجاز با جداکننده کاما | در تنظیمات Django برابر `localhost,127.0.0.1` |
| `DB_NAME` | نام پایگاه داده PostgreSQL | اجباری |
| `DB_USER` | نام کاربری PostgreSQL | اجباری |
| `DB_PASSWORD` | رمز عبور PostgreSQL | اجباری |
| `DB_HOST` | میزبان پایگاه داده | `db` |
| `DB_PORT` | پورت پایگاه داده | `5432` |
| `OPENROUTER_API_KEY` | کلید API سرویس OpenRouter | خالی؛ برای درخواست‌های LLM لازم است |
| `OPENROUTER_MODEL` | شناسه مدل زبانی | `qwen/qwen3-32b:free` |
| `RAG_TOP_K` | حداکثر تعداد بخش‌های بازیابی‌شده | `5` |
| `RAG_MAX_COSINE_DISTANCE` | حداکثر فاصله کسینوسی مجاز | `0.20` |
| `RAG_LLM_MAX_TOKENS` | حداکثر تعداد توکن‌های پاسخ تولیدشده | `1024` |
| `RAG_LLM_TIMEOUT` | مهلت زمانی درخواست به مدل زبانی بر حسب میلی‌ثانیه | `60000` |

فایل `.env.example` مقادیر مناسب محیط توسعه را ارائه می‌کند. به‌طور مشخص، در این فایل `DJANGO_DEBUG=True` تنظیم شده و `0.0.0.0` نیز در فهرست میزبان‌های مجاز قرار دارد. این تنظیمات توصیه‌ای برای محیط Production نیستند.

---

<a name="readme-fa-limitations"></a>
## 🔐 محدودیت‌ها و نکات امنیتی

- فرایند فعلی بارگذاری اسناد فقط از فایل‌های DOCX پشتیبانی می‌کند.
- حداکثر حجم فایل قابل قبول ۱۰ مگابایت است.
- Endpointهای فعلی API بدون احراز هویت قابل دسترسی هستند.
- تنظیمات Docker برای توسعه و تست در نظر گرفته شده‌اند و برای استقرار Production مناسب نیستند.
- در پیکربندی فعلی Docker از سرور توسعه Django استفاده می‌شود.
- پورت پایگاه داده فقط روی رابط loopback میزبان (`127.0.0.1:5432`) منتشر می‌شود و روی تمام رابط‌های شبکه در دسترس نیست.
- پیش از اجرای برنامه باید مقدار معتبر `DJANGO_SECRET_KEY` و متغیرهای ضروری پایگاه داده تنظیم شوند.
- مقدار پیش‌فرض `DJANGO_DEBUG` در تنظیمات Django برابر `False` است؛ فایل `.env.example` برای توسعه محلی آن را فعال می‌کند.
- کیفیت پاسخ‌ها به محتوای اسناد، ارتباط نتایج بازیابی‌شده و مدل زبانی پیکربندی‌شده وابسته است.
- تولید پاسخ به کلید API معتبر OpenRouter و دسترسی به مدل انتخاب‌شده نیاز دارد.

---

<a name="readme-fa-license"></a>
## 📄 مجوز

در حال حاضر مجوز مشخصی برای این پروژه تعیین نشده است.