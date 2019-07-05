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


class G2pC(object):
    def __init__(self):
        '''
        self.cedict looks like:
        {行: {pron: [hang2, xing2],
        meaning: [/row/line, /to walk/to go],
        trad: [行]}
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
                else:
                    prons = [word]
                    meanings = [""]
                    trads = [word]
                analyzed.append((word, pos, prons, meanings, trads))
            _sents.append(analyzed)

        # STEP 3
        features = [sent2features(_sent) for _sent in _sents]
        preds = self.crf.predict(features)

        # concatenate sentences
        tokens = chain.from_iterable(_sents)
        preds = chain.from_iterable(preds)

        # determine pinyin
        ret = []
        for (word, pos, prons, meanings, trads), p in zip(tokens, preds):
            if p in prons:
                pinyin = p
            else:
                pinyin = prons[0]
            ind = prons.index(pinyin)
            meaning = meanings[ind]
            pinyin = pinyin.replace("-", " ")
            trad = trads[ind]
            ret.append((word, pos, pinyin, meaning, trad))

        return ret


if __name__ == "__main__":
    string = "我写了几行代码。"
    g2p = G2pC()
    results = g2p(string)
    print(results)







