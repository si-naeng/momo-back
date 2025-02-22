"""
Django settings for momo project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
from pathlib import Path

from django.urls import path

# environment
import environ
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, 'momo/../.env'))




# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-cqsdnni5y#x2kie7wpx!@^f_ps2r@%+wjcu9dzz0c26p%9d48u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'insight.apps.InsightConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",  # Next.js의 기본 개발 서버
#     "http://127.0.0.1:3000",  # Next.js가 로컬에서 실행되는 주소
# ]


ROOT_URLCONF = 'momo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'momo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

import os
from mongoengine import connect
from dotenv import load_dotenv
from urllib.parse import quote

# .env 파일 로드
load_dotenv()

# 환경 변수 읽기
db_name = os.getenv('MONGO_DB_NAME', 'momo')
hosts = os.getenv('MONGO_DB_HOST', 'localhost')  # 쉼표로 구분된 호스트 목록
port = os.getenv('MONGO_DB_PORT', '27017')
username = os.getenv('MONGO_DB_USERNAME', 'admin')
password = os.getenv('MONGO_DB_PASSWORD', 'k8spass#')  # URL 인코딩을 위해 변경할 필요 있음
replica_set = os.getenv('MONGO_DB_REPLICA_SET_PART', 'rs0')

# 비밀번호 URL 인코딩 (특수문자 처리)
encoded_password = quote(password)

# 호스트가 여러 개일 경우, 각 호스트와 포트를 함께 조합
host_part = ",".join([f"{host}:{port}" for host in hosts.split(",")])

# 인증 정보 설정
auth_part = f"{username}:{encoded_password}@" if username and encoded_password else ""

# replicaSet 옵션 추가
replica_set_part = f"&replicaSet={replica_set}" if replica_set else ""

# 최종 MongoDB URI 생성
MONGO_URI = f"mongodb://{auth_part}{host_part}/{db_name}?authSource=admin{replica_set_part}"

# MongoDB 연결
print(MONGO_URI)
# MongoDB 연결
connect(host=MONGO_URI)


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# environment
import environ
import os

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, 'momo/../.env'))


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'insight.authentication.CognitoAuthentication',  # CognitoAuthentication 추가
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

APPEND_SLASH = False

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'