# infra/bbg_client.py

import blpapi
import pandas as pd
from datetime import datetime
from typing import Optional, List, Any


class BloombergConnection:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.session: Optional[blpapi.Session] = None
        
    def __enter__(self) -> 'BloombergConnection':
        session_options = blpapi.SessionOptions()
        session_options.setServerHost(self.host)
        session_options.setServerPort(self.port)
        
        self.session = blpapi.Session(session_options)
        
        if not self.session.start():
            raise ConnectionError("Failed to start Bloomberg session")
        if not self.session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdata service")
            
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            self.session.stop()


def safe_get_element(field_data: Any, element_name: str, default: float = 0.0) -> float:
    try:
        return field_data.getElementAsFloat(element_name)
    except Exception:
        return default


def fetch_reference_data(
    connection: BloombergConnection,
    securities: List[str],
    fields: List[str],
    date: Optional[str] = None
) -> pd.DataFrame:
    
    ref_data_service = connection.session.getService("//blp/refdata")
    request = ref_data_service.createRequest("ReferenceDataRequest")
    
    for security in securities:
        request.append("securities", security)
    for field in fields:
        request.append("fields", field)
    
    if date:
        request.set("overrides", [{"fieldId": "REFERENCE_DATE", "value": date}])
    
    connection.session.sendRequest(request)
    
    data = {field: [] for field in fields}
    data['security'] = []
    
    while True:
        event = connection.session.nextEvent()
        if event.eventType() == blpapi.Event.RESPONSE:
            for msg in event:
                if msg.hasElement("securityData"):
                    security_data = msg.getElement("securityData")
                    for i in range(security_data.numValues()):
                        security = security_data.getValueAsElement(i)
                        data['security'].append(security.getElementAsString("security"))
                        
                        if security.hasElement("fieldData"):
                            field_data = security.getElement("fieldData")
                            for field in fields:
                                try:
                                    if field_data.hasElement(field):
                                        value = field_data.getElement(field).getValue()
                                        data[field].append(value)
                                    else:
                                        data[field].append(None)
                                except Exception:
                                    data[field].append(None)
            break
    
    return pd.DataFrame(data)


def fetch_historical_data(
    connection: BloombergConnection,
    security: str,
    field: str,
    start_date: str,
    end_date: str,
    period: str = "DAILY"
) -> pd.DataFrame:
    
    ref_data_service = connection.session.getService("//blp/refdata")
    request = ref_data_service.createRequest("HistoricalDataRequest")
    
    request.getElement("securities").appendValue(security)
    request.getElement("fields").appendValue(field)
    request.set("periodicityAdjustment", "ACTUAL")
    request.set("periodicitySelection", period)
    request.set("nonTradingDayFillOption", "NON_TRADING_WEEKDAYS")
    request.set("nonTradingDayFillMethod", "PREVIOUS_VALUE")
    request.set("startDate", start_date)
    request.set("endDate", end_date)
    request.set("maxDataPoints", 10000)
    
    connection.session.sendRequest(request)
    
    dates = []
    values = []
    
    while True:
        event = connection.session.nextEvent(500)
        for msg in event:
            if msg.hasElement("securityData"):
                field_data_array = msg.getElement("securityData").getElement("fieldData")
                for x in range(field_data_array.numValues()):
                    field_data = field_data_array.getValueAsElement(x)
                    dates.append(field_data.getElement("date").getValueAsDatetime())
                    values.append(safe_get_element(field_data, field))
        
        if event.eventType() == blpapi.Event.RESPONSE:
            break
    
    df = pd.DataFrame({'DATE': dates, field: values})
    df = df.set_index('DATE')
    return df


def fetch_option_chain(
    connection: BloombergConnection,
    futures_code: str
) -> List[str]:
    
    ref_data_service = connection.session.getService("//blp/refdata")
    request = ref_data_service.createRequest("ReferenceDataRequest")
    
    request.append("securities", futures_code)
    request.append("fields", "OPT_CHAIN")
    
    connection.session.sendRequest(request)
    
    option_tickers = []
    
    while True:
        event = connection.session.nextEvent()
        if event.eventType() == blpapi.Event.RESPONSE:
            for msg in event:
                if msg.hasElement("securityData"):
                    security_data = msg.getElement("securityData")
                    for i in range(security_data.numValues()):
                        security = security_data.getValueAsElement(i)
                        if security.hasElement("fieldData"):
                            field_data = security.getElement("fieldData")
                            if field_data.hasElement("OPT_CHAIN"):
                                option_chain = field_data.getElement("OPT_CHAIN")
                                for option in option_chain.values():
                                    option_tickers.append(
                                        option.getElementValue("Security Description")
                                    )
            break
    
    return option_tickers