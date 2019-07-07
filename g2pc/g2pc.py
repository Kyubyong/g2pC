#-*- coding:utf8 -*-
'''
g2pC: A context-aware grapheme-to-phoneme module for Chinese
https://github.com/kyubyong/g2pC
kbpark.linguist@gmail.com
'''
import pickle
import re
import os
import pkuseg
from itertools import chain


def convert_hanzi_string_to_number(string):
    return "/".join(str(ord(char)) for char in string)


def word2features(sent, i):
    word = convert_hanzi_string_to_number(sent[i][0])
    postag = sent[i][1]

    features = {
        'bias': 1.0,
        'word':word,
        'postag': postag,
        }
    if i == 0:
        features['BOS'] = True
    else:
        if i > 0:
            word1 = convert_hanzi_string_to_number(sent[i-1][0])
            postag1 = sent[i-1][1]
            features.update({
                '-1:word': word1,
                '-1:postag': postag1,
            })
        if i > 1:
            word1 = convert_hanzi_string_to_number(sent[i-2][0])
            postag1 = sent[i-2][1]
            features.update({
                '-2:word': word1,
                '-2:postag': postag1,
            })
        if i > 2:
            word1 = convert_hanzi_string_to_number(sent[i-3][0])
            postag1 = sent[i-3][1]
            features.update({
                '-3:word': word1,
                '-3:postag': postag1,
            })

    if i == len(sent)-1:
        features['EOS'] = True
    else:
        if i < len(sent)-1:
            word1 = convert_hanzi_string_to_number(sent[i+1][0])
            postag1 = sent[i+1][1]
            features.update({
                '+1:word': word1,
                '+1:postag': postag1,
            })
        if i < len(sent)-2:
            word1 = convert_hanzi_string_to_number(sent[i+2][0])
            postag1 = sent[i+2][1]
            features.update({
                '+2:word': word1,
                '+2:postag': postag1,
            })
        if i < len(sent)-3:
            word1 = convert_hanzi_string_to_number(sent[i+3][0])
            postag1 = sent[i+3][1]
            features.update({
                '+3:word': word1,
                '+3:postag': postag1,
            })

    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]


def tone33_to_23(pinyins):
    '''https://en.wikipedia.org/wiki/Standard_Chinese_phonology#Tone_sandhi

    1. Third tone change
    When there are two consecutive third-tone syllables, the first of them is pronounced with second tone.
    For example, lǎoshǔ老鼠 ("mouse") comes to be pronounced láoshǔ [lau̯˧˥ʂu˨˩]. It has been investigated whether the rising contour (˧˥) on the prior syllable is in fact identical to a normal second tone; it has been concluded that it is, at least in terms of auditory perception.[1]:237

    When there are three or more third tones in a row, the situation becomes more complicated, since a third tone that precedes a second tone resulting from third tone sandhi may or may not be subject to sandhi itself. The results may depend on word boundaries, stress, and dialectal variations. General rules for three-syllable third-tone combinations can be formulated as follows:

    If the first word is two syllables and the second word is one syllable, then the first two syllables become second tones. For example, bǎoguǎn hǎo 保管好 ("to take good care of") takes the pronunciation báoguán hǎo [pau̯˧˥kwan˧˥xau̯˨˩˦].
    If the first word is one syllable, and the second word is two syllables, the second syllable becomes second tone, but the first syllable remains third tone. For example: lǎo bǎoguǎn 老保管("to take care of all the time") takes the pronunciation lǎo báoguǎn [lau̯˨˩pau̯˧˥kwan˨˩˦].
    '''
    def _change(pinyin):
        return re.sub("3( [^ ]+?3)", r"2\1", pinyin)

    pinyins = " ".join(_change(pinyin) for pinyin in pinyins)
    pinyins = _change(pinyins).split()
    return pinyins

def tone_bu(hanzis, pinyins):
    '''https://en.wikipedia.org/wiki/Standard_Chinese_phonology#Tone_sandhi
    2. For 不 bù:

    不 is pronounced with second tone when followed by a fourth tone syllable.

        Example: 不是 (bù+shì, "to not be") becomes búshì [pu˧˥ʂɻ̩˥˩]

    In other cases, 不 is pronounced with fourth tone.
    However, when used between words in an A-not-A question,
    it may become neutral in tone (e.g. 是不是 shìbushì).
    '''
    # A不A -> A bu5 A
    indices = [m.start(0)+1 for m in re.finditer(r"(.)不\1", hanzis)]
    for idx in indices:
        pinyins[idx] = "bu5"

    # 不 + A4 -> bu2 A4
    pinyins = re.sub("bu4( [^ ]+?4)", r"bu2\1", " ".join(pinyins))

    return pinyins.split()


def tone_yi(hanzis, pinyins):
    '''https://en.wikipedia.org/wiki/Standard_Chinese_phonology#Tone_sandhi
    For 一 yī:

    一 is pronounced with second tone when followed by a fourth tone syllable.

        Example: 一定 (yī+dìng, "must") becomes yídìng [i˧˥tiŋ˥˩]

    Before a first, second or third tone syllable, 一 is pronounced with fourth tone.

        Examples：一天 (yī+tiān, "one day") becomes yìtiān [i˥˩tʰjɛn˥], 一年 (yī+nián, "one year") becomes yìnián [i˥˩njɛn˧˥], 一起 (yī+qǐ, "together") becomes yìqǐ [i˥˩t͡ɕʰi˨˩˦].

    When final, or when it comes at the end of a multi-syllable word (regardless of the first tone of the next word), 一 is pronounced with first tone. It also has first tone when used as an ordinal number (or part of one), and when it is immediately followed by any digit (including another 一; hence both syllables of the word 一一 yīyī and its compounds have first tone).
    When 一 is used between two reduplicated words, it may become neutral in tone (e.g. 看一看 kànyikàn ("to take a look of")).
    '''
    # A一A -> A yi5 A
    indices = [m.start(0)+1 for m in re.finditer(r"(.)一\1", hanzis)]
    for idx in indices:
        pinyins[idx] = "yi5"

    # 一 + A4 -> yi2 A4
    pinyins = re.sub("yi1( [^ ]+?4)", r"yi2\1", " ".join(pinyins))

    # 一 + A{1,2,3} -> yi4 A{1,2,3}
    pinyins = re.sub("yi1( [^ ]+?[123])", r"yi4\1", pinyins)

    return pinyins.split()


def tone_change(results):
    hanzis = "".join(result[0] for result in results)
    pinyins = [result[2] for result in results]

    pinyins = tone33_to_23(pinyins)
    pinyins = tone_bu(hanzis, pinyins)
    pinyins = tone_yi(hanzis, pinyins)

    rule_applied = []
    for result in results:
        n_syls = len(result[2].split())
        _pinyin = " ".join(pinyins[:n_syls])
        pinyins = pinyins[n_syls:]
        result = (result[0], result[1], result[2], _pinyin, result[3], result[4])
        rule_applied.append(result)
    return rule_applied


class G2pC(object):
    def __init__(self):
        '''
        self.cedict looks like:
        {行: {pron: [hang2, xing2],
        meaning: [/row/line, /to walk/to go],
        trad: [行, 行]}
        '''
        self.seg = pkuseg.pkuseg(postag=True)
        self.cedict = pickle.load(open(os.path.dirname(os.path.abspath(__file__)) + '/cedict.pkl', 'rb'))
        self.crf = pickle.load(open(os.path.dirname(os.path.abspath(__file__)) + '/crf100.bin', 'rb'))

    def __call__(self, string):
        # fragment into sentences
        sents = re.sub("([！？。])", r"\1[SEP]", string)
        sents = sents.split("[SEP]")

        _sents = []
        for sent in sents:
            if len(sent)==0: continue

            # STEP 1
            tokens = self.seg.cut(sent)

            # STEP 2
            analyzed = []
            for word, pos in tokens:
                if word in self.cedict:
                    features = self.cedict[word]
                    prons = features["pron"]
                    meanings = features["meaning"]
                    trads = features["trad"]
                    analyzed.append((word, pos, prons, meanings, trads))
                else:
                    for char in word:
                        if char in self.cedict:
                            features = self.cedict[char]
                            prons = features["pron"]
                            meanings = features["meaning"]
                            trads = features["trad"]
                        else:
                            prons = [char]
                            meanings = [""]
                            trads = [char]
                        analyzed.append((char, pos, prons, meanings, trads))
            _sents.append(analyzed)

        # print("STEP1", tokens)
        # print("STEP2", analyzed)
        # STEP 3
        features = [sent2features(_sent) for _sent in _sents]
        preds = self.crf.predict(features)

        # concatenate sentences
        tokens = chain.from_iterable(_sents)
        preds = chain.from_iterable(preds)

        # determine pinyin
        ret = []
        for (word, pos, prons, meanings, trads), p in zip(tokens, preds):
            # print(word, pos, prons, p)
            p = p.replace("-", " ")
            if p in prons:
                pinyin = p
            else:
                pinyin = prons[0]
            ind = prons.index(pinyin)
            meaning = meanings[ind]
            trad = trads[ind]
            ret.append((word, pos, pinyin, meaning, trad))

        # print("STEP3", ret)

        # STEP 4
        ret = tone_change(ret)
        return ret


if __name__ == "__main__":
    strings = ["行李不多, 去三几个人就搬回来了", "我写了几行代码。", "来不了", "老鼠", "保管好", "老保管", "不是", "是不是", "一定", "一天", "看一看", "一心一意" ]
    g2p = G2pC()
    for string in strings:
        results = g2p(string)
        print(results)







