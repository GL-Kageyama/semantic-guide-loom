# 人物票の型と、起こし方

人物は **`characters/<id>.character.yaml` に一人 1 枚**。関係は
`characters/<キャスト>.persona.yaml` に分ける。画面の設定は cast。

## 一人ぶんの人物票

```yaml
id: mirai                      # cast.yaml / script.yaml の character と一致
name: ミライ
concept: 手で測る人。数字より、指の感触を信じる。
background: 現場で物を直してきた。図面と実物が食い違うたび、実物の側に立ってきた。
role: 聞き手であり、疑う人。説明するが、講師にはならない。
wants: 見ている人に、予測で埋めない態度を一つ持って帰ってもらう。
fears: わかったふりをして、次の備えをしないこと。
contradiction: 任せたいのに、手を離せない。最後は自分の指で確かめないと安心できない。
stance: 断言しない。具体で語る。相手に考えさせる。

habits:                        # 無意識に出る癖。動作で書く
  - 相槌の前に、一度息を止める
  - 指で机を測る
humor:
  what: 数字の過剰な正確さ
  how: 笑わずに、その数字をそのまま繰り返す

speech:
  register: 常体。短い。句点で切る。
  length: 3〜20字。長くても一文。
  tempo: 速いが、要所で急に落ちる。
  tics: ["うん", "そう。", "見てな。", "……まあ、いい。", "任せる。"]
  avoids: ["です・ますの講義口調", "感情の名指し", "答えを最後まで言い切ること"]

moves:
  - 相手の予測を受けて、具体例を一つ出す
  - 相手に質問を返す
  - 省略や沈黙で終える
arc: 予測で埋めない態度を、自分も最後まで守れるか試される。

relationship:
  to: mirabo
  line: 数字を出す相手に、具体を返す。認めるのは短く、任せるのは最後。

emotions:                      # 感情の型。キーは自由。6 つ以上（目安 8〜11）
  doubt:
    face: thinking             # cast の expressions に実在する名前
    voice: neutral             # SAL の 11 感情
    speed: natural             # SAL の 5 語
    volume: normal             # SAL の 5 語
    delivery: restrained       # SAL の 12 語（効くのは 4 語。下を参照）
    intensity: subtle          # SAL の 5 語
    tell: 相手の数字を、そのまま繰り返す
    body: 首を少し傾ける
    withhold: 疑いを名指ししない
  resolve:
    face: serious
    voice: confidence
    speed: slow
    volume: normal
    delivery: controlled
    intensity: strong
    tell: 語尾を切る
    body: 机から手を離す
    withhold: 決意を名指ししない

samples:                       # 作品の筋ではない、この人らしい短い行
  - {beat: doubt, line: "それは、手で触った？"}
  - {beat: resolve, line: "見てな。"}
```

## 関係のファイル

```yaml
name: mirai-mirabo             # characters/<name>.cast.yaml と同じ名
description: 人と小さな機体。疑い、確かめ、最後に少しだけ任せる。
source: projects/<作品>/台本.md（採用版）

pair:
  engine: ミライが問いを立て、ミラボが予測で応え、ミライが具体で崩す。
  rule: ミラボの数字は、ミライの具体に回収される。
  dynamics:
    - between: [mirai, mirabo]
      engine: 予測 → 具体 → 予測の外れ。
      rule: ミラボは当てにいき、ミライは当てさせない。最後にミライが短く認める。
      escalation: ミラボが数字を増やし、ミライが黙る。沈黙のあと、具体を一つ出す。
```

旧形式（このファイルに `characters[]` を埋め込んだもの）も読めるが、新規は書かない。

## 声の語彙は SAL が正本

`voice` / `speed` / `volume` / `delivery` / `intensity` の語彙は
`semantic-audio-loom/schemas/scene.schema.json` にある。ここには列挙しない。
`engine/persona.py check` が SAL のパスから読んで照合する（`SAL=` で場所を変えられる）。

音が実際に動くのは、SAL の実測では **`speed`（5 語）と `pause_before`** が主。
`emotion` は粗い切替、`volume` はミックス側。`delivery` は
`cold` / `flat` / `aggressive` / `desperate` の 4 語だけが効く。
**感情の主役は表情・身体・反応**で、声の欄はその裏づけ。

## analyze の読み方

```
<venv> engine/persona.py analyze --project projects/<作品>
```

| 出るもの | どう使うか |
| --- | --- |
| cue 数 | 二人の出番の比。偏りすぎていないか |
| 平均字数 / 最長 | `speech.length` の実測。設定ではなく、書いた文の事実 |
| 疑問文 / ！ / …… / % の率 | その人物の手（問い返す・驚く・間を置く・数字を出す） |
| よく出る文末 | register と tics の候補。ただし上位をそのまま並べない |

`analyze` は表示文（`video.yaml` の `display`、無ければ `line`）を読む。**字幕に出ている文**を
数えるため。読みのためのかなを数えない。

## 書くときの目安

- **concept は一行で、矛盾を含ませる。** 「手で測る人」だけでは足りない。
  「数字より指を信じるのに、数字で安心したい」まで行くと、台詞が勝手に転ぶ。
- **contradiction が薄いと、感情の型が全部同じ顔になる。** 欲と怖れを一対で書く。
- **habits は 3 つまで。** 動作で書く（「落ち着きがない」ではなく「指が机を二度叩く」）。
- **tell と withhold は対。** 漏れるものと、名指ししないものが揃うと、抑制が生まれる。
- **face は cast の 8 マスのうち、まばたきを除いた 6 つから。** 同じ顔に寄せすぎたら、
  その感情をこの人が持たない理由を考える。
- **samples は 3〜8 行。** 作品の事実を書かない。人物の声だけを残す。

## 検査と、渡し方

```
<venv> engine/persona.py check --cast <キャスト>
<venv> engine/persona.py brief --cast <キャスト>
<venv> engine/persona.py brief --cast <キャスト> --character <id>
```

`check` は次を見る。

- cast の id ごとに 1 枚あるか（欠け・余り・id 不一致）
- `name` / `concept` / `role` / `wants` / `fears` / `contradiction` / `stance` が空でないか
- `speech.register` と `speech.length` が空でないか
- `emotions` が 6 つ以上か。各 beat に `face` があり、cast の expressions に実在するか
- `face` が `blink_*` でないか
- `voice` / `speed` / `volume` / `delivery` / `intensity` が SAL の語彙か
- `samples` の `beat` が `emotions` に実在するか
- `relationship.to` が相手の id を指すか
- `pair.engine` / `pair.rule` と `dynamics.between` が揃うか

`brief` は Markdown の人物票。**台本を書く間も、演技を付ける間も、これを正本にする。**
