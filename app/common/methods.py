import importlib
import inspect
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import decode_rfc2231
from functools import wraps
from time import sleep, localtime, time_ns
from urllib.parse import unquote, parse_qs, urlparse

import httpx
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication
from loguru import logger

from app.common.config import cfg
from app.common.plugin_base import PluginBase

plugins = []

# def isWin11():
#     return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

def loadPlugins(mainWindow, directory="{}/plugins".format(QApplication.applicationDirPath())):
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".py") or filename.endswith(".pyd") or filename.endswith(".so"):

                module_name = filename.split(".")[0]
                file_path = os.path.join(directory, filename)

                # Dynamic module import
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Iterate through all members in the module
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class and inherits from PluginBase
                    if inspect.isclass(obj) and issubclass(obj, PluginBase) and obj is not PluginBase:
                        try:
                            # Instantiate plugin and call load method
                            plugin_instance = obj(mainWindow)
                            plugin_instance.load()
                            logger.info(f"Loaded plugin: {plugin_instance.name}")
                            plugins.append(plugin_instance)
                        except Exception as e:
                            logger.error(f"Error loading plugin {name}: {e}")
    except Exception as e:
        logger.error(f"Error loading plugins: {e}")


def getSystemProxy():
    if sys.platform == "win32":
        try:
            import winreg

            # Open Windows registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')

            # Get proxy enable status
            proxy_enable, _ = winreg.QueryValueEx(key, 'ProxyEnable')

            if proxy_enable:
                # Get proxy address and port
                proxy_server, _ = winreg.QueryValueEx(key, 'ProxyServer')
                return "http://" + proxy_server
            else:
                return None

        except Exception as e:
            logger.error(f"Cannot get Windows proxy server: {e}")
            return None

    elif sys.platform == "linux":  # Read Linux system proxy
        try:
            return os.environ.get("http_proxy")
        except Exception as e:
            logger.error(f"Cannot get Linux proxy server: {e}")
            return None

    elif sys.platform == "darwin":
        import SystemConfiguration

        _ = SystemConfiguration.SCDynamicStoreCopyProxies(None)

        if _.get('SOCKSEnable', 0):
            return f"socks5://{_.get('SOCKSProxy')}:{_.get('SOCKSPort')}"
        elif _.get('HTTPEnable', 0):
            return f"http://{_.get('HTTPProxy')}:{_.get('HTTPPort')}"
        else:
            return None


def getProxy():
    # print(cfg.proxyServer.value)
    if cfg.proxyServer.value == "Off":
        return None
    elif cfg.proxyServer.value == "Auto":
        return getSystemProxy()
    else:
        return cfg.proxyServer.value


def getReadableSize(size):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    K = 1024.0
    while size >= K:
        size = size / K
        unit_index += 1
    return "%.2f %s" % (size, units[unit_index])


def retry(retries: int = 3, delay: float = 0.1, handleFunction: callable = None):
    """
    A decorator. Retries function execution on failure.

    :param retries: Maximum number of retry attempts
    :param delay: Delay between retries in seconds
    :param handleFunction: Handler function for exceptions
    :return:
    """

    # Validate retry parameters, use default if incorrect
    if retries < 1 or delay <= 0:
        retries = 3
        delay = 1

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries + 1):  # First execution doesn't count as retry, hence retries+1
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check retry count
                    if i == retries:
                        logger.error(f'Error: {repr(e)}! "{func.__name__}()" execution failed after {retries} retries.')
                        try:
                            handleFunction(e)
                        finally:
                            break
                    else:
                        logger.warning(
                            f'Error: {repr(e)}! "{func.__name__}()" failed, retrying [{i+1}/{retries}] in {delay} seconds...'
                        )
                        sleep(delay)

        return wrapper

    return decorator


def openFile(fileResolve):
    """
    打开文件

    :param fileResolve: 文件路径
    """
    QDesktopServices.openUrl(QUrl.fromLocalFile(fileResolve))


def getLocalTimeFromGithubApiTime(gmtTimeStr:str):
    # 解析 GMT 时间
    gmtTime = datetime.fromisoformat(gmtTimeStr.replace("Z", "+00:00"))

    # 获取本地时间的时区偏移量（秒）
    localTimeOffsetSec = localtime().tm_gmtoff

    # 创建带有本地时区偏移量的时区信息
    localTz = timezone(timedelta(seconds=localTimeOffsetSec))

    # 转换为系统本地时间
    localTime = gmtTime.astimezone(localTz)

    # 去掉时区信息
    localTimeNaive = localTime.replace(tzinfo=None)

    return localTimeNaive


def getLinkInfo(url:str, headers:dict, fileName:str="", verify:bool=False, proxy:str=getProxy(), followRedirects:bool=True) -> tuple:
    response = httpx.head(url, headers=headers, verify=verify, proxy=proxy, follow_redirects=followRedirects)
    response.raise_for_status()  # 如果状态码不是 2xx，抛出异常

    head = response.headers

    url = str(response.url)

    # Get file size, check if chunked download is possible
    if "content-length" not in head:
        fileSize = 0
    else:
        fileSize = int(head["content-length"])

    # Get filename
    if not fileName:
        try:
            # Try to process fileName* from Content-Disposition (RFC 5987 format)
            headerValue = head["content-disposition"]
            if 'fileName*' in headerValue:
                match = re.search(r'filename\*\s*=\s*([^;]+)', headerValue, re.IGNORECASE)
                if match:
                    fileName = match.group(1)
                    fileName = decode_rfc2231(fileName)[2] # Part after fileName* is encoding info

            # If fileName* not found, try regular fileName
            if not fileName and 'filename' in headerValue:
                match = re.search(r'filename\s*=\s*["\']?([^"\';]+)["\']?', headerValue, re.IGNORECASE)
                if match:
                    fileName = match.group(1)

            # Remove possible quotes and decode filename
            if fileName:
                fileName = unquote(fileName)
                fileName = fileName.strip('"\'')
            else:
                raise KeyError

            logger.debug(f"Method 1 filename extraction successful: {fileName}")
        except (KeyError, IndexError) as e:
            try:
                logger.info(f"Method 1 filename extraction failed, KeyError or IndexError: {e}")
                fileName = \
                    unquote(parse_qs(urlparse(url).query).get('response-content-disposition', [''])[0]).split(
                        "filename=")[-1]

                if fileName:
                    fileName = unquote(fileName)
                    fileName = fileName.strip('"\'')
                else:
                    raise KeyError

                logger.debug(f"Method 2 filename extraction successful: {fileName}")

            except (KeyError, IndexError) as e:
                logger.info(f"Method 2 filename extraction failed, KeyError or IndexError: {e}")
                fileName = unquote(urlparse(url).path.split('/')[-1])

                if fileName:  # If no extension, use content-type as extension
                    _ = fileName.split('.')
                    if len(_) == 1:
                        fileName += '.' + head["content-type"].split('/')[-1]

                    logger.debug(f"Method 3 filename extraction successful: {fileName}")
                else:
                    logger.debug("Method 3 filename extraction failed: empty filename")
                    # When nothing can be retrieved
                    logger.info(f"Filename extraction failed, error: {e}")
                    content_type = head["content-type"].split('/')[-1]
                    fileName = f"downloaded_file{int(time_ns())}.{content_type}"
                    logger.debug(f"Method 4 filename extraction successful: {fileName}")

    return url, fileName, fileSize