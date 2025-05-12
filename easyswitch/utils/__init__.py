import platform
import urllib.parse
from importlib import metadata

try:
    __version__ = metadata.version("easyswitch")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"


USER_AGENT = (
    f"EasySwitch-python/{__version__} ({platform.machine()}"
    f"{platform.system().lower()}) Python/{platform.python_version()}"
)


####    PARSE PHONE NUMBER
def parse_phone(number: str, raise_exception=False):
    """Return A dict of countrycode and national number"""

    import phonenumbers

    try:
        parsed_number = phonenumbers.parse(number, None)
        return {
            "country_code": parsed_number.country_code,
            "national_number": parsed_number.national_number,
        }
    except phonenumbers.NumberParseException:
        # Raise an exception if needed
        if raise_exception:
            raise phonenumbers.NumberParseException("Invalid phone number")
        return {"country_code": None, "national_number": None}


# DICT TO QUERY STRING
def dict_to_encoded_query_string(data: dict) -> str:
    """Converts a dictt object into a url safe encoded string"""
    query_string = urllib.parse.urlencode(data)
    return urllib.parse.quote(query_string)


# QUERY STRING TO DICT
def encoded_query_string_to_dict(encoded: str) -> dict:
    """Converts a url safe query str into a dict."""
    decoded = urllib.parse.unquote(encoded)
    return dict(urllib.parse.parse_qsl(decoded))
