import requests
from bs4 import BeautifulSoup
import io
import urllib.parse
import time

oauth_urls = (
    "https://courses.sjtu.edu.cn/app/oauth/2.0/login?login_type=outer",
    "https://oc.sjtu.edu.cn/login/openid_connect"
)

class SJTU_Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.cookies = None

    def login(self):
        if self.cookies is not None and test_login(self.cookies):
            return self.cookies
        params, uuid, cookies, url = get_params_uuid_cookies(oauth_urls[0])
        img = get_captcha_img(uuid, cookies, url)
        captcha = solve_captcha(img)
        time.sleep(1)
        cookies = login_jaccount(self.username, self.password, uuid, captcha, params, cookies)
        login_Canvas(oauth_urls[1], cookies)
        return cookies

def parse_params(url):
    return urllib.parse.parse_qs(url[url.find('?')+1:])


def get_params_uuid_cookies(url):
    r = requests.get(
        url,
        headers={"accept-language": "zh-CN"}
    )
    params = parse_params(r.url)
    uuid = BeautifulSoup(
        r.content, "html.parser"
    ).find(
        "input",
        attrs={
            "type": "hidden",
            "name": "uuid"
        }
    )["value"]
    cookies = r.cookies
    for i in r.history:
        cookies.update(i.cookies)
    return params, uuid, cookies, r.url


def get_captcha_img(uuid, cookies, url2):
    r = requests.get(
        "https://jaccount.sjtu.edu.cn/jaccount/captcha",
        params={
            "uuid": uuid,
            "t": time.time_ns()//1000000
        },
        cookies=cookies,
        headers={
            "Referer": url2
        }
    )
    return r.content

def solve_captcha(img):
    try:
        r = requests.post(
            "https://plus.sjtu.edu.cn/captcha-solver/",
            files={"image": ("captcha.jpg", io.BytesIO(img))}
        )
        return r.json()["result"]
    except Exception:
        raise Exception("Captcha solving failed.")


def login_jaccount(username, password, uuid, captcha, params, cookies):
    r = requests.post(
        "https://jaccount.sjtu.edu.cn/jaccount/ulogin",
        data={
            "user": username,
            "pass": password,
            "uuid": uuid,
            "captcha": captcha,
            **params,
        },
        headers={"accept-language": "zh-CN"},
        cookies=cookies,
    )
    if r.url.startswith("https://jaccount.sjtu.edu.cn/jaccount/jalogin"):
        raise Exception("Login failed.")
    cookies = r.cookies
    for i in r.history:
        cookies.update(i.cookies)
    return cookies


def login_Canvas(url, cookies):
    r = requests.get(
        url,
        headers={"accept-language": "zh-CN"},
        cookies=cookies
    )
    cookies.update(r.cookies)
    for i in r.history:
        cookies.update(i.cookies)

def test_login(cookies):
    '''Test whether the cookies are valid, return True if valid.'''
    r = requests.get(
        "https://oc.sjtu.edu.cn/",
        cookies=cookies
    )
    return r.status_code == 200