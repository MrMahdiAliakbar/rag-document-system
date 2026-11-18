
# RAG Sample Questions and Expected Answers

This document contains sample questions for evaluating the RAG Document System using the Persian and English university library documents.

Each question includes an expected answer to help evaluate retrieval accuracy and answer quality.

---

# 1. Persian Questions

## 1.1 Direct Retrieval

### FA-01
**Question:**
ساعات فعالیت کتابخانه در روزهای پنجشنبه چگونه است؟

**Expected Answer:**
کتابخانه روزهای پنجشنبه از ساعت ۸ صبح تا ۱۳ فعالیت می‌کند.

### FA-02
**Question:**
هزینه صدور اولیه کارت عضویت کتابخانه چقدر است؟

**Expected Answer:**
هزینه صدور اولیه کارت عضویت ۱۰۰ هزار تومان است و تمدید سالانه آن رایگان است.

## 1.2 Multi-chunk Reasoning

### FA-03
**Question:**
اگر دانشجویی روز پنجشنبه بخواهد از خدمات چاپ استفاده کند، تا چه ساعتی فرصت دارد و کتابخانه تا چه ساعتی باز است؟

**Expected Answer:**
کتابخانه روز پنجشنبه تا ساعت ۱۳ باز است، اما خدمات چاپ تا ساعت ۱۷:۳۰ ارائه می‌شوند. بنابراین دانشجو باید توجه داشته باشد که ساعت ارائه خدمات چاپ در سند دیرتر از ساعت فعالیت کتابخانه اعلام شده است.

### FA-04
**Question:**
دانشجویی که سالن مطالعه را رزرو کرده اما نمی‌تواند در زمان تعیین‌شده مراجعه کند، چه زمانی باید رزرو خود را لغو کند و مدت استفاده روزانه او چقدر است؟

**Expected Answer:**
دانشجو باید حداقل یک ساعت پیش از زمان رزروشده، رزرو را لغو کند. حداکثر مدت استفاده روزانه از سالن مطالعه دو ساعت است.

## 1.3 Multiple Facts

### FA-05
**Question:**
شرایط امانت کتاب برای دانشجویان کارشناسی، کارشناسی ارشد، دکتری و اعضای هیئت علمی را مقایسه کن.

**Expected Answer:**
- کارشناسی: ۳ کتاب به مدت ۱۴ روز
- کارشناسی ارشد: ۵ کتاب به مدت ۲۱ روز
- دکتری: ۵ کتاب به مدت ۲۱ روز
- هیئت علمی: ۸ کتاب به مدت ۳۰ روز

### FA-06
**Question:**
هزینه چاپ سیاه‌وسفید و رنگی چقدر است و برای سفارش‌های بیشتر از چند صفحه ارسال فایل از قبل توصیه شده است؟

**Expected Answer:**
- چاپ سیاه‌وسفید: هر صفحه ۱٬۵۰۰ تومان
- چاپ رنگی: هر صفحه ۶٬۰۰۰ تومان
- برای سفارش‌های بیشتر از ۵۰ صفحه، ارسال فایل از قبل توصیه شده است.

## 1.4 Unanswerable Questions

### FA-07
**Question:**
شماره تلفن مستقیم کتابخانه دانشگاه چیست؟

**Expected Answer:**
شماره تلفن مستقیمی در سند اعلام نشده است. برای دریافت راهنمایی می‌توان به میز اطلاعات کتابخانه مراجعه کرد یا از سامانه پشتیبانی دانشگاه استفاده کرد.

### FA-08
**Question:**
آدرس خیابان و شماره ساختمان کتابخانه دانشگاه چیست؟

**Expected Answer:**
آدرس دقیق خیابان و شماره ساختمان کتابخانه در سند مشخص نشده است. نباید آدرسی حدس زده شود.

---

# 2. English Questions

## 2.1 Direct Retrieval

### EN-01
**Question:**
What are the library's opening hours on Thursdays?

**Expected Answer:**
The library is open from 8:00 AM to 1:00 PM on Thursdays.

### EN-02
**Question:**
How much is the initial library membership card issuance fee?

**Expected Answer:**
The initial membership card issuance fee is 100,000 tomans. Annual membership renewal is free.

## 2.2 Multi-chunk Reasoning

### EN-03
**Question:**
If a student wants to use the printing service on Thursday, until what time is the service available, and until what time is the library open?

**Expected Answer:**
The library is open until 1:00 PM on Thursdays, while printing services are available until 5:30 PM. The document specifies different closing times for the library and its printing services.

### EN-04
**Question:**
If a student cannot attend a reserved study hall session, how early must they cancel the reservation, and what is the maximum daily usage period?

**Expected Answer:**
The student must cancel at least one hour before the reserved time. The maximum daily study hall usage period is two hours.

## 2.3 Multiple Facts

### EN-05
**Question:**
Compare the borrowing limits and borrowing periods for undergraduate, master's, PhD students, and faculty members.

**Expected Answer:**
- Undergraduate students: 3 books for 14 days
- Master's students: 5 books for 21 days
- PhD students: 5 books for 21 days
- Faculty members: 8 books for 30 days

### EN-06
**Question:**
What are the per-page prices for black-and-white and color printing, and for orders exceeding how many pages is advance file submission recommended?

**Expected Answer:**
- Black-and-white printing: 1,500 tomans per page
- Color printing: 6,000 tomans per page
- Advance file submission is recommended for orders exceeding 50 pages.

## 2.4 Unanswerable Questions

### EN-07
**Question:**
What is the library's direct telephone number?

**Expected Answer:**
The document does not provide a direct telephone number for the library. Visitors can contact the information desk or use the university support system.

### EN-08
**Question:**
What is the library's exact street address and building number?

**Expected Answer:**
The exact street address and building number are not provided in the document. The system should not guess this information.

---

# 3. Evaluation Criteria

Evaluate each response using the following criteria:

1. Retrieval Accuracy: Was the relevant information retrieved correctly?
2. Answer Accuracy: Does the generated answer match the information in the document?
3. Completeness: Does the answer include all requested facts?
4. Hallucination Control: Does the system avoid inventing information when the answer is unavailable?
5. Language Consistency: Does the response use the same language as the question?

A response should be considered incorrect if it invents facts, contradicts the document, or omits important requested information.
