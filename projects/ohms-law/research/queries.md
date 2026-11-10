# 検索と訂正の記録

取得日: 2026-11-10。公式（MEXT / BIPM / Royal Society）と教科書・参照資料を先に当たり、
実験の一次記録（1826年論文の註解付き翻訳）で裏を取った。

## 検索語

- Georg Simon Ohm 1827 book galvanic circuit law history Copley Medal 1841
- Ohm's law non-ohmic device filament lamp resistance increases with temperature
- ohm unit definition SI 2019 ampere elementary charge quantum Hall effect
- オームの法則 中学理科 電圧 電流 抵抗 オーム抵抗 直列 並列 学習指導要領
- Ohm 1826 experiment apparatus torsion balance thermocouple wire length measurement current
- "web of naked fancies" Ohm 1827 criticism quote source
- Royal Society Copley Medal 1841 Georg Ohm award
- 文部科学省 中学校学習指導要領 理科 2年 電流とその利用 オームの法則 内容
- 平成29年告示 中学校学習指導要領 理科 PDF 第2学年 電流とその利用 文部科学省
- "電流・電圧と抵抗" "比例することを見いだす" 中学校学習指導要領 平成29年 第2学年 内容
- 1881 International Electrical Congress Paris adopted ohm volt ampere units
- LED diode I-V characteristic non-ohmic threshold voltage series resistor current limiting
- incandescent lamp I-V characteristic curve non-ohmic resistance cold hot ratio
- NIST quantum Hall effect ohm realization von Klitzing constant 25812.807
- Ohm's law definition of resistance empirical law constant temperature "not a fundamental law"
- オームの法則 抵抗の定義 比例 一定温度 高校物理 説明

## 当たった資料

公式: `mext-curriculum` / `royal-society-ohm` / `science-museum-ohm` / `bipm-ampere`。

一次・論文: `scielo-ohm-1826`（1826年論文の註解付き翻訳）/ `ethw-si-units`（1881年パリ国際電気会議）。

参照: `openstax-ohms-law` / `openstax-power` / `openstax-series-parallel` /
`hyperphysics-ohmlaw` / `hyperphysics-tempcoef` / `ethw-ohm` / `ac-bordeaux-lamp` /
`makeabilitylab-led`。

作品内: `ohms-law-script`（v1 下書き）。

## 分かったこと

- オームの法則の中身は「温度が変わらなければ、電流が電圧に比例する」こと。
  `R = V/I` は抵抗の定義で、法則は「R が変わらない」という経験的な主張。
  **この二つを分けることが、今回の核。**
- `R = V/I` そのものを「オームの法則」と呼ぶ教材もある（`kindai-ohms-law`）。
  本作は、定義（どんな物質でも成り立つ）と経験則（オーム物質で成り立つ）を分ける
  立場を取る。台本では「式は R をそう決めただけだ。R が一定かは、別の話」と言う。
- 白熱電球は、フィラメントの温度上昇で R が上がるため、比例しない。
- LED は閾値まで流れず、超えると急に流れる。直列抵抗で電流を決める。
- 1826年の実験は、8本の銅線（2〜130インチ）と熱電対、ねじり秤。
- 1827年の本は広く読まれず、1841年にコプリーメダル。1881年に単位として採択。

## 訂正

前の想定を、次のように直した。

| 前の値 | 直した値 | 出典 |
|---|---|---|
| 1841年まで、誰も認めなかった | **1820年代後半から一部の物理学者は採用していた。1841年のコプリーメダルが最初の大きな公的評価** | `ethw-ohm` / `royal-society-ohm` |
| 1881年にオームと名付けられた | **1881年9月のパリ国際電気会議で実用単位として採択。名前の提案は1861年の BAAS にさかのぼる** | `ethw-si-units` |
| オームの法則はすべての物質に成り立つ | **オーム物質にのみ成り立つ。OpenStax も「not universally valid」と明記** | `openstax-ohms-law` |
| 抵抗は「流れにくさ」そのもの | **R = V/I で定義される量。物質の種類・長さ・断面積・温度で変わる** | `openstax-ohms-law` / `hyperphysics-tempcoef` |
| 電球の抵抗は一定 | **冷間と点灯で約5倍。測定例は13.9Ω→71.3Ω** | `ac-bordeaux-lamp` |

## 分からなかったこと

- 「web of naked fancies」は1913年の *Popular Science Monthly* に現れるが、批判者の名前と
  原文は特定できない。**台本では引用しない。**
- オームの1826年実験の電圧・電流の絶対値は、当時の単位と装置の校正に依存する。
  **現代のボルト・アンペアに換算した数値は台本で使わない。**
- 白熱電球の13.9Ω / 71.3Ω は、一つの電球の測定例。
  **すべての電球に当てはまる値として言わない。**
- オームの法則の「発見」の正確な日付は、1825年の予備論文、1826年の本論文、1827年の本で
  異なる。**台本では1826年の実験と1827年の本だけを言う。**
- 1881年のオームの定義（0℃の水銀柱）は、その後の国際会議で長さが確定した。
  **台本では「1881年に単位として採択」までにする。**
