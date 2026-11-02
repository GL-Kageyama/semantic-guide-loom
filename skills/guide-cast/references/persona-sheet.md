# persona.yaml の型と、起こし方

```yaml
name: mirai-mirabo            # characters/<name>.cast.yaml と同じ名
description: 人と小さな機体。疑い、確かめ、最後に少しだけ任せる。
source: projects/<作品>/台本.md（採用版）

pair:
  engine: ミライが問いを立て、ミラボが予測で応え、ミライが具体で崩す。
  rule: ミラボの数字は、ミライの具体に回収される。説明はミライ、現在地はミラボ。

characters:
  - id: mirai                 # cast.yaml と script.yaml の character と一致
    name: ミライ
    role: 聞き手であり、疑う人。説明するが、講師にはならない。
    wants: 見ている人に、予測で埋めない態度を一つ持って帰ってもらう。
    fears: わかったふりをして、次の備えをしないこと。
    stance: 断言しない。具体で語る。相手に考えさせる。
    speech:
      register: 常体。短い。句点で切る。
      length: 8〜25字。長くても一文。
      tics: ["うん", "そう。", "見てな。", "……まあ、いい。", "任せる。"]
      avoids: ["です・ますの講義口調", "感情の名指し（悲しい・怖い）", "答えを最後まで言い切ること"]
    moves:
      - 相手の予測を受けて、具体例を一つ出す
      - 相手に質問を返す
      - 省略や沈黙で終える
    arc: 予測で埋めない態度を、自分も最後まで守れるか試される。
```

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

- **role は「何をする人か」ではなく「何を守ろうとしている人か」。**
- **wants と fears は一対。** 欲しいものが、怖いものとぶつかるから場面が立つ。
- **tics は 3〜5 個。** それ以上は記号。台本で全部を使わなくてよい。
- **avoids は具体的に。** 「乱暴な言葉」より「感情の名指し（悲しい・怖い）」。
- **arc は一行。** 解説動画は変化が小さい。数字で守っていた人が、最後に数字なしで渡す、
  くらいの小ささでよい。

## 検査

```
<venv> engine/persona.py check --cast <キャスト>
<venv> engine/persona.py brief --cast <キャスト>   # guide-script に貼る人物票
```

`check` は cast と persona の id が揃うか、`role` / `speech.register` が空でないかを見る。
`brief` は Markdown の短い票。**台本を書く間は、この票を正本にする。**
