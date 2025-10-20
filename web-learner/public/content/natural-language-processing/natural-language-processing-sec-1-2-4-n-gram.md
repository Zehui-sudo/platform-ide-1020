好的，同学！欢迎来到 N-gram 模型的世界。

在之前的课程里，我们已经掌握了词袋模型（Bag-of-Words），它很强大，但也有个明显的“硬伤”——它把一句话的词汇看成一堆乱糟糟的珠子，完全忽略了它们的排列顺序。

比如，对于词袋模型来说，“我 不 喜欢 你”和“你 不 喜欢 我”可能看起来一模一样，这显然丢失了太多信息。今天，我们就来学习一个简单而巧妙的升级版：**N-gram 模型**，它能帮助我们把这些“珠子”按照局部顺序重新串起来。

---

### 1. 问题引入

想象一下，你正在做一个电影评论的情感分析系统。现有两条评论：

*   **评论 A:** "This movie is **not good** at all." (这部电影一点也**不好**。)
*   **评论 B:** "This movie is **good**, **not** bad at all." (这部电影很**好**，**不**坏。)

如果我们使用基础的词袋模型，它会把每条评论拆成词语，然后计数。两篇评论都包含了 `{'this', 'movie', 'is', 'not', 'good', 'at', 'all', ...}` 这些词。对于情感分析来说，“good” 是一个强烈的积极词，“not” 是一个否定词。

在词袋模型眼中，评论 A 和 B 都含有“good”和“not”，它可能会感到困惑，甚至可能因为“good”这个词而将评论 A 错误地判断为偏积极。问题出在哪里？

**关键在于词语的顺序！** 在评论 A 中，“not” 紧邻在 “good” 之前，形成了 “not good” 这个表达强烈负面情绪的短语。而在评论 B 中，它们是分开的。

词袋模型无法捕捉这种相邻词语之间的关系。那么，我们如何升级模型，让它能理解像 "not good" 这样的局部语序呢？这就是 N-gram 模型要解决的核心问题。

### 2. 核心思想与生活化类比

**核心思想**：与其把单个的词作为我们分析的基本单位，不如把**连续的 N 个词**组成的“短语”作为基本单位。

*   当 N=1 时，我们处理的是单个词，这被称为 **Unigram**，它其实就是我们熟悉的词袋模型。
*   当 N=2 时，我们处理的是两个连续的词组，被称为 **Bigram**。例如，"not good" 就是一个 Bigram。
*   当 N=3 时，就是三个连续的词组，被称为 **Trigram**。例如，"I love you" 就是一个 Trigram。

**生活化类比：阅读时的“滑动窗口”**

想象一下你第一次读一篇外语文章。

*   **词袋模型（Unigram）** 就像是你把文章里所有认识的单词都挑出来，写在一张纸上，然后根据这些单词猜测文章大意。对于“我爱你”和“你爱我”这两个句子，词袋模型会得到相同的词语集合 `{'我', '爱', '你'}`，它无法区分是谁爱谁。
*   **N-gram 模型** 则更像我们正常的阅读方式。你用一个“阅读窗口”（比如一次看两个词）来扫描文本。
    *   对于句子“我爱你”，当你用大小为 2 的窗口扫描时：
        *   你先看到 **"我 爱"**（Bigram），
        *   然后窗口向右滑动一个词，你看到 **"爱 你"**（Bigram）。
    *   通过这些连续的词组，你不仅知道了文章里有哪些词，还知道了它们是如何局部组合在一起的，从而准确理解了“我爱你”这个完整的、有语序的信息。如果遇到“你爱我”，它会产生“你 爱”和“爱 我”这两个Bigram，与“我爱你”产生的是不同的Bigram组合，从而能够区分两者。

N-gram 就是用这种“滑动窗口”的方式，来捕捉文本中的局部语序信息。

### 3. 最小可运行示例

让我们用 Python 代码来亲手实现这个“滑动窗口”的过程。下面的函数可以从一个句子中提取出所有的 N-grams。

```python
# code_lang: python
from typing import List

def generate_ngrams(text: str, n: int) -> List[str]:
    """
    从给定的文本中生成 n-grams。

    Args:
        text (str): 输入的文本字符串。
        n (int): N-gram 中 N 的值 (例如, 2 for bigrams, 3 for trigrams)。

    Returns:
        List[str]: 生成的 n-grams 列表。
    """
    # 1. 预处理：分词（这里用最简单的按空格切分）
    words = text.split()
    
    # 2. 检查单词数量是否足够生成至少一个 n-gram
    if len(words) < n:
        return []

    # 3. 滑动窗口，生成 n-grams
    ngrams = []
    # 窗口的起始位置从 0 到 len(words) - n
    # 例如，5个词生成bigram (n=2)，窗口可以从索引0, 1, 2, 3开始，所以循环到 5-2=3
    for i in range(len(words) - n + 1):
        # 从当前位置 i 取出 n 个词，组成一个 n-gram
        ngram = " ".join(words[i:i+n])
        ngrams.append(ngram)
        
    return ngrams

# --- 示例 ---
sentence = "I love natural language processing"

# 1. Unigrams (n=1)，等同于词袋模型的分词结果
unigrams = generate_ngrams(sentence, 1)
print(f"Unigrams (n=1): {unigrams}")

# 2. Bigrams (n=2)，捕捉相邻词对关系
bigrams = generate_ngrams(sentence, 2)
print(f"Bigrams (n=2): {bigrams}")

# 3. Trigrams (n=3)，捕捉更长的短语
trigrams = generate_ngrams(sentence, 3)
print(f"Trigrams (n=3): {trigrams}")

# --- 应用于我们最初的问题 ---
comment_a = "This movie is not good at all"
comment_a_bigrams = generate_ngrams(comment_a, 2)
print(f"\nComment A Bigrams: {comment_a_bigrams}")
# 注意，'not good' 出现在了结果中！
```

**预期输出:**

```
Unigrams (n=1): ['I', 'love', 'natural', 'language', 'processing']
Bigrams (n=2): ['I love', 'love natural', 'natural language', 'language processing']
Trigrams (n=3): ['I love natural', 'love natural language', 'natural language processing']

Comment A Bigrams: ['This movie', 'movie is', 'is not', 'not good', 'good at', 'at all']
```

看到 `Comment A Bigrams` 的输出里包含 `'not good'` 了吗？现在，我们的模型有了一个新的、携带负面情感的“词汇”。这就是 N-gram 的魔力！

### 4. 原理剖析

让我们把 `generate_ngrams("I love NLP", 2)` 的执行过程拆解开来：

1.  **输入**: `text = "I love NLP"`, `n = 2`
2.  **分词**: `words` 列表变为 `['I', 'love', 'NLP']`。列表长度为 3。
3.  **确定循环范围**: `range(len(words) - n + 1)` -> `range(3 - 2 + 1)` -> `range(2)`。这意味着循环将执行两次，`i` 的值分别为 0 和 1。
4.  **第一次循环 (i=0)**:
    *   切片 `words[0:0+2]`，得到 `['I', 'love']`。
    *   `" ".join(['I', 'love'])` 得到字符串 `"I love"`。
    *   `ngrams` 列表变为 `['I love']`。
5.  **第二次循环 (i=1)**:
    *   切片 `words[1:1+2]`，得到 `['love', 'NLP']`。
    *   `" ".join(['love', 'NLP'])` 得到字符串 `"love NLP"`。
    *   `ngrams` 列表变为 `['I love', 'love NLP']`。
6.  **循环结束**: 函数返回 `['I love', 'love NLP']`。

**构建 N-gram 词袋模型**

得到这些 N-grams 后，我们就可以像构建普通词袋模型一样构建一个 "N-gram 词袋模型"。

*   **老方法 (Unigram)**: 词汇表是 `{'I', 'love', 'natural', ...}`，向量表示文档中每个**词**的频率。
*   **新方法 (Bigram)**: 词汇表是 `{'I love', 'love natural', ...}`，向量表示文档中每个**词组**的频率。

**复杂度分析**:

*   **时间复杂度**: `O(L)`，其中 `L` 是文本中的单词数量。因为我们基本上只对文本进行了一次遍历（滑动窗口）。（严格来说是 `O(L*N)`，因为每次 `join` 操作需要 `O(N)`，但 `N` 通常是很小的常数，所以可近似为 `O(L)`）。
*   **空间复杂度**: `O(L)`，因为生成的 N-grams 数量与原始文本长度成正比。

| 特性 | 词袋模型 (BoW / Unigram) | N-gram 模型 (N > 1) |
| :--- | :--- | :--- |
| **核心单元** | 单个词语 | 连续的 N 个词语构成的短语 |
| **语序信息** | 完全忽略 | 保留了局部（窗口 N 内）的语序 |
| **词汇表大小** | 相对较小 (V) | **急剧增大** (理论上界可达 V^N，但实际远小于此值) |
| **向量稀疏性** | 较高 | **非常高**，大多数文档不包含某个特定 N-gram |
| **捕捉能力** | 词频、关键词 | 短语、搭配、局部句法结构 |
| **适用场景** | 主题建模、文档分类（当语序不重要时） | 情感分析、语言模型、机器翻译（当语序重要时） |

### 5. 常见误区与优化点

1.  **误区：N 越大越好？**
    *   **不是的！** N 值的选择是一个权衡。
    *   **N 太小 (如 1)**: 丢失了语序信息。
    *   **N 太大 (如 5, 6)**:
        *   **词汇表爆炸**: 词汇表（特征空间）会变得极其巨大，导致计算成本高昂且向量极度稀疏。
        *   **过拟合**: 模型可能会记住训练集中非常特定的长短语，但在新数据上泛化能力差。
    *   在实践中，**Bigram (n=2)** 和 **Trigram (n=3)** 是最常用的。通常会将 Unigram 和 Bigram 结合使用，以同时捕捉词频和局部语序信息。

2.  **误区：忽略句子边界**
    *   我们简单的实现会跨越句子边界生成 N-gram。例如，对于 "I love NLP. It is fun."，可能会生成 "NLP. It" 这样的 Bigram，这通常是没有意义的。
    *   **优化点**: 在实际应用中，通常会先分句，然后在每个句子的开头和结尾添加特殊的填充符（padding），如 `<START>` 和 `<END>`。这样，对于句子 "I love NLP"，我们可以生成 `<START> I`, `I love`, `love NLP`, `NLP <END>`，从而更好地模拟语言的生成过程。

3.  **优化点：处理稀疏性问题**
    *   由于 N-gram 词汇表巨大，大多数 N-gram 在一个文档中出现的次数都是 0。
    *   **特征选择**: 可以只保留出现频率超过某个阈值的 N-grams，过滤掉稀有的组合。
    *   **平滑技术 (Smoothing)**: 在语言模型中，为了处理未见过的 N-gram，会使用拉普拉斯平滑、古德-图灵平滑等技术，给它们一个极小的概率，避免概率为零。

### 6. 拓展应用

N-gram 模型虽然简单，但它是许多更复杂 NLP 任务的基石：

1.  **统计语言模型 (Statistical Language Models)**: 这是 N-gram 最经典的应用。它通过计算一个词序列出现的概率 `P(w1, w2, ..., wk)` 来判断一句话是否“通顺”。这是输入法自动补全、语音识别和拼写纠错背后的核心原理之一。例如，模型会认为 "I am writing a letter" 的概率远高于 "I am writing letter a"。

2.  **机器翻译**: 在早期的统计机器翻译（SMT）系统中，N-gram 模型被用来评估翻译结果的流畅度，确保生成的译文符合目标语言的语法习惯。

3.  **文本分类与情感分析**: 正如我们最初的例子所示，使用 Bigram 或 Trigram 作为特征（如 "not good", "very happy"）可以显著提升分类器的性能。

4.  **信息检索**: 在搜索引擎中，匹配用户查询的 Bigram 或 Trigram（而不仅仅是单个词）可以提供更相关的搜索结果。

### 7. 总结要点

*   **核心目的**: 在词袋模型的基础上，通过引入**局部语序信息**来增强文本表示能力。
*   **实现方式**: 使用一个大小为 **N** 的**滑动窗口**扫描文本，将窗口内的词组作为一个特征单元。
*   **关键优势**: 简单、有效，能捕捉到词语搭配和否定、转折等局部上下文关系。
*   **主要挑战**: **词汇表爆炸**和**数据稀疏性**，越大的 N 越严重。
*   **常见选择**: 实践中常用 Unigram、Bigram 和 Trigram 的组合，以平衡信息量和稀疏性。

N-gram 是一座桥梁，它连接了完全无序的词袋模型和后来更复杂的、能理解全局依赖的神经网络模型（如 RNN, Transformer）。掌握它，你对文本表示的理解就更进了一步！

### 8. 思考与自测

在实际应用中，我们常常不只使用一种 N-gram，而是将 Unigram 和 Bigram 结合起来作为特征。

**挑战**: 请你修改上面的 `generate_ngrams` 函数，创建一个新函数 `generate_combined_ngrams(text, max_n)`，它能一次性生成从 Unigram 到 `max_n`-gram 的所有结果。

例如，`generate_combined_ngrams("I love NLP", 2)` 应该返回一个包含所有 Unigram 和 Bigram 的列表：`['I', 'love', 'NLP', 'I love', 'love NLP']`。

这会让你更深入地理解如何灵活运用 N-gram 来构建更丰富的特征集。动手试试看吧！