# Method: scoring phrases, not queries

## The failure mode

Speech-analytics queries are boolean volume. `LIKE("1099") OR LIKE("tax document")` going up in February tells leadership **that** tax-document contacts rose. It does not tell them **why**, and it does not tell them whether last year's FAQ/IVR language worked.

Two weeks can have the same query rate and different problems.

## Contrast used here

Same season, two windows, **inside the tax-document queue**. If you score the whole center you only rediscover that February has more 1099 calls — the thing a keyword query already knew.

- **Baseline (normal) window:** 2026-01-20 to 2026-01-31
- **Spike window:** 2026-02-10 to 2026-02-21

Production habit this demo reconstructs: build a "normal" week corpus and a "spike" week corpus **in the same year**, then score what language showed up in the second week that was weak in the first. Year-over-year is a different study. This one answers: *we already tried to explain late 1099s; are clients still asking the same thing?*

## 1. Monroe's Fightin' Words

Monroe, Colaresi, Quinn (2008), "Fightin' Words: Lexical Feature Selection and Evaluation for Identifying the Content of Political Conflict."

Compare two corpora with a log-odds ratio under an informative Dirichlet prior. For phrase \(w\):

\[
\hat{\delta}_w^{(s-b)}
= \log \frac{y_w^{s}+\alpha_w}{n^{s}+\alpha_0-y_w^{s}-\alpha_w}
- \log \frac{y_w^{b}+\alpha_w}{n^{b}+\alpha_0-y_w^{b}-\alpha_w}
\]

\[
\sigma^2(\hat{\delta}_w^{(s-b)})
= \frac{1}{y_w^{s}+\alpha_w}+\frac{1}{y_w^{b}+\alpha_w}
\]

\[
z_w = \hat{\delta}_w^{(s-b)} / \sigma(\hat{\delta}_w^{(s-b)})
\]

- \(y_w^{s}, y_w^{b}\): counts of phrase \(w\) in spike / baseline
- \(n^{s}, n^{b}\): total phrase tokens in each window
- \(\alpha_0 = 500\), \(\alpha_w = \alpha_0 \cdot \hat{p}_w\) from the pooled corpus (the informative prior)

Positive \(z\) means the phrase is distinctive of the spike window, not merely frequent. That is the point. "1099" itself is common in both weeks. "january 31" and "my cpa needs" are not.

## 2. Class-based TF-IDF (c-TF-IDF)

Treat each window as one class. For term \(t\) in class \(c\):

\[
W_{t,c} = \mathrm{tf}_{t,c} \cdot \log\left(1 + \frac{A}{\mathrm{tf}_{t}}\right)
\]

- \(\mathrm{tf}_{t,c}\): count of \(t\) inside class \(c\)
- \(\mathrm{tf}_{t}\): count of \(t\) across classes
- \(A\): average number of tokens per class

c-TF-IDF rewards terms that are concentrated in one window. With two classes it is a cousin of the Fightin' Words contrast, not a replacement. We keep both because one is a significance-style z and the other is a ranking weight leadership can scan.

## 3. Driver score

Phrases are 1–3 grams after light ASR-aware tokenization (`1099`, `ten ninety nine` mapped together).

\[
\mathrm{driver}(w) = 0.65 \cdot \mathrm{minmax}(z_w) + 0.35 \cdot \mathrm{minmax}(W_{w,\mathrm{spike}})
\]

Only phrases with enough combined support are scored. Unigram stopwords are dropped; they stay legal inside bigrams (`when will`, `still waiting`).

The leadership table is the top spike-side phrases plus one raw quote each. Quotes stay noisy on purpose. Floor transcripts are not clean text.

## What this is not

- Not a topic model and not embeddings. The unit leadership can act on is a **phrase they can put on a web page**.
- Not a causal estimate of the FAQ/IVR change. The scores justify *funding the change*. Measurement after deploy is a different packet.
- Not production speech-query logic. No vendor query language ships here.
