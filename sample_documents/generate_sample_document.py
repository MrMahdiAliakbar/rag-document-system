
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


OUTPUT_DIR = Path(__file__).resolve().parent


def set_paragraph_direction(paragraph, is_persian):
    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.RIGHT
        if is_persian
        else WD_ALIGN_PARAGRAPH.LEFT
    )

    if is_persian:
        paragraph_properties = paragraph._p.get_or_add_pPr()
        bidi = OxmlElement("w:bidi")
        paragraph_properties.append(bidi)

    for run in paragraph.runs:
        if is_persian:
            run_properties = run._r.get_or_add_rPr()
            rtl = OxmlElement("w:rtl")
            run_properties.append(rtl)


def add_paragraph(document, text, is_persian):
    paragraph = document.add_paragraph()
    paragraph.add_run(text)
    set_paragraph_direction(paragraph, is_persian)
    return paragraph


def add_heading(document, text, level, is_persian):
    heading = document.add_heading(text, level=level)
    set_paragraph_direction(heading, is_persian)
    return heading


def add_table(document, headers, rows, is_persian):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"

    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = header

    for row in rows:
        cells = table.add_row().cells

        for index, value in enumerate(row):
            cells[index].text = value

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                set_paragraph_direction(
                    paragraph,
                    is_persian
                )

    return table


def configure_document(document, is_persian):
    section = document.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(12)


def create_persian_document():
    document = Document()
    configure_document(document, True)

    title = document.add_heading(
        "راهنمای جامع قوانین و خدمات کتابخانه دانشگاه",
        0
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_paragraph(
        document,
        "این سند با هدف معرفی خدمات، قوانین عضویت، شرایط امانت کتاب، "
        "امکانات دیجیتال و ضوابط استفاده از کتابخانه دانشگاه تهیه شده است.",
        True
    )

    sections = [
        (
            "۱. ساعات فعالیت کتابخانه",
            [
                "کتابخانه دانشگاه در روزهای شنبه تا چهارشنبه از ساعت ۸ صبح "
                "تا ۱۸ فعالیت می‌کند. ساعات فعالیت در روز پنجشنبه از ساعت ۸ "
                "صبح تا ۱۳ است. کتابخانه در روزهای جمعه و تعطیلات رسمی تعطیل است.",
                "خدمات چاپ و اسکن در روزهای کاری تا ساعت ۱۷:۳۰ ارائه می‌شوند. "
                "بنابراین مراجعه‌کنندگان باید درخواست‌های مربوط به چاپ و اسکن "
                "را پیش از پایان این ساعت ثبت کنند."
            ]
        ),
        (
            "۲. عضویت در کتابخانه",
            [
                "دانشجویان برای عضویت در کتابخانه باید کارت دانشجویی معتبر "
                "خود را ارائه دهند. هزینه صدور کارت عضویت برای نخستین بار "
                "۱۰۰ هزار تومان است. تمدید عضویت در سال‌های بعد رایگان خواهد بود.",
                "کارت عضویت برای استفاده از خدمات امانت کتاب الزامی است. "
                "اعضای کتابخانه موظف‌اند هنگام دریافت کتاب، کارت عضویت خود "
                "را به مسئول امانت ارائه کنند."
            ]
        ),
        (
            "۳. قوانین امانت کتاب",
            [
                "تعداد کتاب‌های قابل امانت و مدت زمان نگهداری آن‌ها بر اساس "
                "مقطع تحصیلی یا موقعیت شغلی عضو تعیین می‌شود."
            ]
        ),
        (
            "۴. خدمات و منابع دیجیتال",
            [
                "اعضای کتابخانه می‌توانند از منابع دیجیتال و پایگاه‌های "
                "اطلاعات علمی دانشگاه استفاده کنند. دسترسی از راه دور به این "
                "منابع از طریق پرتال دانشجویی امکان‌پذیر است.",
                "برای ورود به پرتال و استفاده از منابع دیجیتال، نام کاربری "
                "و رمز عبور دانشگاه مورد نیاز است. این اطلاعات باید محرمانه "
                "نگهداری شوند و در اختیار افراد دیگر قرار نگیرند."
            ]
        ),
        (
            "۵. سالن مطالعه",
            [
                "سالن مطالعه کتابخانه در طبقه دوم ساختمان قرار دارد. هر دانشجو "
                "می‌تواند روزانه حداکثر دو ساعت از طریق سامانه داخلی کتابخانه "
                "برای استفاده از سالن مطالعه رزرو انجام دهد.",
                "در صورت انصراف از رزرو، دانشجو باید حداقل یک ساعت پیش از "
                "زمان رزروشده، درخواست خود را لغو کند تا امکان استفاده از "
                "ظرفیت برای سایر دانشجویان فراهم شود.",
                "رعایت سکوت در سالن مطالعه الزامی است. خوردن و آشامیدن در "
                "این سالن مجاز نیست و کاربران باید از ایجاد مزاحمت برای "
                "سایر افراد خودداری کنند."
            ]
        ),
        (
            "۶. خدمات چاپ و اسکن",
            [
                "کتابخانه خدمات چاپ سیاه‌وسفید، چاپ رنگی و اسکن اسناد را "
                "ارائه می‌دهد. هزینه چاپ بر اساس نوع چاپ محاسبه می‌شود.",
                "خدمات چاپ از شنبه تا پنجشنبه تا ساعت ۱۷:۳۰ ارائه می‌شوند. "
                "دانشجویانی که قصد چاپ بیش از ۵۰ صفحه را دارند، بهتر است "
                "فایل خود را از قبل برای کتابخانه ارسال کنند."
            ]
        ),
        (
            "۷. کارگاه‌های آموزشی",
            [
                "کتابخانه به‌صورت دوره‌ای کارگاه‌هایی برای ارتقای مهارت‌های "
                "پژوهشی دانشجویان برگزار می‌کند. موضوع این کارگاه‌ها شامل "
                "جستجوی علمی، ارزیابی منابع، شیوه‌های ارجاع‌دهی و مدیریت "
                "منابع علمی است.",
                "ثبت‌نام در کارگاه‌ها باید حداقل سه روز پیش از برگزاری انجام "
                "شود. ظرفیت هر کارگاه حداکثر ۲۰ نفر است و اولویت ثبت‌نام "
                "با افرادی خواهد بود که زودتر درخواست خود را ثبت کرده‌اند."
            ]
        ),
        (
            "۸. قوانین عمومی استفاده از کتابخانه",
            [
                "تمام مراجعه‌کنندگان موظف‌اند کارت عضویت خود را همراه داشته "
                "باشند و مقررات مربوط به حفظ سکوت، رعایت نظم و نگهداری از "
                "اموال کتابخانه را رعایت کنند.",
                "ورود مواد غذایی و نوشیدنی به سالن مطالعه ممنوع است. اعضا "
                "در صورت وارد کردن خسارت به کتاب‌ها، تجهیزات یا سایر اموال "
                "کتابخانه، مسئول جبران خسارت خواهند بود."
            ]
        ),
        (
            "۹. راه‌های ارتباطی",
            [
                "برای دریافت راهنمایی درباره عضویت، امانت کتاب، منابع دیجیتال "
                "یا سایر خدمات، مراجعه‌کنندگان می‌توانند به میز اطلاعات "
                "کتابخانه مراجعه کنند یا از سامانه پشتیبانی دانشگاه استفاده کنند.",
                "شماره تلفن مستقیمی برای کتابخانه در این سند اعلام نشده است."
            ]
        )
    ]

    for heading, paragraphs in sections:
        add_heading(document, heading, 1, True)

        for paragraph in paragraphs:
            add_paragraph(document, paragraph, True)

        if heading == "۳. قوانین امانت کتاب":
            add_table(
                document,
                ["گروه اعضا", "حداکثر تعداد کتاب", "مدت امانت"],
                [
                    ["دانشجوی کارشناسی", "۳ کتاب", "۱۴ روز"],
                    ["دانشجوی کارشناسی ارشد", "۵ کتاب", "۲۱ روز"],
                    ["دانشجوی دکتری", "۵ کتاب", "۲۱ روز"],
                    ["اعضای هیئت علمی", "۸ کتاب", "۳۰ روز"]
                ],
                True
            )

            add_paragraph(
                document,
                "تمدید مدت امانت هر کتاب فقط یک بار امکان‌پذیر است. تمدید "
                "در صورتی انجام می‌شود که کتاب توسط عضو دیگری رزرو نشده باشد.",
                True
            )

            add_paragraph(
                document,
                "در صورت تأخیر در بازگرداندن کتاب، به ازای هر کتاب و هر روز "
                "تأخیر مبلغ ۲ هزار تومان جریمه دریافت می‌شود. مجموع جریمه "
                "برای هر عضو نمی‌تواند از ۱۰۰ هزار تومان بیشتر شود.",
                True
            )

            add_paragraph(
                document,
                "اگر کتاب بیش از ۳۰ روز پس از پایان مهلت امانت بازگردانده نشود، "
                "کتاب مفقودشده تلقی خواهد شد و عضو مسئول جبران خسارت طبق "
                "مقررات دانشگاه است.",
                True
            )

        if heading == "۶. خدمات چاپ و اسکن":
            add_table(
                document,
                ["نوع خدمت", "هزینه هر صفحه"],
                [
                    ["چاپ سیاه‌وسفید", "۱٬۵۰۰ تومان"],
                    ["چاپ رنگی", "۶٬۰۰۰ تومان"]
                ],
                True
            )

    output_path = OUTPUT_DIR / "sample_library_guide.fa.docx"
    document.save(output_path)

    print(f"Persian document created: {output_path}")


def create_english_document():
    document = Document()
    configure_document(document, False)

    title = document.add_heading(
        "University Library Rules and Services Guide",
        0
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_paragraph(
        document,
        "This document provides information about library services, "
        "membership rules, borrowing conditions, digital resources, "
        "and regulations for using the university library.",
        False
    )

    sections = [
        (
            "1. Library Opening Hours",
            [
                "The university library is open from 8:00 AM to 6:00 PM "
                "Saturday through Wednesday. On Thursdays, the library "
                "operates from 8:00 AM to 1:00 PM. The library is closed "
                "on Fridays and official public holidays.",
                "Printing and scanning services are available until 5:30 PM "
                "on working days. Visitors should submit their printing "
                "and scanning requests before this time."
            ]
        ),
        (
            "2. Library Membership",
            [
                "Students must present a valid student ID card to become "
                "library members. The initial membership card issuance fee "
                "is 100,000 tomans. Membership renewal in subsequent years "
                "is free of charge.",
                "A valid membership card is required to borrow books. "
                "Members must present their card to the circulation desk "
                "when borrowing library materials."
            ]
        ),
        (
            "3. Book Borrowing Rules",
            [
                "The number of books that members can borrow and the "
                "borrowing period depend on their academic level or "
                "professional position."
            ]
        ),
        (
            "4. Digital Services and Resources",
            [
                "Library members can access digital resources and the "
                "university's academic databases. Remote access to these "
                "resources is available through the student portal.",
                "A university username and password are required to access "
                "the portal and use digital resources. These credentials "
                "must be kept confidential and must not be shared with others."
            ]
        ),
        (
            "5. Study Hall",
            [
                "The library study hall is located on the second floor. "
                "Each student can reserve the study hall for a maximum "
                "of two hours per day through the library's internal system.",
                "If a student needs to cancel a reservation, the cancellation "
                "must be submitted at least one hour before the reserved time "
                "so that other students can use the available space.",
                "Silence must be maintained in the study hall. Eating and "
                "drinking are not permitted, and users must avoid disturbing "
                "other students."
            ]
        ),
        (
            "6. Printing and Scanning Services",
            [
                "The library provides black-and-white printing, color "
                "printing, and document scanning services. Printing fees "
                "depend on the selected printing type.",
                "Printing services are available from Saturday through "
                "Thursday until 5:30 PM. Students who need to print more "
                "than 50 pages are advised to submit their files in advance."
            ]
        ),
        (
            "7. Educational Workshops",
            [
                "The library periodically organizes workshops to improve "
                "students' research skills. Topics include academic searching, "
                "source evaluation, citation methods, and reference management.",
                "Workshop registration must be completed at least three days "
                "before the event. Each workshop has a maximum capacity of "
                "20 participants. Registration priority is given to students "
                "who submit their requests earlier."
            ]
        ),
        (
            "8. General Library Regulations",
            [
                "All visitors must carry their membership cards and follow "
                "the library regulations concerning silence, order, and "
                "the proper care of library property.",
                "Food and drinks are not allowed in the study hall. Members "
                "are responsible for compensating the library for any damage "
                "they cause to books, equipment, or other library property."
            ]
        ),
        (
            "9. Contact Information",
            [
                "For assistance with membership, book borrowing, digital "
                "resources, or other services, visitors can contact the "
                "library information desk or use the university support system.",
                "No direct telephone number for the library is provided "
                "in this document."
            ]
        )
    ]

    for heading, paragraphs in sections:
        add_heading(document, heading, 1, False)

        for paragraph in paragraphs:
            add_paragraph(document, paragraph, False)

        if heading == "3. Book Borrowing Rules":
            add_table(
                document,
                ["Member Category", "Maximum Books", "Borrowing Period"],
                [
                    ["Undergraduate Students", "3 books", "14 days"],
                    ["Master's Students", "5 books", "21 days"],
                    ["PhD Students", "5 books", "21 days"],
                    ["Faculty Members", "8 books", "30 days"]
                ],
                False
            )

            add_paragraph(
                document,
                "Each borrowed book can be renewed only once. Renewal "
                "is permitted only if the book has not been reserved "
                "by another member.",
                False
            )

            add_paragraph(
                document,
                "A late return fine of 2,000 tomans is charged for each "
                "book per day. The total fine for each member cannot "
                "exceed 100,000 tomans.",
                False
            )

            add_paragraph(
                document,
                "If a book is not returned within 30 days after its due date, "
                "it is considered lost. The member is responsible for "
                "compensating the library according to university regulations.",
                False
            )

        if heading == "6. Printing and Scanning Services":
            add_table(
                document,
                ["Service Type", "Cost per Page"],
                [
                    ["Black-and-white printing", "1,500 tomans"],
                    ["Color printing", "6,000 tomans"]
                ],
                False
            )

    output_path = OUTPUT_DIR / "sample_library_guide.en.docx"
    document.save(output_path)

    print(f"English document created: {output_path}")


if __name__ == "__main__":
    create_persian_document()
    create_english_document()

    print("Both sample documents have been generated successfully.")
