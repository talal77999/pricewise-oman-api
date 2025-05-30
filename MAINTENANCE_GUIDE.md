# دليل صيانة تطبيق مقارنة الأسعار PriceWise عُمان

هذا الدليل يوفر إرشادات للحفاظ على تطبيق مقارنة الأسعار وتحديثه بعد النشر على منصات الاستضافة المجانية.

## المراقبة الدورية

### قاعدة البيانات (Supabase)

- **مراقبة أسبوعية**:
  - تحقق من استخدام التخزين (الحد المجاني: 500 ميجابايت)
  - تحقق من عدد الصفوف (الحد المجاني: 100,000 صف)
  - تحقق من استخدام نقل البيانات (الحد المجاني: 2 جيجابايت شهريًا)

- **مراقبة شهرية**:
  - قم بتنظيف البيانات القديمة غير الضرورية
  - تحقق من أداء الاستعلامات وقم بتحسين المؤشرات إذا لزم الأمر

### الخادم الخلفي (Render)

- **مراقبة أسبوعية**:
  - تحقق من سجلات الخادم للأخطاء
  - تحقق من استخدام ساعات الخدمة (الحد المجاني: 750 ساعة شهريًا)

- **مراقبة شهرية**:
  - تحقق من أداء API وأوقات الاستجابة
  - تحقق من استخدام الذاكرة والمعالج

### الواجهة الأمامية (Netlify)

- **مراقبة أسبوعية**:
  - تحقق من سجلات النشر للأخطاء
  - تحقق من استخدام نقل البيانات (الحد المجاني: 100 جيجابايت شهريًا)

- **مراقبة شهرية**:
  - تحقق من أداء الموقع باستخدام أدوات مثل Google PageSpeed Insights
  - تحقق من توافق المتصفح وتجربة المستخدم على مختلف الأجهزة

### GitHub Actions

- **مراقبة أسبوعية**:
  - تحقق من سجلات تنفيذ سير العمل
  - تأكد من نجاح تحديثات البيانات اليومية

- **مراقبة شهرية**:
  - تحقق من استخدام دقائق GitHub Actions (الحد المجاني: 2000 دقيقة شهريًا)
  - قم بتحسين سير العمل لتقليل وقت التنفيذ إذا لزم الأمر

## تحديث البيانات

### تحديث بيانات المنتجات

- يتم تحديث بيانات المنتجات والأسعار تلقائيًا كل يوم من خلال GitHub Actions
- للتحديث اليدوي:
  1. انتقل إلى مستودع GitHub
  2. اذهب إلى قسم "Actions"
  3. اختر سير عمل "Update Price Data"
  4. انقر على "Run workflow"

### إضافة متاجر جديدة

لإضافة متجر جديد إلى التطبيق:

1. أضف بيانات المتجر إلى جدول `retailers` في Supabase
2. قم بإنشاء ملف scraper جديد على غرار `lulu_scraper_supabase.py`
3. أضف المتجر الجديد إلى سير عمل GitHub Actions
4. قم بتحديث واجهة المستخدم لعرض المتجر الجديد

## تحديث التطبيق

### تحديث الخادم الخلفي

1. قم بتحديث الكود في المستودع المحلي
2. ادفع التغييرات إلى GitHub
3. سيقوم Render تلقائيًا بإعادة نشر الخدمة

أو للتحديث اليدوي:

1. انتقل إلى لوحة تحكم Render
2. اختر خدمة الويب الخاصة بك
3. انقر على "Manual Deploy" > "Deploy latest commit"

### تحديث الواجهة الأمامية

1. قم بتحديث ملفات HTML/CSS/JavaScript في المستودع المحلي
2. ادفع التغييرات إلى GitHub
3. سيقوم Netlify تلقائيًا بإعادة نشر الموقع

أو للتحديث اليدوي:

1. انتقل إلى لوحة تحكم Netlify
2. اختر موقعك
3. انتقل إلى "Deploys" وانقر على "Trigger deploy"

### تحديث قاعدة البيانات

لتحديث هيكل قاعدة البيانات:

1. قم بإنشاء ملف SQL جديد مع التغييرات المطلوبة
2. انتقل إلى لوحة تحكم Supabase > "SQL Editor"
3. قم بتنفيذ استعلامات SQL للتحديث
4. قم بتحديث كود التطبيق ليتوافق مع التغييرات

## النسخ الاحتياطي واستعادة البيانات

### النسخ الاحتياطي لقاعدة البيانات

قم بإجراء نسخ احتياطي شهري لقاعدة البيانات:

1. انتقل إلى لوحة تحكم Supabase > "Database"
2. انقر على "Backups"
3. انقر على "Download backup"

### استعادة قاعدة البيانات

لاستعادة قاعدة البيانات من نسخة احتياطية:

1. انتقل إلى لوحة تحكم Supabase > "SQL Editor"
2. قم بتنفيذ استعلامات SQL لاستعادة البيانات من النسخة الاحتياطية

## التعامل مع المشاكل الشائعة

### الخادم الخلفي في وضع السكون

في الخطة المجانية من Render، يدخل الخادم في وضع السكون بعد 15 دقيقة من عدم النشاط. للتعامل مع هذا:

1. قم بإعداد "health check" يستدعي الخادم كل 14 دقيقة
2. أو قم بالترقية إلى خطة مدفوعة لتجنب وضع السكون

### تجاوز حدود الخطة المجانية

إذا اقتربت من تجاوز حدود الخطة المجانية:

1. **Supabase**:
   - قم بتنظيف البيانات القديمة
   - قم بضغط البيانات المخزنة
   - قم بالترقية إلى خطة Pro ($25/شهر)

2. **Render**:
   - قم بتحسين كود الخادم لتقليل استخدام الموارد
   - قم بالترقية إلى خطة Individual ($7/شهر)

3. **Netlify**:
   - قم بضغط الصور وملفات JavaScript/CSS
   - قم بتنفيذ التخزين المؤقت بشكل فعال
   - قم بالترقية إلى خطة Pro ($19/شهر)

### مشاكل أداء التطبيق

إذا كان التطبيق بطيئًا:

1. قم بتحسين استعلامات قاعدة البيانات
2. قم بتنفيذ التخزين المؤقت للبيانات المتكررة
3. قم بتحسين أداء الواجهة الأمامية (ضغط الصور، تقليل حجم JavaScript)
4. قم بتنفيذ تحميل البيانات الكسول (lazy loading)

## توسيع نطاق التطبيق

### إضافة ميزات جديدة

لإضافة ميزات جديدة إلى التطبيق:

1. قم بتطوير الميزة محليًا واختبارها
2. قم بتحديث قاعدة البيانات إذا لزم الأمر
3. قم بتحديث الخادم الخلفي والواجهة الأمامية
4. قم بنشر التحديثات على جميع المنصات

### الترقية إلى خطط مدفوعة

عندما ينمو التطبيق، فكر في الترقية إلى خطط مدفوعة:

1. **Supabase Pro** ($25/شهر):
   - 8 جيجابايت تخزين
   - 100 جيجابايت نقل بيانات شهريًا
   - نسخ احتياطي يومي

2. **Render Individual** ($7/شهر):
   - بدون وضع السكون
   - أداء أفضل
   - 750 ساعة شهريًا مضمونة

3. **Netlify Pro** ($19/شهر):
   - 400 جيجابايت نقل بيانات شهريًا
   - 1000 دقيقة بناء شهريًا
   - تحليلات متقدمة

## جدول الصيانة الدوري

| المهمة | التكرار | الوصف |
|--------|---------|-------|
| مراقبة سجلات الأخطاء | أسبوعيًا | تحقق من سجلات الخادم الخلفي والواجهة الأمامية للأخطاء |
| مراقبة استخدام الموارد | أسبوعيًا | تحقق من استخدام التخزين ونقل البيانات وساعات الخدمة |
| تحديث البيانات يدويًا | عند الحاجة | قم بتشغيل سير عمل GitHub Actions يدويًا لتحديث البيانات |
| تنظيف البيانات | شهريًا | قم بإزالة البيانات القديمة غير الضرورية |
| نسخ احتياطي لقاعدة البيانات | شهريًا | قم بتنزيل نسخة احتياطية من قاعدة البيانات |
| تحسين الأداء | ربع سنوي | قم بتحليل وتحسين أداء التطبيق |
| مراجعة حدود الخطط | ربع سنوي | قم بمراجعة استخدام الموارد وفكر في الترقية إذا لزم الأمر |
