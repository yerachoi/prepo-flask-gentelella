def format_datetime(value, fmt='%Y년 %m월 %d일 %H시 %M분'):
    return value.strftime(fmt)


def format_content(content):
    content_short = content.split()[:100]
    content_res = ' '.join(content_short)
    return content_res