import base64
import json
import re
import time

import requests

from utils import removeImage, saveImage, showImage


class RefreshException(Exception):
    pass


def tell(f):
    def w(*a, **kwa):
        print(f"func [{f.__name__}] is running.")
        return f(*a, **kwa)
    return w


class ShangXueBa:
    def __init__(self):
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
        }
        self.session = requests.Session()
        self.timeout = 10

        self.initial_cookies()

    @tell
    def refresh_code(self):
        """刷新口令"""
        try:
            code_url = "http://www.lelunwen.com/e/action/ListInfo/?classid=45&tdsourcetag=sxb_365"
            rep = requests.get(code_url, headers=self.base_headers, timeout=self.timeout)
            rep.raise_for_status()
            code = re.findall(r'【小工具口令为：(\d+)】', rep.text)[0]
            with open("CODE", "w") as f:
                f.write(code)
        except Exception:
            raise RefreshException(
                "口令获取失败，请自行访问:http://www.lelunwen.com/e/action/ListInfo/?classid=45&tdsourcetag=sxb_365,并将口令写入文件\"CODE\"中")

    @tell
    def refresh_cookie(self):
        url = "http://www.shangxueba365.com/"
        try:
            rep = self.session.get(url, headers=self.base_headers, timeout=self.timeout)
            rep.raise_for_status()
            img_base64 = re.findall(
                r'<img class="verifyimg" alt="verify_img" src="data:image/bmp;base64,(.*?)"/>', rep.text)[0]
            img_bytes = base64.b64decode(img_base64)
            img_name = "verify.jpg"
            saveImage(img_bytes, img_name)
            showImage(img_name)
            time.sleep(1)
            verify_code = input("输入验证码：")
            removeImage(img_name)
            # ==============
            # var val = "";
            #         for (var i = 0; i < str.length; i++) {
            #             if (val == "")
            #                 val = str.charCodeAt(i).toString(16);
            #             else
            #                 val += str.charCodeAt(i).toString(16);
            #         }
            # ==============
            啥 = ""
            for item in verify_code:
                啥 += str(ord(item) - 18)
            # ==============
            rep = self.session.get(url + "/?security_verify_img=" + 啥, headers=self.base_headers, timeout=self.timeout)
            cookie_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            with open("cookie.json", "w") as f:
                json.dump(cookie_dict, f)
        except Exception:
            raise RefreshException("cookie获取失败")

    @tell
    def initial_cookies(self):
        """初始化会话cookies"""
        with open("cookie.json") as f:
            cookie_dict = json.load(f)
        if not cookie_dict:
            self.refresh_cookie()
            return self.initial_cookies()
        cookiesJar = requests.utils.cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True)
        self.session.cookies = cookiesJar
        return None

    @tell
    def query_answer(self, question_url):
        """获取答案
        :param question_url: 上学吧问题链接，如：https://www.shangxueba.com/ask/*******.html
        :return: 答案字符串，有图片就返回链接
        """
        query_url = "http://www.shangxueba365.com/api.php"
        try:
            with open("CODE", "r") as f:
                code = int(f.read())
                print(f"Code: {code}")
        except FileNotFoundError:
            # 刷新口令重来
            self.refresh_code()
            return self.query_answer(question_url)

        payload = {
            "docinfo": question_url,
            "anhao": code
        }

        # cookies无效
        rep = self.session.post(query_url, data=payload, headers=self.base_headers, timeout=10)
        # print(rep.text)
        if "{ if (event.keyCode == 13) {YunsuoAutoJump(); } " in rep.text:
            self.initial_cookies()
            return self.query_answer(question_url)

        # 口令错误, 刷新口令重来
        if rep.json()["msg"] == "wronganhao":
            self.refresh_code()
            return self.query_answer(question_url)

        if rep.json()["msg"] == "chaxunshibai":
            print("那个，这个问题应该还没有答案～")
            return None

        # 暂时就发现0和1两个返回状态码，但只有1是成功的
        if not rep.json()["status"] == 1:
            print("Oh,no!获取失败~")
            return None
        msg = rep.json()["msg"]  # type: str
        answer = msg[msg.index("正"):].replace("</div>", "").replace("<br>", "\n\n").replace("<BR>", "\n\n")
        return answer


if __name__ == "__main__":
    shangxueba = ShangXueBa()
    print("多次查询失败，就放弃吧!")

    count = 0
    while True:
        try:
            print("=" * 25)
            question_url = input("问题链接(q to quit)：")

            if count == 3 or question_url.lower() == "q":
                print("bye~")
                break

            if "www.shangxueba.com" not in question_url:
                print("链接格式不正确")
                count += 1
                continue

            count = 0
            answer = shangxueba.query_answer(question_url)
            print(answer)
            print("=" * 25)
        except Exception:
            print("获取失败，可能是题目不支持")
