# -*- coding: utf-8 -*-
# @Description :
import time
import requests
from asyncio import iscoroutinefunction
from DrissionPage import ChromiumPage, WebPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from loguru import logger


# todo 注意事项 若是在无痕模式下 需要手动取打开可在无痕模式运行插件

def cost_time(func):
    if iscoroutinefunction(func):
        async def wrapper(*args, **kwargs):
            t = time.perf_counter()
            result = await func(*args, **kwargs)
            logger.info(f'func {func.__name__} cost time: {time.perf_counter() - t:.8f} s')
            return result
    else:
        def wrapper(*args, **kwargs):
            t = time.perf_counter()
            result = func(*args, **kwargs)
            logger.info(f'func {func.__name__} cost time: {time.perf_counter() - t:.8f} s')
            return result
    return wrapper


class SwitchIPDemo:
    def __init__(self):
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36'
        self.page = self._init_chromium_page()
        self.ip_service_url = 'your ip address'  # Update with actual URL

    def _init_chromium_page(self):
        co = ChromiumOptions()
        logger.debug(f'Setting User-Agent to {self.ua}')
        co.set_user_agent(self.ua)
        co.set_argument('--incognito')
        co.set_argument('--lang=en')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--window-size', '1000,800')
        co.add_extension(r'./switch_proxy_v0.2')  # 加载插件
        co.set_paths(browser_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', local_port=9234)
        return ChromiumPage(co)

    def get_ip(self):
        try:
            response = requests.get(url=self.ip_service_url)
            response.raise_for_status()
            ip = response.text.replace('\r\n', '')
            if '请求频繁,请2秒后再试' in ip:
                logger.warning('Requesting IP too frequently, retrying after 2 seconds.')
                time.sleep(2)
                return self.get_ip()
            return ip
        except requests.RequestException as e:
            logger.error(f'Error fetching IP: {e}')
            return None

    def switch_ip(self):
        tab = self.page.new_tab('chrome://extensions/')
        # todo diepbfpfaekonmekmijcmlknlbdnfjhj这个id是插件id
        # todo 不同浏览器分配的id貌似不一样 需要自己替换为自己的
        tab.get('chrome-extension://diepbfpfaekonmekmijcmlknlbdnfjhj/options.html')
        try:
            tab.ele(f'x://*[@id="proxyType"]/option[4]').click()
            ip = self.get_ip()
            if not ip:
                logger.error('Failed to obtain a new IP address.')
                return False
            tab.ele('x://*[@id="proxyUrl"]').input(ip)
            tab.ele('x://*[@id="setProxyButton"]').click()
            time.sleep(2)
            if 'Proxy set to' in tab.html:
                logger.success(f'Proxy set successfully: {ip}')
                return True
            else:
                logger.error(f'Failed to set proxy: {ip}')
                return False
        finally:
            tab.close()

    @cost_time
    def start(self):
        logger.info(f'Starting with User-Agent: {self.page.user_agent}')
        if self.switch_ip():
            self.page.get('https://www.ipaddress.my/', timeout=30)
            logger.info('Switched IP successfully, waiting...')
            time.sleep(30000)

    def main(self):
        self.start()


if __name__ == '__main__':
    sid = SwitchIPDemo()
    sid.main()
