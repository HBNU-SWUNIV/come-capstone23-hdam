def contentsToSentences(text):
    # .을 기준으로 split
    sentences = text.split('.')

    # 문장이 15글자 이하라면, 앞의 문장과 합쳐준다. (36.5도, 이런걸로 split되는 것을 보완하기 위해)
    new_sentences = []
    for sentence in sentences:
        if len(sentence.strip()) <= 15 and new_sentences:
            new_sentences[-1] += (' ' + sentence.strip())
        else:
            new_sentences.append(sentence.strip())

    # 빈 문자열을 제거하여 결과를 리스트에 추가
    sentences = [sentence for sentence in new_sentences if sentence]

    return sentences