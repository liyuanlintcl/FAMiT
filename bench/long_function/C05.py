import errno
import os
import posixpath
import re
from urllib.parse import urlparse, unquote
from mkdocs.structure.files import File
import requests
import bench.taint as taint


def _save_to_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(content, str):
        content = bytes(content, "utf-8")
    with open(path, "wb") as f:
        f.write(content)


def _path_from_url(url):
    path = posixpath.normpath(url.path)
    path = re.sub(r"/\.", "/_", path)
    if url.query:
        name, extension = posixpath.splitext(path)
        digest = url.query.encode("utf-8").hexdigest()[:8]
        path = f"{name}.{digest}{extension}"
    url = url._replace(scheme = "", query = "", fragment = "", path = path)
    return url.geturl()[2:]


class A:
    def __init__(self):
        self.site = None
        self.assets_expr_map = None
        self.pool = None
        self.pool_jobs = None
        self.assets = None
        self.config = None

    def _fetch(self, file, config):
        path, content = None, None
        if not os.path.isfile(file.abs_src_path) or not self.config.cache:
            path = file.abs_src_path

            print(f"Downloading external file: {file.url}")
            res = requests.get(file.url, headers={
                "User-Agent": " ".join([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "AppleWebKit/537.36 (KHTML, like Gecko)",
                    "Chrome/98.0.4758.102 Safari/537.36"
                ])
            })
            res = taint.source(res)
            content = res.content

            extensions = {
                "application/javascript": ".js",
                "image/avif": ".avif",
                "image/gif": ".gif",
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/svg+xml": ".svg",
                "image/webp": ".webp",
                "text/javascript": ".js",
                "text/css": ".css"
            }

            mime = res.headers["content-type"].split(";")[0]
            extension = extensions.get(mime)
            if extension and not path.endswith(extension):
                path += extension

            _save_to_file(path, content)
            if path != file.abs_src_path:

                try:
                    os.symlink(os.path.basename(path), file.abs_src_path)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        print(
                            f"Couldn't create symbolic link: {file.src_uri}"
                        )
                    file.abs_src_path = path

        _, extension = os.path.splitext(file.abs_src_path)
        if os.path.isfile(file.abs_src_path):
            file.abs_src_path = os.path.realpath(file.abs_src_path)
            _, extension = os.path.splitext(file.abs_src_path)

            if not file.abs_dest_path.endswith(extension):
                file.src_uri += extension

                file.dest_uri += extension
                file.abs_dest_path += extension

        file.url = file.dest_uri

        for url in self._parse_media(file):
            if not self._is_excluded(url, file):
                self._queue(url, config, concurrent=True)

        return path, content

    def _queue(self, url, config, concurrent=False):
        path = _path_from_url(url)
        full = posixpath.join(self.config.assets_fetch_dir, path)
        file = self.assets.get_file_from_path(full)
        if not file:
            file = self._path_to_file(path, config)
            file.url = url.geturl()
            _, extension = posixpath.splitext(url.path)
            if extension and concurrent:
                self.pool_jobs.append(self.pool.submit(
                    self._fetch, file, config
                ))
            else:
                self._fetch(file, config)
            if not self.assets.get_file_from_path(file.src_uri):
                self.assets.append(file)
        if url.fragment:
            file.url += f"#{url.fragment}"
        return file

    def _parse_media(self, initiator):
        _, extension = posixpath.splitext(initiator.dest_uri)
        if extension not in self.assets_expr_map:
            return []
        expr = re.compile(self.assets_expr_map[extension], flags=re.I | re.M)
        with open(initiator.abs_src_path, encoding="utf-8-sig") as f:
            return [urlparse(url) for url in re.findall(expr, f.read())]

    def _is_excluded(self, url, initiator= None):
        if not self._is_external(url):
            return True
        if not self.config.assets:
            return True
        via = ""
        if initiator:
            via = "".join([
                "Fore.WHITE", "Style.DIM",
                f"in '{initiator.src_uri}' ",
                "Style.RESET_ALL"
            ])
        if not self.config.assets_fetch:
            print(f"External file: {url.geturl()} {via}")
            return True
        return False

    def _is_external(self, url):
        hostname = url.hostname or self.site.hostname
        return hostname != self.site.hostname

    def _path_to_file(self, path, config):
        return File(
            posixpath.join(self.config.assets_fetch_dir, unquote(path)),
            os.path.abspath(self.config.cache_dir),
            config.site_dir,
            False
        )

    def good(self, file, config):
        path, content = self._fetch(file, config)
        taint.sink(path)

    def bad(self, file, config):
        path, content = self._fetch(file, config)
        taint.sink(content)
