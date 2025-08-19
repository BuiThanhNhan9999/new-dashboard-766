import json
import requests
import os
from datetime import datetime
import base64
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class APIEndpoints(Enum):
    """Enum chứa các API endpoints"""
    KGG_STATISTIC = 'https://apidvc.angiang.gov.vn/pa/dossier-statistic/--statistic-agency-kgg'
    KGG_ONLINE_REPORT = 'https://apidvc.angiang.gov.vn/pa/kgg-dossier-statistic/--kgg-dossier-report-online'
    DIGITIZATION_REPORT = 'https://apidvc.angiang.gov.vn/pa/kgg-digitize/digitization-by-agency'
    AGENCY_NAME_CODE = 'https://apidvc.angiang.gov.vn/ba/agency/name+code'  # <--- Đã bổ sung

@dataclass
class APIConfig:
    """Configuration class cho API"""
    DEFAULT_AGENCY_ID = '6852c2f06d65221a70e5b26b'
    # Agency levels
    AGENCY_LEVEL_0 = '5f6b17984e1bd312a6f3ae4b'
    AGENCY_LEVEL_1 = '5f7dade4b80e603d5300dcc4'
    AGENCY_LEVEL_2 = '5f6b177a4e1bd312a6f3ae4a'
    # Procedure levels
    PROCEDURE_LEVEL_4 = '62b529f524023d508ef38fc0'
    PROCEDURE_LEVEL_3 = '62b529c424023d508ef38fbd'
    PROCEDURE_LEVEL_2 = '62b52a0224023d508ef38fc1'
    DIGITIZATION_LEVELS = '5f39f42d5224cf235e134c5a,5f39f4155224cf235e134c59,5febfe2995002b5c79f0fc9f'
    CONNECT_TIMEOUT = 30
    READ_TIMEOUT = 180
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

class TokenManager:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('API_TOKEN', self._get_default_token())

    @staticmethod
    def _get_default_token() -> str:
        # Replace by your default token
        return "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJqazlObnpLTWVTeTF6Wk53RW1WMHVzY0FFcWFicTY4MGh5ZFpqY2Q0Wl9zIn0.eyJleHAiOjE3NTU1OTU3MjIsImlhdCI6MTc1NTUwOTMyMiwiYXV0aF90aW1lIjoxNzU1NTA5MjkyLCJqdGkiOiI2MjZhZjU0Yi1kYzJkLTRjOTgtOTkzYi0yODZmMDlhYzkyZTkiLCJpc3MiOiJodHRwczovL3Nzb2R2Yy5hbmdpYW5nLmdvdi52bi9hdXRoL3JlYWxtcy9kaWdvIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6ImY6YzA5OGZmOWYtZGM5ZS00MmI3LTkxNmMtZGI4MWE0YjhmZDc4OnRxcGh1Yy5za2hjbkBhbmdpYW5nLmdvdi52biIsInR5cCI6IkJlYXJlciIsImF6cCI6IndlYi1vbmVnYXRlIiwibm9uY2UiOiJiNGFlNjVlMi1jMWE5LTQ5NjYtYWNjOC1lYjZlMTA2ODZiNWEiLCJzZXNzaW9uX3N0YXRlIjoiNTIyMzUwZTQtNTI5Yy00MmJkLTg3ZjgtYzBlYzQ1NDI0MzA1IiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2FwaWR2Yy5hbmdpYW5nLmdvdi52biIsImh0dHBzOi8vbW90Y3VhLmFuZ2lhbmcuZ292LnZuIiwiaHR0cDovL2xvY2FsaG9zdDo0MjAwIl0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBlbWFpbCBwcm9maWxlIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJnZW5kZXIiOiIxIiwiZ3JvdXBzIjpbImxhbmhkYW9fc290dHR0Iiwic3R0dHR4dWx5IiwidHJ1bmd0YW1kaWV1aGFuaCIsInVibmR0aW5oIiwidGVzdGdyb3VwIiwic290aG9uZ3RpbnZhdHJ1eWVudGhvbmciLCJociIsInN0dHR0dGllcG5oYW4iLCJzdHR0dGR1eWV0IiwiY2FuYm9feHVseV9oaWVudHJ1b25nIl0sIkFsbG93V2hpdGVsaXN0IjpbImh0dHBzOi8vYXBpZHZjLmFuZ2lhbmcuZ292LnZuIl0sInByZWZlcnJlZF91c2VybmFtZSI6InRxcGh1Yy5za2hjbkBhbmdpYW5nLmdvdi52biIsImV4cGVyaWVuY2UiOiI2ODU0YzZmNTJjODU5NDJiMDJkMDU0MTQsNjg1YTY2OTkxOGM2ZWYyZWJiMjZjOTg3LDY4NTJjMmYwNmQ2NTIyMWE3MGU1YjI2YiIsImdpdmVuX25hbWUiOiJUcsawxqFuZyBRdWFuZyBQaOG7pWMiLCJ0eXBlIjoiMyIsImFjY291bnRfaWQiOiI2ODY2YTA3ZmIxN2JhYjJiMjE4ZWNmMWYiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiQUNUSVZJVElfTU9ERUxFUiIsInN0b3JhZ2U0RW1wIiwiaW50ZWdyYXRlRGlnaXRhbFNpZ25hdHVyZSIsIkNCWEwtaUdBVEUiLCJDVERUIiwiQUNUSVZJVElfQURNSU4iLCJBQ1RJVklUSV9VU0VSIiwiQUNUSVZJVElfUFJPQ0VTUyJdfSwidXNlcl9pZCI6IjY4NjZhMDdmYmNhZGM0MDFkM2UxYzViMCIsInBlcm1pc3Npb25zIjpbeyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJhY3Rpdml0aU1vZGVsZXIifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJjaHVuZ1RodWNBY2NlcHRlciJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6ImludGVncmF0ZURpZ2l0YWxTaWduYXR1cmUifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJpc29TdGF0aXN0aWNzIn19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoiaXNvU3RhdGlzdGljc0J5U2VjdG9yIn19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoiaXNvU3RhdGlzdGljc0Z1bGxBZ2VuY3kifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJtYURpZ2l0YWxTaWduYXR1cmVDb25maWcifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJtYW5hZ2VEaWdvIn19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoib25lR2F0ZUNhbmNlbERvc3NpZXJSZXBvcnQifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJvbmVHYXRlRG9zc2llckF1dGhNYW5hZ2VyIn19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoib25lR2F0ZURvc3NpZXJDYW5jZWwifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJvbmVHYXRlRG9zc2llckZlZUtHR1JlcG9ydCJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6Im9uZUdhdGVEb3NzaWVyTG9va3VwIn19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoib25lR2F0ZURvc3NpZXJMb29rdXBCeUFnZW5jeSJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6Im9uZUdhdGVEb3NzaWVyTG9va3VwUGVyc29uYWwifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJvbmVHYXRlRG9zc2llck9ubGluZUtHR1JlcG9ydCJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6Im9uZUdhdGVEb3NzaWVyUHJvY2Vzc2luZyJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6Im9uZUdhdGVEdWVEb3NzaWVyUmVwb3J0In19LHsicGVybWlzc2lvbiI6eyJjb2RlIjoib25lR2F0ZUtHR0RpZ2l0aXphdGlvbkRvc3NpZXJSZXBvcnQifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJvbmVHYXRlTG9nYm9va1N0YXRpc3RpY3MifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJwZXJtaXNzaW9uRG9zc2llcktHRyJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6InN0YXRpc3RpY2FsQWdlbmN5RG9zc2llcktHRyJ9fSx7InBlcm1pc3Npb24iOnsiY29kZSI6InN0YXRpc3RpY2FsQWdlbmN5RG9zc2llcl9LR0cifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJzdGF0aXN0aWNhbEFnZW5jeURvc3NpZXJfTGFuZF9LR0cifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJzdGF0aXN0aWNhbERvc3NpZXJLR0cifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJzdGF0aXN0aWNhbFByb2NlZHVyZURvc3NpZXJLR0cifX0seyJwZXJtaXNzaW9uIjp7ImNvZGUiOiJzdG9yYWdlNEVtcCJ9fV0sIm5hbWUiOiJUcsawxqFuZyBRdWFuZyBQaOG7pWMiLCJkZXBsb3ltZW50X2lkIjoiNjI4YjJlMGVjNzY0YWM2NTEwMmFjM2RjIiwiZW1haWwiOiJbe1widmFsdWVcIiA6IFwidHFwaHVjLnNraGNuQGFuZ2lhbmcuZ292LnZuXCJ9XSJ9.HKQj_kcZs4fD6TmS2kkqJ50SfcvHFObYE8aJw5APF1cOeRCFxNf1Bj_CIK0YRYaOgzgVdZvlGLDkHtIGzqtJYCt0ASGO9lraR7yrNsvXYHhIfhn9haz_9inV0NCuok_lwSMFR3Gix-vfaFPF2vU-3uvUZSWpMZpTQozY2xOprUzeOpaZrv9yxtl3E0wUedIemeWr250pIsj6MLh6X_8TW_EBWChTYf579yr-6mBBl903LDZOqGA4XIsqOScwfGMAf3OjLneKwy_w9UHj0c_yEwtwkP8ZU3KlMi5lFXXIJgvJU96VfmWZD9c4uaVRGD7pJzZvW4YSAV3C3zu3VsSpew"

    def is_valid(self) -> bool:
        if not self.token:
            print("❌ Không có token")
            return False
        try:
            parts = self.token.split('.')
            if len(parts) != 3:
                return False
            payload = json.loads(base64.b64decode(parts[1] + '=='))
            exp_time = payload.get('exp', 0)
            current_time = int(datetime.now().timestamp())
            if current_time > exp_time:
                print(f"❌ Token đã hết hạn lúc: {datetime.fromtimestamp(exp_time)}")
                return False
            else:
                remaining = exp_time - current_time
                print(f"✅ Token còn hiệu lực {remaining//3600} giờ {(remaining%3600)//60} phút")
                return True
        except Exception as e:
            print(f"❌ Lỗi kiểm tra token: {e}")
            return False

    def get_auth_header(self) -> Dict[str, str]:
        return {'Authorization': f'bearer {self.token}'}

class DateTimeUtils:
    @staticmethod
    def format_datetime(date_str: str, is_start: bool = True) -> str:
        if 'T' in date_str:
            return date_str
        if is_start:
            return f"{date_str}T00:00:00.000Z"
        else:
            return f"{date_str}T23:59:59.999Z"

    @staticmethod
    def format_datetime_online(date_str: str, is_start: bool = True) -> str:
        if 'T' in date_str:
            return date_str
        if is_start:
            return f"{date_str}T00:00:00.0Z"
        else:
            return f"{date_str}T23:59:59.0Z"

class HTTPSessionManager:
    @staticmethod
    def create_session() -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=APIConfig.MAX_RETRIES,
            status_forcelist=APIConfig.RETRY_STATUS_CODES,
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=APIConfig.BACKOFF_FACTOR,
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

class APIRequestHandler:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.session_manager = HTTPSessionManager()

    def _validate_token(self) -> bool:
        if not self.token_manager.is_valid():
            print("🔄 Vui lòng cập nhật token mới!")
            return False
        return True

    def _make_request(self, url: str, params: Dict[str, Any], description: str) -> Optional[Any]:
        session = self.session_manager.create_session()
        try:
            print(f"⏳ Đang gửi request {description}... (có thể mất vài phút)")
            start_time = time.time()
            # Đây là điểm then chốt: Gộp mọi header như code mẫu
            headers = {
                **self.token_manager.get_auth_header(),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'vi',
                'Authorization': self.token_manager.get_auth_header()['Authorization'],  # explicit
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            }
           
            response = session.get(
                url,
                headers=headers,
                params=params,
                timeout=(APIConfig.CONNECT_TIMEOUT, APIConfig.READ_TIMEOUT),
                stream=True
            )
            response.raise_for_status()
            elapsed_time = time.time() - start_time
            print(f"✅ Request {description} thành công! Thời gian: {elapsed_time:.2f}s")
            return response.json()
        except requests.RequestException as e:
            elapsed_time = time.time() - start_time
            print(f"❌ Lỗi khi gọi {description} sau {elapsed_time:.2f}s: {e}")
            return None
        finally:
            session.close()



    def _handle_http_error(self, error: requests.exceptions.HTTPError):
        status_code = error.response.status_code
        error_messages = {
            401: "🔐 Lỗi 401: Token hết hạn hoặc không hợp lệ",
            403: "🚫 Lỗi 403: Không có quyền truy cập",
            429: "🚦 Lỗi 429: Rate limit - đợi và thử lại"
        }
        if status_code in error_messages:
            print(error_messages[status_code])
        elif status_code >= 500:
            print(f"🔧 Lỗi server {status_code}: Vấn đề từ phía API")
        else:
            print(f"❌ HTTP Error {status_code}: {error}")

class KGGReportHandler(APIRequestHandler):
    def get_report(self, from_date: str, to_date: str, agency_id: str = None) -> Optional[Any]:
        if not self._validate_token():
            return None
        agency_id = agency_id or APIConfig.DEFAULT_AGENCY_ID
        from_date = DateTimeUtils.format_datetime(from_date, True)
        to_date = DateTimeUtils.format_datetime(to_date, False)
        print(f"📅 Truy vấn: {from_date} -> {to_date}")
        print(f"🏢 Agency: {agency_id}")
        params = {
            'agency-id': agency_id,
            'from-date': from_date,
            'to-date': to_date,
            'agencyLevel0': APIConfig.AGENCY_LEVEL_0,
            'agencyLevel1': APIConfig.AGENCY_LEVEL_1,
            'agencyLevel2': APIConfig.AGENCY_LEVEL_2,
            'procedureLevel4': APIConfig.PROCEDURE_LEVEL_4,
            'procedureLevel3': APIConfig.PROCEDURE_LEVEL_3,
            'procedureLevel2': APIConfig.PROCEDURE_LEVEL_2,
            'suppended-cancelled': 'true',
            'hide-agency-no-dossier': 'false',
            'isOnlineAttachResults': 'false',
            'isKGGReportCancel': 'true'
        }
        return self._make_request(APIEndpoints.KGG_STATISTIC.value, params, "KGG Report")

class KGGOnlineReportHandler(APIRequestHandler):
    def get_report_online(self, from_date: str, to_date: str, agency_id: str = None) -> Optional[Any]:
        if not self._validate_token():
            return None
        agency_id = agency_id or APIConfig.DEFAULT_AGENCY_ID
        from_date = DateTimeUtils.format_datetime_online(from_date, True)
        to_date = DateTimeUtils.format_datetime_online(to_date, False)
        print(f"📅 Truy vấn KGG Dossier: {from_date} -> {to_date}")
        print(f"🏢 Agency: {agency_id}")
        params = {
            'from-applied-date': from_date,
            'to-applied-date': to_date,
            'agency-id': agency_id,
            'agencyLevel0': APIConfig.AGENCY_LEVEL_0,
            'agencyLevel1': APIConfig.AGENCY_LEVEL_1,
            'agencyLevel2': APIConfig.AGENCY_LEVEL_2,
            'procedureLevel4': APIConfig.PROCEDURE_LEVEL_4,
            'procedureLevel3': APIConfig.PROCEDURE_LEVEL_3,
            'procedureLevel2': APIConfig.PROCEDURE_LEVEL_2,
            'is-ignore-free-dossier': 'true'
        }
        return self._make_request(APIEndpoints.KGG_ONLINE_REPORT.value, params, "KGG Online Report")

class DigitizationReportHandler(APIRequestHandler):
    def get_digitization_by_agency(self, from_date: str, to_date: str, ancestor_id: str = None) -> Optional[Any]:
        if not self._validate_token():
            return None
        ancestor_id = ancestor_id or APIConfig.DEFAULT_AGENCY_ID
        from_date = DateTimeUtils.format_datetime(from_date, True)
        to_date = DateTimeUtils.format_datetime(to_date, False)
        print(f"📅 Truy vấn Digitization: {from_date} -> {to_date}")
        print(f"🏢 Ancestor ID: {ancestor_id}")
        params = {
            'from': from_date,
            'to': to_date,
            'ancestor-id': ancestor_id,
            'list-level-id': APIConfig.DIGITIZATION_LEVELS,
            'agency-level-0': APIConfig.AGENCY_LEVEL_0,
            'agency-level-1': APIConfig.AGENCY_LEVEL_1,
            'agency-level-2': APIConfig.AGENCY_LEVEL_2
        }
        result = self._make_request(APIEndpoints.DIGITIZATION_REPORT.value, params, "Digitization Report")
        if result:
            data_length = len(result) if isinstance(result, (dict, list)) else 'unknown'
            print(f"📋 Đã nhận được dữ liệu digitization với {data_length} items")
        return result

class AgencyNameCodeHandler(APIRequestHandler):
    """Handler cho API lấy danh sách tên và mã cơ quan"""
    def get_agency_name_code_list(
        self, 
        tag_id: str = "5f6b17984e1bd312a6f3ae4b"  # giá trị mặc định cũ, có thể đổi
    ) -> Optional[Any]:
        if not self._validate_token():
            return None

        endpoint = "/ba/agency/name+code"
        url = APIEndpoints.AGENCY_NAME_CODE.value  # hoặc dùng trực tiếp endpoint nếu URL đầy đủ chưa có trong enum

        params = {
            "ancestor-id": "6852c2f06d65221a70e5b26b",
            "tag-id": tag_id,                # <- truyền tag-id vào đây
            "page": "0",
            "size": "2000"
        }

        print(f"📅 Truy vấn danh sách cơ quan cố định với endpoint: {endpoint} và params: {params}")
        return self._make_request(url, params, "Agency Name + Code List")



class APIClient:
    def __init__(self, token: Optional[str] = None):
        self.token_manager = TokenManager(token)
        self.kgg_handler = KGGReportHandler(self.token_manager)
        self.kgg_online_handler = KGGOnlineReportHandler(self.token_manager)
        self.digitization_handler = DigitizationReportHandler(self.token_manager)
        self.agency_name_code_handler = AgencyNameCodeHandler(self.token_manager)

    def get_kgg_report(self, from_date: str, to_date: str, agency_id: str = None) -> Optional[Any]:
        return self.kgg_handler.get_report(from_date, to_date, agency_id)
    def get_kgg_online_report(self, from_date: str, to_date: str, agency_id: str = None) -> Optional[Any]:
        return self.kgg_online_handler.get_report_online(from_date, to_date, agency_id)
    def get_digitization_report(self, from_date: str, to_date: str, ancestor_id: str = None) -> Optional[Any]:
        return self.digitization_handler.get_digitization_by_agency(from_date, to_date, ancestor_id)
    def get_agency_name_code_list(self,
                                 ancestor_id: str = APIConfig.DEFAULT_AGENCY_ID,
                                 tag_id: str = APIConfig.AGENCY_LEVEL_0,
                                 page: int = 0,
                                 size: int = 2000) -> Optional[Any]:
        return self.agency_name_code_handler.get_agency_name_code_list(tag_id)

# Entry point functions - tương thích với code cũ
def check_token_expiry(token: str) -> bool:
    token_manager = TokenManager(token)
    return token_manager.is_valid()

def get_report(from_date: str, to_date: str, agency_id: str = APIConfig.DEFAULT_AGENCY_ID) -> Optional[Any]:
    client = APIClient()
    return client.get_kgg_report(from_date, to_date, agency_id)

def get_report_online(from_date: str, to_date: str, agency_id: str = APIConfig.DEFAULT_AGENCY_ID) -> Optional[Any]:
    client = APIClient()
    return client.get_kgg_online_report(from_date, to_date, agency_id)

def get_digitization_by_agency(from_date: str, to_date: str, ancestor_id: str = APIConfig.DEFAULT_AGENCY_ID) -> Optional[Any]:
    client = APIClient()
    return client.get_digitization_report(from_date, to_date, ancestor_id)

def get_agency_name_code_list(ancestor_id: str = APIConfig.DEFAULT_AGENCY_ID,
                              tag_id: str = APIConfig.AGENCY_LEVEL_0,
                              page: int = 0,
                              size: int = 2000) -> Optional[Any]:
    client = APIClient()
    return client.get_agency_name_code_list()

def create_session_with_retries() -> requests.Session:
    return HTTPSessionManager.create_session()

def main():
    client = APIClient()
    # Test Agency Name + Code
    result = client.get_agency_name_code_list()
    print("Test get_agency_name_code_list:", json.dumps(result, ensure_ascii=False, indent=2)[:500], "...")
    # Có thể test các functions khác ở đây

if __name__ == "__main__":
    main()
