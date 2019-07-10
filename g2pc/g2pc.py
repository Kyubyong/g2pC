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


def _tone_change(hanzis, pinyins):
    '''https://en.wikipedia.org/wiki/Standard_Chinese_phonology#Tone_sandhi
    '''
    def tone33_to_23(pinyin):
        return re.sub("3( [^ ]+?3)", r"2\1", pinyin)

    # STEP 1. word-level
    ## Third tone change
    pinyins = [tone33_to_23(pinyin) for pinyin in pinyins]

    ## when it comes at the end of a multi-syllable word
    ##(regardless of the first tone of the next word),
    ## 一 is pronounced with first tone.
    _pinyins = []
    for hanzi, pinyin in zip(hanzis, pinyins):
        if len(hanzi)>1 and hanzi[0]=="一":
            pinyin = re.sub("yi1$", "YI1", pinyin)
        _pinyins.append(pinyin)

    # STEP 2. phrase-level
    ## remove boundaries
    hanzis = "".join(hanzis)
    pinyins = " ".join(_pinyins)

    ## Third tone change
    pinyins = tone33_to_23(pinyins)
    pinyins = pinyins.split()

    hanzis_prev = "^" + hanzis[:-1]
    pinyins_prev = ["^"] + pinyins[:-1]

    hanzis_next = hanzis[1:] + "$"
    pinyins_next = pinyins[1:] + ["$"]

    _pinyins = []
    for h, h_prev, h_next, p, p_prev, p_next in zip(hanzis, hanzis_prev, hanzis_next, pinyins, pinyins_prev, pinyins_next):
        if h == "一" and p == "yi1":
            if h_prev in "第初图表卷":
                p = "YI1"
            elif h_prev == "头" and h_next == "回":
                p = "YI1"
            elif h_prev == "末" and h_next == "次":
                p = "YI1"
            elif h_next in "号楼更等级一二三四五陆七八九十廿卅卌百皕千万亿":
                p = "YI1"
            elif h_prev == h_next: # 4. A一A -> A yi5 A
                p = "yi5"
            elif p_next[-1] == "4": # 一 + A4 -> yi2 A4
                p = "yi2"
            elif p_next[-1] in "123": # 一 + A{1,2,3} -> yi4 A{1,2,3}
                p = "yi4"
        if h == "不" and p=="bu4":
            if p_next[-1] == "4": # 不 + A4 -> bu2 A4
                p = "bu2"
            elif h_prev == h_next: # A不A -> A bu5 A
                p = "bu5"
        p = p.replace("YI", "yi")
        _pinyins.append(p)

    return _pinyins


def tone_change(results):
    hanzis = [result[0] for result in results]
    pinyins = [result[2] for result in results]

    pinyins = _tone_change(hanzis, pinyins)

    # align
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
    strings = ["有一次", "第一次", "十一二岁来到戏校", "同年十一月", "一九八二年英文版", "欧洲统一步伐", "吉林省一号工程", "一是选拔优秀干部"]
    g2p = G2pC()
    for string in strings:
        results = g2p(string)
        change = [each[3] for each in results]
        print(string, "/", "|".join(change))

