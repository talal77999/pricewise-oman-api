# دليل نشر تطبيق مقارنة الأسعار PriceWise عُمان

هذا الدليل يشرح كيفية نشر تطبيق مقارنة الأسعار على منصات استضافة مجانية.

## المتطلبات الأساسية

1. حساب GitHub
2. حساب Netlify (للواجهة الأمامية)
3. حساب Render (للخادم الخلفي)
4. حساب Supabase (لقاعدة البيانات)

## خطوات النشر

### 1. إعداد قاعدة البيانات على Supabase

1. قم بإنشاء حساب على [Supabase](https://supabase.com/) إذا لم يكن لديك حساب بالفعل
2. أنشئ مشروعًا جديدًا
3. انتقل إلى قسم "SQL Editor" وقم بتنفيذ محتوى ملف `supabase_schema.sql`
4. احفظ عنوان URL للمشروع ومفتاح API (ستحتاجهما لاحقًا)

### 2. نشر الخادم الخلفي على Render

1. قم بإنشاء حساب على [Render](https://render.com/) إذا لم يكن لديك حساب بالفعل
2. انقر على "New +" واختر "Web Service"
3. اختر "Build and deploy from a Git repository"
4. اربط حساب GitHub الخاص بك واختر المستودع الذي يحتوي على الكود
5. قم بتكوين الخدمة:
   - اسم: `pricewise-oman-api`
   - بيئة التشغيل: Python
   - أمر البناء: `pip install -r requirements.txt`
   - أمر البدء: `python api_supabase.py`
   - خطة: Free
6. أضف متغيرات البيئة التالية:
   - `SUPABASE_URL`: عنوان URL لمشروع Supabase
   - `SUPABASE_KEY`: مفتاح API لمشروع Supabase
   - `JWT_SECRET`: مفتاح سري من اختيارك لتشفير رموز JWT
7. انقر على "Create Web Service"

### 3. نشر الواجهة الأمامية على Netlify

1. قم بإنشاء حساب على [Netlify](https://www.netlify.com/) إذا لم يكن لديك حساب بالفعل
2. انقر على "New site from Git"
3. اختر GitHub كمزود Git واختر المستودع الخاص بك
4. قم بتكوين إعدادات النشر:
   - فرع: `main`
   - دليل النشر: `frontend`
   - أمر البناء: (اتركه فارغًا)
5. انقر على "Deploy site"
6. بعد اكتمال النشر، انتقل إلى "Site settings" > "Domain management" لتخصيص اسم النطاق الفرعي

### 4. إعداد GitHub Actions لتحديث الأسعار

1. في مستودع GitHub الخاص بك، انتقل إلى قسم "Actions"
2. انقر على "New workflow"
3. اختر "set up a workflow yourself"
4. انسخ محتوى ملف `github_workflow.yml` إلى المحرر
5. أضف الأسرار التالية في إعدادات المستودع (Settings > Secrets > Actions):
   - `SUPABASE_URL`: عنوان URL لمشروع Supabase
   - `SUPABASE_KEY`: مفتاح API لمشروع Supabase
6. انقر على "Commit changes"

## تحديث عناوين API

بعد نشر الخادم الخلفي على Render، ستحتاج إلى تحديث عنوان API في ملفات الواجهة الأمامية:

1. افتح ملف `index.html` وملفات HTML أخرى
2. ابحث عن `const API_URL = 'https://your-render-app.onrender.com/api'`
3. استبدله بعنوان URL الفعلي للخدمة المنشورة على Render
4. أعد نشر الواجهة الأمامية

## الصيانة والتحديث

### تحديث البيانات

- يتم تحديث بيانات الأسعار تلقائيًا كل يوم من خلال GitHub Actions
- يمكنك تشغيل التحديث يدويًا من خلال قسم "Actions" في GitHub

### مراقبة الخدمات

- Render: يوفر لوحة تحكم لمراقبة استخدام الموارد والسجلات
- Supabase: يمكنك مراقبة استخدام قاعدة البيانات من خلال لوحة التحكم
- Netlify: يوفر إحصاءات حول زيارات الموقع والنشر

### حدود الخطط المجانية

- Render: 750 ساعة مجانية شهريًا، وضع السكون بعد 15 دقيقة من عدم النشاط
- Supabase: 500 ميجابايت تخزين، 100,000 صف، 2 جيجابايت نقل بيانات شهريًا
- Netlify: 100 جيجابايت نقل بيانات شهريًا، 300 دقيقة بناء شهريًا

## استكشاف الأخطاء وإصلاحها

### مشاكل الخادم الخلفي

- تحقق من سجلات Render للاطلاع على أي أخطاء
- تأكد من صحة متغيرات البيئة

### مشاكل قاعدة البيانات

- تحقق من سجلات Supabase
- تأكد من تنفيذ جميع استعلامات SQL بشكل صحيح

### مشاكل الواجهة الأمامية

- افتح وحدة تحكم المتصفح للتحقق من أي أخطاء JavaScript
- تأكد من أن عنوان API صحيح في ملفات الواجهة الأمامية

## الترقية إلى خطط مدفوعة

إذا نما التطبيق وتجاوز حدود الخطط المجانية، فكر في الترقية إلى:

- Render: خطة Individual ($7/شهر) للحصول على خدمة بدون وضع السكون
- Supabase: خطة Pro ($25/شهر) للحصول على مساحة تخزين وحدود استخدام أكبر
- Netlify: خطة Pro ($19/شهر) للحصول على مزيد من وقت البناء ونقل البيانات
