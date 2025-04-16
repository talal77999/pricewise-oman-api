#!/bin/bash

# Script to prepare and package the PriceWise Oman application for deployment to free hosting platforms

echo "Preparing PriceWise Oman for deployment..."

# Create deployment directories
mkdir -p deployment_package/frontend
mkdir -p deployment_package/backend
mkdir -p deployment_package/database
mkdir -p deployment_package/github_actions

# Copy frontend files
echo "Packaging frontend files for Netlify..."
cp -r deployment/frontend/* deployment_package/frontend/
cp deployment/netlify.toml deployment_package/frontend/

# Copy backend files
echo "Packaging backend files for Render..."
cp deployment/api_supabase.py deployment_package/backend/
cat > deployment_package/backend/requirements.txt << EOF
flask==3.1.0
flask-cors==5.0.1
supabase==2.0.0
python-dotenv==1.1.0
pyjwt==2.8.0
werkzeug==3.1.3
gunicorn==23.0.0
requests==2.32.3
EOF

# Copy database files
echo "Packaging database files for Supabase..."
cp deployment/supabase_schema.sql deployment_package/database/

# Copy GitHub Actions workflow
echo "Packaging GitHub Actions workflow..."
mkdir -p deployment_package/github_actions/.github/workflows
cp deployment/github_workflow.yml deployment_package/github_actions/.github/workflows/update_prices.yml
cp deployment/lulu_scraper_supabase.py deployment_package/github_actions/

# Copy deployment guide
cp deployment/DEPLOYMENT_GUIDE.md deployment_package/

# Create a README file
cat > deployment_package/README.md << EOF
# PriceWise Oman - مقارنة الأسعار في عُمان

تطبيق لمقارنة الأسعار بين متاجر متعددة في عُمان، بما في ذلك لولو هايبر ماركت وكارفور ونستو.

## محتويات الحزمة

- **frontend/**: ملفات الواجهة الأمامية للنشر على Netlify
- **backend/**: ملفات الخادم الخلفي للنشر على Render
- **database/**: ملفات قاعدة البيانات للنشر على Supabase
- **github_actions/**: سير عمل GitHub Actions لتحديث الأسعار تلقائيًا
- **DEPLOYMENT_GUIDE.md**: دليل مفصل لنشر التطبيق

## متطلبات النشر

- حساب GitHub
- حساب Netlify (للواجهة الأمامية)
- حساب Render (للخادم الخلفي)
- حساب Supabase (لقاعدة البيانات)

## كيفية النشر

يرجى الاطلاع على ملف DEPLOYMENT_GUIDE.md للحصول على تعليمات مفصلة حول كيفية نشر التطبيق.
EOF

# Create a .env.example file for backend
cat > deployment_package/backend/.env.example << EOF
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_jwt_secret
PORT=5000
EOF

# Create a Procfile for Render
cat > deployment_package/backend/Procfile << EOF
web: gunicorn api_supabase:app
EOF

# Create a zip file of the deployment package
echo "Creating deployment zip file..."
cd deployment_package
zip -r ../pricewise_oman_deployment.zip .
cd ..

echo "Deployment package created: pricewise_oman_deployment.zip"
echo "Follow the instructions in DEPLOYMENT_GUIDE.md to deploy the application."
