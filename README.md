# g2pC: A Context-aware Grapheme-to-Phoneme for Chinese

There are several open source libraries of Chinese grapheme-to-phoneme 
conversion such as [python-pinyin](https://github.com/mozillazg/python-pinyin) or [xpinyin](https://github.com/lxneng/xpinyin). 
However, none of them seem to disambiguate Chinese polyphonic words like "行" 
("xíng" (go, walk) vs. "háng" (line)) or "了" ("le" (completed action marker) 
vs. "liǎo" (finish, achieve)). Instead, they pick up the most frequent pronunciation.
Although that may be a simple and economic strategy, machine learning techniques can be of help.
We use CRF to determine the pronunciation of polyphonic words. In addition to the target word itself and its part-of-speech, which are tagged by pkuseg, its neighboring words are also featurized.


## Requirements
* python >= 3.6
* pkuseg
* sklearn_crfsuite

## Installation
```
pip install g2pc
```

## Main Features
* Disambiguate polyphonic Chinese characters/words and return the most likely pinyin in the
 context using CRF implemented with [sklearn_crfsuite](https://github.com/TeamHG-Memex/sklearn-crfsuite).
* By associating segmentation results provided by [pkuseg](https://arxiv.org/abs/1906.11455) with an open-source dictionary [CC-CEDICT](https://cc-cedict.org/wiki/),
display the following comprehensive information.
  * word
  * part-of-speech
  * pinyin
  * English meaning
  * traditional equivalent

## Algorithm (illustrated with an example)

e.g., Input: 我写了几行代码。 (I wrote a few lines of codes.)

* STEP 1. Segment input string using [pkuseg](https://arxiv.org/abs/1906.11455).
  * -> [('我', 'r'), ('写', 'v'), ('了', 'u'), ('几', 'm'), ('行', 'q'), ('代码', 'n'), ('。', 'w')]
* STEP 2. Look up the [CC-CEDICT](https://cc-cedict.org/wiki/). Each token, a tuple, consists of
word, pos, pronunciation candidates, meaning candidates, traditional character candidates.
  * -> [('我', 'r', ['wo3'], ['/I/me/my/'], ['我']), <br>
('写', 'v', ['xie3'], ['/to write/'], ['寫']), <br>
('了', 'u', ['le5', 'liao3', 'liao4'], [dal particle ..], ['了', '了', '瞭']), <br>
('几', 'm', ['ji3', 'ji1'], ['/how much/..'], ['幾', '几']), <br>
('行', 'q', ['xing2', 'hang2'], ['/to walk/.."], ['行', '行']), <br>
('代码', 'n', ['dai4 ma3'], ['/code/'], ['代碼']), <br>
('。', 'w', ['。'], [''], ['。'])]
* STEP 3. For polyphonic words, we disambiguate them, using our pre-trained CRF model.
  * -> [('我', 'r', 'wo3', '/I/me/my/', '我'), <br>
('写', 'v', 'xie3', '/to write/', '寫'), <br>
('了', 'u', 'le5', '/(modal particle ..', '了'), <br>
('几', 'm', 'ji3', '/how much/..', '幾'), <br >
('行', 'q', 'hang2', "/row/..", '行'), <br>
('代码', 'n', 'dai4 ma3', '/code/', '代碼'), <br>
('。', 'w', '。', '', '。')]

## Usage
```
>>> from g2pc import G2pC
>>> g2p = G2pC()
>>> g2p("来不了")
# This returns a list of tuples, each of which consists of
# word, pos, pinyin, English meaning, and equivanlent traditional character.
[('来', 'v', 'lai2', '/to come/to arrive/to come round/ever since/next/', '來'), 
('不', 'd', 'bu4', '/(negative prefix)/not/no/', '不'), 
('了', 'v', 'liao3', '/to finish/to achieve/variant of 瞭|了[liao3]/to understand clearly/', '了')]
```

## Respectful comparison with other libraries
```
>>> text1 = "我写了几行代码。" # pay attention to the 行, which should be read as 'hang2', not 'xing2'
>>> text2 = "来不了" # pay attention to the 了, which should be read as 'liao3', not 'le'

# python-pinyin
>>> pip install pypinyin
>>> from pypinyin import pinyin
>>> pinyin(text1)
[['wǒ'], ['xiě'], ['le'], ['jǐ'], ['xíng'], ['dài'], ['mǎ'], ['。']]
>>> pinyin(text2)
[['lái'], ['bù'], ['le']]

# xpinyin
>>> pip install xpinyin
>>> from xpinyin import Pinyin
>>> p = Pinyin()
>>> p.get_pinyin(text1, tone_marks="numbers")  
'wo3-xie3-le5-ji1-xing2-dai4-ma3-。'
>>> p.get_pinyin(text2, tone_marks="numbers")   
'lai2-bu4-le5'
```
## References

If you use our software for research, please cite:

```
@misc{gp2C2019,
  author = {Park, Kyubyong},
  title = {g2pC},
  year = {2019},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/Kyubyong/g2pC}}
}
```