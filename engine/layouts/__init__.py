"""型ごとの並べ方。1 型 = 1 ファイル。

モジュールの約束は 1 つだけ:

    build(tl: dict, cast: Cast | None, fps: int, W: int, H: int) -> callable

返り値は `(t: float, fi: int) -> PIL.Image` ——時刻を受けて 1 コマを返す。
`cast` は型がキャストを使わないとき None になる。
"""
