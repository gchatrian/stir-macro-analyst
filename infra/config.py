# infra/config.py

import os
from dotenv import load_dotenv

load_dotenv()

BBG_HOST = os.getenv("BBG_HOST", "localhost")
BBG_PORT = int(os.getenv("BBG_PORT", "8194"))

POLICY_RATE_MAPPING = {
    "USD": {
        "ticker": "FDTR Index",
        "name": "Federal Funds Target Rate",
        "central_bank": "Federal Reserve"
    },
    "EUR": {
        "ticker": "EURR002W Index",
        "name": "ECB Deposit Facility Rate",
        "central_bank": "European Central Bank"
    },
    "GBP": {
        "ticker": "UKBRBASE Index",
        "name": "Bank of England Base Rate",
        "central_bank": "Bank of England"
    }
}

DISCOUNT_CURVE_MAPPING = {
    "USD": [
        "USOSFR1Z BGN CURNCY",
        "USOSFR2Z BGN CURNCY",
        "USOSFR3Z BGN CURNCY",
        "USOSFRA BGN CURNCY",
        "USOSFRB BGN CURNCY",
        "USOSFRC BGN CURNCY",
        "USOSFRD BGN CURNCY",
        "USOSFRE BGN CURNCY",
        "USOSFRF BGN CURNCY",
        "USOSFRG BGN CURNCY",
        "USOSFRH BGN CURNCY",
        "USOSFRI BGN CURNCY",
        "USOSFRJ BGN CURNCY",
        "USOSFRK BGN CURNCY",
        "USOSFR1 BGN CURNCY",
        "USOSFR1F BGN CURNCY",
        "USOSFR2 BGN CURNCY",
        "USOSFR3 BGN CURNCY"
    ],
    "EUR": [
        "EESWE1Z BGN CURNCY",
        "EESWE2Z BGN CURNCY",
        "EESWE3Z BGN CURNCY",
        "EESWEA BGN CURNCY",
        "EESWEB BGN CURNCY",
        "EESWEC BGN CURNCY",
        "EESWED BGN CURNCY",
        "EESWEE BGN CURNCY",
        "EESWEF BGN CURNCY",
        "EESWEG BGN CURNCY",
        "EESWEH BGN CURNCY",
        "EESWEI BGN CURNCY",
        "EESWEJ BGN CURNCY",
        "EESWEK BGN CURNCY",
        "EESWE1 BGN CURNCY",
        "EESWE1F BGN CURNCY",
        "EESWE2 BGN CURNCY",
        "EESWE3 BGN CURNCY"
    ],
    "GBP": [
        "BPSWS1Z BGN CURNCY",
        "BPSWS2Z BGN CURNCY",
        "BPSWS3Z BGN CURNCY",
        "BPSWSA BGN CURNCY",
        "BPSWSB BGN CURNCY",
        "BPSWSC BGN CURNCY",
        "BPSWSD BGN CURNCY",
        "BPSWSE BGN CURNCY",
        "BPSWSF BGN CURNCY",
        "BPSWSG BGN CURNCY",
        "BPSWSH BGN CURNCY",
        "BPSWSI BGN CURNCY",
        "BPSWSJ BGN CURNCY",
        "BPSWSK BGN CURNCY",
        "BPSWS1 BGN CURNCY",
        "BPSWS1F BGN CURNCY",
        "BPSWS2 BGN CURNCY",
        "BPSWS3 BGN CURNCY"
    ]
}