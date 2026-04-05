import psycopg


def database_url_to_conninfo(url: str) -> str:
    if "+psycopg" in url:
        return url.replace("postgresql+psycopg", "postgresql", 1)
    return url


def check_database(url: str, *, connect_timeout: float = 3.0) -> None:
    conninfo = database_url_to_conninfo(url)
    with psycopg.connect(conninfo, connect_timeout=int(connect_timeout)) as conn:
        conn.execute("SELECT 1")
