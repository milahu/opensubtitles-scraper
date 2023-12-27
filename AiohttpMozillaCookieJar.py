from http.cookiejar import MozillaCookieJar
from http.cookies import BaseCookie, Morsel, SimpleCookie
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from http.cookiejar import Cookie
from typing import Union


from aiohttp import CookieJar


PathLike = Union[str, "os.PathLike[str]"]


class AiohttpMozillaCookieJar(CookieJar):
    """
    load/save cookies from/to a cookies.txt file with aiohttp

    convert between http.cookiejar.MozillaCookieJar and aiohttp.CookieJar

    import aiohttp
    from AiohttpMozillaCookieJar import AiohttpMozillaCookieJar
    jar = AiohttpMozillaCookieJar()
    cookies_txt_path = "cookies.txt"
    jar.load(cookies_txt_path)
    async with aiohttp.ClientSession(cookie_jar=jar) as session:
        url = "..."
        response = await aiohttp_session.get(url)
    jar.save(cookies_txt_path)

    author: Milan Hauth <milahu@gmail.com>
    license: MIT License
    """

    def load(self, file_path):

        file_path = Path(file_path)

        jar_1 = MozillaCookieJar()
        jar_1.load(file_path)

        # Cookie in jar_1 -> Morsel in jar_2

        # jar_1._cookies # dict
        # jar_1._cookies[domain] # dict
        # jar_1._cookies[domain][path] # dict
        # jar_1._cookies[domain][path][name] # Cookie

        # jar_2._cookies # collections.defaultdict(SimpleCookie)
        # jar_2._cookies[(domain, path)] # SimpleCookie
        # jar_2._cookies[(domain, path)][name] # Morsel

        for cookie_1 in jar_1:

            morsel_2 = Morsel()

            domain = cookie_1.domain
            path = cookie_1.path
            name = cookie_1.name

            if name.lower() in Morsel._reserved:
                #print(f"illegal morsel name: {name}")
                continue

            for key in (
                'path',
                'comment',
                'domain',
                'secure',
                'version',
            ):
                if (value := getattr(cookie_1, key)) is not None:
                    morsel_2[key] = value

            morsel_2._key = cookie_1.name
            morsel_2._value = cookie_1.value
            morsel_2._coded_value = cookie_1.value

            try:
                morsel_2['expires'] = datetime.fromtimestamp(cookie_1.expires).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            except (
                OSError,  # Invalid argument (value of cookie.expires is invalid)
                TypeError,  # cookie.expires is None
            ):
                pass

            for key in ('HttpOnly', 'SameSite'):
                if (value := cookie_1.get_nonstandard_attr(key, None)) is not None:
                    morsel_2[key] = value

            self._cookies[(domain, path)][name] = morsel_2


    def save(self, file_path: PathLike) -> None:

        file_path = Path(file_path)

        jar_1 = MozillaCookieJar()

        # Morsel in jar_2 -> Cookie in jar_1

        # jar_2._cookies # collections.defaultdict(SimpleCookie)
        # jar_2._cookies[(domain, path)] # SimpleCookie
        # jar_2._cookies[(domain, path)][name] # Morsel

        # jar_1._cookies # dict
        # jar_1._cookies[domain] # dict
        # jar_1._cookies[domain][path] # dict
        # jar_1._cookies[domain][path][name] # Cookie

        for (domain, path), cookie_2 in self._cookies.items():

            for name, morsel_2 in cookie_2.items():

                try:
                    expires = self._expirations[(domain, path, name)].timestamp()
                except KeyError:
                    expires = datetime.strptime(morsel_2["expires"], "%a, %d %b %Y %H:%M:%S %Z").timestamp()

                cookie_1 = Cookie(
                    0, # version
                    name, # name
                    morsel_2.value, # value
                    None, # port
                    False, # port_specified
                    domain, # domain
                    False, # domain_specified
                    False, # domain_initial_dot
                    path, # path
                    False, # path_specified
                    morsel_2["secure"], # secure
                    expires, # expires
                    False, # discard
                    None, # comment
                    None, # comment_url
                    {}, # rest
                )
                if not domain in jar_1._cookies:
                    jar_1._cookies[domain] = dict()
                if not path in jar_1._cookies[domain]:
                    jar_1._cookies[domain][path] = dict()
                jar_1._cookies[domain][path][name] = cookie_1

        jar_1.save(file_path)
