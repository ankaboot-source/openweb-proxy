from fake_useragent import UserAgent


def random_ua_headers() -> dict[str, str]:
    """
    generate a random user-agent
    most basic technique against bot blockers
    """
    ua = UserAgent()
    return {"user-agent": ua.random}
