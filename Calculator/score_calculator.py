# score_calculator.py

# 写文满1500得20pt，之后每100字+1pt
TEXT_BASE_WORDS = 1500
TEXT_BASE_POINTS = 20
TEXT_EXTRA_PER = 100
TEXT_EXTRA_POINTS = 1

ILLUSTRATION_POINTS = {
    'sketch': 8, # 精草
    'lineart': 12, # 线稿
    'bw': 15, # 黑白
    'color': 20 # 彩色
}

COMIC_POINTS = {
    'sketch': 1,
    'lineart': 3,
    'bw': 5,
    'color': 8
}

def calc_text_score(word_count):
    if word_count < TEXT_BASE_WORDS:
        return 0
    extra_words = word_count - TEXT_BASE_WORDS
    return TEXT_BASE_POINTS + (extra_words // TEXT_EXTRA_PER) * TEXT_EXTRA_POINTS

def calc_illustration_score(counts):
    return sum(ILLUSTRATION_POINTS.get(style, 0) * num for style, num in counts.items())

def calc_comic_score(panels):
    return sum(num * COMIC_POINTS.get(style, 0) for num, style in panels)

def calc_total_score(word_count, illustrations, comics):
    return (calc_text_score(word_count)
            + calc_illustration_score(illustrations)
            + calc_comic_score(comics))
